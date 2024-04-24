import os
from typing import List
from typing import Generator
import logging

from util import generators

def normalize_bbox(bbox: List[str], img_width: int, img_height: int) -> List[str]:
    """
    Normalize YOLO bounding box to be between 0 and 1

    Values are expected to be in pixels
    """
    logging.debug("BBOX before: %s", ' '.join(bbox))
    for i, x in enumerate(bbox):
        x = float(x)
        if i % 2 == 0:
            x /= img_width
        else:
            x /= img_height
        bbox[i] = str(x)
    logging.debug("BBOX after: %s", ' '.join(bbox))
    return bbox

def normalize_bbox_in_label_file(file: str, img_width: int, img_height: int) -> None:
    """
    Overwrite a dataset file with normalized bounding boxes

    Expecting lines of the file to be in YOLO format: <class_id> <x> <y> <width> <height>
    """
    with open(file, 'r+') as f:
        lines = f.readlines()
        for i, line in enumerate(lines):
            line = line.split(' ')
            if len(line) < 5:
                logging.error("Invalid line #%i in %s: %s", i, file, line)
                continue
            bbox = normalize_bbox(line[1:5], img_width, img_height) # Skip class_id
            line = f"{line[0]} {' '.join(bbox)}\n"
            lines[i] = line
        f.seek(0)
        f.writelines(lines)
        f.truncate()

def annotation_files(dir: str, skip_directories: List[str], skip_files: List[str]) -> Generator[int, None, None]:
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

def normalize_bbox_in_label_files_of_dir(root: str, img_width: int, img_height: int, skip_directories: List[str] = ['rico'], skip_files: List[str] = ['test.txt', 'train.txt', 'val.txt']) -> None:
    """
    Recursively normalize all bounding boxes in a dataset directory

    Skips by default directories named 'rico' and files named 'test.txt', 'train.txt', and 'val.txt'
    """
    for file in annotation_files(root, skip_directories, skip_files):
        logging.debug(f"Normalizing {file}...")
        normalize_bbox_in_label_file(root, file, img_width, img_height)

def normalize_bbox_in_label_files_of_dirs(img_width: int, img_height: int, target_directories: List[str]) -> None:
    """
    Recursively normalize all bounding boxes in a dataset directory

    Skips by default directories named 'rico' and files named 'test.txt', 'train.txt', and 'val.txt'
    """
    for file in generators.annotation_files_in_dirs(target_directories):
        logging.debug(f"Normalizing {file}...")
        normalize_bbox_in_label_file(file, img_width, img_height)

if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG, format='%(levelname)s %(message)s')
    root = os.path.join(os.getcwd(), 'data')
    normalize_bbox_in_label_files_of_dir(root, 416, 416) # Use default skip_directories and skip_files