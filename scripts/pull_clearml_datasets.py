from datetime import date, datetime
from pull_clearml_tasks import json_serial, pull_plots, pull_artifacts

def pull_dataset_data(dataset_id: str, dataset_info: dict, output_folder: str, 
                         write_dataset_name: bool = False, skip_existing: bool = False, cookie: str = None):
    from clearml import Dataset, Task
    import os
    import json
    dataset_dir = f"{dataset_id}_" + dataset_info['name'].replace(' ', '_') if write_dataset_name else dataset_id
    dataset_folder = os.path.join(output_folder, dataset_dir)
    if skip_existing and os.path.exists(dataset_folder):
        print(f"Skipping dataset {dataset_id} as folder already exists")
        return dataset_folder
    dataset = Dataset.get(dataset_id=dataset_id)
    os.makedirs(dataset_folder, exist_ok=True)
    # Save dataset content (if finalized)
    if dataset.is_final():
        save_dir = dataset.get_local_copy()
        if save_dir is not None:
            shutil.copytree(save_dir, os.path.join(dataset_folder, 'content'))
    # Save dependency graph
    dependency_graph = dataset.get_dependency_graph()
    with open(os.path.join(dataset_folder, 'dependency_graph.json'), 'w') as f:
        json.dump(dependency_graph, f, indent=4, sort_keys=True)
    # Retrieve dataset task
    experiment = Task.get_task(dataset.id)
    # Save reported scalars
    reported_scalars = experiment.get_all_reported_scalars()
    with open(os.path.join(dataset_folder, 'reported_scalars.json'), 'w') as f:
        json.dump(reported_scalars, f, indent=4, sort_keys=True)
    # Save last metrics
    last_metrics = experiment.get_last_scalar_metrics()
    with open(os.path.join(dataset_folder, 'last_metrics.json'), 'w') as f:
        json.dump(last_metrics, f, indent=4, sort_keys=True)
    # Save configuration (task configuration)
    task_configuration = experiment.export_task()
    keys_to_convert = ['created', 'started', 'completed', 'last_update', 'last_change']
    with open(os.path.join(dataset_folder, 'task_configuration.json'), 'w') as f:
        json.dump(task_configuration, f, indent=4, sort_keys=True, default=json_serial)
    # Save artifacts
    pull_artifacts(experiment, dataset_folder)
    # Save console output
    output = experiment.get_reported_console_output(10000)
    with open(os.path.join(dataset_folder, 'output.txt'), 'w') as f:
        f.writelines(output)
    # Save output models, plots, and debug samples if dataset is completed
    if experiment.get_status() == 'completed':
        # Save plots
        pull_plots(experiment, dataset_folder, cookie=cookie)
    # Save script info
    script_info = experiment.get_script()
    with open(os.path.join(dataset_folder, 'script_info.json'), 'w') as f:
        json.dump(script_info, f, indent=4, sort_keys=True)
    # Save tags and parameters
    tags = experiment.get_tags()
    if tags:
        with open(os.path.join(dataset_folder, 'tags.txt'), 'w') as f:
            f.write("\n".join(tags))
    parameters = experiment.get_parameters_as_dict(cast=True)
    with open(os.path.join(dataset_folder, 'parameters.json'), 'w') as f:
        json.dump(parameters, f, indent=4, sort_keys=True)
    return dataset_dir

def gather_datasets(project: str = "LVGL UI Detector", recursive: bool = False):
    from clearml import Dataset
    datasets = {}
    for dataset in Dataset.list_datasets(dataset_project=project, recursive_project_search=recursive):
        datasets[dataset['id']] = {
            'name': dataset['name'], 
            'created': dataset['created'].isoformat(),
            'tags': dataset['tags'],
            'version': dataset['version'],
            'project': dataset['project'],
        }
    return datasets

if __name__ == '__main__':
    import argparse
    import os
    import shutil
    import json
    parser = argparse.ArgumentParser(description='Pull ClearML data')
    parser.add_argument('--project', type=str, help='The name of the project to pull datasets from', required=True)
    parser.add_argument('--recursive', action='store_true', help='Whether to query projects recursively')
    parser.add_argument('--output_folder', type=str, help='The output folder to save the data to', required=True)
    parser.add_argument('--zip', action='store_true', help='Whether to zip the output folder')
    parser.add_argument('--write_dataset_name', action='store_true', help='Whether to write the dataset name in the output folder (default is dataset ID)')
    parser.add_argument('--skip_existing', action='store_true', help='Whether to skip pulling data for datasets that already have a folder in the output folder')
    parser.add_argument('--cookie', type=str, help='The cookie to use for downloading files from ClearML')
    args = parser.parse_args()
    datasets = gather_datasets(args.project, args.recursive)
    os.makedirs(args.output_folder, exist_ok=True)
    for dataset_id, dataset_info in datasets.items():
        print(f'Pulling data from dataset "{dataset_info["name"]}" with ID "{dataset_id}"')
        dataset_folder = pull_dataset_data(dataset_id, dataset_info, 
                                                 args.output_folder, 
                                                 args.write_dataset_name, 
                                                 args.skip_existing, 
                                                 args.cookie)
        datasets[dataset_id]['folder'] = dataset_folder
    with open(os.path.join(args.output_folder, 'datasets.json'), 'w') as f:
        json.dump(datasets, f, indent=4, sort_keys=True)
    if args.zip:
        shutil.make_archive(args.output_folder, 'zip', args.output_folder)
        shutil.rmtree(args.output_folder)
