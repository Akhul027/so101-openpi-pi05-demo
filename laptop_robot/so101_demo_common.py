from __future__ import annotations

import base64
import os
import platform
import time
from pathlib import Path
from typing import Any

import cv2
import numpy as np
import requests

from lerobot.cameras.opencv.configuration_opencv import OpenCVCameraConfig
from lerobot.robots.so_follower import SO101Follower, SO101FollowerConfig


SERVER_URL = os.getenv("SO101_SERVER_URL", "http://127.0.0.1:8000/predict")
HEALTH_URL = os.getenv("SO101_HEALTH_URL", SERVER_URL.rsplit("/", 1)[0] + "/health")
RESET_URL = os.getenv("SO101_RESET_URL", SERVER_URL.rsplit("/", 1)[0] + "/reset")
DEFAULT_PORT = "COM3" if platform.system() == "Windows" else "/dev/ttyACM0"
PORT = os.getenv("SO101_PORT", DEFAULT_PORT)
TOP_CAM = int(os.getenv("SO101_TOP_CAM", "2"))
WRIST_CAM = int(os.getenv("SO101_WRIST_CAM", "3"))
TASK = os.getenv("SO101_TASK", "move red cube to the brown area")
HTTP = requests.Session()
HTTP.trust_env = False

FPS = int(os.getenv("SO101_FPS", "30"))
WIDTH = int(os.getenv("SO101_WIDTH", "640"))
HEIGHT = int(os.getenv("SO101_HEIGHT", "480"))
REQUEST_TIMEOUT_S = float(os.getenv("SO101_REQUEST_TIMEOUT_S", "20"))
MAX_STEP_DEG = float(os.getenv("SO101_MAX_STEP_DEG", "5.0"))
MAX_SHOULDER_LIFT_STEP_DEG = float(os.getenv("SO101_MAX_SHOULDER_LIFT_STEP_DEG", "3.0"))
MAX_GRIPPER_STEP = float(os.getenv("SO101_MAX_GRIPPER_STEP", "12.0"))
LOOP_HZ = float(os.getenv("SO101_LOOP_HZ", "5.0"))

# Initial pose from training dataset episode 0, frame 60 (NOT frame 0!).
# Episodes start with ~1s of idle frames at the folded pose; starting there makes the
# policy predict "stay idle". Frame 60 is just past the idle phase, so the policy acts.
_START_POSE_DEFAULT = "4.7,-100.0,71.0,50.6,-10.0,1.3"
START_POSE = [float(v) for v in os.getenv("SO101_START_POSE", _START_POSE_DEFAULT).replace(",", " ").split()]

TOP_IMAGE_KEY = "observation.images.front"
WRIST_IMAGE_KEY = "observation.images.wrist"
JOINT_KEYS = [
    "shoulder_pan.pos",
    "shoulder_lift.pos",
    "elbow_flex.pos",
    "wrist_flex.pos",
    "wrist_roll.pos",
    "gripper.pos",
]


def print_config() -> None:
    print("SO101 demo config")
    print(f"  OS: {platform.system()} {platform.release()}")
    print(f"  SERVER_URL: {SERVER_URL}")
    print(f"  HEALTH_URL: {HEALTH_URL}")
    print(f"  PORT: {PORT}")
    print(f"  TOP_CAM: {TOP_CAM}")
    print(f"  WRIST_CAM: {WRIST_CAM}")
    print(f"  TASK: {TASK}")
    print(f"  image: {WIDTH}x{HEIGHT}@{FPS}")
    print(
        "  max step: "
        f"joints={MAX_STEP_DEG}, shoulder_lift={MAX_SHOULDER_LIFT_STEP_DEG}, "
        f"gripper={MAX_GRIPPER_STEP}"
    )


def step_limit_for_key(key: str) -> float:
    if key == "shoulder_lift.pos":
        return MAX_SHOULDER_LIFT_STEP_DEG
    if key == "gripper.pos":
        return MAX_GRIPPER_STEP
    return MAX_STEP_DEG


def build_robot(include_cameras: bool = True) -> SO101Follower:
    cameras = {}
    if include_cameras:
        cameras = {
            TOP_IMAGE_KEY: OpenCVCameraConfig(index_or_path=TOP_CAM, fps=FPS, width=WIDTH, height=HEIGHT),
            WRIST_IMAGE_KEY: OpenCVCameraConfig(index_or_path=WRIST_CAM, fps=FPS, width=WIDTH, height=HEIGHT),
        }

    config = SO101FollowerConfig(
        id="so101_pick_place_follower",
        port=PORT,
        cameras=cameras,
        max_relative_target={key.removesuffix(".pos"): step_limit_for_key(key) for key in JOINT_KEYS},
        # Training dataset was recorded with normalized positions (-100..100), not degrees.
        use_degrees=False,
    )
    return SO101Follower(config)


def connect_robot(include_cameras: bool = True) -> SO101Follower:
    robot = build_robot(include_cameras=include_cameras)
    robot.connect(calibrate=False)
    return robot


def state_from_observation(obs: dict[str, Any]) -> list[float]:
    missing = [key for key in JOINT_KEYS if key not in obs]
    if missing:
        raise KeyError(f"Missing joint keys from observation: {missing}")
    return [float(obs[key]) for key in JOINT_KEYS]


def print_state(state: list[float], prefix: str = "state") -> None:
    pretty = ", ".join(f"{name}={value:.3f}" for name, value in zip(JOINT_KEYS, state, strict=True))
    print(f"{prefix}: {pretty}")


def encode_jpeg_base64(image: Any) -> str:
    arr = np.asarray(image)
    if arr.dtype != np.uint8:
        max_value = float(np.nanmax(arr)) if arr.size else 0.0
        if max_value <= 1.0:
            arr = (arr * 255.0).clip(0, 255).astype(np.uint8)
        else:
            arr = arr.clip(0, 255).astype(np.uint8)
    if arr.ndim != 3 or arr.shape[2] < 3:
        raise ValueError(f"Expected HWC image with 3 channels, got shape={arr.shape}")

    rgb = arr[:, :, :3]
    bgr = cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR)
    ok, encoded = cv2.imencode(".jpg", bgr, [int(cv2.IMWRITE_JPEG_QUALITY), 90])
    if not ok:
        raise RuntimeError("Failed to JPEG-encode camera image")
    return base64.b64encode(encoded.tobytes()).decode("ascii")


def observation_to_payload(obs: dict[str, Any], task: str = TASK) -> dict[str, Any]:
    state = state_from_observation(obs)
    top = encode_jpeg_base64(obs[TOP_IMAGE_KEY])
    wrist = encode_jpeg_base64(obs[WRIST_IMAGE_KEY])
    return {
        "task": task,
        "state": state,
        "joint_names": JOINT_KEYS,
        "images": {"front": top, "wrist": wrist},
        "image_format": "jpeg_base64",
        "camera_names": ["front", "wrist"],
        "observation": {
            "state": state,
            "images": {"front": top, "wrist": wrist},
        },
    }


def health_check(timeout_s: float = 5.0) -> dict[str, Any]:
    response = HTTP.get(HEALTH_URL, timeout=timeout_s)
    response.raise_for_status()
    try:
        return response.json()
    except Exception:
        return {"raw": response.text}


def reset_policy(timeout_s: float = 10.0) -> None:
    try:
        response = HTTP.post(RESET_URL, timeout=timeout_s)
        response.raise_for_status()
        print("policy reset:", response.json())
    except Exception as exc:
        print(f"WARNING: policy reset failed (continuing anyway): {exc!r}")


def request_policy_action(obs: dict[str, Any], task: str = TASK) -> Any:
    payload = observation_to_payload(obs, task=task)
    response = HTTP.post(SERVER_URL, json=payload, timeout=REQUEST_TIMEOUT_S)
    response.raise_for_status()
    try:
        data: Any = response.json()
    except Exception:
        data = response.text
    return extract_action(data)


def extract_action(data: Any) -> Any:
    if isinstance(data, dict):
        for key in ("action", "actions", "pred_action", "prediction", "result"):
            if key in data:
                return extract_action(data[key])
        if all(key in data for key in JOINT_KEYS):
            return data
        short_keys = [key.removesuffix(".pos") for key in JOINT_KEYS]
        if all(key in data for key in short_keys):
            return {f"{key}.pos": data[key] for key in short_keys}
        raise ValueError(f"Response JSON has no recognizable action key. Keys={list(data.keys())}")

    if isinstance(data, (list, tuple)):
        if len(data) == 0:
            raise ValueError("Policy returned an empty action list")
        first = data[0]
        if isinstance(first, (list, tuple)) and len(first) >= len(JOINT_KEYS):
            return list(first[: len(JOINT_KEYS)])
        if len(data) >= len(JOINT_KEYS) and all(isinstance(v, (int, float)) for v in data[: len(JOINT_KEYS)]):
            return list(data[: len(JOINT_KEYS)])

    raise ValueError(f"Unsupported policy response format: {type(data)!r}")


def action_to_list(action: Any) -> list[float]:
    if isinstance(action, dict):
        values = []
        for key in JOINT_KEYS:
            short_key = key.removesuffix(".pos")
            if key in action:
                values.append(float(action[key]))
            elif short_key in action:
                values.append(float(action[short_key]))
            else:
                raise KeyError(f"Action dict missing {key!r}")
        return values
    if isinstance(action, np.ndarray):
        action = action.tolist()
    if isinstance(action, (list, tuple)):
        if action and isinstance(action[0], (list, tuple)):
            action = action[0]
        return [float(v) for v in action[: len(JOINT_KEYS)]]
    raise TypeError(f"Cannot convert action type {type(action)!r} to list")


def clip_action_to_safe_step(action: Any, current_state: list[float]) -> dict[str, float]:
    target = action_to_list(action)
    safe_action: dict[str, float] = {}
    for key, current, desired in zip(JOINT_KEYS, current_state, target, strict=True):
        step_limit = step_limit_for_key(key)
        delta = float(np.clip(desired - current, -step_limit, step_limit))
        safe_action[key] = current + delta
    return safe_action


def move_to_start_pose(
    robot: SO101Follower,
    pose: list[float] | None = None,
    tolerance: float = 2.0,
    max_seconds: float = 20.0,
) -> None:
    """Ramp the arm slowly to the training start pose using the same per-step safety clipping."""
    target = pose if pose is not None else START_POSE
    print_state(target, prefix="moving to start pose")
    deadline = time.perf_counter() + max_seconds
    while time.perf_counter() < deadline:
        start = time.perf_counter()
        obs = robot.get_observation()
        state = state_from_observation(obs)
        max_err = max(abs(t - c) for t, c in zip(target, state, strict=True))
        if max_err <= tolerance:
            print(f"start pose reached (max joint error {max_err:.2f})")
            return
        robot.send_action(clip_action_to_safe_step(target, state))
        sleep_for_loop(start)
    print("WARNING: start pose not fully reached before timeout; continuing.")


def hold_action_from_state(state: list[float]) -> dict[str, float]:
    return {key: float(value) for key, value in zip(JOINT_KEYS, state, strict=True)}


def sleep_for_loop(start_time: float) -> None:
    if LOOP_HZ <= 0:
        return
    period = 1.0 / LOOP_HZ
    elapsed = time.perf_counter() - start_time
    if elapsed < period:
        time.sleep(period - elapsed)


def save_image(path: str | Path, image: Any) -> None:
    arr = np.asarray(image)
    if arr.ndim == 3 and arr.shape[2] >= 3:
        arr = cv2.cvtColor(arr[:, :, :3], cv2.COLOR_RGB2BGR)
    cv2.imwrite(str(path), arr)
