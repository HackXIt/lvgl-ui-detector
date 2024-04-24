import subprocess
import os
import sys
import shutil
import time
import logging as log
import yaml
import numpy as np

from typing import List
from typing import Tuple
from clearml import Dataset, Task, Logger, PipelineDecorator
from argparse import Namespace

from util.cli import create_parser, validate_arguments, widget_types
from util.dataset import create_dataset, create_datalist_file

# Dictionary to provide original widget class name (appending "lv_" to the widget type) and the index of the widget type in the list
# NOTE Some class names might actually be an abbreviated version of the widget type, but we ignore those special cases as in the future they all should follow the same pattern
classes = {}
for i, widget in enumerate(widget_types):
    classes[i] = widget
poetry_invoke = "poetry run invoke".split(' ')

def run_ui_generator(micropython: str, main: str, generator, working_dir: str, *args, use_absolute_paths: bool = False, capture_output: bool = False, continue_on_error: bool = False):
    # NOTE Assumes correct input arguments, to be validated before calling this function
    # NOTE subprocess arguments only accepts strings, which is why we convert all arguments to strings for this action
    if use_absolute_paths:
        args = [os.path.abspath(micropython), os.path.abspath(main), "-m", generator] + [str(arg) for arg in args]
    else:
        args = [micropython, main, "-m", generator] + [str(arg) for arg in args]
    log.info("Running command: %s", ' '.join(args))
    gen = subprocess.run(args, cwd=os.path.abspath(working_dir), capture_output=capture_output, text=True)
    if gen.returncode != 0:
        log.error("UI generation failed with return code %s.", gen.returncode)
        log.debug("STDOUT:\n%s", gen.stdout)
        log.debug("STDERR:\n%s", gen.stderr)
        if not continue_on_error:
            sys.exit(1)
    else:
        log.info("UI generation successful with return code %s.", gen.returncode)
        if capture_output:
            log.debug("STDOUT:\n%s", gen.stdout)

def prepare_output_folder(output_folder: str, clean: bool = False):
    if clean:
        shutil.rmtree(output_folder, ignore_errors=True)
    os.makedirs(output_folder, exist_ok=True)
    return os.path.abspath(output_folder)

@PipelineDecorator.component(name="capture designs",
                             task_type=Task.TaskTypes.data_processing,
                             continue_on_fail=False,
                             return_values=['data'])
def capture_with_designs(**kwargs) -> List[Tuple[str, str]]:
    import os, shutil, time, subprocess
    data = {'files': [], 'errors': []}
    # kwargs["output_folder"] = prepare_output_folder(kwargs["output_folder"], kwargs["clean"])
    if kwargs["clean"]:
        shutil.rmtree(kwargs["output_folder"], ignore_errors=True)
    os.makedirs(kwargs["output_folder"], exist_ok=True)
    kwargs["output_folder"] = os.path.abspath(kwargs["output_folder"])
    args = [os.path.abspath(kwargs["micropython"]), os.path.abspath(kwargs["main"]), "-m", kwargs["generator"], "-f", design_file, "-o", f"{design_base}.jpg", "--normalize" if kwargs["normalize"] else ""]
    for design in os.listdir(kwargs["design_folder"]):
        design_file = os.path.abspath(os.path.join(kwargs["design_folder"], design))
        design_base = os.path.splitext(design)[0]
        gen = subprocess.run(args, cwd=os.path.abspath(kwargs["working_dir"]), capture_output=kwargs['capture_output'], text=True)
        if gen.returncode != 0:
            log.error("UI generation failed with return code %s.", gen.returncode)
            log.debug("STDOUT:\n%s", gen.stdout)
            log.debug("STDERR:\n%s", gen.stderr)
        else:
            log.info("UI generation successful with return code %s.", gen.returncode)
            if kwargs['capture_output']:
                log.debug("STDOUT:\n%s", gen.stdout)
        tmp_image = os.path.abspath(os.path.join(kwargs["working_dir"], f"{design_base}.jpg"))
        tmp_text = os.path.abspath(os.path.join(kwargs["working_dir"], f"{design_base}.txt"))
        gen_image = os.path.abspath(os.path.join(kwargs["output_folder"], f"{design_base}.jpg"))
        gen_text = os.path.abspath(os.path.join(kwargs["output_folder"], f"{design_base}.txt"))
        try:
            shutil.move(tmp_image, gen_image)
            shutil.move(tmp_text, gen_text)
        except FileNotFoundError as e:
            log.error("Failed to move files for widget %s in iteration %s:\n%s -> %s\n%s -> %s", 
                      widget, i, tmp_image, gen_image, tmp_text, gen_text)
            data['errors'].append((design, e.strerror))
            continue
        data.append((gen_image, gen_text))
        if kwargs["delay"] > 0:
            time.sleep(kwargs["delay"] / 1000)
    return data

@PipelineDecorator.component(name="capture random",
                             task_type=Task.TaskTypes.data_processing,
                             continue_on_fail=False,
                             return_values=['data'])
def capture_with_random(**kwargs) -> List[Tuple[str, str]]:
    import os, shutil, time, subprocess
    data = {'files': [], 'errors': [], 'types': {}}
    if kwargs["clean"]:
        shutil.rmtree(kwargs["output_folder"], ignore_errors=True)
    os.makedirs(kwargs["output_folder"], exist_ok=True)
    kwargs["output_folder"] = os.path.abspath(kwargs["output_folder"])
    args = [os.path.abspath(kwargs["micropython"]), os.path.abspath(kwargs["main"]), "-m", kwargs["generator"], 
            "-W", kwargs["width"], "-H", kwargs["height"], "-c", kwargs["count"], "-l", kwargs["layout"], 
            "-o", "screenshot.jpg", "-t", *kwargs["widget_types"], "--normalize" if kwargs["normalize"] else ""]
    for i in range(kwargs["iterations"]):
        gen = subprocess.run(args, cwd=os.path.abspath(kwargs["working_dir"]), capture_output=kwargs['capture_output'], text=True)
        if gen.returncode != 0:
            log.error("UI generation failed with return code %s.", gen.returncode)
            log.debug("STDOUT:\n%s", gen.stdout)
            log.debug("STDERR:\n%s", gen.stderr)
        else:
            log.info("UI generation successful with return code %s.", gen.returncode)
            if kwargs['capture_output']:
                log.debug("STDOUT:\n%s", gen.stdout)
        tmp_image = os.path.abspath(os.path.join(kwargs["working_dir"], "screenshot.jpg"))
        tmp_text = os.path.abspath(os.path.join(kwargs["working_dir"], "screenshot.txt"))
        gen_image = os.path.abspath(os.path.join(kwargs["output_folder"], f"ui_{i}.jpg"))
        gen_text = os.path.abspath(os.path.join(kwargs["output_folder"], f"ui_{i}.txt"))
        try:
            shutil.move(tmp_image, gen_image)
            shutil.move(tmp_text, gen_text)
        except FileNotFoundError as e:
            log.error("Failed to move files in iteration {}:\n{} -> {}\n{} -> {}",
                        i, tmp_image, gen_image, tmp_text, gen_text)
            data['errors'].append((str(i), e.strerror))
            continue
        data["files"].append((gen_image, gen_text))
        for type in kwargs["widget_types"]:
            data["types"][type] = data["types"].get(type, 0) + 1
        if kwargs["delay"] > 0:
            time.sleep(kwargs["delay"] / 1000)
    return data

@PipelineDecorator.component(name="upload dataset",
                             task_type=Task.TaskTypes.data_processing,
                             continue_on_fail=False,
                             return_values=['dataset_id'])
def upload_dataset(data: dict, output_folder: str, dataset_name: str, generator: str, used_classes: dict, dataset_dict: dict, 
                prefix: str = "UI Randomizer", project: str = "LVGL UI Detector", tags: List[str] = ["lvgl-ui-detector"]):
    import os
    from clearml import Dataset
    dataset = Dataset.get(dataset_name=f"{prefix} - {dataset_name}",
                              dataset_project=project,
                              dataset_tags=tags + [generator],
                              auto_create=True, alias=dataset_name, overridable=True)
    if dataset.is_final():
        dataset = Dataset.create(dataset_name=f"{prefix} - {dataset_name}",
                                    dataset_project=project,
                                    dataset_tags=tags + [generator],
                                    parent_datasets=[dataset.id])
    counts = []
    root = os.path.abspath(output_folder)
    folders = sorted(os.listdir(root))
    for folder in folders:
        counts.append([len(os.listdir(root / folder))])
    dataset.add_files(path=os.path.abspath(os.path.join(output_folder, dataset_name)))
    dataset.add_files(path=os.path.abspath(os.path.join(output_folder, dataset_name + ".yaml")))
    metadata = {
        "generator": generator,
        "command": ' '.join(sys.argv),
        "dataset_file": dataset_name + ".yaml",
        "errors": len(data['errors']),
        "used_classes": used_classes,
        "counts": counts,
    }
    dataset.set_metadata(metadata, metadata_name="generator_meta")
    log = dataset.get_logger()
    log.report_text(f"Generator: {generator}")
    log.report_text(f"Command: {' '.join(sys.argv)}")
    log.report_text(f"Dataset:\n{yaml.dump(dataset_dict)}")
    log.report_text(f"Generator had {len(data['errors'])} errors.")
    for i, error in enumerate(data['errors']):
        log.report_text(f"Error #{i}: {error}", log.ERROR)
    if generator == "random":
        values = np.array([int(value) for value in data['types'].values()])
        log.report_histogram("Widget Type Count", 
                                "Counts", 
                                values=values, 
                                xlabels=[key for key in data['types'].keys()], 
                                xaxis="Widget Types", 
                                yaxis="Count")
    log.report_histogram(title="Dataset statistics", series='Train Test Val split', labels=folders, values=counts)
    dataset.finalize(auto_upload=True)
    return dataset.id

#args={"args": ['args'], "ClearML": ['project_name', 'task_name', 'task_tags']}
@PipelineDecorator.pipeline(name="UI Randomizer", project="LVGL UI Detector", version="0.1.0",
                            args_map={"args": ['args']})
def clearml_main(args: Namespace):
    from util.dataset import create_dataset, create_datalist_file
    used_classes = {}
    if args.generator == "random":
        data = capture_with_random(**vars(args))
        used_classes = {k: v for k, v in classes.items() if v in args.widget_types}
    elif args.generator == "design":
        data = capture_with_designs(**vars(args))
        used_classes = classes

    dataset_kwargs = {}
    if args.split_ratio is not None:
        dataset_kwargs["split_ratio"] = args.split_ratio
    if args.clean:
        dataset_kwargs["clean"] = args.clean
    dataset_kwargs["fixes"] = {}
    if args.normalize_bbox and args.generator == "random":
        dataset_kwargs["fixes"]["normalize_bbox"] = {"width": args.width, "height": args.height}
    if args.replace_class_names:
        dataset_kwargs["fixes"]["class_replace"] = {"class_names": widget_types}
    dataset_dict = create_dataset(args.output_folder, args.dataset, data['files'], classes, **dataset_kwargs)
    # Add comment to dataset file with the command used to generate the data
    dataset_file = os.path.join(args.output_folder, args.dataset + ".yaml")
    with open(dataset_file, "a") as f:
        f.write(f"# Command: {' '.join(sys.argv)}")
    if args.datalist is not None:
        datalist_file = os.path.join(args.output_folder, args.datalist)
        create_datalist_file(data, datalist_file)
    if args.clearml_upload:
        upload_args = {"data": data, 
                    "output_folder": args.output_folder, 
                    "dataset_name": args.dataset, 
                    "generator": args.generator, 
                    "used_classes": used_classes, 
                    "dataset_dict": dataset_dict}
        print(f"Created dataset ID: f{upload_dataset(**upload_args)}")

if __name__ == "__main__":
    PipelineDecorator.run_locally()
    parser = create_parser()
    args = parser.parse_args()
    # Configure logger
    if args.verbose:
        level = log.DEBUG
    else:
        level = log.INFO
    log.basicConfig(level=level, format="%(asctime)s|%(levelname)s: %(message)s", datefmt='%Y-%m-%d %H:%M:%S')
    log.debug(args)
    validate_arguments(args)
    log.debug(args)
    # Run main function
    clearml_main(args)
    print("UI Randomizer completed.")
