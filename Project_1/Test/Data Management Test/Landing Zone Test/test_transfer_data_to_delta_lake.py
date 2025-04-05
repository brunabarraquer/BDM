import unittest
from unittest.mock import patch, MagicMock, call
from pathlib import Path
import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../Python/Data_Management/Landing_Zone')))

# Import the functions to test
from transfer_data_to_delta_lake import clean_column_names, start_spark, transfer_data_to_delta_lake, create_delta_tables # type: ignore

class TestCreateDeltaTables(unittest.TestCase):
    
    def setUp(self):
        # Create some paths for testing
        self.temp_path = Path("/fake/temporal/path")
        self.persist_path = Path("/fake/persistent/path")
        
    @patch("pyspark.sql.DataFrame")
    def test_clean_column_names(self, mock_df):
        # Setup mock DataFrame with problematic column names
        mock_df.columns = ["column name", "value%", "error±range"]
        mock_df.withColumnRenamed = MagicMock(return_value=mock_df)
        
        # Call the function
        result = clean_column_names(mock_df)
        # Check the function made correct calls to withColumnRenamed
        mock_df.withColumnRenamed.assert_has_calls([
            call("column name", "column_name"),
            call("value%", "valuepercent"),
            call("error±range", "errorplus_minusrange")
        ])
        
        # Verify result is as expected
        self.assertEqual(result, mock_df)
    

    @patch("pyspark.sql.SparkSession.builder")
    @patch("transfer_data_to_delta_lake.configure_spark_with_delta_pip")
    def test_start_spark(self, mock_configure, mock_builder):
        # Setup mocks
        mock_session = MagicMock()
        mock_configured = MagicMock()
        mock_configured.getOrCreate.return_value = mock_session
        mock_config = MagicMock()
        mock_config.config.return_value = mock_config
        mock_builder.appName.return_value = mock_config
        mock_configure.return_value = mock_configured
        
        # Call the function
        result = start_spark()
        
        # Verify correct methods were called
        mock_builder.appName.assert_called_once_with("LocalDeltaTable")
        mock_config.config.assert_has_calls([
            call("spark.sql.extensions", "io.delta.sql.DeltaSparkSessionExtension"),
            call("spark.sql.catalog.spark_catalog", "org.apache.spark.sql.delta.catalog.DeltaCatalog")
        ])
        mock_configure.assert_called_once_with(mock_config)
        mock_configured.getOrCreate.assert_called_once()
        
        # Verify result
        self.assertEqual(result, mock_session)
    
    @patch("os.listdir")
    @patch("os.path.join")
    def test_transfer_data_to_delta_lake(self, mock_join, mock_listdir):
        # Setup mocks
        mock_spark = MagicMock()
        mock_df = MagicMock()
        mock_spark.read.format.return_value.option.return_value.option.return_value.load.return_value = mock_df
        mock_spark.read.format.return_value.option.return_value.load.return_value = mock_df
        mock_df.write.format.return_value.mode.return_value.option.return_value.save = MagicMock()
        mock_df.write.format.return_value.mode.return_value.save = MagicMock()
        
        # Setup test files
        mock_listdir.return_value = ["source1_data.csv", "source2_data.tsv", "source3_data.json"]
        mock_join.side_effect = lambda path, filename: str(path) + "/" + filename
        
        # Create a version of Path.mkdir that can be mocked
        with patch.object(Path, "mkdir") as mock_mkdir:
            # Call the function
            transfer_data_to_delta_lake(mock_spark, self.temp_path, self.persist_path)
            
            # Verify Path.mkdir calls
            self.assertEqual(mock_mkdir.call_count, 3)
            mock_mkdir.assert_has_calls([
                call(parents=True, exist_ok=True),
                call(parents=True, exist_ok=True),
                call(parents=True, exist_ok=True)
            ])
        
        # Verify dataframe operations for each file type
        # CSV file
        mock_spark.read.format.assert_any_call("csv")
        mock_df.write.format.assert_any_call("delta")
        mock_df.write.format.return_value.mode.assert_any_call("overwrite")
        
        # TSV file
        mock_spark.read.format.assert_any_call("csv")
        mock_df.write.format.assert_any_call("delta")
        
        # JSON file
        mock_spark.read.format.assert_any_call("json")
        mock_df.write.format.assert_any_call("delta")
        mock_df.write.format.return_value.mode.return_value.option.assert_called_with("mergeSchema", True)
    
    @patch("transfer_data_to_delta_lake.start_spark")
    @patch("transfer_data_to_delta_lake.transfer_data_to_delta_lake")
    def test_create_delta_tables(self, mock_transfer, mock_start_spark):
        # Setup mocks
        mock_spark = MagicMock()
        mock_start_spark.return_value = mock_spark
        
        # Call the function
        create_delta_tables(self.temp_path, self.persist_path)
        
        # Verify correct methods were called
        mock_start_spark.assert_called_once()
        mock_transfer.assert_called_once_with(mock_spark, self.temp_path, self.persist_path)


if __name__ == "__main__":
    unittest.main()