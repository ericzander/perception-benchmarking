#!/usr/bin/env bash
# --network host and ROS_DOMAIN_ID are per docs ("Running ROS in Docker
# Containers", which needs --net=host for Isaac Sim <-> ROS communication):
# https://docs.isaacsim.omniverse.nvidia.com/6.0.1/installation/install_ros.html
# Everything else here (detached/named run instead of their -it --rm, --gpus
# for later training work, the FASTRTPS_DEFAULT_PROFILES_FILE mount matching
# infra/fastdds.xml, RMW_IMPLEMENTATION, and the project mount) is extra.
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

docker rm -f robot-benchmark-ros >/dev/null 2>&1 || true

docker run -d \
    --name robot-benchmark-ros \
    --network host \
    --gpus all \
    --user "$(id -u):$(id -g)" \
    --env ROS_DOMAIN_ID="${ROS_DOMAIN_ID:-0}" \
    --env RMW_IMPLEMENTATION=rmw_fastrtps_cpp \
    --env FASTRTPS_DEFAULT_PROFILES_FILE=/root/.ros/fastdds.xml \
    --volume "$PROJECT_ROOT/infra/fastdds.xml:/root/.ros/fastdds.xml:ro" \
    --volume "$PROJECT_ROOT:/workspace/project" \
    --workdir /workspace/project \
    robot-benchmark-ros:jazzy

echo "ROS container started."
echo
echo "Enter it with:"
echo "docker exec -it robot-benchmark-ros bash"
