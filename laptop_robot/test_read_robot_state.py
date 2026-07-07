from __future__ import annotations

from serial.tools import list_ports

from so101_demo_common import connect_robot, print_config, print_state, state_from_observation


def main() -> None:
    print_config()
    ports = [port.device for port in list_ports.comports()]
    print("Available serial ports:", ports)

    robot = connect_robot(include_cameras=False)
    try:
        obs = robot.get_observation()
        state = state_from_observation(obs)
        print_state(state)
        print("Read robot state OK")
    finally:
        robot.disconnect()


if __name__ == "__main__":
    main()
