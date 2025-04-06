from kafka import KafkaProducer
import json
import numpy as np
import os
import sys
import time
current_folder = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_folder)


# Function to create a Kakfa Producer to simulate warm path
def create_producer():
    producer = KafkaProducer(
        bootstrap_servers='localhost:9092',
        value_serializer=lambda v: json.dumps(v).encode('utf-8')
    )
    return producer


# Function to simulate a near real time processing minutely (it's possible to change at hourly) 
def near_real_time_processing():
    producer = create_producer()
    topic = 'movie-click-rate'
    movie_ids = ['movie1', 'movie2', 'movie3']

    for _ in range(1000):
        click_rate = {
            'movie_id': np.random.choice(movie_ids),
            'clicks': np.random.randint(1,5),
        }
        producer.send(topic, click_rate)
        time.sleep(1)

    producer.close()
