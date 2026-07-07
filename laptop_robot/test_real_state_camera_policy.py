from __future__ import annotations

from so101_demo_common import (
    TOP_IMAGE_KEY,
    WRIST_IMAGE_KEY,
    connect_robot,
    health_check,
    print_config,
    print_state,
    request_policy_action,
    save_image,
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
        save_image("latest_top.jpg", obs[TOP_IMAGE_KEY])
        save_image("latest_wrist.jpg", obs[WRIST_IMAGE_KEY])
        print("saved latest_top.jpg and latest_wrist.jpg")

        action = request_policy_action(obs)
        print("policy action:", action)
        print("State + camera + policy request OK. No robot action was sent.")
    finally:
        robot.disconnect()


if __name__ == "__main__":
    main()
