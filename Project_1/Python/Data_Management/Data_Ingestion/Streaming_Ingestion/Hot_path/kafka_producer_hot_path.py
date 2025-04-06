from kafka import KafkaProducer
import json
import time
import random
import os
import sys
current_folder = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_folder)
from generate_reviews import generate_review_bank


# Function to create a Kafka Producer
def create_producer():
    producer = KafkaProducer(
        bootstrap_servers='localhost:9092',
        value_serializer=lambda v: json.dumps(v).encode('utf-8')
    )
    return producer


# Function to simulate a real time processing
def real_time_processing():    
    producer = create_producer()
    # Generate 1000 reviews randomly
    all_reviews = generate_review_bank(100)
    movies_id = ['movie1', 'movie2', 'movie3']
    topic = 'user-reviews-topic'

    for _ in all_reviews:
        review_data = {
            'timestamp': time.strftime("%Y-%m-%d %H:%M:%S"),
            'user_id': f"user_{random.randint(1000, 9999)}",
            'movie_id': random.choice(movies_id),
            'review': random.choice(all_reviews),
            'rating': random.randint(1, 5)  # Ratings from 1 to 5
        }

        producer.send(topic, review_data)
        # print(f"Sent: {review_data}")
        time.sleep(1)  # Send data every 1 second

    producer.close()
    return
