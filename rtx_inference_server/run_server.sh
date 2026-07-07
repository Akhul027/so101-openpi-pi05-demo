#!/usr/bin/env bash
set -euo pipefail

cd /data/robot_project/inference_server

export PYTORCH_CUDA_ALLOC_CONF="${PYTORCH_CUDA_ALLOC_CONF:-expandable_segments:True}"
export CUDA_MODULE_LOADING="${CUDA_MODULE_LOADING:-LAZY}"
export HF_HOME="${HF_HOME:-/data/robot_project/cache/hf}"
export HUGGINGFACE_HUB_CACHE="${HUGGINGFACE_HUB_CACHE:-/data/robot_project/cache/hf/hub}"
export HF_HUB_OFFLINE="${HF_HUB_OFFLINE:-1}"
export TRANSFORMERS_OFFLINE="${TRANSFORMERS_OFFLINE:-1}"
export TMPDIR="${TMPDIR:-/data/robot_project/tmp}"
export TORCHDYNAMO_DISABLE="${TORCHDYNAMO_DISABLE:-1}"
export TOKENIZERS_PARALLELISM="${TOKENIZERS_PARALLELISM:-false}"
export PI05_MODEL_PATH="${PI05_MODEL_PATH:-/data/robot_project/models/pi05_v2model/pretrained_model}"
export PI05_DEVICE="${PI05_DEVICE:-cuda}"
export PI05_LOAD_ON_STARTUP="${PI05_LOAD_ON_STARTUP:-1}"

mkdir -p /data/robot_project/cache/hf/hub /data/robot_project/tmp /data/robot_project/logs

exec /home/rootx90/miniforge3/envs/lerobot/bin/python -m uvicorn server_policy:app \
  --host 0.0.0.0 \
  --port "${PORT:-8000}" \
  --workers 1
