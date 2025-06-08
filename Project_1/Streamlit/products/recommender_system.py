import streamlit as st
import pandas as pd
import time
import os 
from pyspark.sql.functions import col

# --- Importing your custom modules with relative paths ---
try:
    from .utility_codes.user_based_recommender import UserToUser
    from .utility_codes.item_based_recommender import ItemToItem
    from .utility_codes.utils import split_users, get_spark_session
except ImportError as e:
    st.error(f"Failed to import necessary modules. Make sure all recommender scripts are in the 'products' directory. Error: {e}")
    st.stop()

# --- Data Loading and Caching ---
@st.cache_data(show_spinner="Loading and preparing recommender data...")
def load_data():
    """
    Loads data from Delta tables using Spark, preprocesses it, and splits it into
    training and validation sets. This function is cached for better performance.
    """
    try:
        # --- PATH CORRECTION ---
        # Make the path relative to THIS script file, not the execution directory.
        # This ensures the path works whether run directly or via Streamlit.
        script_dir = os.path.dirname(os.path.abspath(__file__))
        base_path = os.path.join(script_dir, '..', '..')
        exploit_path = os.path.join(base_path, 'Data Management', 'Exploitation Zone', 'ml-20m')
        
        # Normalize the path to resolve '..' and ensure it's in the correct format
        exploit_path = os.path.normpath(exploit_path)

        spark = get_spark_session(app_name="StreamlitRecommender")

        # Load ratings and movies using the corrected, unambiguous path
        ratings_df = spark.read.format('delta').load(os.path.join(exploit_path, "ml-20m_rating"))
        movies_df = spark.read.format('delta').load(os.path.join(exploit_path, 'ml-20m_movie'))

        # Filter ratings to a manageable size for the app
        ratings_df = ratings_df.filter(col('userId') <= 100)
        ratings = ratings_df.limit(10000).toPandas()

        # Get unique movieIds from the filtered ratings to load only relevant movies.
        movieIds = list(set(ratings['movieId']))
        
        # Filter movies.
        movies_df = movies_df.filter(col('movieId').isin(movieIds))
        movies = movies_df.toPandas()

        # Split data for training and validation.
        ratings_train, ratings_val = split_users(ratings, k=5)
        
        # Get a list of users available for recommendations.
        available_users = sorted(list(set(ratings_train["userId"].values)))
        
        spark.stop()
        return ratings_train, ratings_val, movies, available_users
    except Exception as e:
        # Return None and the error to be handled in the main app.
        return None, None, None, str(e)


def display_recommendations(recommender_name, recommendations, movies_df, similarity_score, top_k=10):
    """
    Formats and displays the recommendations and similarity score in a Streamlit table.
    """
    st.subheader(f"Results for: {recommender_name}")

    if not recommendations:
        st.warning("Could not generate recommendations for this user.")
        return

    # Prepare data for display.
    top_recs_ids = [rec[0] for rec in recommendations[:top_k]]
    
    display_data = []
    for movie_id in top_recs_ids:
        movie_info = movies_df.loc[movies_df['movieId'] == movie_id]
        if not movie_info.empty:
            display_data.append({
                "Movie Title": movie_info["title"].values[0],
                "Genres": ", ".join(movie_info["genres"].values[0]),
                "Tags" : ", ".join(movie_info["tags"].values[0][:10])
            })
    
    if not display_data:
        st.warning("Could not find details for the recommended movies.")
        return
        
    display_df = pd.DataFrame(display_data)

    # --- Display Results ---
    col1, col2 = st.columns([3, 1])
    with col1:
        st.write("Top Recommendations")
        st.table(display_df)
    with col2:
        st.metric(label="Validation Similarity", value=f"{similarity_score:.4f}")
        st.info("This score represents the cosine similarity between the genres of the user's validation movies and the genres of the recommended movies.")

def main():
    st.title("🎬 Personalized Movie Recommender")

    # --- Load Data ---
    ratings_train, ratings_val, movies, available_users_or_error = load_data()

    if isinstance(available_users_or_error, str):
        st.error(f"Failed to load data. Please check the Spark configuration and file paths. Error: {available_users_or_error}")
        return

    available_users = available_users_or_error
    st.markdown("Configure the recommender and get personalized movie suggestions below.")

    # --- Recommender Configuration in Main Panel ---
    st.header("🔧 Recommender Configuration")

    recommender_choice = st.selectbox(
        "Choose Recommender Type",
        ("User-to-User", "Item-to-Item", "Both")
    )

    target_user_idx = st.selectbox(
        "Choose a User ID",
        options=available_users
    )

    top_k = st.slider(
        "Number of recommendations",
        min_value=5, max_value=20, value=10
    )

    run_button = st.button("Get Recommendations")

    # --- Run Recommendations ---
    if run_button:
        with st.spinner(f"Running recommendations for User `{target_user_idx}`... This may take a moment."):
            start_time = time.time()
            users_idy = available_users

            if recommender_choice in ("User-to-User", "Both"):
                try:
                    user_recommender = UserToUser(ratings_train, movies, users_idy, k=top_k)
                    user_recs = user_recommender.user_based_recommender(target_user_idx)
                    user_sim = user_recommender.validation(ratings_val, target_user_idx)
                    display_recommendations("User-to-User Recommender", user_recs, movies, user_sim, top_k)
                except Exception as e:
                    st.error(f"User-to-User recommender error: {e}", icon="🚨")

            if recommender_choice in ("Item-to-Item", "Both"):
                try:
                    item_recommender = ItemToItem(ratings_train, movies, users_idy, k=top_k)
                    item_recs = item_recommender.item_based_recommender(target_user_idx)
                    item_sim = item_recommender.validation(ratings_val, target_user_idx)
                    display_recommendations("Item-to-Item Recommender", item_recs, movies, item_sim, top_k)
                except Exception as e:
                    st.error(f"Item-to-Item recommender error: {e}", icon="🚨")

            st.success(f"Completed in {time.time() - start_time:.2f} seconds.")
    else:
        st.info("Configure the settings above and click 'Get Recommendations'.")

    st.markdown("---")
    st.caption("🎬 Movies DataSources | MovieLens Recommender System | Powered by Streamlit")
