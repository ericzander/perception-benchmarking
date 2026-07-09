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

# Per the Brev deployment doc, chown to uid 1234 (the image's own user; see
# isaac-compose.override.yml/run-script-isaac.sh for why it stays that way).
# Group is set to the host user's and made writable so the container
# (running with umask 002) leaves files here manageable without sudo.
mkdir -p "$HOME/docker/isaac-sim"/{cache/main,cache/computecache,cache/kit,config,data,logs,pkg}
mkdir -p "$HOME/.cache/ov/hub"
sudo chown -R "1234:$(id -g)" "$HOME/docker/isaac-sim" "$HOME/.cache/ov/hub"
sudo chmod -R u+rwX,g+rwX "$HOME/docker/isaac-sim" "$HOME/.cache/ov/hub"

# Same reasoning for the project repo: run-script-isaac.sh runs scripts
# against it as uid 1234, so new output dirs need a group-writable ancestor.
find "$PROJECT_ROOT" -type d -not -path '*/.git*' -exec chmod g+w {} +

# Small ROS 2 development image with this project mounted in at runtime.
docker build \
    -f "$PROJECT_ROOT/infra/ros.Dockerfile" \
    -t robot-benchmark-ros:jazzy \
    "$PROJECT_ROOT"

echo
echo "Bootstrap complete."
echo "Run: bash infra/start-isaac.sh"
echo "Run: bash infra/start-ros.sh"
