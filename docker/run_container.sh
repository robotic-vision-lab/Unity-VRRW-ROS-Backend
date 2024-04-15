#!/usr/bin/env bash

# get the full path of the script parent directory
SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )

# extension of usage of SCRIPT_DIR
# get the path of the included colcon_ws
HOST_CATKIN_WS=$( cd "${SCRIPT_DIR}/../catkin_ws/src" &> /dev/null && pwd )

# name of the container to be created
CONTAINER_NAME=unity-vrrw-ROS-side-container

# docker image and tag to use
DOCKER_IMAGE=mqt0029/robosim:noetic

# get docker container ID if exists
CONTAINER_ID=`docker ps -aqf "name=^/${CONTAINER_NAME}$"`

# if container with name not found
if [ -z "${CONTAINER_ID}" ]; then

    # creating the docker container
    docker run \
    --tty \
    --detach \
    --privileged \
    --publish 10000:10000 \
    --name ${CONTAINER_NAME} \
    -e DISPLAY=$DISPLAY \
    -v /tmp/.X11-unix:/tmp/.X11-unix \
    -v ${HOST_CATKIN_WS}:/root/catkin_ws/src \
    ${DOCKER_IMAGE}

else

    # allow UI spawning through X server
    xhost +local:`docker inspect --format='{{ .Config.Hostname }}' ${CONTAINER_ID}`

    # check if the container is already running and start if necessary.
    if [ -z `docker ps -qf "name=^/${CONTAINER_NAME}$"` ]; then
        docker start ${CONTAINER_ID}
    fi

    # actually attaching to container
    docker exec -it ${CONTAINER_ID} bash

    # disallow UI spawning through X server
    xhost -local:`docker inspect --format='{{ .Config.Hostname }}' ${CONTAINER_ID}`

fi
