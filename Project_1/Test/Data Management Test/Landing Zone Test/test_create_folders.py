import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../Python/Data_Management/Landing_Zone')))
import unittest
from pathlib import Path
from unittest.mock import patch, call, MagicMock
from create_folders import create_folders  # type: ignore


class TestCreateFolders(unittest.TestCase):

    @patch("pathlib.Path.mkdir")
    @patch("builtins.print")
    def test_successful_folder_creation(self, mock_print, mock_mkdir):
        """Test that folders are created successfully"""
        # Mock project path
        project_path = Path("/fake/project/root")
        
        # Call the function
        create_folders(project_path)
        
        # Expected folder paths that should be created
        temporal_folder = project_path / "Data Management" / "Landing Zone" / "Temporal Zone"
        persistent_folder = project_path / "Data Management" / "Landing Zone" / "Persistent Zone"
        
        # Verify mkdir was called exactly twice (once for each folder)
        self.assertEqual(mock_mkdir.call_count, 2)
        
        # Verify mkdir was called with the correct parameters for both folders
        mock_mkdir.assert_has_calls([
            call(parents=True, exist_ok=True),
            call(parents=True, exist_ok=True)
        ], any_order=True)
        
        # Verify success message was printed
        mock_print.assert_called_with('All folders created successfully !!!')

    @patch("pathlib.Path.mkdir")
    @patch("builtins.print")
    def test_error_handling(self, mock_print, mock_mkdir):
        """Test error handling when folder creation fails"""
        # Mock project path
        project_path = Path("/fake/project/root")
        
        # Set up mock to raise an exception
        mock_mkdir.side_effect = PermissionError("Access denied")
        
        # Call the function (should not raise exception due to try/except)
        create_folders(project_path)
        
        # Verify error was printed
        mock_print.assert_any_call("error ocurred: Access denied")
        
        # Verify mkdir was called at least once
        mock_mkdir.assert_called()
        

    @patch("pathlib.Path.mkdir")
    @patch("builtins.print")
    def test_first_folder_fails_second_succeeds(self, mock_print, mock_mkdir):
        """Test when first folder creation fails but second succeeds"""
        # Mock project path
        project_path = Path("/fake/project/root")
        
        # Set up mock to raise an exception only on first call
        mock_mkdir.side_effect = [PermissionError("Access denied"), None]
        
        # Call the function
        create_folders(project_path)
        
        # Verify mkdir was called twice (tried to create both folders)
        self.assertEqual(mock_mkdir.call_count, 1)
        
        # Verify error was printed
        mock_print.assert_any_call("error ocurred: Access denied")
        

    @patch("pathlib.Path.mkdir")
    @patch("builtins.print")
    def test_both_folders_fail(self, mock_print, mock_mkdir):
        """Test when both folder creations fail"""
        # Mock project path
        project_path = Path("/fake/project/root")
        
        # Set up mock to raise different exceptions for each call
        mock_mkdir.side_effect = [
            PermissionError("Access denied"), 
            FileExistsError("File exists")
        ]
        
        # Call the function
        create_folders(project_path)
        
        # Verify mkdir was called twice (tried to create both folders)
        self.assertEqual(mock_mkdir.call_count, 1)
        
        mock_print.assert_any_call("error ocurred: Access denied")

if __name__ == "__main__":
    unittest.main()
