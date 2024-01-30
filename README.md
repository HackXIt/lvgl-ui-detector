# LVGL UI Detector

This machine learning project is a user interface widget detector for the [LVGL](https://lvgl.io/) framework. The base is the [YOLOv8 model](https://github.com/ultralytics/ultralytics), trained on the synthesized dataset from the programs/scripts in this repository.

The purpose of the model is to detect and locate widgets from a provided screenshot to aid in automated testing procedures requiring this information.

It was fine-tuned specifically for the LVGL framework, and is able to detect the following widgets:

- Button
- Switch
- Slider
- Checkbox
- Label
- ...(more to come in the future)

The model is able to detect these widgets in a variety of different contexts, including:

- (work in progress)

# Creator's Note

This project was created for my bachelor thesis at the [University of Applied Sciences Technikum Vienna](https://www.technikum-wien.at/en/).

All currently relevant information can be found in the [Exposé](./doc/Exposé_Precision_at_Pixel_Level___YOLOv8_vs__conventional_embedded_UI_testing.pdf) and later on in the [thesis](./doc/Thesis.pdf) itself.

The project is still a work in progress. The model is not yet properly trained and the UI generator is not yet fully functional.

----

## The LVGL UI generator

The UI generator is a modification of the LVGL simulator for PC to generate synthetic UIs. 
It is based on the [lv_port_pc_vscode](https://github.com/lvgl/lv_port_pc_vscode) since that is the IDE I use and also the only one I dared to modify.

When launched with the proper arguments, it will open a window with a single container widget of the provided size placed inside. After rendering the UI, it will generate a screenshot of the container and save it to the provided path. It will also generate a text file with the bounding boxes of the placed widgets.

Keep in mind, that the provided path must be prefixed with `/` as that is the local file system indicator for LVGL, otherwise it doesn't know where to save the file (i.e. which file driver to use). Also the generated label file uses the widget name instead of a class id and the bounding box is in pixel values. This is by design, as it is far easier to perform the proper normalization and class ID replacement in python.

The generated UI places randomly chosen widgets from the provided widget list. The supported widget list is currently limited to the following: 
_(the names to the left are valid arguments for the generator, the right ones are the LVGL widget names)_
- `button` -> `lv_btn`
- `switch` -> `lv_switch`
- `slider` -> `lv_slider`
- `checkbox` -> `lv_checkbox`	
- `label` -> `lv_label`
- `progressbar` -> `lv_bar`

The generated label `*.txt` file follows the YOLO format for the bounding boxes. 
_(YOLO format: `<label> <x_center> <y_center> <width> <height>`, values are in pixels)_
This information can later be used to build a dataset for training the model when processed with the UI randomizer.

### Usage

To use the Random UI Generator, open a terminal or command-line interface and navigate to the directory containing the binary. Use the following command structure:

`./random_ui_generator [options]`

#### Options

    -w <width>: (Required) Width of the UI screenshot in pixels.
    -h <height>: (Required) Height of the UI screenshot in pixels.
    -c <widget_count>: (Required) Number of widgets to include in the UI.
    -t <widget_types>: (Required) Comma-separated list of widget types to include (e.g., button,slider).
    -o <output_file>: (Required) Path to save the generated screenshot.
        Must be prefixed with /.
        Annotations will be saved in a .txt file with the same name.
    -d <screenshot_delay>: Delay in seconds before capturing the screenshot. Useful for ensuring UI rendering is complete.
    -l <layout>: Layout option for arranging widgets (optional).

#### Example

To generate a UI with a width of 500 pixels, height of 500 pixels, containing 3 widgets of types button and slider, with an absolute layout, and saving the output to ui_output.jpg with a delay of 5000 milliseconds, the command would be:

`./random_ui_generator -w 500 -h 500 -c 3 -t button,slider -o /ui_output.jpg -d 5 -l none`

### Known issues

- The generator currently will always crash in a SEGFAULT when exiting the program. For now it is fine since it correctly generates the screenshot and the label file. The crash occurs during de-initialization of the UI due to an already missing image for the application. I believe it is due to the mouse cursor icon when using X11. I have not yet found a way to fix it.
- Due to the failed de-initialization, the generator will leak memory and sometimes will fail on multiple runs. Retrying usually fixes the issue. Rerunning the generator multiple times in a row will however clog up memory and possibly cause issues that come with that effect.
- The memory of the LVGL driver is currently set to `(2048U * 2048U)`. The main window size in which the screenshot container is placed is 1024x800. Any image sizes that either exceed this memory limitation or exceed the window size will cause the generator to crash. In general, if causing issues, this can be changed in `lv_conf.h` and `lv_demo_conf.h` respectively.

----

## The UI randomizer

The UI randomizer is a python script that leverages the binary of the UI generator, and uses it to generate multiple random UI in sequence. 

It is helpful in making the generator much more user-friendly, since it can be used to generate a large number of UIs with a single command, without having to repeatedly run the generator manually.

Since the label data from the generator still needs to be normalized, the randomizer will pre-process the annotation files and place the data in the correct folder structure for training the model.

### Usage
`python ui_capture.py [arguments]`

#### Arguments

The script accepts several arguments to customize the dataset generation:

    -p or --app_path: (Required) Path to the random UI generator binary.
    -i or --iterations: Number of user interface screenshots to generate (default: 10).
    -t or --widget_types: (Required) List of widget types to be included in the UI. The names of these types must match the naming convention of the generator (e.g. button, checkbox, etc.).
    --width: Width of the UI screenshot (default: 250).
    --height: Height of the UI screenshot (default: 250).
    -o or --output_folder: (Required) Folder path to save the output images.
    -d or --delay_count: Delay count for UI capture (default: 10).
    --split_widgets: Option to split widgets into subfolders.
    -l or --layout: The used layout in the generation:
        - `none` (randomized absolute positions)
        - `grid` (randomized cell placement - grid size is the amount widgets squared, e.g. 9x9 for 9 widgets)
        - `flex` (randomized flexbox placement)
    -r or --split_ratio: Split ratio for train, validation, and test datasets.
    -s or --single: Create only a single widget per iteration.
    -m or --multi: Number of widgets to create per iteration (if multiple).

#### Example
An example command might look like this:

`python ui_capture.py -p path/to/ui/generator -i 20 -t button checkbox -o path/to/output -d 5 --split_widgets`

The script will generate the UI images and organize them into a dataset placed into the specified output folder. It creates necessary subfolders for images and labels. The script will also automatically pre-process the label data _(i.e. normalize pixel values and replace widget names with class IDs)_.

### Known issues

- The code is not very well written and currently just performs the bare minimum to get the job done. It is not very error-friendly and could use some refactoring.

----

## The model

The base model is the YOLOv8 object detection model. For early testing, the provided weights from the official YOLOv8 image were used. Later, a new base model will be trained using YOLOv8 and a custom generated dataset. This base model will then be fine-tuned with proprietary user interface screenshots.

Code can be found in the [notebook of the root repository](lvgl-ui-detector_yolov8.ipynb). `(lvgl-ui-detector_yolov8.ipynb)`

Other notebooks are still a work in progress and will be updated later but serve as a placeholder for now.

----

# Milestones

- [x] Create UI generator
- [x] Create UI randomizer
- [x] Create model
- [x] Make model predict the pre-defined widget list
- [ ] Finished bachelor thesis
- [ ] Didn't catch burn-out syndrome

# Feature roadmap

- [ ] Add more widgets to the generator and model
- [ ] Improve dataset size (min. 50 per class) and training process (1-click-pipeline)
- [ ] Add widget customization in generator (color, size, etc.)
- [ ] Add design file system for randomizer & generator
- [ ] Add UI presets in generator (e.g. login screen, settings screen, etc.)
