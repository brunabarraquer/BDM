import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))
from Python.Data_Management.Data_Ingestion.Batch_Ingestion.imbd_ingestion import imbd_ingestion
from Python.Data_Management.Data_Ingestion.Batch_Ingestion.ml_20m_ingestion import ml_20m_dataset_ingestion
from Python.Data_Management.Data_Ingestion.Batch_Ingestion.boxoffice_ingestion import boxOffice_daily_ingestion
from Python.Data_Management.Landing_Zone.transfer_data_to_delta_lake import create_delta_tables
from Python.Data_Management.Landing_Zone.create_folders import create_folders
from Python.Data_Management.Trusted_Zone.data_cleaning_pipeline import main_cleaning_pipeline
from Python.Data_Management.Exploitation_Zone.exploitation_tables import exploitation_tables
from airflow import DAG # type: ignore
from airflow.operators.python import PythonOperator # type: ignore
from datetime import datetime
from pathlib import Path

# Get the folder paths that we need to use
project_folder = Path(__file__).resolve().parents[1]
temporal_folder_path = project_folder / 'Data Management' / 'Landing Zone' / 'Temporal Zone'
persistent_folder_path = project_folder / 'Data Management' / 'Landing Zone' / 'Persistent Zone'

def batch_ingestion(temporal_folder_path):
    create_folders(project_folder) # In the case that the folders have not been created (UI.py has not executed first)
    imbd_ingestion(temporal_folder_path)
    ml_20m_dataset_ingestion(temporal_folder_path)
    boxOffice_daily_ingestion(temporal_folder_path)
    return


# Create the DAG
with DAG(
    dag_id='update_daily_data_dag',
    start_date=datetime(2024, 1, 1, 23, 30, 0),
    schedule_interval='30 23 * * *',  # Run every day at 23:30:00
    catchup=False,
) as dag:
    
    # Create batch ingestion tasks
    batch_ingestion_tasks = PythonOperator(
        task_id='batch_ingestion_tasks',
        python_callable=batch_ingestion,
        op_args=[temporal_folder_path],
    )
    
    # Create update delta tables task
    update_delta_tables_task = PythonOperator(
        task_id='update_delta_tables_task',
        python_callable=create_delta_tables,
        op_args=[temporal_folder_path, persistent_folder_path],
    )

    # Create trusted zone tasks
    trusted_delta_tables_task = PythonOperator(
        task_id='trusted_delta_tables_task',
        python_callable=main_cleaning_pipeline
    )

    # Create exploitation zone tasks
    exploitation_delta_tables_task = PythonOperator(
        task_id='exploitation_delta_tables_task',
        python_callable=exploitation_tables
    )


    # Set the task dependencies 
    batch_ingestion_tasks >> update_delta_tables_task >> trusted_delta_tables_task >> exploitation_delta_tables_task
    
