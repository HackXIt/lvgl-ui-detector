#!/bin/bash

# $1 = container name
# $2 = port
# $3 = mount directory

# Check parameters and override default variables if provided
container_name=${1:-ultralytics-dev}
port=${2:-8888}
mount_dir=${3:-$(pwd)}

# Check if container with given name already exists
if docker ps -a --format '{{.Names}}' | grep -q "^$container_name$"; then
    # Container exists, start it
    docker start $container_name
else
    # Container does not exist, create a new one
    docker run -d \
        --gpus all \
        --name $container_name \
        -v "$mount_dir:/workspace/project/" \
        -p $port:8888 \
        hackxit/ui-detector:jupyter-dev-dark
fi