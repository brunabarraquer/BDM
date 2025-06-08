import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from kafka import KafkaConsumer, KafkaProducer
import json
import threading
import time
from collections import defaultdict
import queue
from datetime import datetime, timedelta
import numpy as np

# --- Producer Code (Integrated from your snippet) ---

def create_producer():
    """Creates a Kafka Producer to simulate the warm path."""
    return KafkaProducer(
        bootstrap_servers='localhost:9094',
        value_serializer=lambda v: json.dumps(v).encode('utf-8')
    )

def near_real_time_processing(stop_event):
    """
    Simulates near-real-time processing by sending movie click rates
    to Kafka until the stop event is set.
    """
    producer = create_producer()
    topic = 'movie-click-rate'
    movies_ids = [f"movie{i}" for i in range(1, 21)]  # movie1 to movie20

    while not stop_event.is_set():
        click_rate = {
            'movie_id': np.random.choice(movies_ids),
            'clicks': np.random.randint(1, 5),
        }
        # print(f"\033[33mWarm Path Producer\033[0m -> Sent: {click_rate}")
        producer.send(topic, click_rate)
        time.sleep(1) # Sends one message per second

    print("\033[31mWarm Path Producer\033[0m -> Stopped.")
    producer.close()


# --- Streamlit Application ---

class MovieClickAnalyzer:
    """
    Analyzes movie click data from Kafka, displaying the top 10 movies
    by clicks in a one-minute, resetting window.
    """
    def __init__(self):
        self.movie_clicks = defaultdict(int)
        self.last_reset_time = datetime.now()
        self.data_queue = queue.Queue()

        # Consumer state
        self.consumer_thread = None
        self.consumer_running = False

        # Producer state
        self.producer_thread = None
        self.producer_running = False
        self.producer_stop_event = threading.Event()


    def create_consumer(self):
        """Creates a Kafka consumer for the warm path topic."""
        try:
            consumer = KafkaConsumer(
                'movie-click-rate', # Topic for movie clicks
                bootstrap_servers='localhost:9094',
                auto_offset_reset='latest',
                value_deserializer=lambda m: json.loads(m.decode('utf-8')),
                consumer_timeout_ms=1000
            )
            return consumer
        except Exception as e:
            st.error(f"Failed to connect to Kafka on 'localhost:9094': {e}")
            return None

    def consume_messages(self):
        """Background thread function to consume Kafka messages."""
        consumer = self.create_consumer()
        if not consumer:
            return

        while self.consumer_running:
            try:
                for message in consumer:
                    if message and message.value:
                        self.data_queue.put(message.value)
                time.sleep(0.1)
            except Exception as e:
                if self.consumer_running:
                    st.error(f"Error consuming messages: {e}")
                break
        consumer.close()


    def process_new_data(self):
        """Processes data from the queue and resets clicks every minute."""
        if datetime.now() - self.last_reset_time >= timedelta(hours=1):
            self.movie_clicks.clear()
            self.last_reset_time = datetime.now()
            st.info("Minute elapsed. Click counts have been reset.")

        while not self.data_queue.empty():
            try:
                click_data = self.data_queue.get_nowait()
                movie_id = click_data.get('movie_id')
                clicks = click_data.get('clicks', 0)
                if movie_id:
                    self.movie_clicks[movie_id] += clicks # Aggregate clicks
            except queue.Empty:
                break
            except Exception as e:
                st.error(f"Error processing click data: {e}")


    def start_producer(self):
        """Starts the Kafka producer in a separate thread."""
        if not self.producer_running:
            self.producer_stop_event.clear()
            self.producer_thread = threading.Thread(
                target=near_real_time_processing,
                args=(self.producer_stop_event,),
                daemon=True
            )
            self.producer_thread.start()
            self.producer_running = True


    def stop_producer(self):
        """Stops the Kafka producer thread."""
        if self.producer_running:
            self.producer_stop_event.set()
            if self.producer_thread:
                self.producer_thread.join(timeout=2)
            self.producer_running = False


    def start_consuming(self):
        """Starts the consumer thread."""
        if not self.consumer_running:
            self.consumer_running = True
            self.consumer_thread = threading.Thread(target=self.consume_messages, daemon=True)
            self.consumer_thread.start()


    def stop_consuming(self):
        """Stops the consumer thread."""
        self.consumer_running = False
        if self.consumer_thread:
            self.consumer_thread.join(timeout=2)


    def get_top_movies_by_clicks(self, top_n=10):
        """Calculates the top N movies based on click counts."""
        sorted_movies = sorted(
            self.movie_clicks.items(),
            key=lambda item: item[1],
            reverse=True
        )
        return sorted_movies[:top_n]


    def create_bar_chart(self):
        """Creates a Plotly bar chart of the top 10 movies."""
        top_movies = self.get_top_movies_by_clicks(10)

        if not top_movies:
            return go.Figure().add_annotation(
                text="Waiting for movie click data...",
                x=0.5, y=0.5, xref="paper", yref="paper", showarrow=False
            )

        movie_ids = [movie[0] for movie in top_movies]
        clicks = [movie[1] for movie in top_movies]

        fig = go.Figure(data=[
            go.Bar(
                x=movie_ids,
                y=clicks,
                text=clicks,
                textposition='auto',
                marker_color='lightcoral',
                marker_line_color='darkred',
                marker_line_width=1.5
            )
        ])
        fig.update_layout(
            title={
                'text': "Top 10 Movies by Clicks (Resets Every Hour)",
                'x': 0.5, 'xanchor': 'center', 'font': {'size': 20}
            },
            xaxis_title="Movie ID",
            yaxis_title="Total Clicks",
            height=500
        )
        return fig


# Use Streamlit's session state to persist the analyzer object
if 'movie_click_analyzer' not in st.session_state:
    st.session_state.movie_click_analyzer = MovieClickAnalyzer()

analyzer = st.session_state.movie_click_analyzer


def main():
    """Main function to run the Streamlit application."""
    st.title("📈 Real-Time Movie Click Analysis - Warm Path")
    st.markdown("---")

    # --- Control Panel ---
    st.subheader("🎛️ Control Panel")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**📤 Producer Control**")
        
        # Create two columns for horizontal button layout
        btn_col1, btn_col2 = st.columns(2)
        
        with btn_col1:
            if st.button("▶️ Start Producer", key="start_producer", disabled=analyzer.producer_running):
                analyzer.start_producer()
                st.success("✅ Producer started!")
                time.sleep(1)
                st.rerun()
        
        with btn_col2:
            if st.button("⏹️ Stop Producer", key="stop_producer", disabled=not analyzer.producer_running):
                analyzer.stop_producer()
                st.success("⏹️ Producer stopped!")
                time.sleep(1)
                st.rerun()
        
        producer_status = "🟢 Running" if analyzer.producer_running else "🔴 Stopped"
        st.markdown(f"**Status:** {producer_status}")

    with col2:
        st.markdown("**📥 Consumer Control**")
        # Create two columns for horizontal button layout
        btn_col3, btn_col4 = st.columns(2)

        with btn_col3:
            if st.button("▶️ Start Consumer", key="start_consumer", disabled=analyzer.consumer_running):
                analyzer.start_consuming()
                st.success("✅ Consumer started!")
                time.sleep(1)
                st.rerun()

        with btn_col4:
            if st.button("⏹️ Stop Consumer", key="stop_consumer", disabled=not analyzer.consumer_running):
                analyzer.stop_consuming()
                st.success("⏹️ Consumer stopped!")
                time.sleep(1)
                st.rerun()
        consumer_status = "🟢 Connected" if analyzer.consumer_running else "🔴 Disconnected"
        st.markdown(f"**Status:** {consumer_status}")

    # --- Data Display ---
    st.markdown("---")
    analyzer.process_new_data()

    st.subheader("📊 Top 10 Movies by Clicks in the Current Hour")


    # Countdown timer for the next reset
    time_left = max(0, 3600 - int((datetime.now() - analyzer.last_reset_time).total_seconds()))
    minutes, seconds = divmod(time_left, 60)
    st.progress(time_left / 3600)
    st.info(f"Click counts will reset in **{minutes} minutes and {seconds} seconds**.")

    fig = analyzer.create_bar_chart()
    st.plotly_chart(fig, use_container_width=True)

    # Display raw data
    st.subheader("📋 Raw Click Data")
    if analyzer.movie_clicks:
        clicks_df = pd.DataFrame(
            analyzer.movie_clicks.items(),
            columns=['Movie ID', 'Total Clicks']
        ).sort_values(by='Total Clicks', ascending=False).reset_index(drop=True)
        st.dataframe(clicks_df, use_container_width=True)
    else:
        st.write("No clicks recorded in the current minute.")

    st.markdown("---")
    st.caption("🎬 Movies DataSources | Movie Click Relevance (Warm Path) | Powered by Streamlit")

    # Auto-refresh mechanism
    if analyzer.producer_running:
        time.sleep(2)
        st.rerun()

if __name__ == "__main__":
    main()