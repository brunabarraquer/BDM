import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))
from Python.Data_Management.Data_Ingestion.Batch_Ingestion.imbd_ingestion import imbd_ingestion
from Python.Data_Management.Data_Ingestion.Batch_Ingestion.ml_20m_ingestion import ml_20m_dataset_ingestion
from Python.Data_Management.Data_Ingestion.Batch_Ingestion.boxoffice_ingestion import boxOffice_daily_ingestion
from Python.Data_Management.Landing_Zone.transfer_data_to_delta_lake import create_delta_tables
from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime
from pathlib import Path
project_folder = Path(__file__).resolve().parents[1]


temporal_folder_path = project_folder / 'Data Management' / 'Landing Zone' / 'Temporal Zone'
persistent_folder_path = project_folder / 'Data Management' / 'Landing Zone' / 'Persistent Zone'

def batch_ingestion(temporal_folder_path):
    imbd_ingestion(temporal_folder_path)
    ml_20m_dataset_ingestion(temporal_folder_path)
    boxOffice_daily_ingestion(temporal_folder_path)
    return



# Create the DAG
with DAG(
    dag_id='update_daily_data_dag',
    start_date=datetime(2024, 1, 1, 23, 59, 59),
    schedule_interval='@daily',
    catchup=False,
) as dag:
    
    # Create tasks that call the Python function
    batch_ingestion_tasks = PythonOperator(
        task_id='batch_ingestion_tasks',
        python_callable=batch_ingestion,
        op_args=[temporal_folder_path],
    )
    
    update_delta_tables_task = PythonOperator(
        task_id='update_delta_tables_task',
        python_callable=create_delta_tables,
        op_args=[temporal_folder_path, persistent_folder_path],
    )

    # Set the task dependencies
    batch_ingestion_tasks >> update_delta_tables_task
    
