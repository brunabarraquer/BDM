import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../../../Python/Data_Management/Data_Ingestion/Streaming_Ingestion/Hot_path')))
import unittest
from unittest.mock import patch, MagicMock, call
from  kafka_producer_hot_path import create_producer, start_streaming  # type: ignore


class TestKafkaProducerHotPath(unittest.TestCase):

    @patch('kafka_producer.KafkaProducer')
    def test_create_producer(self, mock_kafka_producer):
        mock_instance = MagicMock()
        mock_kafka_producer.return_value = mock_instance

        producer = create_producer()

        mock_kafka_producer.assert_called_once_with(
            bootstrap_servers='localhost:9092',
            value_serializer=unittest.mock.ANY
        )
        self.assertEqual(producer, mock_instance)

    @patch('kafka_producer.generate_review_bank')
    @patch('kafka_producer.KafkaProducer')
    @patch('kafka_producer.time.sleep', return_value=None)  # prevent real sleep
    def test_start_streaming(self, mock_sleep, mock_kafka_producer, mock_generate_reviews):
        # Setup mock return values
        mock_producer_instance = MagicMock()
        mock_kafka_producer.return_value = mock_producer_instance
        mock_generate_reviews.return_value = ['Great movie!', 'Bad plot', 'Loved it!']

        start_streaming()

        # Verify producer is created
        mock_kafka_producer.assert_called_once()

        # Verify reviews were sent for each generated review
        self.assertEqual(mock_producer_instance.send.call_count, len(mock_generate_reviews.return_value))

        # Each call should be to the correct topic with a dict payload
        for call_args in mock_producer_instance.send.call_args_list:
            topic, message = call_args[0]
            self.assertEqual(topic, 'user-reviews-topic')
            self.assertIsInstance(message, dict)
            self.assertIn('timestamp', message)
            self.assertIn('user_id', message)
            self.assertIn('movie_id', message)
            self.assertIn('review', message)
            self.assertIn('rating', message)

        # Verify close was called
        mock_producer_instance.close.assert_called_once()
