import os
import json
from PIL import Image

def get_image_info(image_path):
    with Image.open(image_path) as img:
        width, height = img.size
    return width, height

def convert_yolo_to_coco(yolo_folder, image_folder):
    categories = set()
    annotations = []
    images = []
    img_id_map = {}
    ann_id = 1
    img_id = 1

    for filename in os.listdir(yolo_folder):
        if filename.endswith('.txt'):
            image_filename = filename.split('.')[0] + '.jpg'
            image_path = os.path.join(image_folder, image_filename)
            width, height = get_image_info(image_path)

            images.append({
                "id": img_id,
                "width": width,
                "height": height,
                "file_name": image_filename
            })
            img_id_map[image_filename] = img_id
            img_id += 1

            annotation_path = os.path.join(yolo_folder, filename)
            with open(annotation_path, 'r') as file:
                for line in file:
                    category_id, x_center, y_center, w, h = map(float, line.strip().split())
                    categories.add(category_id)

                    # Convert x_center, y_center, w, h from normalized YOLO format to COCO format
                    x_min = (x_center - w / 2) * width
                    y_min = (y_center - h / 2) * height
                    bbox_width = w * width
                    bbox_height = h * height

                    annotations.append({
                        "id": ann_id,
                        "image_id": img_id_map[image_filename],
                        "category_id": int(category_id),
                        "bbox": [x_min, y_min, bbox_width, bbox_height],
                        "area": bbox_width * bbox_height,
                        "segmentation": [],
                        "iscrowd": 0
                    })
                    ann_id += 1

    return categories, annotations


def format_categories(categories):
    return [{"id": int(cat_id), "name": str(cat_id)} for cat_id in categories]


def save_coco_format(output_json_path, output_json_name, images, annotations, categories):
    coco_format = {
        "images": images,
        "annotations": annotations,
        "categories": categories
    }

    os.makedirs(os.path.dirname(output_json_path), exist_ok=True)
    with open(os.path.join(output_json_path, output_json_name), 'w') as f:
        json.dump(coco_format, f, indent=4)


def yolo_to_coco_annotation(yolo_folder, image_folder, output_json_path, output_json_name):
    images = []
    categories, annotations = convert_yolo_to_coco(yolo_folder, image_folder)
    categories = format_categories(categories)
    save_coco_format(output_json_path, output_json_name, images, annotations, categories)

if __name__ == '__main__':
    yolo_folder = os.path.join(os.getcwd(), 'data', 'val')
    image_folder = os.path.join(os.getcwd(), 'data', 'val')
    output_json_path = os.path.join(os.getcwd(), 'data/rico/annotations')
    output_json_name = 'instances_val.json'
    yolo_to_coco_annotation(yolo_folder, image_folder, output_json_path, output_json_name)