import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../../Python/Data_Management/Data_Ingestion/Batch_Ingestion')))
import unittest
from unittest.mock import patch, mock_open, MagicMock
import requests
from imbd_ingestion import download_file, unzip_file, imbd_ingestion  # type: ignore


class TestIMDBIngestion(unittest.TestCase):

    @patch("builtins.print")
    @patch("requests.get")
    def test_download_file_success(self, mock_get, mock_print):
        # Create a fake response object with iter_content
        mock_response = MagicMock()
        mock_response.iter_content = lambda chunk_size: [b'data1', b'data2']
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        with patch("builtins.open", mock_open()) as mock_file:
            download_file("http://fake-url.com/file.tsv.gz", "/fake/path/file.tsv.gz")
            mock_file().write.assert_any_call(b'data1')
            mock_file().write.assert_any_call(b'data2')
            mock_print.assert_called_with("Downloaded: /fake/path/file.tsv.gz")

    @patch("builtins.print")
    @patch("requests.get", side_effect=requests.exceptions.RequestException("Download error"))
    def test_download_file_failure(self, mock_get, mock_print):
        download_file("http://fake-url.com/fail.tsv.gz", "/fake/path/fail.tsv.gz")
        mock_print.assert_called_once_with("Error downloading http://fake-url.com/fail.tsv.gz: Download error")

    @patch("builtins.print")
    def test_unzip_file_success(self, mock_print):
        # Create a fake .gz file in memory
        fake_gz_path = "test.gz"
        fake_out_path = "unzipped.tsv"

        with patch("gzip.open", mock_open(read_data=b"compressed-data")) as mock_gz:
            with patch("builtins.open", mock_open()) as mock_out:
                with patch("os.remove") as mock_remove:
                    unzip_file(fake_gz_path, fake_out_path)
                    mock_out().write.assert_called()
                    mock_remove.assert_called_once_with(fake_gz_path)

    @patch("builtins.print")
    @patch("gzip.open", side_effect=OSError("Unzip failed"))
    def test_unzip_file_error(self, mock_gzip, mock_print):
        unzip_file("invalid.gz", "out.tsv")
        mock_print.assert_called_once_with("Error unzip: Unzip failed")

    @patch("imbd_ingestion.download_file")
    @patch("imbd_ingestion.unzip_file")
    @patch("builtins.print")
    def test_imbd_ingestion(self, mock_print, mock_unzip, mock_download):
        temp_path = "/mock/temp"
        imbd_ingestion(temp_path)

        self.assertEqual(mock_download.call_count, 7)
        self.assertEqual(mock_unzip.call_count, 7)
        mock_print.assert_any_call("All data ingested in the Temporal Folder")


if __name__ == "__main__":
    unittest.main()
