# LeRobot SO101 Pick-and-Place using Pi05 Policy

This repository documents the implementation, debugging process, and current evaluation status of a Pi05 policy deployment for a pick-and-place task on the LeRobot SO101 robotic arm.

The main task is:

> Pick the cube and place it into the box.

The system uses a client-server architecture. The robot laptop is connected directly to the SO101 follower arm and cameras, while the RTX 5090 PC is used as a remote policy inference server. The robot laptop captures observations, sends them to the policy server, receives predicted actions, and executes those actions on the physical robot.

This project is currently a proof-of-concept implementation. The full inference pipeline is functional, but the physical pick-and-place behavior still requires further tuning, especially due to latency, camera mapping, action chunking, and gripper control issues.

## Project Overview

This project explores the deployment of a Vision-Language-Action policy, Pi05, on a real SO101 robotic arm.

The implementation focuses on:

* SO101 follower arm control
* Pi05 policy inference
* Remote RTX 5090 policy server
* Top and wrist camera observations
* Robot state and action streaming
* Client-server inference communication
* Safety clipping for robot actions
* Pick-and-place behavior evaluation
* Latency and asynchronous inference debugging

## System Architecture

```text
Top Camera + Wrist Camera + Robot State
                 |
                 v
        Robot Laptop / Client
                 |
                 v
      Network / SSH / VPN Connection
                 |
                 v
        RTX 5090 Policy Server
                 |
                 v
          Pi05 Policy Inference
                 |
                 v
        Action Command to SO101
```

The robot and the GPU server are not located on the same machine. This creates additional deployment challenges, especially related to network latency, action synchronization, and real-time robot control.

## Hardware Setup

The experiment uses:

* LeRobot SO101 follower arm
* Laptop connected to the SO101 robot via USB
* RTX 5090 PC for Pi05 policy inference
* Top camera
* Wrist camera
* Cube object
* Target box

## Software Setup

Main software components:

* Ubuntu Linux
* Conda environment
* Python
* LeRobot
* Pi05 policy
* PyTorch
* OpenCV
* LeRobot asynchronous inference
* Client-server communication over network

## Repository Structure

```text
.
├── README.md
├── requirements.txt
├── scripts/
│   ├── check_cameras.py
│   ├── test_read_robot_state.py
│   ├── test_send_hold_pose.py
│   ├── test_real_state_camera_policy.py
│   └── run_pick_and_place_demo.py
├── inference_server/
│   └── server_policy.py
├── docs/
│   ├── setup_laptop_robot.md
│   ├── setup_rtx_server.md
│   ├── troubleshooting.md
│   └── experiment_notes.md
├── assets/
│   ├── system_architecture.png
│   ├── robot_setup.jpg
│   └── demo_preview.gif
└── logs/
    └── sample_demo_log.txt
```

## Robot Calibration

The SO101 follower robot is calibrated using:

```bash
lerobot-calibrate \
  --robot.type=so101_follower \
  --robot.port=/dev/ttyACM0 \
  --robot.id=so101_follower_pi
```

The robot ID must remain consistent during calibration, dataset recording, and policy evaluation. If the robot ID changes, LeRobot may not load the correct calibration file.

## Camera Setup

The system uses two camera views:

* `top`: camera observing the workspace from above
* `wrist`: camera mounted near the robot gripper

Camera indices may change after unplugging or reconnecting USB devices. Therefore, camera mapping should be checked before every experiment.

Example camera configuration:

```text
top camera index: 4
wrist camera index: 2
```

Before running the policy, verify the camera mapping using a camera-checking script or OpenCV preview. Incorrect camera mapping can significantly reduce policy performance because the model receives observations that do not match the training setup.

## Running the Policy Server

On the RTX 5090 PC:

```bash
cd ~/robot_project/repos/lerobot
conda activate lerobot

python -m lerobot.async_inference.policy_server \
  --host=0.0.0.0 \
  --port=8080
```

The server should be reachable from the robot laptop through the local network, SSH tunnel, or VPN.

For public documentation, avoid hardcoding private IP addresses or credentials. Use a placeholder instead:

```text
<RTX_SERVER_IP>:8080
```

## Running the Robot Client

On the robot laptop:

```bash
cd ~/lerobot
conda activate lerobot
export PYTHONPATH=src

python -m lerobot.async_inference.robot_client \
  --server_address=<RTX_SERVER_IP>:8080 \
  --robot.type=so101_follower \
  --robot.port=/dev/ttyACM0 \
  --robot.id=so101_follower_pi \
  --robot.cameras="{ top: {type: opencv, index_or_path: 4, width: 640, height: 480, fps: 15}, wrist: {type: opencv, index_or_path: 2, width: 640, height: 480, fps: 15}}" \
  --task="Pick the cube and place it into the box." \
  --policy_type=pi05 \
  --pretrained_name_or_path=/path/to/pretrained_model \
  --policy_device=cuda \
  --actions_per_chunk=20 \
  --chunk_size_threshold=0.5 \
  --aggregate_fn_name=weighted_average \
  --debug_visualize_queue_size=True
```

## Current Progress

The current implementation has successfully achieved:

* Pi05 policy server running on the RTX 5090 PC
* Policy checkpoint loaded successfully
* Robot laptop connected to the SO101 follower arm
* Robot state successfully read from the SO101
* Top and wrist camera capture tested
* Observation request sent from the robot laptop to the policy server
* Policy action received from the server
* Action command sent to the SO101 robot
* End-to-end client-server inference pipeline verified

## Current Limitations

Although the full inference pipeline is functional, the physical pick-and-place behavior is not yet optimal.

The robot can move based on the policy output, but it has not consistently completed the full sequence:

```text
approach cube → close gripper → lift cube → move to box → release cube
```

The main limitations are:

* Network latency between the robot laptop and the RTX 5090 server
* Possible delay between observation capture and action execution
* Camera index changes after USB reconnect
* Top and wrist camera mismatch compared to the training setup
* Checkpoint mismatch or incomplete fine-tuning
* Gripper action not changing significantly during rollout
* Safety clipping modifying raw policy trajectories
* Action chunking parameters not fully tuned
* Asynchronous inference queue behavior not fully optimized
* Differences between the demonstration dataset and the real evaluation environment
* Possible mismatch between absolute and relative action representations

## Latency and Real-Time Control Challenges

A key challenge in this setup is that the policy does not run directly on the robot laptop. Instead, the robot laptop communicates with a remote RTX 5090 server.

This can introduce several issues:

```text
observation capture delay
network transmission delay
policy inference delay
action return delay
robot execution delay
```

Even small delays can affect manipulation tasks because the robot may execute actions based on slightly outdated observations. This is especially critical during grasping, where timing and gripper position are important.

To reduce the impact of latency, the system uses asynchronous inference and action chunking. However, the parameters still need further tuning.

Recommended starting parameters:

```text
actions_per_chunk = 20
chunk_size_threshold = 0.5
aggregate_fn_name = weighted_average
camera fps = 15
```

Further testing is required to determine whether smaller or larger action chunks produce smoother behavior.

## Troubleshooting Checklist

Before running the final demo, check:

* Robot port is correct
* Robot ID matches the calibration ID
* Calibration file exists
* Top and wrist camera indices are correct
* Cube and box are visible from both camera views
* Lighting condition is similar to the training dataset
* Policy checkpoint is the correct trained checkpoint
* Gripper open and close values are verified
* Raw policy actions are logged before clipping
* Clipped actions are logged after safety filtering
* Safety clipping does not overly modify the policy output
* Async inference queue is not empty during rollout
* Network connection to the RTX 5090 server is stable
* Latency is low enough for real-time control

## Experiment Notes

Initial testing used a custom HTTP-based inference server. The server successfully returned actions, and the robot client successfully sent the actions to the SO101 follower arm.

However, HTTP-based inference is not ideal for smooth real-time robot control. For better performance, the system should use the official LeRobot asynchronous inference pipeline with action chunking.

The current implementation is best interpreted as a debugging and migration repository from a basic inference pipeline toward a more reliable LeRobot async inference setup.

## Result Summary

This project demonstrates that a Pi05 policy can be deployed in a client-server architecture for SO101 robot control.

The main pipeline is functional:

```text
camera + robot state → robot client → RTX 5090 policy server → policy action → SO101 robot
```

However, the physical pick-and-place performance is not yet stable. Further tuning is required to improve latency handling, camera consistency, action execution, and gripper behavior.

## Future Work

Planned improvements:

* Use the official LeRobot async inference pipeline consistently
* Validate top and wrist camera mapping before every test
* Measure end-to-end inference latency
* Log raw action versus clipped action
* Analyze gripper open and close behavior
* Evaluate different `actions_per_chunk` values
* Tune asynchronous inference parameters
* Try relative action training
* Improve dataset consistency
* Compare Pi05 performance with SmolVLA or ACT baseline
* Add demo video and experiment logs to this repository

## Acknowledgements

This project uses the LeRobot framework and Pi05 policy for robotic imitation learning and Vision-Language-Action policy evaluation.

