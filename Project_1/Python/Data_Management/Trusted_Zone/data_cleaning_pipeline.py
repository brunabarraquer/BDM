import os
from pathlib import Path
import pyspark
from delta import *
from pyspark.sql.functions import (
    col, when, split, regexp_replace, regexp_extract, to_date, to_timestamp, round as pyspark_round, lower, isnan
)
from pyspark.sql.types import FloatType, IntegerType
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from utils import *

# Utility Functions

def replace_nulls(df, null_values=None):
    """Replaces null values in the DataFrame with None."""
    if null_values is None:
        null_values = ["NULL", "N/A", "n/a", "-", ""]
    return df.replace(null_values, None)

def replace_none_to_zero_columns(df, number_columns):
    for col_name in number_columns:
        df = df.fillna({col_name: 0})
    return df

def filter_out_nan_and_duplicates(df, cols):
    condition = None
    for c in cols:
        this_cond = col(c).isNotNull() & ~isnan(col(c))
        condition = this_cond if condition is None else condition & this_cond
    return df.filter(condition).dropDuplicates(cols)

def clean_percentage_columns(df, percentage_columns):
    """Cleans percentage columns by removing % symbol and converting to float."""
    for col_name in percentage_columns:
        df = df.withColumn(col_name, regexp_replace(col(col_name), "%", "").cast(FloatType()) / 100)
    return df

def clean_currency_columns(df, currency_columns):
    """Cleans currency columns by removing $ and , symbols."""
    for col_name in currency_columns:
        df = df.withColumn(col_name, regexp_replace(col(col_name), "[$,]", "").cast(FloatType()))
    return df


def clean_runtime_column(df, runtime_col="Runtime"):
    """Cleans the runtime column by extracting the numeric value.
    Assumes the runtime is in the format 'Xh Ym' or 'Xm'."""
    return df.withColumn(runtime_col, regexp_extract(runtime_col, r"(\d+)", 1).cast(IntegerType()))

def convert_to_date(df, col_name, fmt="dd MMM yyyy", new_col_name=None):
    if not new_col_name:
        new_col_name = col_name
    return df.withColumn(new_col_name, to_date(col_name, fmt))

def clean_response_column(df, response_col="Response"):
    """Cleans the response column by converting to boolean.
    Assumes the response is either 'True' or 'False'."""
    return df.withColumn(response_col, when(col(response_col) == "True", True).otherwise(False))

def split_array_columns(df, array_columns):
    for col_name in array_columns:
        df = df.withColumn(col_name, split(col(col_name), ",\\s*"))
    return df

def extract_awards_metrics(df, awards_col="Awards"):
    """Extracts awards wins and nominations from the awards column."""
    df = df.withColumn("Awards_Wins", regexp_extract(col(awards_col), r"(\d+)\s+win", 1).cast(IntegerType()))
    df = df.withColumn("Awards_Nominations", regexp_extract(col(awards_col), r"(\d+)\s+nomination", 1).cast(IntegerType()))
    return df

def round_float_columns(df, float_columns, precision=2):
    """Rounds float columns to the specified precision."""
    for col_name in float_columns:
        df = df.withColumn(col_name, pyspark_round(col(col_name), precision))
    return df

def lower_case_columns(df, columns):
    """Converts specified columns to lowercase."""
    for col_name in columns:
        df = df.withColumn(col_name, lower(col(col_name)))
    return df

def replace_column_values(df, columns, old_value, new_value):
    return df.select([
        when(col(c) == old_value, new_value).otherwise(col(c)).alias(c)
        for c in df.columns
    ])

# Cleaning Functions for Specific Datasets
def clean_ml_20m_tables(ml_tables):
    # genome_scores
    df = ml_tables['ml-20m_genome_scores']
    df = filter_out_nan_and_duplicates(df, ['movieId', 'tagId'])
    df = df.withColumn('relevance', pyspark_round(col('relevance'), 2))
    ml_tables['ml-20m_genome_scores'] = df

    # genome_tags
    df = ml_tables['ml-20m_genome_tags']
    df = filter_out_nan_and_duplicates(df, ['tagId'])
    ml_tables['ml-20m_genome_tags'] = df

    # link
    df = ml_tables['ml-20m_link']
    df = filter_out_nan_and_duplicates(df, ['movieId', 'imdbId', 'tmdbId'])
    ml_tables['ml-20m_link'] = df

    # movie
    df = ml_tables['ml-20m_movie']
    df = filter_out_nan_and_duplicates(df, ['movieId'])
    df = df.withColumn("genres", split(col("genres"), "\\|"))
    df = df.withColumn("year", regexp_extract(col("title"), r"\((\d{4})\)", 1))
    df = df.withColumn("title", regexp_replace(col("title"), r"\s*\(\d{4}\)", ""))
    ml_tables['ml-20m_movie'] = df

    # rating
    df = ml_tables['ml-20m_rating']
    df = filter_out_nan_and_duplicates(df, ['movieId', 'userId'])
    df = df.withColumn("timestamp", to_timestamp(col("timestamp")))
    df = df.withColumn("rating", col("rating").cast("float"))
    ml_tables['ml-20m_rating'] = df

    # tag
    df = ml_tables['ml-20m_tag']
    df = filter_out_nan_and_duplicates(df, ['userId', 'movieId'])
    ml_tables['ml-20m_tag'] = df

    return ml_tables

def clean_boxoffice_table(df):
    null_values = ["NULL", "N/A", "n/a", "-", ""]
    df = replace_nulls(df, null_values)
    df = filter_out_nan_and_duplicates(df, ['imdbID'])
    df = clean_percentage_columns(df, ["percentplus_minus_LW", "percentplus_minus_YD"])
    df = clean_currency_columns(df, ["Avg", "BoxOffice", "Daily", "To_Date"])
    df = clean_runtime_column(df, "Runtime")
    df = convert_to_date(df, "Release", "dd MMM yyyy", "ReleasedDate")
    df = clean_response_column(df, "Response")
    df = split_array_columns(df, ["Actors", "Genre", "Language", "Country", "Writer"])
    df = extract_awards_metrics(df, "Awards")
    float_columns = ["percentplus_minus_LW", "percentplus_minus_YD", "Avg", "BoxOffice", "Daily", "To_Date"]
    df = round_float_columns(df, float_columns, 2)
    numeric_columns = ['percentplus_minus_LW', 'percentplus_minus_YD', 'Avg', 'Daily', 'Days', 'Metascore', 'Runtime', 'TD', 'Theaters', 'YD', 'Year', 'imdbRating', 'imdbVotes', 'Awards_Wins', 'Awards_Nominations']
    df = replace_none_to_zero_columns(df, numeric_columns)
    return df

def clean_imbd_tables(imbd_tables):
    # name.basics

    df = imbd_tables['imbd_name.basics']
    df = replace_column_values(df, df.columns, '\\N', None)
    df = filter_out_nan_and_duplicates(df, ["nconst"])
    imbd_tables['imbd_name.basics'] = df

    # title.akas
    df = imbd_tables['imbd_title.akas']
    df = replace_column_values(df, df.columns, '\\N', None)
    df = filter_out_nan_and_duplicates(df, ['titleId'])
    # df = lower_case_columns(df, ["title", "region", "language"])
    imbd_tables['imbd_title.akas'] = df

    # title.basics
    df = imbd_tables['imbd_title.basics']
    df = replace_column_values(df, df.columns, '\\N', None)
    df = filter_out_nan_and_duplicates(df, ['tconst'])
    #df = lower_case_columns(df, ["genres"])
    df = df.withColumn("genres", split(col("genres"), "\\,"))
    imbd_tables['imbd_title.basics'] = df

    # title.crew
    df = imbd_tables['imbd_title.crew']
    df = replace_column_values(df, df.columns, '\\N', None)
    df = filter_out_nan_and_duplicates(df, ['tconst'])
    imbd_tables['imbd_title.crew'] = df

    # title.episode
    df = imbd_tables['imbd_title.episode']
    df = replace_column_values(df, df.columns, '\\N', None)
    df = filter_out_nan_and_duplicates(df, ['tconst'])
    df = df.filter(col("episodeNumber").isNotNull() & ~isnan(col("episodeNumber")) & col("seasonNumber").isNotNull() & ~isnan(col("seasonNumber")))
    imbd_tables['imbd_title.episode'] = df

    # title.principals
    df = imbd_tables['imbd_title.principals']
    df = replace_column_values(df, df.columns, '\\N', None)
    df = filter_out_nan_and_duplicates(df, ['tconst'])
    imbd_tables['imbd_title.principals'] = df

    # title.ratings
    df = imbd_tables['imbd_title.ratings']
    df = filter_out_nan_and_duplicates(df, ['tconst'])
    df = df.filter((col("averageRating") >= 0.0) & (col("numVotes") >= 0.0))
    df = df.select([
        when(col(c) == '\\N', 0).otherwise(col(c)).alias(c)
        for c in df.columns
    ])
    imbd_tables['imbd_title.ratings'] = df

    return imbd_tables

# At the top of the file (after all imports and function definitions)

def main_cleaning_pipeline(
    ml_delta_path='../../../Data Management/Landing Zone/Persistent Zone/ml-20m/',
    boxoffice_delta_path='../../../Data Management/Landing Zone/Persistent Zone/boxoffice/',
    imbd_delta_path='../../../Data Management/Landing Zone/Persistent Zone/imbd/',
    trusted_zone_base='../../../Data Management/Trusted Zone/'
):
    try:
        spark = get_spark_session()
        trusted_zone_base = Path(trusted_zone_base)
        trusted_zone_base.mkdir(parents=True, exist_ok=True)

        # --- MovieLens 20M ---
        ml_tables = load_delta_tables(ml_delta_path, spark)
        ml_tables = clean_ml_20m_tables(ml_tables)
        ml_trusted_path = Path(trusted_zone_base) / 'ml-20m'
        ml_trusted_path.mkdir(parents=True, exist_ok=True)
        ml_tables['ml-20m_genome_scores'].write.format('delta').mode('overwrite').save(str(ml_trusted_path / 'ml-20m_genome_scores'))
        ml_tables['ml-20m_genome_tags'].write.format('delta').mode('overwrite').save(str(ml_trusted_path / 'ml-20m_genome_tags'))
        ml_tables['ml-20m_link'].write.format('delta').mode('overwrite').save(str(ml_trusted_path / 'ml-20m_link'))
        ml_tables['ml-20m_movie'].write.format('delta').mode('overwrite').save(str(ml_trusted_path / 'ml-20m_movie'))
        ml_tables['ml-20m_rating'].write.format('delta').mode('overwrite').save(str(ml_trusted_path / 'ml-20m_rating'))
        ml_tables['ml-20m_tag'].write.format('delta').mode('overwrite').save(str(ml_trusted_path / 'ml-20m_tag'))

        # --- BoxOffice ---
        boxoffice_tables = load_delta_tables(boxoffice_delta_path, spark)
        boxoffice_df = clean_boxoffice_table(boxoffice_tables['boxoffice_movie_data'])
        boxoffice_trusted_path = Path(trusted_zone_base) / 'boxoffice'
        boxoffice_trusted_path.mkdir(parents=True, exist_ok=True)
        boxoffice_df.write.format('delta').mode('overwrite').save(str(boxoffice_trusted_path / 'boxoffice_movie_data'))

        # --- IMBD ---
        imbd_tables = load_delta_tables(imbd_delta_path, spark)
        imbd_tables = clean_imbd_tables(imbd_tables)
        imbd_trusted_path = Path(trusted_zone_base) / 'imbd'
        imbd_trusted_path.mkdir(parents=True, exist_ok=True)
        imbd_tables['imbd_name.basics'].write.format('delta').mode('overwrite').save(str(imbd_trusted_path / 'imbd_name_basics'))
        imbd_tables['imbd_title.akas'].write.format('delta').mode('overwrite').save(str(imbd_trusted_path / 'imbd_title_akas'))
        imbd_tables['imbd_title.basics'].write.format('delta').mode('overwrite').save(str(imbd_trusted_path / 'imbd_title_basics'))
        imbd_tables['imbd_title.crew'].write.format('delta').mode('overwrite').save(str(imbd_trusted_path / 'imbd_title_crew'))
        imbd_tables['imbd_title.episode'].write.format('delta').mode('overwrite').save(str(imbd_trusted_path / 'imbd_title_episode'))
        imbd_tables['imbd_title.principals'].write.format('delta').mode('overwrite').save(str(imbd_trusted_path / 'imbd_title_principals'))
        imbd_tables['imbd_title.ratings'].write.format('delta').mode('overwrite').save(str(imbd_trusted_path / 'imbd_title_ratings'))

        spark.stop()
    except Exception as e:
        print(f'Error: {e}')
        return False
    return True



# main_cleaning_pipeline()