import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../../Python/Data_Management/Data_Ingestion/Batch_Ingestion')))
import unittest
from unittest.mock import patch, mock_open
from datetime import datetime, timedelta
from boxoffice_ingestion import boxOffice_daily_ingestion # type: ignore


class TestBoxOfficeIngestion(unittest.TestCase):
    
    def setUp(self):
        # Create test data
        self.temporal_folder = "/fake/temporal_folder"
        self.expected_date = (datetime.today() - timedelta(days=2)).strftime('%Y-%m-%d')
        self.expected_file_path = f"{self.temporal_folder}\\boxoffice_movie_data.json"
        
        # Sample box office data for mocking
        self.sample_data = {
            "date": self.expected_date,
            "movies": [
                {
                    "rank": 1,
                    "title": "Test Movie 1",
                    "gross": 10000000,
                    "theaters": 3500
                },
                {
                    "rank": 2,
                    "title": "Test Movie 2",
                    "gross": 8000000,
                    "theaters": 3200
                }
            ]
        }

    @patch('boxoffice_ingestion.BoxOffice')
    @patch('os.makedirs')
    @patch('builtins.open', new_callable=mock_open)
    @patch('json.dump')
    @patch('builtins.print')
    def test_successful_ingestion(self, mock_print, mock_json_dump, mock_file_open, mock_makedirs, mock_box_office_class):
        # Set up BoxOffice API mock
        mock_box_office_instance = mock_box_office_class.return_value
        mock_box_office_instance.get_daily.return_value = self.sample_data
        
        # Call the function
        boxOffice_daily_ingestion(self.temporal_folder)
        
        # Verify BoxOffice was initialized with correct API key
        mock_box_office_class.assert_called_once_with(api_key="46f1c1bd")
        
        # Verify API was called with correct date
        mock_box_office_instance.get_daily.assert_called_once_with(self.expected_date)
        
        # Verify directory was created
        mock_makedirs.assert_called_once_with(self.temporal_folder, exist_ok=True)
        
        # Verify file was opened for writing
        mock_file_open.assert_called_once_with(self.expected_file_path, "w", encoding="utf-8")
        
        # Verify data was written correctly
        mock_json_dump.assert_called_once()
        args, kwargs = mock_json_dump.call_args
        self.assertEqual(args[0], self.sample_data)  # First arg should be our data
        self.assertEqual(kwargs['indent'], 4)  # Check indent parameter
        
        # Verify success message was printed
        mock_print.assert_called_once_with('All data ingested in the Temporal Folder')

    @patch('boxoffice_ingestion.BoxOffice')
    @patch('builtins.print')
    def test_api_exception_handling(self, mock_print, mock_box_office_class):
        # Set up BoxOffice API mock to raise exception
        mock_box_office_instance = mock_box_office_class.return_value
        mock_box_office_instance.get_daily.side_effect = Exception("API Error")
        
        # Call the function
        boxOffice_daily_ingestion(self.temporal_folder)
        
        # Verify error message was printed
        mock_print.assert_called_once_with("Failed to fetch box office data: API Error")

    @patch('boxoffice_ingestion.BoxOffice')
    @patch('os.makedirs')
    @patch('builtins.print')
    def test_directory_creation_error(self, mock_print, mock_makedirs, mock_box_office_class):
        # Set up mock API response
        mock_box_office_instance = mock_box_office_class.return_value
        mock_box_office_instance.get_daily.return_value = self.sample_data
        
        # Make directory creation fail
        mock_makedirs.side_effect = PermissionError("Access denied")
        
        # Call the function
        boxOffice_daily_ingestion(self.temporal_folder)
        
        # Verify error message was printed
        mock_print.assert_called_once_with("Failed to fetch box office data: Access denied")

    @patch('boxoffice_ingestion.BoxOffice')
    @patch('os.makedirs')
    @patch('builtins.open')
    @patch('builtins.print')
    def test_file_write_error(self, mock_print, mock_open, mock_makedirs, mock_box_office_class):
        """Test handling of file writing errors"""
        # Set up mock API response
        mock_box_office_instance = mock_box_office_class.return_value
        mock_box_office_instance.get_daily.return_value = self.sample_data
        
        # Make file opening fail
        mock_open.side_effect = IOError("File write error")
        
        # Call the function
        boxOffice_daily_ingestion(self.temporal_folder)
        
        # Verify error message was printed
        mock_print.assert_called_once_with("Failed to fetch box office data: File write error")

if __name__ == "__main__":
    unittest.main()