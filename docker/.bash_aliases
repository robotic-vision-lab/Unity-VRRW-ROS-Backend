# if .bash_aliases exists, it WILL be source by default bash (at least on Ubuntu)
# so you can actually define some configs here...

# ------------------------------- BASH CONFIGS ------------------------------- #

# always source the default catkin setup.bash
source ${CATKIN_WS}/devel/setup.bash

# auto cd into catkin workspace instead of / (base path)
cd ${CATKIN_WS}

# nice, shorter prompt
PS1='\n\[\e[0;38;5;122m\]\u \[\e[0;38;5;147m\]\w\n\[\e[0m\]> \[\e[0m\]'

# -------------------------------- ROS ALIASES ------------------------------- #

alias src_ros='source ${CATKIN_WS}/devel/setup.bash'

alias run_rosdep='apt-get update -qq && cd ${CATKIN_WS} && rosdep update && rosdep install --from-paths src --ignore-src -r -y'

alias run_catkin='catkin build --cmake-args -Wno-dev -DCMAKE_BUILD_TYPE=Debug && src_ros'

alias rebuild_catkin='catkin clean -y && catkin build --cmake-args -Wno-dev -DCMAKE_BUILD_TYPE=Debug && src_ros'

alias kill_gazebo="ps -aux | grep gazebo | egrep -v color | awk '{print \$2}' | xargs kill -9"

alias kill_rviz="ps -aux | grep rviz | egrep -v color | awk '{print \$2}' | xargs kill -9"

echo "predefined aliases: src_ros, run_rosdep, run_catkin, rebuild_catkin, kill_gazebo, kill_rviz"