from kafka import KafkaConsumer
import json


def create_consumer():
    # Kafka consumer configuration
    consumer = KafkaConsumer(
        'user-reviews-topic',
        bootstrap_servers='localhost:9092',
        auto_offset_reset='earliest',
        value_deserializer=lambda m: json.loads(m.decode('utf-8'))
    )

    return consumer

def receive_messages():
    consumer = create_consumer()
    for message in consumer:
        print(f"Hot Path -> message received: {message.value}\n")

    consumer.close()
    return
