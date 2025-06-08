import streamlit as st
# Import the existing products and the new recommender system
from products import hot_path_top_movies, warm_path_movie_click_relevance, recommender_system, imdb_kpi_dashboard


# --- APP CONFIGURATION ---
st.set_page_config(
    page_title="Product Showcase",
    page_icon="🛍️",
    layout="wide"
)

# --- SIDEBAR NAVIGATION ---
st.sidebar.title("Our Products")

# A dictionary mapping product names to their main functions
PRODUCTS = {
    "Top 10 Movies (Hot Path)": hot_path_top_movies.main,
    "Movie Analytics (Warm Path)": warm_path_movie_click_relevance.main,
    "MovieLens Personalized Recommender": recommender_system.main,
    "IMDb KPI Dashboard": imdb_kpi_dashboard.main,  # New product added
}

# Create a list of product names for the selectbox
product_selection = st.sidebar.selectbox("Choose a Product", list(PRODUCTS.keys()))

# --- LOAD THE SELECTED PRODUCT'S FUNCTIONALITY ---
# Get the main function of the selected product and run it
page = PRODUCTS[product_selection]
page()