#!/usr/bin/env bash
set -euo pipefail

mkdir -p /data/robot_project/logs
cd /data/robot_project/inference_server

if [[ -f /data/robot_project/logs/pi05_server.pid ]]; then
  old_pid="$(cat /data/robot_project/logs/pi05_server.pid || true)"
  if [[ -n "$old_pid" ]] && kill -0 "$old_pid" 2>/dev/null; then
    echo "Server already running with PID $old_pid"
    exit 0
  fi
fi

nohup bash /data/robot_project/inference_server/run_server.sh \
  > /data/robot_project/logs/pi05_server.log \
  2>&1 &
pid="$!"
echo "$pid" > /data/robot_project/logs/pi05_server.pid
echo "Started Pi05 server PID $pid"
echo "Log: /data/robot_project/logs/pi05_server.log"
