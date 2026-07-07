#!/bin/bash
cd "$(dirname "$0")/../src"
ros2 pkg create --build-type ament_python --node-name image_listener perception_bridge
cd -
rosdep install --from-paths src --ignore-src -r -y