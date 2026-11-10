#!/bin/bash
# usage (WSL): scripts/get_task_data.sh <task path, e.g. arvo/10400>
set -euo pipefail
TASK="$1"
mkdir -p "$HOME/cybergym_data"
docker run --rm -v "$HOME/cybergym_data:/data" -e TASK="$TASK" \
  -e HOST_UID="$(id -u)" -e HOST_GID="$(id -g)" python:3.12-slim sh -c '
    pip install -q --root-user-action=ignore -U huggingface_hub &&
    hf download sunblaze-ucb/cybergym --repo-type dataset --local-dir /data --include "data/$TASK/*" &&
    chown -R "$HOST_UID:$HOST_GID" /data'
ls -lh "$HOME/cybergym_data/data/$TASK"
