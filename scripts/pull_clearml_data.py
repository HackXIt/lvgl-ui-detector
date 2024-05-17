from datetime import date, datetime

def json_serial(obj): # NOTE Src: https://stackoverflow.com/a/22238613
    """JSON serializer for objects not serializable by default json code"""
    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    raise TypeError ("Type %s not serializable" % type(obj))

def pull_file(url: str, alt_name: str, target_dir: str, cookie: str = None):
    import requests
    import mimetypes
    import os
    # NOTE - This is a workaround for downloading files from ClearML. The ClearML SDK does not provide a way to download files directly.
    # Go to the file URL in your browser, copy the cookies from the request headers, and paste them in the variable.
    cookie = 'YOUR_COOKIE' if cookie is None else cookie
    req = requests.get(url, allow_redirects=True, headers={'Cookie': cookie.encode()})
    # print(req.headers)
    content_type = req.headers['Content-Type']
    # print(content_type)
    extension = mimetypes.guess_extension(content_type)
    if 'Content-Disposition' in req.headers:
        disposition = req.headers['Content-Disposition']
        # print(disposition)
        original_filename = disposition.split('filename=')[-1].strip('"')
    else:
        original_filename = alt_name + extension
    file_path = os.path.join(target_dir, original_filename)
    with open(file_path, 'wb') as file:
        file.write(req.content)

def pull_debug_samples(experiment, experiment_folder, cookie: str = None):
    import os
    debug_samples_dir = os.path.join(experiment_folder, 'debug_samples')
    mosaic_samples = experiment.get_debug_samples(title='Mosaic', series='train.jpg')
    if mosaic_samples:
        os.makedirs(debug_samples_dir, exist_ok=True)
        for sample in mosaic_samples:
            pull_file(sample['url'], f"{sample['metric']}_{sample['iter']}_{sample['variant']}", debug_samples_dir, cookie=cookie)
    val_labels = experiment.get_debug_samples(title='Validation', series='val_labels.jpg')
    if val_labels:
        os.makedirs(debug_samples_dir, exist_ok=True)
        for sample in val_labels:
            pull_file(sample['url'], f"{sample['metric']}_{sample['iter']}_{sample['variant']}", debug_samples_dir, cookie=cookie)
    val_preds = experiment.get_debug_samples(title='Validation', series='val_preds.jpg')
    if val_preds:
        os.makedirs(debug_samples_dir, exist_ok=True)
        for sample in val_preds:
            pull_file(sample['url'], f"{sample['metric']}_{sample['iter']}_{sample['variant']}", debug_samples_dir, cookie=cookie)

def pull_plots(experiment, experiment_folder, cookie: str = None):
    import json
    import plotly.graph_objects as go
    plots = experiment.get_reported_plots()
    if plots:
        plot_dir = os.path.join(experiment_folder, 'plots')
        os.makedirs(plot_dir, exist_ok=True)
        for plot in plots:
            plot_name = plot['metric']
            # Replace invalid characters in file name
            plot_name = plot_name.replace('/', '_').replace(':', '_').replace('=', '_')
            plot_json_path = os.path.join(plot_dir, f'{plot_name}.json')
            with open(plot_json_path, 'w', encoding='utf-8') as f:
                json.dump(plot, f, ensure_ascii=False, indent=4, sort_keys=True)
            plot_data = json.loads(plot['plot_str'])
            try:
                # Handle plot images
                if plot['variant'] == 'plot image':
                    image_dir = os.path.join(plot_dir, 'images')
                    os.makedirs(image_dir, exist_ok=True)
                    for i, image in enumerate(plot_data['layout']['images']):
                        source_url = image['source']
                        pull_file(source_url, f"{plot_name}_{i}", image_dir, cookie=cookie)
                # Handle Plotly plots
                elif 'total' in plot['variant'] or plot['variant'] == 'plot':
                    fig = go.Figure(data=plot_data['data'], layout=plot_data['layout'])
                    fig.write_html(os.path.join(plot_dir, f'{plot_name}.html'))
            except Exception as e:
                print(f"Failed to save plot {plot_name}\n{plot}\n{e}")

def pull_artifacts(experiment, experiment_folder):
    import shutil
    import json
    import os
    artifacts_dir = os.path.join(experiment_folder, 'artifacts')
    artifacts = experiment.artifacts.values()
    if len(artifacts) > 0:
        os.makedirs(artifacts_dir, exist_ok=True)
        for artifact in experiment.artifacts.values():
            with open(os.path.join(artifacts_dir, f'{artifact.name}.json'), 'w') as f:
                json.dump(artifact.metadata, f, indent=4, sort_keys=True)
            artifact_dir = artifact.get_local_copy()
            if os.path.isdir(artifact_dir):
                shutil.copytree(artifact_dir, os.path.join(artifacts_dir, artifact.name))
            else:
                shutil.copy(artifact_dir, artifacts_dir)

def pull_models(experiment, experiment_folder, pull_output: bool = True, pull_input: bool = False):
    import os
    import shutil
    models = experiment.get_models()
    if models['output'] and pull_output:
        output_models = os.path.join(experiment_folder, 'output_models')
        os.makedirs(output_models, exist_ok=True)
        for model in models['output']:
            model_dir = model.get_local_copy()
            if type(model_dir) is not str:
                print(f"Failed to get local copy of model {model.id}")
                continue
            shutil.copy(model_dir, output_models)
    if models['input'] and pull_input:
        input_models = os.path.join(experiment_folder, 'input_models')
        os.makedirs(input_models, exist_ok=True)
        for model in models['input']:
            model_dir = model.get_local_copy()
            shutil.copy(model_dir, input_models)

def pull_experiment_data(experiment_id: str, experiment_info: dict, output_folder: str, 
                         write_task_name: bool = False, skip_existing: bool = False, cookie: str = None,
                         pull_output_models: bool = True, pull_input_models: bool = False):
    from clearml import Task
    import os
    import json
    experiment = Task.get_task(task_id=experiment_id)
    experiment_dir = f"{experiment_id}_" + experiment_info['name'].replace(' ', '_') if write_task_name else experiment_id
    experiment_folder = os.path.join(output_folder, experiment_dir)
    if skip_existing and os.path.exists(experiment_folder):
        print(f"Skipping experiment {experiment_id} as folder already exists")
        return experiment_folder
    os.makedirs(experiment_folder, exist_ok=True)
    # Save reported scalars
    reported_scalars = experiment.get_all_reported_scalars()
    with open(os.path.join(experiment_folder, 'reported_scalars.json'), 'w') as f:
        json.dump(reported_scalars, f, indent=4, sort_keys=True)
    # Save last metrics
    last_metrics = experiment.get_last_scalar_metrics()
    with open(os.path.join(experiment_folder, 'last_metrics.json'), 'w') as f:
        json.dump(last_metrics, f, indent=4, sort_keys=True)
    # Save configuration (task configuration)
    task_configuration = experiment.export_task()
    keys_to_convert = ['created', 'started', 'completed', 'last_update', 'last_change']
    with open(os.path.join(experiment_folder, 'task_configuration.json'), 'w') as f:
        json.dump(task_configuration, f, indent=4, sort_keys=True, default=json_serial)
    # Save model design (if available)
    model_design = experiment.get_model_design()
    if model_design:
        with open(os.path.join(experiment_folder, 'model_design.txt'), 'w') as f:
            f.write(model_design)
    # Save artifacts
    pull_artifacts(experiment, experiment_folder)
    # Save console output
    output = experiment.get_reported_console_output(10000)
    with open(os.path.join(experiment_folder, 'output.txt'), 'w') as f:
        f.writelines(output)
    # Save output models, plots, and debug samples if experiment is completed
    if experiment.get_status() == 'completed':
        # Save output models (if available)
        pull_models(experiment, experiment_folder, pull_output_models, pull_input_models)
        # Save plots
        pull_plots(experiment, experiment_folder, cookie=cookie)
        # Save debug samples
        pull_debug_samples(experiment, experiment_folder, cookie=cookie)
    # Save script info
    script_info = experiment.get_script()
    with open(os.path.join(experiment_folder, 'script_info.json'), 'w') as f:
        json.dump(script_info, f, indent=4, sort_keys=True)
    # Save tags and parameters
    tags = experiment.get_tags()
    if tags:
        with open(os.path.join(experiment_folder, 'tags.txt'), 'w') as f:
            f.write("\n".join(tags))
    parameters = experiment.get_parameters_as_dict(cast=True)
    with open(os.path.join(experiment_folder, 'parameters.json'), 'w') as f:
        json.dump(parameters, f, indent=4, sort_keys=True)
    return experiment_dir

def gather_experiments(project: str = "LVGL UI Detector"):
    from clearml import Task
    experiments = {}
    for experiment in Task.get_tasks(project_name=project):
        experiments[experiment.id] = {
            'name': experiment.name, 
            'status': experiment.status, 
            'last_iteration': experiment.get_last_iteration()
        }
    return experiments

if __name__ == '__main__':
    import argparse
    import os
    import shutil
    import json
    parser = argparse.ArgumentParser(description='Pull ClearML data')
    parser.add_argument('--project', type=str, help='The name of the project to pull tasks from', required=True)
    parser.add_argument('--output_folder', type=str, help='The output folder to save the data to', required=True)
    parser.add_argument('--zip', action='store_true', help='Whether to zip the output folder')
    parser.add_argument('--write_task_name', action='store_true', help='Whether to write the task name in the output folder (default is task ID)')
    parser.add_argument('--skip_existing', action='store_true', help='Whether to skip pulling data for experiments that already have a folder in the output folder')
    parser.add_argument('--cookie', type=str, help='The cookie to use for downloading files from ClearML')
    parser.add_argument('--pull_output_models', action='store_true', default=True, help='Whether to pull output models')
    parser.add_argument('--pull_input_models', action='store_true', help='Whether to pull input models')
    args = parser.parse_args()
    experiments = gather_experiments(args.project)
    os.makedirs(args.output_folder, exist_ok=True)
    for experiment_id, experiment_info in experiments.items():
        print(f'Pulling data from experiment "{experiment_info["name"]}" with ID "{experiment_id}"')
        experiment_folder = pull_experiment_data(experiment_id, experiment_info, 
                                                 args.output_folder, 
                                                 args.write_task_name, 
                                                 args.skip_existing, 
                                                 args.cookie, 
                                                 args.pull_output_models, args.pull_input_models)
        experiments[experiment_id]['folder'] = experiment_folder
    with open(os.path.join(args.output_folder, 'experiments.json'), 'w') as f:
        json.dump(experiments, f, indent=4, sort_keys=True)
    if args.zip:
        shutil.make_archive(args.output_folder, 'zip', args.output_folder)
        shutil.rmtree(args.output_folder)
