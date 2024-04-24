import os
from typing import List
from typing import Generator
import logging

from util import generators

def replace_in_file(replace: tuple, file: str):
    """
    Replace occurence of replace[0] with replace[1] in a file

    Assumes correct tuple length of 2 and that file exists
    """
    logging.debug("Replacing %s with %s in %s", replace[0], replace[1], file)
    with open(file, 'r+') as f:
        lines = f.readlines()
        for i, line in enumerate(lines):
            line = line.replace(replace[0] + " ", replace[1] + " ")
            lines[i] = line
        f.seek(0)
        f.writelines(lines)
        f.truncate()

def replace_paths_in_files_of_dir(root: str, replace: tuple, skip_directories: List[str] = ['rico', 'test', 'train', 'val'], skip_files: List[str] = ['classes.names']) -> None:
    """
    Recursively replace all paths in a dataset directory

    Skips by default directories named 'rico', 'test', 'train', and 'val' and files named 'classes.names'
    """
    if len(replace) != 2:
        raise ValueError("Argument replace must be a tuple of length 2")
    for file in generators.dataset_files_in_dir(root, skip_directories, skip_files):
        logging.debug(f"Replacing paths in {file}...")
        replace_in_file(replace, file)

def replace_class_names_with_id_in_file(class_names: List[str], file: str) -> None:
    logging.debug(f"Replacing class names in {file}...")
    with open(file, 'r+') as f:
        for a_class in class_names:
            replace_in_file((a_class, str(class_names.index(a_class))), file)

def replace_class_names_with_id_in_dirs(class_names: List[str], directories: List[str]) -> None:
    """
    Recursively replace all class names in annotation files with their corresponding id
    """
    for file in generators.annotation_files_in_dirs(directories):
        logging.debug(f"Replacing class names in {file}...")
        with open(file, 'r+') as f:
            for a_class in class_names:
                replace_in_file((a_class, str(class_names.index(a_class))), file)

if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    root_dir = os.path.join(os.getcwd(), 'data')
    replace = (root_dir, "/app/project")
    replace_paths_in_files_of_dir(root_dir, replace)