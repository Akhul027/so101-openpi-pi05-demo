from __future__ import annotations

from so101_demo_common import connect_robot, move_to_start_pose, print_state, state_from_observation


def main() -> None:
    robot = connect_robot(include_cameras=False)
    try:
        move_to_start_pose(robot)
        state = state_from_observation(robot.get_observation())
        print_state(state, prefix="final state")
    finally:
        try:
            robot.disconnect()
        except Exception as exc:
            print(f"WARNING: robot disconnect raised: {exc!r}")


if __name__ == "__main__":
    main()
