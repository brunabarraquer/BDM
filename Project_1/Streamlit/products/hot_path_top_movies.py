import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from kafka import KafkaConsumer
import json
import threading
import time
from collections import defaultdict, deque
from datetime import datetime
import queue
import subprocess
import os
import sys


class MovieAnalyzer:
    def __init__(self):
        self.movie_ratings = defaultdict(list)  # movie_id: [ratings]
        self.recent_reviews = deque(maxlen=50)  # Keep last 50 reviews
        self.consumer = None
        self.consumer_thread = None
        self.running = False
        self.data_queue = queue.Queue()
        
        # Producer management
        self.producer_process = None
        self.producer_running = False
        
        # Initialize with some sample data for immediate display
        self._initialize_sample_data()
    
    def _initialize_sample_data(self):
        """Initialize with sample data for immediate display"""
        sample_movies = {
            
        }
        
        for movie_id, ratings in sample_movies.items():
            self.movie_ratings[movie_id] = ratings
            
        # Add some sample reviews
        sample_reviews = []
        
        for review in sample_reviews:
            self.recent_reviews.append(review)
    
    def create_consumer(self):
        """Create Kafka consumer"""
        try:
            consumer = KafkaConsumer(
                'user-reviews-topic',
                bootstrap_servers='localhost:9092',
                auto_offset_reset='latest',  # Start from latest messages
                value_deserializer=lambda m: json.loads(m.decode('utf-8')),
                consumer_timeout_ms=1000  # Timeout after 1 second if no messages
            )
            return consumer
        except Exception as e:
            st.error(f"Failed to connect to Kafka: {e}")
            return None
    
    def consume_messages(self):
        """Background thread function to consume Kafka messages"""
        self.consumer = self.create_consumer()
        if not self.consumer:
            return
            
        try:
            while self.running:
                try:
                    # Poll for messages with timeout
                    messages = self.consumer.poll(timeout_ms=1000)
                    
                    for topic_partition, records in messages.items():
                        for message in records:
                            review_data = message.value
                            self.data_queue.put(review_data)
                            
                except Exception as e:
                    if self.running:  # Only log errors if we're still supposed to be running
                        st.error(f"Error consuming messages: {e}")
                    break
                    
        finally:
            if self.consumer:
                self.consumer.close()
    
    def process_new_data(self):
        """Process new data from the queue"""
        processed_any = False
        while not self.data_queue.empty():
            try:
                review_data = self.data_queue.get_nowait()
                
                # Update movie ratings
                movie_id = review_data['movie_id']
                rating = review_data['rating']
                self.movie_ratings[movie_id].append(rating)
                
                # Keep only last 100 ratings per movie to prevent memory issues
                if len(self.movie_ratings[movie_id]) > 100:
                    self.movie_ratings[movie_id] = self.movie_ratings[movie_id][-100:]
                
                # Add to recent reviews
                self.recent_reviews.append(review_data)
                
                processed_any = True
                
            except queue.Empty:
                break
            except Exception as e:
                st.error(f"Error processing review data: {e}")
        
        return processed_any
    
    def start_producer(self):
        """Start the Kafka producer in a separate process"""
        if not self.producer_running:
            try:
                # Try to import and run the producer function directly
                try:
                    producer_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../Python/Data_Management/Data_Ingestion/Streaming_Ingestion/Hot_Path/"))
                    sys.path.append(producer_dir)

                    from kafka_producer_hot_path import real_time_processing # type: ignore
                    
                    def run_producer():
                        try:
                            real_time_processing()
                        except Exception as e:
                            print(f"Producer error: {e}")
                    
                    self.producer_thread_process = threading.Thread(target=run_producer, daemon=True)
                    self.producer_thread_process.start()
                    self.producer_running = True
                    return True
                    
                except ImportError:
                    # Fallback: try to run as subprocess using wrapper script
                    scripts_to_try = ["producer_runner.py", "kafka_producer_hot_path.py"]
                    
                    for script in scripts_to_try:
                        if os.path.exists(script):
                            try:
                                self.producer_process = subprocess.Popen([
                                    sys.executable, script
                                ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                                self.producer_running = True
                                return True
                            except Exception as e:
                                continue
                    
                    st.error(f"❌ Could not find producer script. Please ensure 'kafka_producer_hot_path.py' is in the same directory. Check the directory: {producer_dir}")
                    return False
                        
            except Exception as e:
                st.error(f"❌ Failed to start producer: {e}")
                return False
        return True
    
    def stop_producer(self):
        """Stop the Kafka producer"""
        if self.producer_running:
            try:
                if hasattr(self, 'producer_process') and self.producer_process:
                    self.producer_process.terminate()
                    self.producer_process.wait(timeout=5)
                    self.producer_process = None
                
                self.producer_running = False
                return True
            except Exception as e:
                st.error(f"Error stopping producer: {e}")
                return False
        return True
    
    def is_producer_running(self):
        """Check if producer is still running"""
        if hasattr(self, 'producer_process') and self.producer_process:
            return self.producer_process.poll() is None
        return self.producer_running
    def start_consuming(self):
        """Start the consumer thread"""
        if not self.running:
            self.running = True
            self.consumer_thread = threading.Thread(target=self.consume_messages, daemon=True)
            self.consumer_thread.start()
    
    def stop_consuming(self):
        """Stop the consumer thread"""
        self.running = False
        if self.consumer_thread and self.consumer_thread.is_alive():
            self.consumer_thread.join(timeout=2)
    
    def get_top_movies(self, top_n=10):
        """Calculate top N movies by average rating"""
        movie_averages = {}
        
        for movie_id, ratings in self.movie_ratings.items():
            if ratings:  # Only include movies with ratings
                avg_rating = sum(ratings) / len(ratings)
                movie_averages[movie_id] = {
                    'average_rating': round(avg_rating, 2),
                    'total_reviews': len(ratings)
                }
        
        # Sort by average rating (descending) and take top N
        sorted_movies = sorted(
            movie_averages.items(), 
            key=lambda x: x[1]['average_rating'], 
            reverse=True
        )[:top_n]
        
        return sorted_movies
    
    def create_histogram(self):
        """Create histogram of top 10 movies"""
        top_movies = self.get_top_movies(10)
        
        if not top_movies:
            return go.Figure().add_annotation(
                text="No movie data available",
                x=0.5, y=0.5,
                xref="paper", yref="paper",
                showarrow=False
            )
        
        movie_ids = [movie[0] for movie in top_movies]
        avg_ratings = [movie[1]['average_rating'] for movie in top_movies]
        review_counts = [movie[1]['total_reviews'] for movie in top_movies]
        
        # Create bar chart with Plotly
        fig = go.Figure(data=[
            go.Bar(
                x=movie_ids,
                y=avg_ratings,
                text=[f"{rating}<br>({count} reviews)" for rating, count in zip(avg_ratings, review_counts)],
                textposition='auto',
                marker_color='lightblue',
                marker_line_color='darkblue',
                marker_line_width=1
            )
        ])
        
        fig.update_layout(
            title={
                'text': "Top 10 Movies by Average Rating",
                'x': 0.5,
                'xanchor': 'center',
                'font': {'size': 20}
            },
            xaxis_title="Movie ID",
            yaxis_title="Average Rating",
            yaxis=dict(range=[0, 5.5]),
            height=500,
            showlegend=False
        )
        
        return fig
    
    def get_recent_reviews_df(self):
        """Get recent reviews as DataFrame"""
        if not self.recent_reviews:
            return pd.DataFrame(columns=['Timestamp', 'User ID', 'Movie ID', 'Review', 'Rating'])
        
        reviews_list = list(self.recent_reviews)
        reviews_list.reverse()  # Show most recent first
        
        df = pd.DataFrame(reviews_list)
        df = df[['timestamp', 'user_id', 'movie_id', 'review', 'rating']]
        df.columns = ['Timestamp', 'User ID', 'Movie ID', 'Review', 'Rating']
        return df


# Initialize the analyzer (using Streamlit session state to persist across reruns)
if 'movie_analyzer' not in st.session_state:
    st.session_state.movie_analyzer = MovieAnalyzer()

analyzer = st.session_state.movie_analyzer


def main():
    """Main function for the Top 10 Movies real-time analysis"""
    st.title("🎬 Real-Time Movie Analysis - Hot Path")
    st.markdown("---")
    
    # Control panel for Producer and Consumer
    st.subheader("🎛️ Control Panel")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**📤 Producer Control**")
        producer_col1, producer_col2 = st.columns(2)
        
        with producer_col1:
            if st.button("▶️ Start Producer", key="start_producer"):
                if analyzer.start_producer():
                    st.success("✅ Producer started!")
                    time.sleep(1)
                    st.rerun()
        
        with producer_col2:
            if st.button("⏹️ Stop Producer", key="stop_producer"):
                if analyzer.stop_producer():
                    st.success("⏹️ Producer stopped!")
                    time.sleep(1)
                    st.rerun()
        
        # Producer status
        producer_status = "🟢 Running" if analyzer.producer_running and analyzer.is_producer_running() else "🔴 Stopped"
        st.markdown(f"**Status:** {producer_status}")
    
    with col2:
        st.markdown("**📥 Consumer Control**")
        consumer_col1, consumer_col2 = st.columns(2)
        
        with consumer_col1:
            if st.button("▶️ Start Consumer", key="start_consumer"):
                if not analyzer.producer_running:
                    st.warning("⚠️ Please start the producer first!")
                else:
                    analyzer.start_consuming()
                    st.success("✅ Consumer started!")
                    time.sleep(1)
                    st.rerun()
        
        with consumer_col2:
            if st.button("⏹️ Stop Consumer", key="stop_consumer"):
                analyzer.stop_consuming()
                st.success("⏹️ Consumer stopped!")
                time.sleep(1)
                st.rerun()
        
        # Consumer status
        consumer_status = "🟢 Connected" if analyzer.running else "🔴 Disconnected"
        st.markdown(f"**Status:** {consumer_status}")
    
    # Additional controls
    st.markdown("---")
    col1, col2, col3 = st.columns([2, 2, 2])
    
    with col1:
        if st.button("🔄 Refresh Data"):
            st.rerun()
    
    with col2:
        if st.button("🗑️ Clear Data"):
            analyzer.movie_ratings.clear()
            analyzer.recent_reviews.clear()
            analyzer._initialize_sample_data()
            st.success("Data cleared and reset!")
            time.sleep(1)
            st.rerun()
    
    with col3:
        auto_refresh = st.checkbox("Auto-refresh (5s)", value=True)
    
    # Instructions
    if not analyzer.producer_running and not analyzer.running:
        st.info("""
        🚀 **Getting Started:**
        1. Click "Start Producer" to begin generating movie reviews
        2. Click "Start Consumer" to start analyzing the data in real-time
        3. Watch the charts and reviews update automatically!
        """)
    
    analyzer.process_new_data()

    st.markdown("---")
    
    # Top 10 Movies Histogram
    st.subheader("📊 Top 10 Movies by Average Rating")
    
    fig = analyzer.create_histogram()
    st.plotly_chart(fig, use_container_width=True)
    
    # Statistics
    top_movies = analyzer.get_top_movies(10)
    if top_movies:
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Best Movie", top_movies[0][0], f"⭐ {top_movies[0][1]['average_rating']}")
        with col2:
            total_reviews = sum(movie[1]['total_reviews'] for movie in top_movies)
            st.metric("Total Reviews", total_reviews)
        with col3:
            st.metric("Movies Analyzed", len(analyzer.movie_ratings))
    
    st.markdown("---")
    
    # Recent Reviews Section
    st.subheader("💬 Recent User Reviews")
    
    reviews_df = analyzer.get_recent_reviews_df()
    
    if not reviews_df.empty:
        st.dataframe(
            reviews_df,
            use_container_width=True,
            height=400,
            column_config={
                "Rating": st.column_config.NumberColumn(
                    "Rating",
                    help="User rating (1-5 stars)",
                    min_value=1,
                    max_value=5,
                    format="⭐ %d"
                ),
                "Review": st.column_config.TextColumn(
                    "Review",
                    help="User review text",
                    max_chars=100
                )
            }
        )
        
        # Review statistics
        if len(reviews_df) > 0:
            col1, col2, col3 = st.columns(3)
            with col1:
                avg_rating = reviews_df['Rating'].mean()
                st.metric("Average Rating", f"{avg_rating:.2f} ⭐")
            with col2:
                st.metric("Recent Reviews", len(reviews_df))
            with col3:
                rating_dist = reviews_df['Rating'].value_counts().sort_index()
                most_common = rating_dist.index[-1]
                st.metric("Most Common Rating", f"{most_common} ⭐")
    else:
        st.info("📝 No reviews available yet. Start the real-time analysis or generate some sample data!")

    st.markdown("---")
    st.caption("🎬 Movies DataSources | Top Movies (Hot Path) | Powered by Streamlit")
    
    # Auto-refresh mechanism - this will now correctly rerun the script after
    # the UI has been drawn.
    if auto_refresh and analyzer.running:
        time.sleep(5)
        st.rerun()
    # --- FIX ENDS HERE ---


if __name__ == "__main__":
    main()