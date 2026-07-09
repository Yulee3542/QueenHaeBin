# 차량/센서 설정 — 새 환경에서는 이 파일(또는 main.py 인자)만 바꾸면 된다.
# 포트가 None이면 자동 감지를 시도한다. 실패 시 --arduino / --lidar 인자로 지정.

ARDUINO_PORT = None      # 예: "/dev/ttyACM0"
ARDUINO_BAUD = 9600
LIDAR_PORT = None        # 예: "/dev/ttyUSB0"
LIDAR_BAUD = 115200

# 카메라: C920 한 대를 상/하로 분할해 사용 (상단=신호등, 하단=차선)
FRONT_CAMERA = 0         # /dev/video0
REAR_CAMERA = None       # T주차용 후방 카메라 인덱스. 없으면 None
CAMERA_SPLIT = True      # False면 전방 프레임 전체를 top/bottom 양쪽에 그대로 전달
FRAME_WIDTH = 640
FRAME_HEIGHT = 480

LOOP_HZ = 30             # 메인 제어 루프 주기

DRIVE_SPEED = 100        # 기본 주행 속도 (-255..255, 실차 검증값)
SLOW_SPEED = 60          # 주차 등 저속 기동 속도
OBSTACLE_STOP_M = 0.7    # 라이다 장애물 정지 거리 (m, 실차 검증값 700mm)
LIDAR_FRONT_SECTOR = 30  # 전방 ±N도만 장애물 판정에 사용

# 팀 검증 완료된 차선 인식(edge_detection) 파라미터 (main3_c920_record.py)
LANE_EDGE = dict(width=500, height=120, gap=40, threshold=150)

# 신호등 판정: 상단 프레임에서 해당 색 픽셀이 이 비율을 넘어야 인식
TRAFFIC_PIXEL_RATIO = 0.005
