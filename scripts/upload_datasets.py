import os
import glob
from clearml import Dataset

# Path to the target directory
target_directory = os.path.join(os.path.curdir, "tmp")

# Finding all *.yaml files in the target directory
yaml_files = glob.glob(os.path.join(target_directory, '*.yaml'))

for yaml_file in yaml_files:
    # Extracting the base name (without .yaml extension)
    base_name = os.path.basename(yaml_file).replace('.yaml', '')

    # Get/Create a new dataset with the base name
    dataset = Dataset.get(dataset_project='LVGL UI Detector', dataset_name=base_name, auto_create=True, dataset_tags=['lvgl-ui-detector'])

    # Add the corresponding folder and yaml file to the dataset
    folder_path = os.path.join(target_directory, base_name)
    if os.path.exists(folder_path) and os.path.isdir(folder_path):
        dataset.add_files(path=folder_path)
    dataset.add_files(path=yaml_file)

    # Upload and finalize the dataset
    dataset.upload()
    dataset.finalize()
