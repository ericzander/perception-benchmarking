# osrf/ros:jazzy-desktop matches the ROS docker container Isaac Sim's docs
# use for the ROS 2 bridge, per "Running ROS in Docker Containers":
# https://docs.isaacsim.omniverse.nvidia.com/6.0.1/installation/install_ros.html
# The rest of this Dockerfile (apt packages, venv, CMD) is extra infra.
FROM osrf/ros:jazzy-desktop

SHELL ["/bin/bash", "-c"]

RUN apt-get update && apt-get install -y --no-install-recommends \
        python3-colcon-common-extensions \
        python3-rosdep \
        python3-venv \
        ros-jazzy-cv-bridge \
        ros-jazzy-image-transport \
        ros-jazzy-vision-msgs \
        ros-jazzy-rqt-image-view \
        build-essential \
        git \
    && rm -rf /var/lib/apt/lists/*

# --system-site-packages lets the venv see rclpy, cv_bridge, and other
# ROS Python packages installed through apt above.
RUN python3 -m venv --system-site-packages /opt/project-venv
ENV PATH="/opt/project-venv/bin:${PATH}"

COPY requirements.txt /tmp/requirements.txt
RUN python -m pip install --upgrade pip \
    && python -m pip install -r /tmp/requirements.txt

# infra/start-ros.sh runs this container with --user <host UID>:<host GID> so
# files created in the bind-mounted project (colcon build/, ros2 pkg create,
# etc.) are owned by the host user instead of root
ENV HOME=/tmp
RUN echo "source /opt/ros/jazzy/setup.bash" >> /etc/bash.bashrc

WORKDIR /workspace/project

CMD ["sleep", "infinity"]
