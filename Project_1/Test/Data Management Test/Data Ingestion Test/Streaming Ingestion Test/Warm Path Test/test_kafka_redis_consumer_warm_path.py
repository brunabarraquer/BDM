import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../../../Python/Data_Management/Data_Ingestion/Streaming_Ingestion/Warm_path')))
import unittest
from unittest.mock import patch, MagicMock
import json
from kafka_redis_consumer_warm_path import create_consumer, create_redis, store_in_buffer, get_buffer_data, receive_messages_minutely # type: ignore


class TestKafkaRedisConsumerWarmPath(unittest.TestCase):

    @patch('kafka_redis_consumer_warm_path.KafkaConsumer')
    def test_create_consumer(self, mock_kafka_consumer):
        mock_consumer_instance = MagicMock()
        mock_kafka_consumer.return_value = mock_consumer_instance

        consumer = create_consumer()
        self.assertEqual(consumer, mock_consumer_instance)
        mock_kafka_consumer.assert_called_once_with(
            'movie-click-rate',
            bootstrap_servers="localhost:9092",
            value_deserializer=unittest.mock.ANY,
            auto_offset_reset="earliest",
            enable_auto_commit=True
        )

    @patch('kafka_redis_consumer_warm_path.redis.Redis')
    def test_create_redis(self, mock_redis_class):
        mock_redis_instance = MagicMock()
        mock_redis_class.return_value = mock_redis_instance

        redis_client = create_redis()
        self.assertEqual(redis_client, mock_redis_instance)
        mock_redis_class.assert_called_once_with(host="localhost", port=6379, db=0)

    def test_store_in_buffer(self):
        mock_redis = MagicMock()
        data = {'movie_id': 1, 'clicks': 2}

        store_in_buffer(data, mock_redis)
        mock_redis.rpush.assert_called_once_with("warm_path_buffer", json.dumps(data))

    @patch('kafka_redis_consumer_warm_path.create_redis')
    def test_get_buffer_data(self, mock_create_redis):
        mock_redis = MagicMock()
        mock_create_redis.return_value = mock_redis
        fake_data = [
            json.dumps({'movie_id': 1, 'clicks': 2}).encode('utf-8'),
            json.dumps({'movie_id': 1, 'clicks': 3}).encode('utf-8'),
            json.dumps({'movie_id': 2, 'clicks': 5}).encode('utf-8')
        ]
        mock_redis.lrange.return_value = fake_data

        result = get_buffer_data()

        expected_result = {1: 5, 2: 5}
        self.assertEqual(result, expected_result)
        mock_redis.delete.assert_called_once_with("warm_path_buffer")

    @patch('kafka_redis_consumer_warm_path.create_consumer')
    @patch('kafka_redis_consumer_warm_path.create_redis')
    @patch('kafka_redis_consumer_warm_path.get_buffer_data')
    @patch('kafka_redis_consumer_warm_path.store_in_buffer')
    @patch('time.time')
    def test_receive_messages_minutely(self, mock_time, mock_store, mock_get_data, mock_create_redis, mock_create_consumer):
        mock_consumer = MagicMock()
        mock_redis = MagicMock()
        mock_create_consumer.return_value = mock_consumer
        mock_create_redis.return_value = mock_redis

        message1 = MagicMock(value={'movie_id': 1, 'clicks': 1})
        message2 = MagicMock(value={'movie_id': 2, 'clicks': 2})
        mock_consumer.__iter__.return_value = [message1, message2]

        # Simulate time passing
        mock_time.side_effect = [0, 30, 61, 62]  # 2nd loop triggers the minute check

        mock_get_data.return_value = {"mock": "data"}

        with patch('builtins.print') as mock_print:
            try:
                receive_messages_minutely()
            except StopIteration:
                pass  # expected to break early since infinite loop is not suited for unit test

            mock_store.assert_any_call(message1.value, mock_redis)
            mock_store.assert_any_call(message2.value, mock_redis)
            mock_get_data.assert_called()
            mock_print.assert_called_with("\033[38;5;214mWarm Path\033[0m -> get movies rellevance in a minute: {'mock': 'data'}\n")

# Run test suite
if __name__ == '__main__':
    unittest.main()
