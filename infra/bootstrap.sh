#!/usr/bin/env bash
# Brev Launchable setup script. Keep this the ONLY thing configured in the
# Brev UI ("bash infra/bootstrap.sh") so the actual setup stays versioned here.
# Per docs, VM Mode setup steps (ports, GPU choice, setup script field):
# https://docs.isaacsim.omniverse.nvidia.com/6.0.1/installation/install_advanced_cloud_setup_brev.html
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ISAAC_INFRA="$HOME/IsaacSim"
ISAAC_SIM_REF="v6.0.1"

echo "Project: $PROJECT_ROOT"

# Brev VM Mode normally provides Docker and the NVIDIA Container Toolkit, but verify them.
command -v docker >/dev/null
nvidia-smi

# tools/docker/README.md documents a full clone + `git lfs pull` for people
# building Isaac Sim from source:
# https://github.com/isaac-sim/IsaacSim/blob/main/tools/docker/README.md#clone-the-repository
# This project uses the prebuilt NGC image instead, so this only needs tools/docker/ (the
# compose file + web-viewer build context), not the full source or LFS assets.
if [[ ! -d "$ISAAC_INFRA/.git" ]]; then
    git clone \
        --branch "$ISAAC_SIM_REF" \
        --depth 1 \
        --filter=blob:none \
        --sparse \
        https://github.com/isaac-sim/IsaacSim.git \
        "$ISAAC_INFRA"
    git -C "$ISAAC_INFRA" sparse-checkout set tools/docker
fi

# Cache/config/log/data dirs + chown 1234 (the container's user), exactly as
# shown in the Brev deployment doc linked above.
mkdir -p "$HOME/docker/isaac-sim"/{cache/main,cache/computecache,config,data,logs,pkg}
mkdir -p "$HOME/.cache/ov/hub"
sudo chown -R 1234:1234 "$HOME/docker/isaac-sim" "$HOME/.cache/ov/hub"

# Small ROS 2 development image with this project mounted in at runtime.
docker build \
    -f "$PROJECT_ROOT/infra/ros.Dockerfile" \
    -t robot-benchmark-ros:jazzy \
    "$PROJECT_ROOT"

echo
echo "Bootstrap complete."
echo "Run: bash infra/start-isaac.sh"
echo "Run: bash infra/start-ros.sh"
