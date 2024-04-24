import os
from typing import List
from typing import Generator
import logging

def dataset_files_in_dir(dir: str, skip_directories: List[str], skip_files: List[str]) -> Generator[str, None, None]:
    """
    Generator for dataset files in a directory

    Skips directories and files specified in skip_directories and skip_files

    Returns a generator of absolute file paths
    """
    if not os.path.isdir(dir):
        raise ValueError(f"{dir} is not a directory")
    for root, dirs, files in os.walk(dir):
        logging.debug("%i directories in %s: %s...", len(dirs), root, ' '.join(dirs))
        dirs[:] = [d for d in dirs if d not in skip_directories]
        for file in files:
            if file in skip_files:
                continue
            if file.endswith('.data'):
                logging.debug("Found %s", file)
                yield os.path.join(root, file)

def annotation_files_in_dirs(target_directories: List[str]) -> Generator[str, None, None]:
    """
    Generator for label files in the provided directories

    Returns a generator of absolute file paths to the annotation files
    """
    for directory in target_directories:
        for root, dirs, files in os.walk(directory):
            for file in files:
                if file.endswith('.txt'):
                    logging.debug("Found %s", file)
                    yield os.path.join(root, file)

def annotation_files_in_dir(dir: str, skip_directories: List[str], skip_files: List[str]) -> Generator[str, None, None]:
    """
    Generator for annotation files in a directory

    Skips directories and files specified in skip_directories and skip_files

    Returns a generator of absolute file paths
    """
    for root, dirs, files in os.walk(dir):
        logging.debug("%i directories in %s: %s...", len(dirs), root, ' '.join(dirs))
        dirs[:] = [d for d in dirs if d not in skip_directories]
        for file in files:
            if file in skip_files:
                continue
            if file.endswith('.txt'):
                logging.debug("Found %s", file)
                yield os.path.join(root, file)