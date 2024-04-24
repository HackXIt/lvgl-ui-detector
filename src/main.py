from clearml import PipelineDecorator
from generate import *
from train import *

@PipelineDecorator.pipeline(name="UI Detector Training Pipeline", project="LVGL UI Detector", version="0.1.0", abort_on_failure=True)
def main(args):
    dataset_id = clearml_main(args)
    env = Environment()
    training_task(env, "yolov5n", dataset_id, args)

if __name__ == "__main__":
    PipelineDecorator.debug_pipeline()
    parser = create_parser()
    args = parser.parse_args()
    validate_arguments(args)
    main(args)
    print("completed")