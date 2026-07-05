#!/usr/bin/env bash
# Source: https://github.com/isaac-sim/IsaacSim/blob/main/tools/docker/README.md
set -euo pipefail

ISAAC_INFRA="$HOME/IsaacSim"

docker compose \
    -p isim \
    -f "$ISAAC_INFRA/tools/docker/docker-compose.yml" \
    down
