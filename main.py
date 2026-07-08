import argparse
import time

try:
    import cv2
except ImportError:
    cv2 = None

import config
from src.missions import MISSIONS
from src.nodes.arduino_node import ArduinoNode
from src.nodes.camera_node import CameraNode
from src.nodes.lidar_node import LidarNode
from src.nodes.ports import autodetect_ports

MISSION_DESC = {
    "track": "트랙 주행 (차선 추종)",
    "obstacle": "장애물 회피",
    "parking": "수직 주차",
    "escape": "탈출",
}


def pick_mission():
    names = list(MISSIONS)
    print("\n미션 선택:")
    for i, name in enumerate(names, 1):
        print(f"  {i}. {name:<10} {MISSION_DESC.get(name, '')}")
    while True:
        choice = input("번호 또는 이름 입력 > ").strip().lower()
        if choice in MISSIONS:
            return choice
        if choice.isdigit() and 1 <= int(choice) <= len(names):
            return names[int(choice) - 1]
        print("잘못된 입력입니다.")


def show_frames(top, bottom):
    if cv2 is None:
        return True
    if top is not None:
        cv2.imshow("top_camera", top)
    if bottom is not None:
        cv2.imshow("bottom_camera", bottom)
    return (cv2.waitKey(1) & 0xFF) != ord("q")


def main():
    parser = argparse.ArgumentParser(description="autodrive_for_skku 미션 런처")
    parser.add_argument("--mission", choices=list(MISSIONS), help="생략하면 메뉴에서 선택")
    parser.add_argument("--arduino", default=config.ARDUINO_PORT, help="아두이노 시리얼 포트")
    parser.add_argument("--lidar", default=config.LIDAR_PORT, help="라이다 시리얼 포트")
    parser.add_argument("--top-camera", type=int, default=config.TOP_CAMERA)
    parser.add_argument("--bottom-camera", type=int, default=config.BOTTOM_CAMERA)
    parser.add_argument("--show", action="store_true", help="카메라 창 표시 (q로 종료)")
    args = parser.parse_args()

    mission_name = args.mission or pick_mission()
    mission = MISSIONS[mission_name]()

    arduino_port, lidar_port = args.arduino, args.lidar
    if arduino_port is None or lidar_port is None:
        auto_arduino, auto_lidar = autodetect_ports()
        arduino_port = arduino_port or auto_arduino
        lidar_port = lidar_port or auto_lidar

    print(f"[main] mission={mission_name} arduino={arduino_port} lidar={lidar_port}")

    car = ArduinoNode(arduino_port, config.ARDUINO_BAUD)
    cameras = CameraNode(args.top_camera, args.bottom_camera,
                         config.FRAME_WIDTH, config.FRAME_HEIGHT)
    lidar = LidarNode(lidar_port, config.LIDAR_BAUD)

    period = 1.0 / config.LOOP_HZ
    mission.on_start(car, config)
    print("[main] 실행 중 — Ctrl+C 로 종료")
    try:
        while True:
            top, bottom = cameras.latest()
            sensors = {
                "top": top,
                "bottom": bottom,
                "lidar_min_m": lidar.min_distance_m(config.LIDAR_FRONT_SECTOR),
                "lidar_scan": lidar.scan,
                "ultrasonic": car.ultrasonic,
                "state": car.state,
            }
            mission.step(sensors, car)
            if args.show and not show_frames(top, bottom):
                break
            time.sleep(period)
    except KeyboardInterrupt:
        pass
    finally:
        print("\n[main] 종료 — 차량 정지")
        mission.on_stop(car)
        car.close()
        cameras.close()
        lidar.close()


if __name__ == "__main__":
    main()
