from __future__ import annotations

import argparse
import os
import posixpath
import stat
import sys
from pathlib import Path

import paramiko


ALLOWED_REMOTE_ROOT = "/data/robot_project"

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")


def connect() -> paramiko.SSHClient:
    host = os.environ.get("RTX_HOST")
    user = os.environ.get("RTX_USER")
    password = os.environ.get("RTX_PASS")
    missing = [name for name, value in {"RTX_HOST": host, "RTX_USER": user, "RTX_PASS": password}.items() if not value]
    if missing:
        raise SystemExit(f"Missing required environment variables: {', '.join(missing)}")

    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(
        hostname=host,
        username=user,
        password=password,
        timeout=20,
        banner_timeout=20,
        auth_timeout=20,
        look_for_keys=False,
        allow_agent=False,
    )
    return client


def is_allowed_remote_path(path: str) -> bool:
    normalized = posixpath.normpath(path)
    return normalized == ALLOWED_REMOTE_ROOT or normalized.startswith(ALLOWED_REMOTE_ROOT + "/")


def exec_command(client: paramiko.SSHClient, command: str, timeout: int) -> int:
    stdin, stdout, stderr = client.exec_command(command, timeout=timeout, get_pty=False)
    stdin.close()
    out = stdout.read().decode("utf-8", errors="replace")
    err = stderr.read().decode("utf-8", errors="replace")
    if out:
        print(out, end="")
    if err:
        print(err, end="", file=sys.stderr)
    return stdout.channel.recv_exit_status()


def mkdir_p(sftp: paramiko.SFTPClient, remote_dir: str) -> None:
    if not is_allowed_remote_path(remote_dir):
        raise ValueError(f"Refusing to create directory outside {ALLOWED_REMOTE_ROOT}: {remote_dir}")
    parts = []
    cur = posixpath.normpath(remote_dir)
    while cur not in ("", "/"):
        parts.append(cur)
        cur = posixpath.dirname(cur)
    for directory in reversed(parts):
        try:
            sftp.stat(directory)
        except FileNotFoundError:
            sftp.mkdir(directory)


def put_file(client: paramiko.SSHClient, local: Path, remote: str) -> None:
    if not is_allowed_remote_path(remote):
        raise ValueError(f"Refusing to write outside {ALLOWED_REMOTE_ROOT}: {remote}")
    sftp = client.open_sftp()
    try:
        mkdir_p(sftp, posixpath.dirname(remote))
        sftp.put(str(local), remote)
    finally:
        sftp.close()
    print(f"uploaded {local} -> {remote}")


def put_tree(client: paramiko.SSHClient, local_dir: Path, remote_dir: str) -> None:
    if not is_allowed_remote_path(remote_dir):
        raise ValueError(f"Refusing to write outside {ALLOWED_REMOTE_ROOT}: {remote_dir}")
    sftp = client.open_sftp()
    try:
        mkdir_p(sftp, remote_dir)
        for path in local_dir.rglob("*"):
            if path.is_dir():
                continue
            rel = path.relative_to(local_dir).as_posix()
            remote_path = posixpath.join(remote_dir, rel)
            mkdir_p(sftp, posixpath.dirname(remote_path))
            sftp.put(str(path), remote_path)
            print(f"uploaded {path} -> {remote_path}")
    finally:
        sftp.close()


def ls_tree(client: paramiko.SSHClient, remote_dir: str) -> None:
    sftp = client.open_sftp()
    try:
        for item in sftp.listdir_attr(remote_dir):
            mode = stat.filemode(item.st_mode)
            print(f"{mode} {item.st_size:>12} {item.filename}")
    finally:
        sftp.close()


def main() -> int:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_exec = sub.add_parser("exec")
    p_exec.add_argument("remote_command")
    p_exec.add_argument("--timeout", type=int, default=120)

    p_put = sub.add_parser("put")
    p_put.add_argument("local")
    p_put.add_argument("remote")

    p_put_tree = sub.add_parser("put-tree")
    p_put_tree.add_argument("local_dir")
    p_put_tree.add_argument("remote_dir")

    p_ls = sub.add_parser("ls")
    p_ls.add_argument("remote_dir")

    args = parser.parse_args()
    client = connect()
    try:
        if args.cmd == "exec":
            return exec_command(client, args.remote_command, args.timeout)
        if args.cmd == "put":
            put_file(client, Path(args.local), args.remote)
            return 0
        if args.cmd == "put-tree":
            put_tree(client, Path(args.local_dir), args.remote_dir)
            return 0
        if args.cmd == "ls":
            ls_tree(client, args.remote_dir)
            return 0
    finally:
        client.close()
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
