from __future__ import annotations

import cv2

from so101_demo_common import HEIGHT, TOP_CAM, WIDTH, WRIST_CAM, print_config


def check_camera(index: int, name: str) -> None:
    cap = cv2.VideoCapture(index)
    if not cap.isOpened():
        raise RuntimeError(f"Could not open {name} camera index {index}")
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, WIDTH)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, HEIGHT)
    ok, frame = cap.read()
    cap.release()
    if not ok:
        raise RuntimeError(f"Opened {name} camera index {index}, but failed to read a frame")
    out = f"camera_{name}.jpg"
    cv2.imwrite(out, frame)
    print(f"{name}: index={index}, shape={frame.shape}, saved={out}")


def main() -> None:
    print_config()
    check_camera(TOP_CAM, "top")
    check_camera(WRIST_CAM, "wrist")
    print("Camera check OK")


if __name__ == "__main__":
    main()
