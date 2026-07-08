# 차량/센서 설정 — 새 환경에서는 이 파일(또는 main.py 인자)만 바꾸면 된다.
# 포트가 None이면 자동 감지를 시도한다. 실패 시 --arduino / --lidar 인자로 지정.

ARDUINO_PORT = None      # 예: "/dev/ttyACM0"
ARDUINO_BAUD = 9600
LIDAR_PORT = None        # 예: "/dev/ttyUSB0"
LIDAR_BAUD = 115200

TOP_CAMERA = 0           # /dev/video0
BOTTOM_CAMERA = 1        # /dev/video1
FRAME_WIDTH = 640
FRAME_HEIGHT = 480

LOOP_HZ = 30             # 메인 제어 루프 주기

DRIVE_SPEED = 150        # 기본 주행 속도 (-255..255)
SLOW_SPEED = 100         # 주차/탈출 등 저속 기동 속도
STEER_ERROR_PX = 50      # 차선 중심 오차 허용 픽셀 (넘으면 조향)
OBSTACLE_STOP_M = 1.0    # 라이다 장애물 정지 거리 (m)
LIDAR_FRONT_SECTOR = 30  # 전방 ±N도만 장애물 판정에 사용
