# if .bash_aliases exists, it WILL be source by default bash (at least on Ubuntu)
# so you can actually define some configs here...

# ------------------------------- BASH CONFIGS ------------------------------- #

# always source the default catkin setup.bash
source ${CATKIN_WS}/devel/setup.bash

# auto cd into catkin workspace instead of / (base path)
cd ${CATKIN_WS}

# nice, shorter prompt
PS1='\n\[\e[0;38;5;122m\]\u \[\e[0;38;5;147m\]\w\n\[\e[0m\]> \[\e[0m\]'

# unlimited history
export HISTSIZE=-1
export HISTFILESIZE=-1

# time stamping history
export HISTTIMEFORMAT="[%F %T] "

# Change the file location because certain bash sessions truncate .bash_history file upon close.
# http://superuser.com/questions/575479/bash-history-truncated-to-500-lines-on-each-login
export HISTFILE=~/.bash_eternal_history

# Force prompt to write history after every command.
# http://superuser.com/questions/20900/bash-history-loss
export PROMPT_COMMAND="history -a; history -n; $PROMPT_COMMAND"

# Appending history across sessions
shopt -s histappend

# ------------------------------- BASH ALIASES ------------------------------- #

# TBA

# -------------------------------- ROS ALIASES ------------------------------- #

alias src_ros='source ${CATKIN_WS}/devel/setup.bash'

alias run_rosdep='cd ${CATKIN_WS} && rosdep update && rosdep install --from-paths src --ignore-src -r -y'

alias run_catkin='catkin build -DCMAKE_BUILD_TYPE=Debug'

alias rebuild_catkin='catkin clean -y && catkin build --cmake-args -DCMAKE_BUILD_TYPE=Debug'

# ------------------------------ DOCKER ALIASES ------------------------------ #

# https://gist.github.com/jgrodziski/9ed4a17709baad10dbcd4530b60dfcbb
function dexec_func
{ 
    docker exec -i -t $1 ${2:-bash}
}

function dcrm_func
{
    docker container stop $1 && docker container rm $1
}

# short-hand for docker ps -a with extra info
alias dclsa='docker container ls --all --no-trunc --size'

# short-hand for docker container ls
alias dcls='docker container ls'

# short-hand for docker image ls with extra info
alias dilsa='docker image ls --all'

# short-hand for docker image ls
alias dils='docker image ls'

# docker container rm [id]
alias dcrm=dcrm_func

# docker image rm [id]
alias dirm='docker image rm'

# delete all containers including volumes
alias dcrma='docker container prune --force'

# delete all images
alias dirma='docker image prune --force'

# delete everything
alias docker_clean='docker system prune -a --volumes'

# docker start [container name]
alias dstart='docker start'

# docker stop [container name]
alias dstop='docker stop'

# docker restart [container name]
alias drestart='docker restart'

# docker exec
alias dexec=dexec_func
