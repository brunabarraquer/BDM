import unittest
from unittest.mock import patch,  call
import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../../Python/Data_Management/Data_Ingestion/Batch_Ingestion')))
from ml_20m_ingestion import ml_20m_dataset_ingestion  # type: ignore


class TestML20MDatasetIngestion(unittest.TestCase):

    @patch('ml_20m_ingestion.kagglehub.dataset_download', return_value="/fake/dataset_path")
    @patch('ml_20m_ingestion.os.listdir')
    @patch('ml_20m_ingestion.os.rename')
    @patch('ml_20m_ingestion.os.path.isfile', return_value=True)
    @patch('ml_20m_ingestion.shutil.move')
    def test_full_ingestion_success(self, mock_move, mock_isfile, mock_rename, mock_listdir, mock_kaggle_download):
        # Use side_effect to simulate the directory listing before and after renaming
        mock_listdir.side_effect = [
            ["ratings.csv", "movies.csv"],  # Before renaming
            ["ml-20m_ratings.csv", "ml-20m_movies.csv"]  # After renaming, before move
        ]
        # Run the ingestion function
        ml_20m_dataset_ingestion("/fake/temporal_folder")

        # Validate Kaggle download
        mock_kaggle_download.assert_called_once_with("grouplens/movielens-20m-dataset")

        # Validate renaming
        mock_rename.assert_has_calls([
            call("/fake/dataset_path\\ratings.csv", "/fake/dataset_path\\ml-20m_ratings.csv"),
            call("/fake/dataset_path\\movies.csv", "/fake/dataset_path\\ml-20m_movies.csv")
        ], any_order=True)

        # Validate moving
        mock_move.assert_has_calls([
            call('/fake/dataset_path\\ml-20m_ratings.csv', '/fake/temporal_folder\\ml-20m_ratings.csv'),
            call("/fake/dataset_path\\ml-20m_movies.csv", "/fake/temporal_folder\\ml-20m_movies.csv")
        ], any_order=True)

    @patch('ml_20m_ingestion.kagglehub.dataset_download', side_effect=Exception("API error"))
    def test_kaggle_download_failure(self, mock_download):
        ml_20m_dataset_ingestion("/fake/temporal_folder")
        mock_download.assert_called_once()

    @patch('ml_20m_ingestion.kagglehub.dataset_download', return_value="/fake/dataset_path")
    @patch('ml_20m_ingestion.os.listdir', return_value=["ratings.csv"])
    @patch('ml_20m_ingestion.os.rename', side_effect=Exception("Rename error"))
    def test_rename_failure(self, mock_rename, mock_listdir, mock_download):
        ml_20m_dataset_ingestion("/fake/temporal_folder")
        mock_rename.assert_called_once()

    @patch('ml_20m_ingestion.kagglehub.dataset_download', return_value="/fake/dataset_path")
    @patch('ml_20m_ingestion.os.listdir', side_effect=[["ratings.csv"], ["ml-20m_ratings.csv"]])
    @patch('ml_20m_ingestion.os.rename')
    @patch('ml_20m_ingestion.os.path.isfile', return_value=True)
    @patch('ml_20m_ingestion.shutil.move', side_effect=Exception("Move error"))
    def test_move_failure(self, mock_move, mock_isfile, mock_rename, mock_listdir, mock_download):
        ml_20m_dataset_ingestion("/fake/temporal/folder")
        mock_move.assert_called_once()
        
if __name__ == "__main__":
    unittest.main()
