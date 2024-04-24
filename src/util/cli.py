import argparse
import sys
import os
import logging as log

valid_generators = ["random", "design"]
valid_layouts = ["grid", "flex", "none"]
# Widget types as they are fed into the random UI generator
widget_types = ["arc", "bar", "button", "buttonmatrix", "calendar", "chart", "checkbox", "dropdown", "image", "imagebutton", "keyboard", "label", "led", "line", "list", "menu", "messagebox", "roller", "scale", "slider", "spangroup", "spinbox", "spinner", "switch", "table", "tabview", "textarea", "tileview", "window"]

def create_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description='Invoke the generator and structure the captured UI images into a dataset')
    parser.add_argument('-mpy', '--micropython', type=str, default="", help='Path to the micropython binary')
    parser.add_argument('-m', '--main', type=str, default="", help='Path to the main script')
    parser.add_argument('-o','--output_folder', required=True, help='Folder to save the output images')
    options = parser.add_argument_group('options', 'Additional options')
    options.add_argument('-r', '--split_ratio', type=str, default=None, help='Split ratio for train, val, test')
    options.add_argument('--datalist', type=str, default=None, help='Create a textfile with provided name to write all images and labels')
    options.add_argument('-cwd', '--working_dir', type=str, default=os.path.curdir, help='Working directory for the generator')
    options.add_argument('--clean', action='store_true', help='Clean the output folder before generating new data')
    options.add_argument('-d','--delay', type=int, default=0, help='Fixed delay between each generator call in milliseconds')
    options.add_argument('--dataset', type=str, default='custom', help='Name of the dataset')
    options.add_argument('--continue_on_error', action='store_true', help='Continue running the generator even if an error occurs')
    options.add_argument('--capture_output', action='store_true', help='Capture the output of the generator')
    options.add_argument('--normalize', action='store_true', help='Activate normalize functionality of the generator')
    options.add_argument('-v', '--verbose', action='store_true', help='Enable verbose output')
    clearml = parser.add_argument_group('clearml', 'Options for working with ClearML')
    clearml.add_argument('--clearml_project', type=str, default="LVGL UI Detector", help='ClearML Dataset project name')
    clearml.add_argument('--clearml_task', type=str, default="UI Randomizer", help='ClearML Dataset task name prefix')
    clearml.add_argument('--clearml_upload', action='store_true', help='Upload the created dataset to ClearML')
    run_group = clearml.add_mutually_exclusive_group()
    run_group.add_argument('--clearml_run_as_task', action='store_true', help='Run the randomizer as a ClearML task')
    run_group.add_argument('--clearml_run_as_pipeline', action='store_true', help='Run the randomizer as a ClearML pipeline')
    fix_group = parser.add_argument_group('fixes', 'Annotation fixes')
    fix_group.add_argument('--normalize_bbox', action='store_true', help='Post-process annotation files to normalize bounding boxes')
    fix_group.add_argument('--replace_class_names', action='store_true', help='Replace class names with their index in annotations')
    generators = parser.add_subparsers(dest='generator', help='Generator options')
    random_gen = generators.add_parser('random', help='Random UI generator options')
    random_gen.add_argument('-t','--widget_types', required=True, nargs='+', help='List of widgets to be used in the UI')
    random_gen.add_argument('-W', '--width', type=int, default=250, help='Width of the UI screenshot')
    random_gen.add_argument('-H', '--height', type=int, default=250, help='Height of the UI screenshot')
    random_gen.add_argument('--split_widgets', action='store_true', help='Split widgets into subfolders (only creates one widget type per iteration)')
    random_gen.add_argument('-c', '--count', type=int, default=1, help='Number of widgets to create per iteration')
    random_gen.add_argument('-l', '--layout', type=str, default='none', help='The main container layout of the random UI ["grid", "flex", "none"]')
    random_gen.add_argument('-i', '--iterations', type=int, default=10, help='Number of UIs to generate')
    design_gen = generators.add_parser('design', help='Design file generator options')
    design_gen.add_argument('-f', '--design_folder', type=str, help='Folder containing the design files')
    return parser

def validate_arguments(args):
    # NOTE Validate main input arguments
    if not os.path.exists(args.micropython) or not os.path.isfile(args.micropython):
        if 'MICROPYTHON_BIN' in os.environ:
            args.micropython = os.environ['MICROPYTHON_BIN']
        else:
            log.error("Path to micropython binary '{}' is not valid (does not exist or is not a file).", args.micropython)
            sys.exit(1)
    if not os.path.exists(args.main) or not os.path.isfile(args.main):
        if 'MICROPYTHON_MAIN' in os.environ:
            args.main = os.environ['MICROPYTHON_MAIN']
        else:
            log.error("Path to main script '{}' is not valid (does not exist or is not a file).", args.main)
            sys.exit(1)
    if args.generator not in valid_generators:
        log.error("Generator type '{}' not supported. Please use one of the following: {}", args.generator, ', '.join(valid_generators))
        sys.exit(1)
    if not os.path.exists(args.working_dir) or not os.path.isdir(args.working_dir):
        log.error("Working directory '{}' is not valid (does not exist or is not a directory).", args.working_dir)
        sys.exit(1)
    if args.delay < 0:
        log.error("Delay must be greater than or equal to 0.")
        sys.exit(1)
    if args.split_ratio is not None:
        split_ratio = args.split_ratio.split(',')
        if len(split_ratio) != 3:
            log.error("Split ratio must be in the format 'train,val,test'")
            sys.exit(1)
        split_ratio = [int(ratio) for ratio in split_ratio]
        if sum(split_ratio) != 100:
            log.error("Split ratio must sum up to 100.")
            sys.exit(1)
    if args.clearml_upload and not args.dataset:
        log.error("Dataset name must be provided when uploading.")
        sys.exit(1)
    # NOTE Validate random generator input arguments
    if args.generator == "random":
        if args.iterations <= 0:
            log.error("Number of iterations must be greater than 0.")
            sys.exit(1)
        if args.layout not in valid_layouts:
            log.error("Layout type '{}' not supported. Please use one of the following: {}", args.layout, ', '.join(valid_layouts))
            sys.exit(1)
        if args.width <= 0 or args.height <= 0:
            log.error("Width and height must be greater than 0.")
            sys.exit(1)
        if len(args.widget_types) == 0:
            log.error("At least one widget type must be provided.")
            sys.exit(1)
        # Check if widget types are valid
        for widget in args.widget_types:
            if widget not in widget_types:
                log.error("Widget type '{}' not supported. Please use one of the following: {}", widget, ', '.join(widget_types))
                sys.exit(1)
        if args.count <= 0:
            log.error("Number of widgets to create must be greater than 0.")
            sys.exit(1)
    # NOTE Validate design generator input arguments
    elif args.generator == "design":
        if not os.path.exists(args.design_folder) or not os.path.isdir(args.design_folder):
            log.error("Design folder '{}' is not valid (does not exist or is not a directory).", args.design_folder)
            sys.exit(1)
        elif os.listdir(args.design_folder) == 0:
            log.error("Design folder '{}' is empty.", args.design_folder)
            sys.exit(1)