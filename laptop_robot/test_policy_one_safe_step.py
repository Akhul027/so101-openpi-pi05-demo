from __future__ import annotations

import time

from so101_demo_common import (
    clip_action_to_safe_step,
    connect_robot,
    health_check,
    print_config,
    print_state,
    request_policy_action,
    state_from_observation,
)


def main() -> None:
    print_config()
    print("health:", health_check())

    robot = connect_robot(include_cameras=True)
    try:
        obs = robot.get_observation()
        state = state_from_observation(obs)
        print_state(state, prefix="current")

        raw_action = request_policy_action(obs)
        print("raw policy action:", raw_action)
        safe_action = clip_action_to_safe_step(raw_action, state)
        print("safe one-step action:", safe_action)

        sent = robot.send_action(safe_action)
        print("sent action:", sent)
        time.sleep(0.5)
        print("One safe policy step OK")
    finally:
        robot.disconnect()


if __name__ == "__main__":
    main()
