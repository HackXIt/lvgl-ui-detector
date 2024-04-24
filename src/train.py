# Standard library imports
import os
import sys
import yaml
import logging as log
# Import all dependencies
# Set constants for environment
required_modules = ['ultralytics', 'clearml', 'pyyaml']
missing_deps = False
try:
    from ultralytics import YOLO
    from clearml import Task, TaskTypes, Dataset, PipelineDecorator
    import yaml
except ImportError as e:
    log.error(f"Failed to import required dependencies: (expected: %s) %s", required_modules, e)
    missing_deps = True

class Environment(dict):
    def __init__(self, 
                 project_name: str = "LVGL UI Detector", 
                 project_tag: str = "lvgl-ui-detector", 
                 dataset_partial_name: str = "UI Randomizer", *args, **kwargs):
        super(Environment, self).__init__(*args, **kwargs)
        self.setup_environment(project_name=project_name, project_tag=project_tag)
        self.query_datasets(partial_name=dataset_partial_name)
        return self

    def setup_environment(self, project_name: str, project_tag: str):
        IN_COLAB = 'google.colab' in sys.modules
        IN_LOCAL_CONTAINER = 'HOMELAB' in os.environ
        self['PROJECT_NAME'] = project_name
        self['PROJECT_TAG'] = project_tag
        self['IN_COLAB'] = IN_COLAB
        self['IN_LOCAL_CONTAINER'] = IN_LOCAL_CONTAINER
        self['DIRS'] = {}
        self['FILES'] = {}
        self['ENV'] = os.environ
        if IN_COLAB:
            # NOTE Ignore pylance single line: https://github.com/microsoft/pylance-release/issues/196
            from google.colab import drive # type: ignore
            drive.mount('/content/drive') # Mount Google Drive
            self['DIRS']['root'] = os.path.join("/content/drive/MyDrive/project")
        elif IN_LOCAL_CONTAINER:
            # NOTE Local container already comes with the required modules pre-installed
            self['DIRS']['root'] = "/usr/src"
        else:
            # NOTE Local development environment needs to have the required modules installed
            self['DIRS']['root'] = os.path.curdir

        # Configure folders
        self['DIRS']['data'] = os.path.join(self['DIRS']['root'], "datasets")
        return self

    # Query ClearML for available datasets
    def query_datasets(self, only_completed: bool = True, **kwargs):
        if 'PROJECT_NAME' not in self:
            raise ValueError("PROJECT_NAME not set in environment")
        if 'PROJECT_TAG' not in self:
            raise ValueError("PROJECT_TAG not set in environment")
        if 'FILES' not in self:
            self['FILES'] = {}
        if 'DATASETS' not in self:
            self['DATASETS'] = {}
        datasets = Dataset.list_datasets(self['PROJECT_NAME'], 
                                         tags=[self['PROJECT_TAG']], 
                                         only_completed=only_completed,
                                         **kwargs)
        # Store dataset filenames per dataset
        self['DATASETS'] = {}
        for dataset in datasets:
            self['FILES'][dataset['id']] = Dataset.get(dataset['id']).list_files("*.yaml")
            self['DATASETS'][dataset['id']] = dataset
        return self

@PipelineDecorator.component(return_values=['base_folder'],name="Download Dataset")
def download_dataset(env: Environment, id: str, overwrite: bool = True, **kwargs):
    dataset = Dataset.get(id)
    base_folder = dataset.get_mutable_local_copy(env['DIRS']['data'], overwrite=overwrite, **kwargs)
    return base_folder

@PipelineDecorator.component(return_values=['dataset_content'], name="Fix Dataset Path")
def fix_dataset_path(file: str, replacement_path: str):
    # Replace path in dataset file to match current environment
    with open(file, 'r+') as f:
        dataset_content = yaml.safe_load(f)
        dataset_content['path'] = replacement_path
        print(f"Original dataset:\n{dataset_content}")
        f.seek(0)
        yaml.dump(dataset_content, f)
        f.truncate()
        f.seek(0)
        print(f"Adjusted dataset:\n{f.read()}")
        return dataset_content

@PipelineDecorator.component(return_values=['results'], name="Train Model")
def training_task(env: Environment, model_variant: str, dataset_id: str, args: dict, project: str = "LVGL UI Detector"):
    # Download & modify dataset
    env['DIRS']['target'] = env.download_dataset(dataset_id)
    dataset_file = os.path.join(env['DIRS']['target'], env['FILES'][dataset_id][0])
    dataset_content = fix_dataset_path(dataset_file, env['DIRS']['target'])
    args['data'] = os.path.join(env['DIRS']['target'], env['FILES'][dataset_id][0])
    # Create a ClearML Task
    task = Task.init(
        project_name="LVGL UI Detector",
        task_name=f"Train {model_variant} ({env['DATASETS'][dataset_id]['name']})",
        task_type=TaskTypes.training,
    )
    # Log "model_variant" parameter to task
    task.connect(env, name="Environment")
    task.set_parameter("model_variant", model_variant)
    task.connect_configuration(name="Dataset YAML", configuration=args['data'])
    task.connect_configuration(name="Dataset Content", configuration=dataset_content)

    # Load the YOLOv8 model
    model = YOLO(f'{model_variant}.pt')
    task.connect(args)

    # Train the model 
    # If running remotely, the arguments may be overridden by ClearML if they were changed in the UI
    try:
        results = model.train(**args)
    except Exception as e:
        raise e
    finally:
        task.close()
    return results