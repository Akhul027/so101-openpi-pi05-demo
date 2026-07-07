from __future__ import annotations

import os
import time

from so101_demo_common import (
    LOOP_HZ,
    clip_action_to_safe_step,
    connect_robot,
    health_check,
    print_config,
    print_state,
    move_to_start_pose,
    request_policy_action,
    reset_policy,
    sleep_for_loop,
    state_from_observation,
)


STEPS = int(os.getenv("SO101_STEPS", "120"))


def main() -> None:
    print_config()
    print(f"loop steps: {STEPS}, loop hz: {LOOP_HZ}")
    print("health:", health_check())
    reset_policy()

    robot = connect_robot(include_cameras=True)
    try:
        if os.getenv("SO101_GO_START", "1") == "1":
            move_to_start_pose(robot)
        consecutive_failures = 0
        for step in range(STEPS):
            start = time.perf_counter()
            try:
                obs = robot.get_observation()
                state = state_from_observation(obs)
                raw_action = request_policy_action(obs)
                safe_action = clip_action_to_safe_step(raw_action, state)
                sent = robot.send_action(safe_action)
                consecutive_failures = 0
            except Exception as exc:
                consecutive_failures += 1
                print(f"step {step + 1}/{STEPS} FAILED ({consecutive_failures} in a row): {exc!r}")
                if consecutive_failures >= 10:
                    print("Too many consecutive failures; aborting loop.")
                    break
                time.sleep(0.2)
                continue
            print(f"step {step + 1}/{STEPS}")
            print_state(state, prefix="  current")
            print(f"  sent: {sent}")
            sleep_for_loop(start)
        print("Safe policy loop finished")
    except KeyboardInterrupt:
        print("Interrupted by user; disconnecting robot.")
    finally:
        try:
            robot.disconnect()
        except Exception as exc:
            print(f"WARNING: robot disconnect raised: {exc!r}")


if __name__ == "__main__":
    main()
