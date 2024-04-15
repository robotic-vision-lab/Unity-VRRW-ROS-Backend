## Virtual Reality Robotic Workspace (ROS-Side Package) 

### Overview 

This repository contains the ROS-side package to communicate and control a
simulated or real (e.g., UR5e) robot through a Unity UI for the virtual reality
robotic workspace software project.

### Citation

If you find this project useful, then please consider citing our work.

```bibitex
@inproceedings{tram2023intuitive,
  title={Intuitive Robot Integration via Virtual Reality Workspaces},
  author={Tram, Minh Q. and Cloud, Joseph M. and Beksi, William J},
  booktitle={Proceedings of the IEEE International Conference on Robotics and Automation (ICRA)},
  pages={11654--11660},
  year={2023}
}
```

### Quick Start

1. Clone this repository and `cd` into it:

```console
user@DESKTOP:~$ git clone https://github.com/robotic-vision-lab/VRRW-ROS.git
user@DESKTOP:~$ cd VRRW-ROS 
```

2. Build or pull the Docker image:

```console
user@DESKTOP:~$ docker pull mqt0029/robosim:noetic
```

3. Run the Docker container:

A convenient script is provided to run the Docker container. The script will do
the following:

- Create a container if it does not exist.
- If the container exists, then it will start the container and attach to it.
- Mount the `catkin_ws` directory to the container.
- Expose sufficient ports and devices for rendering and ROS communication.

A subsequent re-run of the script will just attach to the existing container.

```console
user@DESKTOP:~$ ./run_container.sh
```

Several convenient aliases have also been defined in the container. They will
be listed when a user attaches to the container.

```
user@DESKTOP:~$ ./run_container.sh
non-network local connections being added to access control list
predefined aliases: src_ros, run_rosdep, run_catkin, rebuild_catkin, kill_gazebo, kill_rviz

root ~/catkin_ws
>
```

4. Install the dependencies and build the catkin workspace:

```console
root ~/catkin_ws
> run_rosdep

[...]

root ~/catkin_ws
> run_catkin

[...]

root ~/catkin_ws
> src_ros
```

> 🗒️ **In order for autocomplete to find all ROS commands and packages, for
every new terminal or package rebuild you must run `src_ros` to source the ROS 
environment.**

5. Run the simulation or real robot control backend:

```console
root ~/catkin_ws
> roslaunch rvl_unity_communicator start_backend.launch
```

or

```console
root ~/catkin_ws
> roslaunch rvl_unity_communicator start_real_robot.launch
```

> 🗒️ **Remember to modify the `start_real_robot.launch` file to match your robot's and control computer's IP addresses.**

6. Start the Unity-side application package:

Refer to the [VRRW-Unity](https://github.com/robotic-vision-lab/VRRW-Unity.git) repository for more information.

### Troubleshooting

In many cases, the most common issues are the following:

1. Either the ROS-side, Unity-side, or physical robot (if applicable), does not
   have proper permissions to communicate through the LAN. To ensure that all
   devices are able to communicate with each other, a simple ping test may 
   suffice:

```console
user@DESKTOP:~$ ping <IP_ADDRESS>
```

Raw IP address i.e. `192.168.___.___` is preferred over hostname i.e. `localhost` or `robot.local`,
however, we have not experienced any issues with the hostname.

2. On the Unity-side application, the ROS configuration is incorrect. Ensure
   that the `ROS IP Adress` under `Robotics > ROS Settings` is set to the IP
   address of the ROS-side computer where this package is running.

### License

[![license](https://img.shields.io/badge/license-Apache%202-blue)](https://github.com/robotic-vision-lab/VRRW-ROS/blob/ros1/LICENSE)
