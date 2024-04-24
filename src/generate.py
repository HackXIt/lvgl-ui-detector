import os
from typing import List, Tuple
from clearml import PipelineDecorator, Task

@PipelineDecorator.component(return_values=['gen_image', 'gen_text'], name="Capture random widgets")
def capture_random_widgets(output_folder: str, widget_types: List[str], 
                           i: int = 1,
                           micropython: str = "", main: str = "",
                           width: str = "480", height: str = "480", count: int = 3, layout: str = "none", normalize: bool = True):
    import subprocess, os, shutil
    task = Task.current_task()
    if not os.path.exists(micropython) or not os.path.isfile(micropython):
        if 'MICROPYTHON_BIN' in os.environ:
            micropython = os.environ['MICROPYTHON_BIN']
            # task.get_logger().report_text(f"Using micropython binary from environment variable 'MICROPYTHON_BIN': '{micropython}'.")
        else:
            task.get_logger().report_text(f"Path to micropython binary '{micropython}' is not valid (does not exist or is not a file).")
            task.mark_failed()
    if not os.path.exists(main) or not os.path.isfile(main):
        if 'MICROPYTHON_MAIN' in os.environ:
            main = os.environ['MICROPYTHON_MAIN']
            # task.get_logger().report_text(f"Using main script from environment variable 'MICROPYTHON_MAIN': '{main}'.")
        else:
            task.get_logger().report_text(f"Path to main script '{main}' is not valid (does not exist or is not a file).")
            task.mark_failed()
    if not os.path.exists(output_folder) or not os.path.isdir(output_folder):
        task.get_logger().report_text(f"Output folder '{output_folder}' is not valid (does not exist or is not a directory).")
        task.mark_failed()
    # Generate random widget capture
    command = [os.path.abspath(micropython), os.path.abspath(main), "-m", "random", "-o", 'screenshot.jpg', "-W", width, "-H", height, "-c", str(count), "-l", layout, "-t", *widget_types, "--normalize" if normalize else ""]
    gen = subprocess.run(args=command, cwd=os.path.abspath(os.path.curdir), capture_output=True, text=True)
    if gen.returncode != 0:
        task.get_logger().report_text(f"Failed to generate random widgets in iteration {i}:\n{gen.stdout}\n{gen.stderr}")
        task.mark_failed()
    tmp_image = os.path.abspath(os.path.join(os.path.abspath(os.path.curdir), "screenshot.jpg"))
    tmp_text = os.path.abspath(os.path.join(os.path.abspath(os.path.curdir), "screenshot.txt"))
    gen_image = os.path.abspath(os.path.join(output_folder, f"ui_{i}.jpg"))
    gen_text = os.path.abspath(os.path.join(output_folder, f"ui_{i}.txt"))
    try:
        shutil.move(tmp_image, gen_image)
        shutil.move(tmp_text, gen_text)
    except FileNotFoundError as e:
        task.get_logger().report_text(f"Failed to move files in iteration {i}:\n{tmp_image} -> {gen_image}\n{tmp_text} -> {gen_text}\n{e}")
        task.mark_failed()
    return gen_image, gen_text

@PipelineDecorator.component(return_values=['gen_image', 'gen_text'], name="Capture design")
def capture_design(output_folder: str, design_file: str,
                   micropython: str = "", main: str = "", normalize: bool = True):
    import subprocess, os, shutil
    task = Task.current_task()
    design_file = str(design_file) # Need to evaluate LazyEvalWrapper objects
    if not os.path.exists(micropython) or not os.path.isfile(micropython):
        if 'MICROPYTHON_BIN' in os.environ:
            micropython = os.environ['MICROPYTHON_BIN']
        else:
            task.get_logger().report_text(f"Path to micropython binary '{micropython}' is not valid (does not exist or is not a file).")
            task.mark_failed()
    if not os.path.exists(main) or not os.path.isfile(main):
        if 'MICROPYTHON_MAIN' in os.environ:
            main = os.environ['MICROPYTHON_MAIN']
        else:
            task.get_logger().report_text(f"Path to main script '{main}' is not valid (does not exist or is not a file).")
            task.mark_failed()
    if not os.path.exists(output_folder) or not os.path.isdir(output_folder):
        task = Task.current_task()
        task.get_logger().report_text(f"Output folder '{output_folder}' is not valid (does not exist or is not a directory).")
        task.mark_failed()
    if not os.path.exists(design_file) or not os.path.isfile(design_file):
        task = Task.current_task()
        task.get_logger().report_text(f"Design file '{design_file}' is not valid (does not exist or is not a file).")
        task.mark_failed()
    # Generate design capture
    command = [micropython, main, "-m", "design", "-o", 'screenshot.jpg', "-f", design_file, "--normalize" if normalize else ""]
    gen = subprocess.run(args=command, cwd=os.path.abspath(os.path.curdir), capture_output=True, text=True)
    if gen.returncode != 0:
        task.get_logger().report_text(f"Failed to generate design {design_file}:\n{gen.stdout}\n{gen.stderr}")
        task.mark_failed()
    tmp_image = os.path.abspath(os.path.join(os.path.abspath(os.path.curdir), "screenshot.jpg"))
    tmp_text = os.path.abspath(os.path.join(os.path.abspath(os.path.curdir), "screenshot.txt"))
    gen_image = os.path.abspath(os.path.join(output_folder, f"design_{os.path.basename(os.path.abspath(design_file))}.jpg"))
    gen_text = os.path.abspath(os.path.join(output_folder, f"design_{os.path.basename(os.path.abspath(design_file))}.txt"))
    try:
        shutil.move(tmp_image, gen_image)
        shutil.move(tmp_text, gen_text)
    except FileNotFoundError as e:
        task.get_logger().report_text(f"Failed to move files:\n{tmp_image} -> {gen_image}\n{tmp_text} -> {gen_text}")
    return gen_image, gen_text

@PipelineDecorator.component(return_values=['dataset'], name="Create dataset")
def create_dataset(output_folder: str, dataset_name: str, proxy_files: List[str], **kwargs):
    import os, yaml, random, shutil
    task = Task.current_task()
    files = [(str(image), str(annotation)) for image, annotation in proxy_files] # Need to evaluate LazyEvalWrapper objects
    widget_types = ["arc", "bar", "button", "buttonmatrix", "calendar", "chart", "checkbox", "dropdown", "image", "imagebutton", "keyboard", "label", "led", "line", "list", "menu", "messagebox", "roller", "scale", "slider", "spangroup", "spinbox", "spinner", "switch", "table", "tabview", "textarea", "tileview", "window"]
    dataset_file = os.path.abspath(os.path.join(output_folder, f"{dataset_name}.yaml"))
    train_img_dir = "images/train"
    train_label_dir = "labels/train"
    val_img_dir = "images/val"
    val_label_dir = "labels/val"
    test_img_dir = "images/test"
    test_label_dir = "labels/test"
    target_dir = os.path.join(output_folder, dataset_name)
    train_img_folder = os.path.join(target_dir, train_img_dir)
    train_label_folder = os.path.join(target_dir, train_label_dir)
    val_img_folder = os.path.join(target_dir, val_img_dir)
    val_label_folder = os.path.join(target_dir, val_label_dir)
    test_img_folder = os.path.join(target_dir, test_img_dir)
    test_label_folder = os.path.join(target_dir, test_label_dir)
    # Create all necessary folders
    folders = [target_dir, train_img_folder, train_label_folder, val_img_folder, val_label_folder, test_img_folder, test_label_folder]
    for folder in folders:
        os.makedirs(folder, exist_ok=kwargs.get("clean", True))
    for i,(image, annotation) in enumerate(files):
        # task.get_logger().report_text(f"[{i}]: {image} ({type(image)}) - {annotation} ({type(annotation)})")
        # test = str(annotation)
        # task.get_logger().report_text(f"Annotation file: {test} ({type(test)})")
        for a_class in widget_types:
            replacement = str(widget_types.index(a_class))
            with open(annotation, 'r+') as f:
                lines = f.readlines()
                for i, line in enumerate(lines):
                    line = line.replace(a_class + " ", replacement + " ")
                    lines[i] = line
                f.seek(0)
                f.writelines(lines)
                f.truncate()
    def shuffle_split(input: List[str], split_ratio: tuple = (0.7, 0.1, 0.2)):
        if len(split_ratio) != 3 or sum(split_ratio) != 1:
            raise ValueError("Split ratio must be a tuple of 3 values that sum up to 1. (e.g. (0.7, 0.1, 0.2))")
        random.shuffle(input)
        part1 = int(len(input) * split_ratio[0])
        part2 = int(len(input) * split_ratio[1])
        # NOTE Part3 is the remainder of the input

        split1 = input[:part1]
        split2 = input[part1:part1 + part2]
        split3 = input[part1 + part2:]
        return (split1, split2, split3)
    # Shuffle images
    if kwargs.get("split_ratio", None) is not None:
        train, val, test = shuffle_split(files, kwargs["split_ratio"])
    else:
        train, val, test = shuffle_split(files)
    # Copy images and labels to their respective folders
    for _, (image_path, label_path) in enumerate(train):
        shutil.move(image_path, os.path.join(train_img_folder, os.path.basename(image_path)))
        shutil.move(label_path, os.path.join(train_label_folder, os.path.basename(label_path)))
    for _, (image_path, label_path) in enumerate(val):
        shutil.move(image_path, os.path.join(val_img_folder, os.path.basename(image_path)))
        shutil.move(label_path, os.path.join(val_label_folder, os.path.basename(label_path)))
    for _, (image_path, label_path) in enumerate(test):
        shutil.move(image_path, os.path.join(test_img_folder, os.path.basename(image_path)))
        shutil.move(label_path, os.path.join(test_label_folder, os.path.basename(label_path)))
    def dump_yaml_dataset(output_folder: str, name: str, classes: dict, train_dir: str, val_dir: str, test_dir: str = None) -> str:
        dataset_yaml = {
            'path': os.path.join(os.path.curdir, name),
            'train': train_dir,
            'val': val_dir,
            'test': test_dir,
            'names': classes
        }
        yaml_file = os.path.join(output_folder, f"{name}.yaml")
        with open(yaml_file, 'w') as file:
            yaml.dump(dataset_yaml, file)
        return yaml_file
    yaml_file = dump_yaml_dataset(output_folder, dataset_name, kwargs.get("classes", widget_types), train_img_dir, val_img_dir, test_img_dir)
    return yaml_file

@PipelineDecorator.component(return_values=['dataset_id'], name="Run randomizer")
def run_randomizer(mode: str, **kwargs):
    from clearml import Task, Dataset
    task = Task.current_task()
    files = []
    if mode == "random" and "iterations" in kwargs:
        for i in range(kwargs.get("iterations", 1)):
            capture, annotation = capture_random_widgets(output_folder=kwargs.get("output_folder", "./tmp"),
                                                         i=i,
                                                         widget_types=kwargs.get("widget_types", ["button", "label", "switch"]))
            files.append((capture, annotation))
    elif mode == "design" and "designs" in kwargs:
        for file in kwargs["designs"]:
            capture, annotation = capture_design(**kwargs)
            files.append((capture, annotation))
    else:
        task.get_logger().report_text(f"Invalid mode '{mode}'.")
        task.mark_failed()
    dataset_file = create_dataset(proxy_files=files, **kwargs)
    dataset = Dataset.create(kwargs["dataset_name"], kwargs.get("project_name", "LVGL UI Detector"), kwargs.get("dataset_tags", "randomizer"), use_current_task=True)
    dataset.add_files(kwargs.get("output_folder"))
    dataset.add_files(dataset_file)
    return dataset.id

@PipelineDecorator.pipeline(name="UI Randomizer", project="LVGL UI Detector",
                            pipeline_execution_queue="default", default_queue="default")
def ui_randomizer_pipeline(mode: str, **kwargs):
    from clearml import Dataset
    files = []
    if mode == "random" and "iterations" in kwargs:
        for i in range(kwargs.get("iterations", 1)):
            capture, annotation = capture_random_widgets(output_folder=kwargs.get("output_folder", "./tmp"),
                                                         i=i,
                                                         widget_types=kwargs.get("widget_types", ["button", "label", "switch"]))
            files.append((capture, annotation))
    elif mode == "design" and "designs" in kwargs:
        for file in kwargs["designs"]:
            capture, annotation = capture_design(**kwargs)
            files.append((capture, annotation))
    dataset_file = create_dataset(proxy_files=files, **kwargs)
    dataset = Dataset.create(kwargs["dataset_name"], kwargs.get("project_name", "LVGL UI Detector"), kwargs.get("dataset_tags", "randomizer"), use_current_task=True)
    dataset.add_files(kwargs.get("output_folder"))

if __name__ == '__main__':
    implemented_types = ["arc", 
                     "bar", "button", "buttonmatrix", 
                     "calendar", "checkbox", 
                     "dropdown", 
                     "label", "led", 
                     "roller", 
                     "scale", "slider", "spinbox", "switch", 
                     "table", "textarea"]
    # PipelineDecorator.debug_pipeline()
    # PipelineDecorator.run_locally()
    ui_randomizer_pipeline(mode="random", 
                           output_folder="./tmp", 
                           widget_types=implemented_types, 
                           iterations=2, 
                           dataset_name="random_dataset",
                           micropython=os.environ.get("MICROPYTHON_BIN", ""),
                           main=os.environ.get("MICROPYTHON_MAIN", ""))
    print("Pipeline executed successfully")