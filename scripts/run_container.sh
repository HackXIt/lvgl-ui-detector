#!/bin/bash

# $1 = container name
# $2 = port
# $3 = mount directory

# Check parameters and override default variables if provided
container_name=${1:-ultralytics-dev}
port=${2:-8888}
mount_dir=${3:-$(pwd)}

docker run -d \
    --name $container_name \
    -v "$mount_dir:/workspace/project/" \
    -p $port:8888 \
    hackxit/ui-detector:jupyter-dev-dark