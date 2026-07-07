#!/bin/bash
cd "$(dirname "$0")/.."
colcon build --symlink-install
source install/setup.bash