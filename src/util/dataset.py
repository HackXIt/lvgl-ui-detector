import yaml
import shutil
import os
import random

from typing import List, Tuple

from util import replace
from util import generators
from util import normalize

def create_dataset_file(target_folder: str, name: str, num_classes: int, train_file: str, val_file: str, names_file: str) -> str:
    os.makedirs(target_folder, exist_ok=True)
    data_file_path = os.path.join(target_folder, f'{name}.data')
    with open(data_file_path, 'w') as file:
        file.write(f"classes={num_classes}\n")
        file.write(f"train={train_file}\n")
        file.write(f"valid={val_file}\n")
        file.write(f"names={names_file}\n")
    return data_file_path

def create_datalist_file(data: List[Tuple[str, str]], output_file: str):
    with open(output_file, 'w') as file:
        for image, label in data:
            file.write(f"{image} {label}\n")

def dump_yaml_dataset(output_folder: str, name: str, classes: dict, train_dir: str, val_dir: str, test_dir: str = None) -> dict:
    """
    Create a yaml file for the dataset using the provided name, classes and directories

    Example dataset.yaml file:
    # Train/val/test sets as 1) dir: path/to/imgs, 2) file: path/to/imgs.txt, or 3) list: [path/to/imgs1, path/to/imgs2, ..]
    path: ../datasets/coco8  # dataset root dir
    train: images/train  # train images (relative to 'path') 4 images
    val: images/val  # val images (relative to 'path') 4 images
    test:  # test images (optional)

    # Classes (80 COCO classes)
    names:
      0: person
      1: bicycle
      2: car
      # ...
      77: teddy bear
      78: hair drier
      79: toothbrush
    """
    dataset_yaml = {
        'path': os.path.join(os.path.curdir, name),
        'train': train_dir,
        'val': val_dir,
        'test': test_dir,
        'names': classes
    }
    with open(os.path.join(output_folder, f"{name}.yaml"), 'w') as file:
        yaml.dump(dataset_yaml, file)
    return dataset_yaml

def shuffle_split(input: List[str], split_ratio: tuple = (0.7, 0.1, 0.2)) -> Tuple[List[str], List[str], List[str]]:
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

def create_dataset(output_folder: str, name: str, data: List[Tuple[str, str]], class_names: dict, **kwargs) -> dict:
    """
    Generate a dataset from a list of images
    """
    # Some variables
    train_img_dir = "images/train"
    train_label_dir = "labels/train"
    val_img_dir = "images/val"
    val_label_dir = "labels/val"
    test_img_dir = "images/test"
    test_label_dir = "labels/test"
    target_dir = os.path.join(output_folder, name)
    if os.path.exists(target_dir):
        if kwargs.get("clean", False):
            shutil.rmtree(target_dir)
        else:
            raise FileExistsError(f"Directory '{target_dir}' already exists. Please remove it or use the 'clean' option to overwrite it.")
    train_img_folder = os.path.join(target_dir, train_img_dir)
    train_label_folder = os.path.join(target_dir, train_label_dir)
    val_img_folder = os.path.join(target_dir, val_img_dir)
    val_label_folder = os.path.join(target_dir, val_label_dir)
    test_img_folder = os.path.join(target_dir, test_img_dir)
    test_label_folder = os.path.join(target_dir, test_label_dir)

    # Create all necessary folders
    folders = [target_dir, train_img_folder, train_label_folder, val_img_folder, val_label_folder, test_img_folder, test_label_folder]
    for folder in folders:
        os.makedirs(folder, exist_ok=kwargs.get("clean", False))

    # Shuffle images
    if kwargs.get("split_ratio", None) is not None:
        train, val, test = shuffle_split(data, kwargs["split_ratio"])
    else:
        train, val, test = shuffle_split(data)

    # Copy images and labels to their respective folders
    for i, (image_path, label_path) in enumerate(train):
        shutil.move(image_path, os.path.join(train_img_folder, os.path.basename(image_path)))
        shutil.move(label_path, os.path.join(train_label_folder, os.path.basename(label_path)))
    for i, (image_path, label_path) in enumerate(val):
        shutil.move(image_path, os.path.join(val_img_folder, os.path.basename(image_path)))
        shutil.move(label_path, os.path.join(val_label_folder, os.path.basename(label_path)))
    for i, (image_path, label_path) in enumerate(test):
        shutil.move(image_path, os.path.join(test_img_folder, os.path.basename(image_path)))
        shutil.move(label_path, os.path.join(test_label_folder, os.path.basename(label_path)))

    # Dictionary in the format: {class_id: class_name}
    dataset_dict = dump_yaml_dataset(output_folder, name, class_names, train_img_dir, val_img_dir, test_img_dir)

    # Apply fixes to the dataset if needed
    if kwargs.get("fixes", None) is not None or not kwargs["fixes"]:
        class_replace = kwargs["fixes"].get("class_replace", None)
        normalize_bbox = kwargs["fixes"].get("normalize_bbox", None)
        if class_replace and "class_names" not in class_replace:
            raise KeyError("Class names must be provided to replace the class names.")
        if normalize_bbox and ("width" not in normalize_bbox or "height" not in normalize_bbox):
            raise KeyError("Width and Height must be provided to normalize the bounding boxes.")
        for label_file in generators.annotation_files_in_dirs([train_label_folder, val_label_folder, test_label_folder]):
            if class_replace is not None:
                replace.replace_class_names_with_id_in_file(class_replace["class_names"], label_file)
            if normalize_bbox is not None:
                normalize.normalize_bbox_in_label_file(label_file, normalize_bbox["width"], normalize_bbox["height"])
    return dataset_dict