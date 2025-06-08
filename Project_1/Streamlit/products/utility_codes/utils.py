import pandas as pd
import numpy as np
import sklearn.model_selection 
import pyspark
from delta import *
from pyspark.sql.functions import col

def split_users(ratings: object , k: int = 5) -> tuple: 
    """
    Splits user ratings into training and validation sets.
    
    Args:
        ratings (DataFrame): The input ratings DataFrame containing "userId" column.
        k (int): The number of ratings to include in the validation set for each user.
    
    Returns:
        Tuple of DataFrames: Two DataFrames, the first containing training data, and the second containing validation data.
    """
    # ratings_train, rating_validation = [], []
        
    # for idx, ratings_users in ratings.groupby("userId"):
    #     ratings_users = ratings_users.sample(frac=1, random_state=42)
    #     rating_validation.append(ratings_users.iloc[:k]) # First top k rows
    #     ratings_train.append(ratings_users.iloc[k:]) # Remaining M-k rows
    # return pd.concat(ratings_train), pd.concat(rating_validation)
    
    train, val = sklearn.model_selection.train_test_split(ratings, test_size= 0.2, random_state=42)
    return train, val


def matrix_genres(movies: object) -> dict: 
    """
      Generate a binary movie-genre matrix from a DataFrame of movie information.
    
      This function takes a DataFrame containing movie information, extracts the genres associated with each movie,
      and generates a binary matrix representing the presence or absence of each genre for each movie.
    
      Args:
          movies (pd.DataFrame): A DataFrame containing movie information, including 'movieId' and 'genres' columns.
    
      Returns:
          pd.DataFrame: A binary movie-genre matrix where rows represent movies (indexed by 'movieId'),
                       and columns represent unique genres. Each cell in the matrix contains 1 if the movie belongs to
                       the genre, and 0 otherwise.
    """
    # Create a dictionary where keys are movieIds and values are sets of genres
    dict_movies = {movie["movieId"]: set(movie["genres"]) for _, movie in movies.iterrows()}
         
    unique_genres = set.union(*dict_movies.values())

    # Populate the DataFrame matrix with 1s for the genres each movie belongs to
    matrix = pd.DataFrame(np.zeros([len(dict_movies.keys()), len(unique_genres)]), 
                          columns=list(unique_genres), index=list(dict_movies.keys()))
    
    for idx_movie, genres in dict_movies.items():
        for genre in genres: matrix.loc[idx_movie, genre] = 1
     
    return matrix


'''
Calculate the cosinu similarity between two movies genres
'''
def cosinuSimilarity(validationMoviesGenres, recommendsMoviesGenres):

    # Compute the TF-IDF for each movie genres set
    genres1 = toTfIdf(validationMoviesGenres)
    genres2 = toTfIdf(recommendsMoviesGenres)

    genres1 = sorted(genres1, key = lambda x:x[0])
    genres2 = sorted(genres2, key = lambda x:x[0])
    i = 0
    j = 0
    d1 = 0
    d2 = 0
    sum = 0
    while (i < len(genres1) and j < len(genres2)):
        if (genres1[i][0] == genres2[j][0]):
            d1 += genres1[i][1]*genres1[i][1]
            d2 += genres2[j][1]*genres2[j][1]
            sum += genres1[i][1]*genres2[j][1]
            i += 1
            j += 1
        elif (genres1[i][0] < genres2[j][0]):
            d1 += genres1[i][1]*genres1[i][1]
            i += 1
        else:
            d2 += genres2[j][1]*genres2[j][1]
            j += 1

    while (i < len(genres1)):
        d1 += genres1[i][1]*genres1[i][1]
        i += 1
    while (j < len(genres2)):
        d2 += genres2[j][1]*genres2[j][1]
        j += 1
        
    if (np.sqrt(d1)*np.sqrt(d2) == 0): return 0
    return sum/(np.sqrt(d1)*np.sqrt(d2))


'''
Compute the TF-IDF for a set of movie genres
'''
def toTfIdf(moviesGenre):
    moviesCount = moviesGenre.shape[0]
    genresTotal = moviesGenre.sum()
    maxGenre = genresTotal.max()
    toTfIdf = genresTotal/maxGenre * np.log2(moviesCount/genresTotal)
    toTfIdf = toTfIdf/((toTfIdf**2).sum())
    
    indexs = toTfIdf.index.tolist()
    values = toTfIdf.values.tolist()
    result = []
    for i in range(len(indexs)):
        if (np.isnan(values[i])): result.append((indexs[i], 0))
        else: result.append((indexs[i], values[i]))
    return result

'''
Validation of the movies genres for the comparation with recommender models
'''
def validationMoviesGenres(datasetMovies, ratings_val, target_user_idx):
    matrixmpa_genres = matrix_genres(datasetMovies)
    validationMovies = ratings_val['movieId'].loc[ratings_val['userId'] == target_user_idx].values.tolist()
    validationMoviesGenres = matrixmpa_genres.loc[validationMovies]
    return matrixmpa_genres, validationMoviesGenres


def get_spark_session(app_name="LocalDeltaTable"):
    builder = pyspark.sql.SparkSession.builder.appName(app_name) \
        .config("spark.sql.extensions", "io.delta.sql.DeltaSparkSessionExtension") \
        .config("spark.sql.catalog.spark_catalog", "org.apache.spark.sql.delta.catalog.DeltaCatalog") \
        .config("spark.driver.memory", "8g") \
        .config("spark.executor.memory", "6g") \
        .config("spark.memory.offHeap.enabled", "true") \
        .config("spark.memory.offHeap.size", "2g") \
        .config("spark.sql.shuffle.partitions", "10") \
        .config("spark.network.timeout", "800s") \
        .config("spark.executor.heartbeatInterval", "400s") \
        .config("spark.driver.maxResultSize", "4g") \
        .config("spark.kryoserializer.buffer.max", "1g") \
        .config("spark.sql.broadcastTimeout", "600") \
        .config("spark.rpc.message.maxSize", "512")
    return configure_spark_with_delta_pip(builder).getOrCreate()