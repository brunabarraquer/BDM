import streamlit as st
import pandas as pd
import altair as alt
import pyspark
from pyspark.sql import SparkSession
import logging
from pathlib import Path
from typing import Tuple, Optional, List
import gc

from delta import configure_spark_with_delta_pip

# Configuration
class Config:
    BASE_PATH = Path("../Data Management/Exploitation Zone/imbd/").resolve()
    KPI_MOVIE_PARQUET = BASE_PATH / "movie_episode_ratings_kpi_parquet"
    KPI_PEOPLE_PARQUET = BASE_PATH / "people_movies_kpi_parquet"
    DELTA_MOVIE_PATH = BASE_PATH / "movie_episode_ratings_kpi"
    DELTA_PEOPLE_PATH = BASE_PATH / "people_movies_kpi"
    
    # Display columns for better performance
    DISPLAY_COLUMNS = ["originalTitle", "startYear", "genres", "total_episodes", "trend", "score"]
    PEOPLE_DISPLAY_COLUMNS = ["person_name", "avg_rating", "num_titles"]
    
    # Spark configuration optimized for better performance
    SPARK_CONFIG = {
        "spark.sql.extensions": "io.delta.sql.DeltaSparkSessionExtension",
        "spark.sql.catalog.spark_catalog": "org.apache.spark.sql.delta.catalog.DeltaCatalog",
        "spark.driver.memory": "8g",
        "spark.executor.memory": "6g",
        "spark.memory.offHeap.enabled": "true",
        "spark.memory.offHeap.size": "2g",
        "spark.sql.shuffle.partitions": "10",
        "spark.network.timeout": "800s",
        "spark.executor.heartbeatInterval": "400s",
        "spark.driver.maxResultSize": "4g",
        "spark.kryoserializer.buffer.max": "1g",
        "spark.sql.broadcastTimeout": "600",
        "spark.rpc.message.maxSize": "512"
    }

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@st.cache_resource
def get_spark_session(app_name: str = "LocalDeltaTable") -> SparkSession:
    """Create and cache Spark session"""
    try:
        builder = pyspark.sql.SparkSession.builder.appName(app_name)
        for key, value in Config.SPARK_CONFIG.items():
            builder = builder.config(key, value)
        return configure_spark_with_delta_pip(builder).getOrCreate()
    except Exception as e:
        logger.error(f"Failed to create Spark session: {e}")
        raise

def convert_delta_to_parquet() -> Tuple[bool, str]:
    """Convert Delta tables to Parquet format with better error handling"""
    spark = None
    try:
        spark = get_spark_session()
        
        # Check if source Delta tables exist
        if not Config.DELTA_MOVIE_PATH.exists():
            return False, f"Delta table not found: {Config.DELTA_MOVIE_PATH}"
        if not Config.DELTA_PEOPLE_PATH.exists():
            return False, f"Delta table not found: {Config.DELTA_PEOPLE_PATH}"
        
        # Convert movie/episode ratings KPI
        logger.info("Converting movie ratings KPI...")
        kpi = spark.read.format("delta").load(str(Config.DELTA_MOVIE_PATH))
        kpi.write.format("parquet").mode("overwrite").save(str(Config.KPI_MOVIE_PARQUET))
        
        # Convert people KPI
        logger.info("Converting people KPI...")
        kpi_people = spark.read.format("delta").load(str(Config.DELTA_PEOPLE_PATH))
        kpi_people.write.format("parquet").mode("overwrite").save(str(Config.KPI_PEOPLE_PARQUET))
        
        return True, "Delta tables successfully converted to Parquet format!"
        
    except Exception as e:
        logger.error(f"Error converting tables: {e}")
        return False, f"Error converting tables: {str(e)}"
    finally:
        if spark:
            spark.stop()

@st.cache_data(ttl=3600)  # Cache for 1 hour
def load_data(path: Path) -> Optional[pd.DataFrame]:
    """Load data from Parquet files with caching, error handling, and data limiting"""
    try:
        if path.exists():
            logger.info(f"Loading data from {path}")
            # Load only first N rows for better performance
            df = pd.read_parquet(path)
            logger.info(f"Loaded {len(df)} records")
            return df
        else:
            logger.warning(f"Path does not exist: {path}")
            return None
    except Exception as e:
        logger.error(f"Error loading data from {path}: {e}")
        st.error(f"Error loading data: {e}")
        return None

def process_genres(genres_input) -> List[str]:
    """Process genres string into list"""
    try:
        # Handle pandas Series, numpy arrays, or scalar values
        if hasattr(genres_input, 'iloc'):
            # If it's a pandas Series, get the first element
            genres_str = genres_input.iloc[0] if len(genres_input) > 0 else None
        else:
            genres_str = genres_input
        
        # Convert to string and check for null/empty values
        if pd.isna(genres_str):
            return []
        
        genres_str = str(genres_str).strip()
        if not genres_str or genres_str.lower() == 'nan':
            return []
            
        return [g.strip() for g in genres_str.split(",") if g.strip()]
    except Exception as e:
        logger.error(f"Error processing genres: {e}")
        return []

@st.cache_data(hash_funcs={pd.DataFrame: lambda x: str(x.shape)})
def get_genre_options(df: pd.DataFrame) -> Tuple[List[str], List[str]]:
    """Extract and cache genre options"""
    try:
        # Process all genres efficiently
        all_genres = []
        for genres_str in df["genres"].dropna():
            all_genres.extend(genres_str)
        all_genres = list(set(all_genres))

        if all_genres:
            genre_counts = pd.Series(all_genres).value_counts()
            top5_genres = genre_counts.head(5).index.tolist()
            all_unique_genres = sorted(genre_counts.index.tolist())
            return all_unique_genres, top5_genres
        else:
            return [], []
    except Exception as e:
        logger.error(f"Error processing genres: {e}")
        return [], []

def apply_filters(df: pd.DataFrame, selected_years: List[int], selected_genres: List[str]) -> pd.DataFrame:
    """Apply filters efficiently with better error handling"""
    try:
        filtered = df.copy()
        
        if selected_years:
            # Ensure startYear is numeric and handle NaN values
            filtered = filtered[filtered["startYear"].isin(selected_years)]
        
        if selected_genres:
            # Create a more efficient and safer genre filter
            filtered = filtered[filtered["genres"].notnull()]
            filtered = filtered[filtered["genres"].apply(lambda genre_list: any(g in genre_list for g in selected_genres))]
        
        return filtered
    except Exception as e:
        logger.error(f"Error applying filters: {e}")
        return df  # Return original dataframe if filtering fails

def create_kpi_metrics(filtered_df: pd.DataFrame):
    """Create KPI metrics section"""
    st.subheader("📈 Key Performance Indicators")
    
    kpi_col1, kpi_col2, kpi_col3, kpi_col4 = st.columns(4)
    
    # Calculate metrics
    avg_rating = filtered_df['averageRating'].mean()
    total_votes = filtered_df['numVotes'].sum()
    episodes_count = len(filtered_df)
    trendy_episodes = filtered_df['trend'].sum()
    
    kpi_col1.metric("⭐ Average Rating", f"{avg_rating:.2f}")
    kpi_col2.metric("🗳️ Total Votes", f"{total_votes:,}")
    kpi_col3.metric("🎬 Title", f"{episodes_count:,}")
    kpi_col4.metric("🔥 Trendy Title", f"{trendy_episodes:,}")

def create_visualization(filtered_df: pd.DataFrame):
    """Create visualization section"""
    st.subheader("📊 Data Visualization")
    
    x_axis = st.selectbox("Select X-axis", ["genres", "startYear"])
    
    if x_axis == "genres":
        genre_df = filtered_df[Config.DISPLAY_COLUMNS].dropna(subset=['genres']).copy()
        genre_df = genre_df.assign(genre=genre_df['genres']).explode("genre")
        chart = alt.Chart(genre_df).mark_bar().encode(
            x=alt.X("genre:N", title="Genre"),
            y=alt.Y("score:Q", title="Total Score", aggregate="sum")
        ).properties(width=700)
    else:
        chart = alt.Chart(filtered_df).mark_bar().encode(
            x=alt.X("startYear:O", title="Year"),
            y=alt.Y("score:Q", title="Total Score", aggregate="sum")
        ).properties(width=700)
    st.altair_chart(chart, use_container_width=True)

def create_people_analytics(kpi_people: pd.DataFrame):
    """Create people analytics section"""
    st.subheader("👨‍💻 People Analytics")
    
    # More efficient filtering
    actors_mask = kpi_people['category'].str.contains('actor', na=False) & kpi_people['id_person'].notnull()
    directors_mask = (kpi_people['category'] == 'director') & kpi_people['id_person'].notnull()
    
    actors = kpi_people[actors_mask].nlargest(10, "avg_rating")
    directors = kpi_people[directors_mask].nlargest(10, "avg_rating")
    
    people_col1, people_col2 = st.columns(2)
    
    with people_col1:
        st.markdown("#### 🎭 Top 10 Actors by Rating")
        if not actors.empty:
            st.dataframe(
                actors[Config.PEOPLE_DISPLAY_COLUMNS], 
                use_container_width=True,
                height=400
            )
        else:
            st.info("No actor data available.")
    
    with people_col2:
        st.markdown("#### 🎬 Top 10 Directors by Rating")
        if not directors.empty:
            st.dataframe(
                directors[Config.PEOPLE_DISPLAY_COLUMNS], 
                use_container_width=True,
                height=400
            )
        else:
            st.info("No director data available.")

def main():
    """Main function for the IMDB KPI Dashboard"""

    # Page header
    st.title("🎬 IMDb KPI Dashboard")
    st.markdown("---")
    
    # Data pipeline status with performance info
    st.subheader("📊 Data Pipeline Status")
    
    # Check and convert data if needed
    if not Config.KPI_MOVIE_PARQUET.exists() or not Config.KPI_PEOPLE_PARQUET.exists():
        st.info("🔄 Converting Delta tables to Parquet format...")
        with st.spinner("Processing data pipeline..."):
            success, message = convert_delta_to_parquet()
            if success:
                st.success("✅ " + message)
            else:
                st.error("❌ " + message)
                st.stop()
    else:
        st.success("✅ Data pipeline ready - Parquet files found!")
    
    # Load data with user-defined limits
    with st.spinner("Loading data..."):
        df = load_data(Config.KPI_MOVIE_PARQUET)
        kpi_people = load_data(Config.KPI_PEOPLE_PARQUET)
    
    if df is None:
        st.error("Failed to load movie data. Please check the data pipeline.")
        st.stop()
    
    # Filters Section
    st.subheader("🎛️ Filters")
    
    filter_col1, filter_col2 = st.columns(2)
    
    with filter_col1:
        years = sorted(df["startYear"].dropna().unique())
        selected_years = st.multiselect(
            "📅 Select Year(s)", 
            years, 
            default=years[-5:] if len(years) >= 5 else years,
            help="Choose the years you want to analyze"
        )
    
    with filter_col2:
        genres, top5_genres = get_genre_options(df)
        selected_genres = st.multiselect(
            "🎭 Select Genre(s)", 
            genres, 
            default=top5_genres,
            help="Choose the genres you want to analyze"
        )
    
    # Apply filters
    filtered_df = apply_filters(df, selected_years, selected_genres)
    
    st.markdown("---")
    

    # Create sections
    create_kpi_metrics(filtered_df)
    
    st.markdown("---")
    
    # Data Table
    st.subheader("📋 Filtered Data Table")
    if not filtered_df.empty:
        st.dataframe(filtered_df[Config.DISPLAY_COLUMNS], use_container_width=True, height=400)
    else:
        st.info("No data matches the selected filters.")

    # Data Export
    st.subheader("💾 Data Export")
    export_col1, export_col2 = st.columns([3, 1])
    
    with export_col1:
        st.info(f"Export {len(filtered_df):,} filtered records to CSV format")
    
    with export_col2:
        if not filtered_df.empty:
            csv = filtered_df[Config.DISPLAY_COLUMNS].to_csv(index=False).encode()
            st.download_button(
                "📥 Download CSV", 
                csv, 
                "filtered_movies.csv", 
                "text/csv",
                type="primary"
            )
    
    
    st.markdown("---")
    
    # # Visualization
    if not filtered_df.empty:
        create_visualization(filtered_df)
        st.markdown("---")
    
    # People Analytics
    if kpi_people is not None and not kpi_people.empty:
        create_people_analytics(kpi_people)
        st.markdown("---")
    
    # Data Summary
    st.subheader("📊 Data Summary")
    
    summary_col1, summary_col2 = st.columns(2)
    
    with summary_col1:
        st.markdown("**📈 Dataset Overview:**")
        st.write(f"• Total records loaded: **{len(df):,}**")
        st.write(f"• Filtered records: **{len(filtered_df):,}**")
        if not df.empty:
            st.write(f"• Year range: **{df['startYear'].min()} - {df['startYear'].max()}**")
        if kpi_people is not None:
            st.write(f"• People records loaded: **{len(kpi_people):,}**")
    
    with summary_col2:
        st.markdown("**⭐ Rating Statistics:**")
        st.write(f"• Average rating: **{df['averageRating'].mean():.2f}**")
        st.write(f"• Highest rated: **{df['averageRating'].max():.2f}**")
        st.write(f"• Lowest rated: **{df['averageRating'].min():.2f}**")
        st.write(f"• Total votes: **{df['numVotes'].sum():,}**")
    
    # Memory cleanup
    gc.collect()
    
    # Footer
    st.markdown("---")
    st.caption("🎬 Movies DataSources | IMDb Analytics Dashboard | Powered by Streamlit")

if __name__ == "__main__":
    main()