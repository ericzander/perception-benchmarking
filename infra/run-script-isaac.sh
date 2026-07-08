#!/usr/bin/env bash
# Runs a standalone Isaac Sim Python script (e.g. a Replicator data generation
# script) in a throwaway container, separate from the persistent streaming
# container started by start-isaac.sh. Useful for headless batch jobs
#
# Usage:
#   infra/run-script-isaac.sh <path-to-script.py> [script args...]
set -euo pipefail

if [[ $# -lt 1 ]]; then
    echo "Usage: $0 <path-to-script.py> [script args...]" >&2
    exit 1
fi

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ISAAC_SIM_IMAGE="${ISAAC_SIM_IMAGE:-nvcr.io/nvidia/isaac-sim:6.0.1}"
ISAAC_SIM_DATA="${ISAAC_SIM_DATA:-$HOME/docker/isaac-sim}"

SCRIPT_PATH="$(cd "$(dirname "$1")" && pwd)/$(basename "$1")"
shift

# The script has to live under the repo so the bind mount below can see it.
if [[ "$SCRIPT_PATH" != "$PROJECT_ROOT"/* ]]; then
    echo "Script must live under $PROJECT_ROOT (got $SCRIPT_PATH)" >&2
    exit 1
fi
CONTAINER_SCRIPT_PATH="/workspace/project${SCRIPT_PATH#"$PROJECT_ROOT"}"

# --network host: matches start-isaac.sh/start-ros.sh, in case the script
# talks to the ROS container. Cache volumes reuse shader compilation across
# runs. PYTHONPATH exposes perception/ via plain sys.path. PYTHONUNBUFFERED
# keeps prints from being lost in a block buffer if the process is piped/killed.
#
# --entrypoint overrides the image's default runheadless.sh, which hardcodes
# the full streaming experience and would make SimulationApp(experience=...)
# in the script a no-op.
docker run --rm \
    --network host \
    --gpus all \
    --user "$(id -u):$(id -g)" \
    --entrypoint /isaac-sim/python.sh \
    --env ACCEPT_EULA=Y \
    --env PYTHONPATH=/workspace/project \
    --env PYTHONUNBUFFERED=1 \
    --volume "$PROJECT_ROOT:/workspace/project" \
    --volume "$ISAAC_SIM_DATA/cache/main:/isaac-sim/.cache:rw" \
    --volume "$ISAAC_SIM_DATA/cache/computecache:/isaac-sim/.nv/ComputeCache:rw" \
    --workdir /workspace/project \
    "$ISAAC_SIM_IMAGE" \
    "$CONTAINER_SCRIPT_PATH" "$@"
