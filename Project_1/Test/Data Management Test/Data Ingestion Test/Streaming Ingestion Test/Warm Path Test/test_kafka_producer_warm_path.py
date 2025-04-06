import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../../../Python/Data_Management/Data_Ingestion/Streaming_Ingestion/Warm_path')))
import unittest
from unittest.mock import patch, MagicMock
from kafka_producer_warm_path import create_producer, near_real_time_processing  # type: ignore


class TestKafkaProducerWarmPath(unittest.TestCase):

    @patch('kafka_producer_warm_path.KafkaProducer')
    def test_create_producer(self, mock_kafka_producer):
        mock_instance = MagicMock()
        mock_kafka_producer.return_value = mock_instance

        producer = create_producer()
        self.assertEqual(producer, mock_instance)
        mock_kafka_producer.assert_called_once_with(
            bootstrap_servers='localhost:9092',
            value_serializer=unittest.mock.ANY
        )

    @patch('kafka_producer_warm_path.create_producer')
    @patch('kafka_producer_warm_path.time.sleep', return_value=None)  # skip actual sleeping
    @patch('kafka_producer_warm_path.np.random.randint')
    @patch('kafka_producer_warm_path.np.random.choice')
    def test_near_real_time_processing(self, mock_choice, mock_randint, mock_sleep, mock_create_producer):
        mock_producer = MagicMock()
        mock_create_producer.return_value = mock_producer

        mock_choice.side_effect = ['movie1', 'movie2'] * 500
        mock_randint.side_effect = [1, 2] * 500

        near_real_time_processing()

        self.assertEqual(mock_producer.send.call_count, 1000)
        mock_producer.close.assert_called_once()
        mock_create_producer.assert_called_once()
        mock_sleep.assert_called()  # Sleep should be called, but mocked

        # Verify structure of at least one message sent
        topic, value = mock_producer.send.call_args[0]
        self.assertEqual(topic, 'movie-click-rate')
        self.assertIn('movie_id', value)
        self.assertIn('clicks', value)

# Run tests
if __name__ == '__main__':
    unittest.main()
