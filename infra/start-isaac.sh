#!/usr/bin/env bash
# PUBLIC_IP/ISAACSIM_HOST/ISAAC_SIM_IMAGE and the docker compose invocation
# below are the documented Brev + prebuilt-image workflow, per docs:
# https://docs.isaacsim.omniverse.nvidia.com/6.0.1/installation/install_advanced_cloud_setup_brev.html
# https://docs.isaacsim.omniverse.nvidia.com/6.0.1/installation/install_container.html
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ISAAC_INFRA="$HOME/IsaacSim"
PUBLIC_IP="${ISAACSIM_HOST:-$(curl -fsS ifconfig.me)}"

export PROJECT_ROOT
export ISAACSIM_HOST="$PUBLIC_IP"
export ISAAC_SIM_IMAGE="nvcr.io/nvidia/isaac-sim:6.0.1"
export ISAAC_SIM_DATA="$HOME/docker/isaac-sim"
# See isaac-compose.override.yml: overrides the base compose file's fixed
# uid 1234, which gets silently remapped to nobody on write on this host.
export HOST_UID="$(id -u)"
export HOST_GID="$(id -g)"

cd "$ISAAC_INFRA"

# The override file layers in the FastDDS fix (see its own comment) for our
# separate-ROS-container setup; NVIDIA's examples don't cover that scenario,
docker compose \
    -p isim \
    -f tools/docker/docker-compose.yml \
    -f "$PROJECT_ROOT/infra/isaac-compose.override.yml" \
    up --build -d

echo
echo "Isaac Sim starting."
echo "Browser viewer: http://${PUBLIC_IP}:8210 (Chrome or Edge)"
echo "Or connect with the native WebRTC Streaming Client to ${PUBLIC_IP} (signal 49100 / stream 47998):"
echo "https://docs.isaacsim.omniverse.nvidia.com/6.0.1/installation/manual_livestream_clients.html"
echo
echo "Logs:"
echo "docker compose -p isim -f $ISAAC_INFRA/tools/docker/docker-compose.yml logs -f"
