from kafka import KafkaConsumer
import json


# Function to create a Kafka Consumer
def create_consumer():
    # Kafka consumer configuration
    consumer = KafkaConsumer(
        'user-reviews-topic',
        bootstrap_servers='localhost:9092',
        auto_offset_reset='earliest',
        value_deserializer=lambda m: json.loads(m.decode('utf-8'))
    )
    return consumer


# Function to connect to the Kafka Consumer and receive messages sent by Kafka Producer
def receive_messages():
    consumer = create_consumer()
    for message in consumer:
        print(f"\033[31mHot Path\033[0m -> message received: {message.value}\n") 

    consumer.close()
    return
