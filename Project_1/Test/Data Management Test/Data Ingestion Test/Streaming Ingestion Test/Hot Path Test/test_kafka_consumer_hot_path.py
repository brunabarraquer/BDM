import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../../../Python/Data_Management/Data_Ingestion/Streaming_Ingestion/Hot_path')))
import unittest
from unittest.mock import patch, MagicMock
from kafka_consumer_hot_path import create_consumer, receive_messages  # type: ignore


class TestKafkaConsumerHotPath(unittest.TestCase):

    @patch('consumer.KafkaConsumer')
    def test_create_consumer(self, mock_kafka_consumer):
        mock_instance = MagicMock()
        mock_kafka_consumer.return_value = mock_instance

        consumer = create_consumer()

        mock_kafka_consumer.assert_called_once_with(
            'user-reviews-topic',
            bootstrap_servers='localhost:9092',
            auto_offset_reset='earliest',
            value_deserializer=unittest.mock.ANY
        )
        self.assertEqual(consumer, mock_instance)

    @patch('consumer.KafkaConsumer')
    @patch('builtins.print')
    def test_receive_messages(self, mock_print, mock_kafka_consumer):
        # Mock KafkaConsumer instance and simulate incoming messages
        mock_instance = MagicMock()
        mock_instance.__iter__.return_value = [
            MagicMock(value={'user': 'Alice', 'review': 'Great!'}),
            MagicMock(value={'user': 'Bob', 'review': 'Not bad'})
        ]
        mock_kafka_consumer.return_value = mock_instance

        receive_messages()

        # Check that print was called with the mock messages
        mock_print.assert_any_call("Received: {'user': 'Alice', 'review': 'Great!'}")
        mock_print.assert_any_call("Received: {'user': 'Bob', 'review': 'Not bad'}")

        # Check consumer.close() was called
        mock_instance.close.assert_called_once()
