from __future__ import annotations

import os
import sys
import time

import paramiko

from pathlib import Path

HOST = os.environ["RTX_HOST"]
USER = os.environ["RTX_USER"]
PASSWORD = os.environ["RTX_PASSWORD"]
REPO_ROOT = Path(__file__).resolve().parents[1]
LOCAL_FILE = os.getenv(
    "LOCAL_SERVER_POLICY", str(REPO_ROOT / "rtx_inference_server" / "server_policy.py")
)
REMOTE_DIR = os.getenv("RTX_REMOTE_DIR", "/data/robot_project/inference_server")
REMOTE_FILE = f"{REMOTE_DIR}/server_policy.py"


def run(client: paramiko.SSHClient, cmd: str, timeout: float = 60) -> str:
    _, stdout, stderr = client.exec_command(cmd, timeout=timeout)
    out = stdout.read().decode()
    err = stderr.read().decode()
    code = stdout.channel.recv_exit_status()
    print(f"$ {cmd}\n  exit={code}")
    if out.strip():
        print("  " + out.strip().replace("\n", "\n  "))
    if err.strip():
        print("  [err] " + err.strip().replace("\n", "\n  "))
    return out


def main() -> None:
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(HOST, username=USER, password=PASSWORD, timeout=15)
    print(f"Connected to {USER}@{HOST}")

    stamp = time.strftime("%Y%m%d_%H%M%S")
    run(client, f"cp {REMOTE_FILE} {REMOTE_FILE}.bak_{stamp}")

    sftp = client.open_sftp()
    sftp.put(LOCAL_FILE, REMOTE_FILE)
    sftp.close()
    print(f"Uploaded {LOCAL_FILE} -> {REMOTE_FILE}")

    run(client, f"grep -n 'observation.images.front\\|TASK_DEFAULT' {REMOTE_FILE} | head -5")

    pid = run(client, "cat /data/robot_project/logs/pi05_server.pid 2>/dev/null").strip()
    if pid:
        run(client, f"kill {pid} 2>/dev/null; sleep 2; kill -9 {pid} 2>/dev/null; true")
    run(client, "rm -f /data/robot_project/logs/pi05_server.pid")
    run(client, f"bash {REMOTE_DIR}/start_server.sh")

    print("Waiting for model load...")
    for i in range(24):
        time.sleep(5)
        out = run(client, "curl -sS --max-time 4 http://127.0.0.1:8000/health || true", timeout=15)
        if '"ok":true' in out.replace(" ", ""):
            print("SERVER HEALTHY")
            client.close()
            return
    print("Timed out waiting for healthy server; last log lines:")
    run(client, "tail -20 /data/robot_project/logs/pi05_server.log")
    client.close()
    sys.exit(1)


if __name__ == "__main__":
    main()
