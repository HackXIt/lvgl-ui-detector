import cv2
import os
import yaml
import matplotlib.pyplot as plt

def load_dataset_config(yaml_path):
    """
    Load dataset configuration from a YAML file.
    """
    with open(yaml_path, 'r') as file:
        dataset_config = yaml.safe_load(file)
    return dataset_config

def draw_yolo_annotations(image, annotations, class_names):
    """
    Draw YOLO annotations on an image.
    """
    height, width = image.shape[:2]
    
    for annotation in annotations:
        class_id, x_center, y_center, w, h = map(float, annotation.split())
        x_center, y_center, w, h = x_center * width, y_center * height, w * width, h * height
        x_min, y_min = int(x_center - w / 2), int(y_center - h / 2)

        cv2.rectangle(image, (x_min, y_min), (int(x_min + w), int(y_min + h)), (255, 0, 0), 2)
        label = class_names[int(class_id)]
        cv2.putText(image, label, (x_min, y_min - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255,255,255), 1)

    return image

def show_images_with_annotations(base_path, image_paths, class_names):
    """
    Display a grid of images with their YOLO annotations.
    """
    plt.figure(figsize=(12, 12))
    for i, image_path in enumerate(image_paths, 1):
        image = cv2.imread(os.path.join(base_path, image_path))
        # Images are already in RGB format
        #image = cv2.cvtColor(image, cv2.COLOR_RGB)
        print(f"Image path: {image_path}")
        annotation_path = os.path.join(base_path, image_path).replace("images", "labels").replace(".jpg", ".txt")
        print(f"Annotation path: {annotation_path}")
        with open(annotation_path, "r") as file:
            annotations = file.readlines()

        image_with_annotations = draw_yolo_annotations(image, annotations, class_names)
        
        plt.subplot(3, 3, i)
        plt.imshow(image_with_annotations)
        plt.axis('off')
    plt.show()