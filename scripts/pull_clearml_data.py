
def pull_experiment_data(experiment_id: str, experiment_info: dict, output_folder: str, write_task_name: bool = False):
    from clearml import Task
    import os
    import shutil
    import json
    import requests
    import plotly.graph_objects as go
    experiment = Task.get_task(task_id=experiment_id)
    experiment_dir = f"{experiment_id}_" + experiment_info['name'].replace(' ', '_') if write_task_name else experiment_id
    experiment_folder = os.path.join(output_folder, experiment_dir)
    os.makedirs(experiment_folder, exist_ok=True)
    # Save reported scalars
    reported_scalars = experiment.get_all_reported_scalars()
    with open(os.path.join(experiment_folder, 'reported_scalars.json'), 'w') as f:
        json.dump(reported_scalars, f)
    # Save last metrics
    last_metrics = experiment.get_last_scalar_metrics()
    with open(os.path.join(experiment_folder, 'last_metrics.json'), 'w') as f:
        json.dump(last_metrics, f)
    # Save configuration
    configuration = experiment.get_configuration_objects()
    with open(os.path.join(experiment_folder, 'configuration.json'), 'w') as f:
        json.dump(configuration, f)
    # Save model design (if available)
    model_design = experiment.get_model_design()
    if model_design:
        with open(os.path.join(experiment_folder, 'model_design.txt'), 'w') as f:
            f.write(model_design)
    # Save artifacts
    artifacts_dir = os.path.join(experiment_folder, 'artifacts')
    os.makedirs(artifacts_dir, exist_ok=True)
    for artifact in experiment.artifacts.values():
        with open(os.path.join(artifacts_dir, f'{artifact.name}.json'), 'w') as f:
            json.dump(artifact.metadata, f)
        artifact_dir = artifact.get_local_copy()
        if os.path.isdir(artifact_dir):
            shutil.copytree(artifact_dir, os.path.join(artifacts_dir, artifact.name))
        else:
            shutil.copy(artifact_dir, artifacts_dir)
    # Save output models (if available)
    models = experiment.get_models()
    if models['output']:
        output_models = os.path.join(experiment_folder, 'output_models')
        os.makedirs(output_models, exist_ok=True)
        for model in models['output']:
            model_dir = model.get_local_copy()
            shutil.copy(model_dir, output_models)
    # Save console output
    output = experiment.get_reported_console_output(10000)
    with open(os.path.join(experiment_folder, 'output.txt'), 'w') as f:
        f.writelines(output)
    # Save plots
    plot_data = experiment.get_reported_plots()
    plot_dir = os.path.join(experiment_folder, 'plots')
    os.makedirs(plot_dir, exist_ok=True)
    for plot in plot_data:
        plot_name = plot['metric']
        with open(os.path.join(plot_dir, f'{plot_name}.json'), 'w') as f:
            json.dump(plot, f)
        plot_data = json.loads(plot['plot_str'])
        fig = go.Figure(data=plot_data['data'], layout=plot_data['layout'])
        fig.write_html(os.path.join(plot_dir, f'{plot_name}.html'))
        if 'source' not in plot:
            continue
        req = requests.get(plot['source'], allow_redirects=True)
        open(os.path.join(plot_dir, f'{plot_name}.png'), 'wb').write(req.content)
    # Save debug samples
    debug_samples_dir = os.path.join(experiment_folder, 'debug_samples')
    os.makedirs(debug_samples_dir, exist_ok=True)
    mosaic_samples = experiment.get_debug_samples(title='Mosaic', series='train.jpg')
    if mosaic_samples:
        for sample in mosaic_samples:
            req = requests.get(sample['url'], allow_redirects=True)
            open(os.path.join(debug_samples_dir, f"{sample['metric']}_{sample['iter']}_{sample['variant']}"), 'wb').write(req.content)
    val_labels = experiment.get_debug_samples(title='Validation', series='val_labels.jpg')
    if val_labels:
        for sample in val_labels:
            req = requests.get(sample['url'], allow_redirects=True)
            open(os.path.join(debug_samples_dir, f"{sample['metric']}_{sample['iter']}_{sample['variant']}"), 'wb').write(req.content)
    val_preds = experiment.get_debug_samples(title='Validation', series='val_preds.jpg')
    if val_preds:
        for sample in val_preds:
            req = requests.get(sample['url'], allow_redirects=True)
            open(os.path.join(debug_samples_dir, f"{sample['metric']}_{sample['iter']}_{sample['variant']}"), 'wb').write(req.content)
    # Save script info
    script_info = experiment.get_script()
    with open(os.path.join(experiment_folder, 'script_info.json'), 'w') as f:
        json.dump(script_info, f)
    # Save tags and parameters
    tags = experiment.get_tags()
    if tags:
        with open(os.path.join(experiment_folder, 'tags.txt'), 'w') as f:
            f.writelines(tags)
    parameters = experiment.get_parameters_as_dict(cast=True)
    with open(os.path.join(experiment_folder, 'parameters.json'), 'w') as f:
        json.dump(parameters, f)
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
    args = parser.parse_args()
    experiments = gather_experiments(args.project)
    os.makedirs(args.output_folder, exist_ok=True)
    for experiment_id, experiment_info in experiments.items():
        print(f'Pulling data for experiment {experiment_info["name"]} with ID {experiment_id}')
        experiment_folder = pull_experiment_data(experiment_id, experiment_info, args.output_folder, args.write_task_name)
        experiments[experiment_id]['folder'] = experiment_folder
    with open(os.path.join(args.output_folder, 'experiments.json'), 'w') as f:
        json.dump(experiments, f)
    if args.zip:
        shutil.make_archive(args.output_folder, 'zip', args.output_folder)
        shutil.rmtree(args.output_folder)
