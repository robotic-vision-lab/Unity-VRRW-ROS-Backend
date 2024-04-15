# using OSRF ROS Noetic 
FROM osrf/ros:noetic-desktop-full-focal

# no prompts from apt-get
ARG DEBIAN_FRONTEND=noninteractive

# use bash as primary shell for RUN commands
SHELL [ "/bin/bash", "-c" ]

# installing initial setup packages
RUN apt-get update && apt-get -y --no-install-recommends install \
    git \
    curl \
    wget \
    build-essential \
    cmake \
    lsb-release \
    python3-pip \
    python3-dev \
    gnupg2 \
    libxext6 \
    libx11-6 \
    libglvnd0 \
    libgl1 \
    libglx0 \
    libegl1 \
    freeglut3-dev \
    net-tools \
    mesa-utils \
    mesa-utils-extra \
    locales \
    net-tools \
    software-properties-common \
    && apt-get -y autoremove \
    && apt-get clean

# installing ROS dependencies
RUN apt-get update && apt-get -y --no-install-recommends install \
    ros-noetic-desktop-full \
    ros-noetic-moveit \
    ros-noetic-moveit-resources \
    ros-noetic-moveit-visual-tools \
    ros-noetic-moveit-resources-prbt-moveit-config \
    ros-noetic-pilz-industrial-motion \
    ros-noetic-gazebo-ros \
    ros-noetic-gazebo-ros-control \
    ros-noetic-ros-control \
    ros-noetic-ros-controllers \
    ros-noetic-roboticsgroup-upatras-gazebo-plugins \
    python3-rosdep \
    python3-rosinstall \
    python3-rosinstall-generator \
    python3-wstool \
    python3-catkin-tools

# installing Gazebo 11
RUN sh -c 'echo "deb http://packages.osrfoundation.org/gazebo/ubuntu-stable `lsb_release -cs` main" > /etc/apt/sources.list.d/gazebo-stable.list' && \
    wget https://packages.osrfoundation.org/gazebo.key -O - | apt-key add - && \
    apt-get update && apt-get -y --no-install-recommends install gazebo11 libgazebo11-dev

# upgrade MESA for Ignition Gazebo
RUN add-apt-repository ppa:kisak/kisak-mesa && \
    apt-get update && \
    apt-get -y full-upgrade

# define catkin workspace
ENV HOME /root
ENV CATKIN_WS /root/catkin_ws
ENV CATKIN_SRC /root/catkin_ws/src

# setup environment
ENV LANG C.UTF-8
ENV LC_ALL C.UTF-8
ENV ROS_DISTRO noetic
ENV QT_X11_NO_MITSHM 1
ENV TERM xterm-256color

# setup catkin workspace
# https://wiki.ros.org/rosdep
RUN rm -f /etc/ros/rosdep/sources.list.d/20-default.list && \
    rosdep init && \
    rosdep update && \
    source /opt/ros/${ROS_DISTRO}/setup.bash && \
    mkdir -p ${CATKIN_SRC} && \
    cd ${CATKIN_WS} && \
    catkin init && \
    rosdep install --from-paths src --ignore-src -r -y && \
    catkin build --cmake-args -DCMAKE_BUILD_TYPE=Release

# convenient aliases
COPY .bash_aliases /root/.bash_aliases
