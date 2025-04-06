from kafka import KafkaConsumer
import json
import time
import redis
import redis.client


# Function to create a Kafka Consumer for warm path
def create_consumer():
    # Initialize Kafka Consumer
    consumer = KafkaConsumer(
        'movie-click-rate',
        bootstrap_servers="localhost:9092",
        value_deserializer=lambda m: json.loads(m.decode('utf-8')),
        auto_offset_reset="earliest",
        enable_auto_commit=True
    )

    return consumer


# Functio to create a temporal storage using Redis
def create_redis():
    # Connect to Redis (Temporary Storage)
    redis_client = redis.Redis(host="localhost", port=6379, db=0)
    return redis_client


# Store in Buffer (Simulate a warm path)
def store_in_buffer(data, redis_client):
    redis_client.rpush("warm_path_buffer", json.dumps(data))


# Retrieve & Clear Buffer
def get_buffer_data():

    redis_client = create_redis()

    buffer_data = redis_client.lrange("warm_path_buffer", 0, -1)
    movie_clicks = {}
    for item in buffer_data:
        data = json.loads(item)

        if data['movie_id'] in movie_clicks:
            movie_clicks[data['movie_id']] += data['clicks']
        else:
            movie_clicks[data['movie_id']] = data['clicks']

    redis_client.delete('warm_path_buffer')
    return movie_clicks


# Function that receive messages from Kafka Producer and store temporaly in buffer until has passed a minute
def receive_messages_minutely():
    # Start Timer
    start_time = time.time()
    consumer = create_consumer()
    redis_client = create_redis()

    # Process Stream
    for message in consumer:
        store_in_buffer(message.value, redis_client)

        # Check if 1 hour passed
        if time.time() - start_time >= 60:
            batch_data = get_buffer_data()
            print(f"\033[38;5;214mWarm Path\033[0m -> get movies rellevance in a minute: {batch_data}\n")
            start_time = time.time()  # Reset Timer

    consumer.close()
    redis_client.close()
