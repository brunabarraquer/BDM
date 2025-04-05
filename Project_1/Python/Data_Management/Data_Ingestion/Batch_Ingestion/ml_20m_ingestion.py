import os
import kagglehub
import shutil


def ml_20m_dataset_ingestion(temporal_folder_path):
    try:
        # Download the dataset and store it in the current folder
        dataset_path = kagglehub.dataset_download("grouplens/movielens-20m-dataset")
    except Exception as e:
        print(f'Error occurred to ingest the data from kaggle API: {e}')
        return
    
    # Rename the data files to ensure the data convention
    for filename in os.listdir(dataset_path):
        if filename.endswith('.csv'):
            try:
                old_path = os.path.join(dataset_path, filename)
                new_file_name = 'ml-20m_' + filename
                new_path = os.path.join(dataset_path, new_file_name)
                os.rename(old_path, new_path)
                
            except Exception as e:
                print(f'Error occurred when renaming the files: {e}')
                return
    
    # Loop through all files in dataset_path
    for filename in os.listdir(dataset_path):
        file_path = os.path.join(dataset_path, filename)

        # Check if it's a file before moving
        if filename.endswith('.csv') and os.path.isfile(file_path):
            try:
                shutil.move(file_path, os.path.join(temporal_folder_path, filename))
                print(f"Moved: {filename} -> {temporal_folder_path}")
        
            except Exception as e:
                print(f'Error occurred when move the data to Temporal folder: {e}')
                return

    print('All the data ingested in the Temporal Folder')

