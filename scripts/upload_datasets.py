import os
import glob
import argparse
from clearml import Dataset

def upload_dataset(dataset_name, input_path):
    # Get/Create a new dataset with the dataset name
    dataset = Dataset.get(dataset_project='LVGL UI Detector', dataset_name=dataset_name, auto_create=True, dataset_tags=['lvgl-ui-detector', 'manual'])
    # Add the corresponding folder and yaml file to the dataset
    folder_path = os.path.join(input_path)
    if os.path.exists(folder_path) and os.path.isdir(folder_path):
        dataset.add_files(path=folder_path)
    # Upload and finalize the dataset
    dataset.upload()
    dataset.finalize()
    print(f"Dataset {dataset_name} uploaded successfully: {dataset.id}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Upload datasets')
    parser.add_argument('--dataset_name', type=str, required=True, help='Name of the dataset')
    parser.add_argument('--input_path', type=str, required=True, help='Input path to search for YAML files')
    args = parser.parse_args()

    upload_dataset(args.dataset_name, args.input_path)
