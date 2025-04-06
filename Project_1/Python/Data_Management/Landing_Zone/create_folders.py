from pathlib import Path


# Create the folders for the Data Management stages
def create_folders(project_path):
    # Define base folder paths
    data_management_folder = project_path / "Data Management"
    landing_zone_folder = data_management_folder / "Landing Zone"
    temporal_folder = landing_zone_folder / "Temporal Zone"
    persistent_folder = landing_zone_folder / "Persistent Zone"

    for folder in [temporal_folder, persistent_folder]:
        try:
            folder.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            print(f'error ocurred: {e}')
            return False

    print('All folders created successfully !!!')
    return True

# project_folder = Path(__file__).resolve().parents[3]
# create_folders(project_folder)
