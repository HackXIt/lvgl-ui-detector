from clearml import StorageManager, Dataset
import os

# Create a new dataset
ui_designs = Dataset.create(dataset_name='UI Designs', dataset_project='LVGL UI Detector')
ui_randoms = Dataset.create(dataset_name='UI Randoms', dataset_project='LVGL UI Detector')
ui_widgets = Dataset.create(dataset_name='UI Widgets', dataset_project='LVGL UI Detector')

# Add files
ui_designs.add_files(path=os.path.join(os.path.curdir, "tmp", "designs"))
ui_designs.add_files(path=os.path.join(os.path.curdir, "tmp", "designs.yaml"))
ui_randoms.add_files(path=os.path.join(os.path.curdir, "tmp", "random_uis"))
ui_randoms.add_files(path=os.path.join(os.path.curdir, "tmp", "random_uis.yaml"))
ui_widgets.add_files(path=os.path.join(os.path.curdir, "tmp", "random_widgets"))
ui_widgets.add_files(path=os.path.join(os.path.curdir, "tmp", "random_widgets.yaml"))

# Upload
ui_designs.upload()
ui_randoms.upload()
ui_widgets.upload()

# Commit changes
ui_designs.finalize()
ui_randoms.finalize()
ui_widgets.finalize()
