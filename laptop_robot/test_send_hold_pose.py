from __future__ import annotations

import time

from so101_demo_common import connect_robot, hold_action_from_state, print_config, print_state, state_from_observation


def main() -> None:
    print_config()
    robot = connect_robot(include_cameras=False)
    try:
        obs = robot.get_observation()
        state = state_from_observation(obs)
        print_state(state, prefix="current")
        hold_action = hold_action_from_state(state)
        sent = robot.send_action(hold_action)
        print("sent hold action:", sent)
        time.sleep(0.5)
        print("Hold pose test OK")
    finally:
        robot.disconnect()


if __name__ == "__main__":
    main()
