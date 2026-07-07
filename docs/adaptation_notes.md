# Adaptation Notes: Trossen OpenPI to LeRobot SO101

This project adapts the OpenPI / Pi05 workflow from the Trossen Robotics tutorial to the LeRobot SO101 robotic arm.

## Original Reference Workflow

The original Trossen workflow uses:

- Trossen AI arm hardware
- OpenPI / Pi05 policy
- LeRobot-based data collection
- Remote policy inference
- Client-server deployment

## Target Hardware

This project targets:

- LeRobot SO101 follower arm
- SO101 leader arm for teleoperation
- Top camera
- Wrist camera
- Remote RTX 5090 policy server
- Ubuntu laptop as the robot client

## Main Adaptation Points

The Trossen tutorial cannot be used directly because the robot hardware is different.

Required adaptation points:

1. Robot type must be changed to `so101_follower`.
2. Teleoperation must use `so101_leader`.
3. Camera names must match the SO101 dataset.
4. Robot state dimension must be validated.
5. Action dimension must be validated.
6. Gripper action range must be checked.
7. Policy output must be safely clipped before being sent to the robot.
8. Remote inference latency must be measured.
9. The checkpoint must match the SO101 dataset format.

## Current Status

Robot hardware has not been connected yet in the fresh setup. The current stage focuses on repository cleanup, environment preparation, and configuration templates.

## Expected Pipeline

```text
SO101 cameras + robot state
        ↓
Robot laptop / client
        ↓
Network connection
        ↓
RTX 5090 policy server
        ↓
Pi05 inference
        ↓
Action command
        ↓
SO101 follower arm
