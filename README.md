# lvgl-ui-detector

This machine learning project is a user interface widget detector for the [LVGL](https://lvgl.io/) framework. The base model is the [YOLOv4]() object detection algorithm, trained on the [RICO]() dataset.

It was fine-tuned specifically for the LVGL framework, and is able to detect the following widgets:

- Button
- Switch
- Slider
- Checkbox
- Label
- TODO ...(add more)

The model is able to detect these widgets in a variety of different contexts, including:

- TODO

# Note

This project was created for my bachelor thesis at the University of Applied Sciences Technikum Vienna.

All relevant documentation about the project can be found in the [thesis](thesis.pdf) under the `doc` folder.

The project is still a work in progress. The model is not yet trained and the UI generator is not yet fully functional.

## The LVGL UI generator

The UI generator is a modification of the LVGL simulator for PC to generate synthetic UIs. 
It is based on the [lv_port_pc_vscode](https://github.com/lvgl/lv_port_pc_vscode) since that is the IDE I use and also the only one I could get to work with my poor generator code.

It is able to generate a single UI with a varied number of widgets and then create a screenshot of the holding container. The container of the widgets determines the size of the resulting screenshot.

Alongside the screenshot it also generates a text file with the bounding boxes of the placed widgets. 
*(YOLO format: `<label> <x_center> <y_center> <width> <height>`, values are in pixels)* 
This information can later be used to build a dataset for training the model.

### Usage

TODO ... (add usage instructions for binary)

### Known issues

- The generator currently will always crash in a SEGFAULT when exiting the program. I have not yet found a way to fix it. For now it is fine since it correctly generates the screenshot and the label file. The crash occurs during de-initialization of the UI.
- Due to the failed de-initialization, the generator will leak memory and sometimes will fail on multiple runs. Retrying usually fixes the issue.
- Due to memory issues, screenshots larger than 400x400 pixels will cause the generator to crash. This is a known issue with the generator and I have not yet found a way to fix it.

## The UI randomizer

The UI randomizer is a python script that leverages the binary of the UI generator, and uses it to generate multiple random UI in sequence. 

It is helpful in making the generator much more user-friendly, since it can be used to generate a large number of UIs with a single command, without having to repeatedly run the generator manually.

Since the label data from the generator still needs to be normalized, the randomizer will pre-process the annotation files and place the data in the correct folder structure for training the model.

### Usage

TODO ... (add usage instructions for script)

### Known issues

- The code is not very well written and currently just performs the bare minimum to get the job done. It is not very error-friendly and could use some refactoring.

## The model

The model is a YOLOv4 object detection model, trained on the RICO dataset and fine-tuned for the LVGL framework.

Code can be found in the `notebook` folder.

TODO ... (add more)

# Milestones

- [x] Create UI generator
- [x] Create UI randomizer
- [ ] Create model
- [ ] Make model predict the pre-defined widget list

# Feature roadmap

- [ ] Add widget customization in generator (color, size, etc.)
- [ ] Add UI presets in generator (e.g. login screen, settings screen, etc.)
- [ ] Add more widgets
- [ ] Add 
