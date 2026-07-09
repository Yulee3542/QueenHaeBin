try:
    import cv2
except ImportError:
    cv2 = None

from .base import Mission
from .lane_follow import follow_lane

try:
    from ..vendor import Function_Library as fl
    from ..vendor.Function_Library import HUE_THRESHOLD, SATURATION, RED, GREEN
except ImportError:  # 패키지 미설치 개발 환경 — 검증된 상수값만 복사해 사용
    fl = None
    RED, GREEN = 0, 1
    HUE_THRESHOLD = ([4, 176], [40, 80])
    SATURATION = 150


def detect_light_color(frame, min_ratio=0.005):
    """상단 프레임에서 빨강/초록 픽셀 비율로 신호등 판정. 'red'/'green'/None.

    검증된 HUE_THRESHOLD/SATURATION 값을 그대로 사용한다. 디스플레이가 있는
    환경에서는 fl.libCAMERA().object_detection(원 검출 방식)으로 교체 가능.
    """
    if cv2 is None or frame is None:
        return None

    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    h, s, _v = cv2.split(hsv)
    s_cond = s > SATURATION

    red = (((h < HUE_THRESHOLD[RED][0]) | (h > HUE_THRESHOLD[RED][1])) & s_cond).sum()
    green = (((h > HUE_THRESHOLD[GREEN][0]) & (h < HUE_THRESHOLD[GREEN][1])) & s_cond).sum()

    min_pixels = frame.shape[0] * frame.shape[1] * min_ratio
    if red >= min_pixels and red > green * 2:
        return "red"
    if green >= min_pixels and green > red * 2:
        return "green"
    return None


class TrafficMission(Mission):
    """2. 신호등 주행

    목표:
      (1) 정지선 인식      — TODO: stop_line_detected()
      (2) 신호등 라이트 인식 — 동작 (HSV 픽셀 비율 판정)

    동작: 차선 추종 주행 중 정지선을 만나면 정지, 초록불이면 다시 출발.
    빨간불은 언제든 즉시 정지 (main3 검증 로직과 동일).
    """

    name = "traffic"

    def on_start(self, car, config):
        assert set(config.LANE_EDGE) == {"width", "height", "gap", "threshold"}, \
            f"config.LANE_EDGE 키가 예상과 다름: {set(config.LANE_EDGE)}"
        self.config = config
        self.env = fl.libCAMERA() if fl is not None else None
        self.waiting = False  # 정지선/빨간불로 멈춰 신호 대기 중인지
        car.go()
        car.drive(config.DRIVE_SPEED)

    def step(self, sensors, car):
        color = detect_light_color(sensors["top"], self.config.TRAFFIC_PIXEL_RATIO)

        if color == "red":
            self.waiting = True

        if self.waiting:
            car.drive(0)
            if color == "green":
                self.waiting = False
                car.drive(self.config.DRIVE_SPEED)
            return

        if self.stop_line_detected(sensors["bottom"]):
            self.waiting = True
            car.drive(0)
            return

        car.drive(self.config.DRIVE_SPEED)
        follow_lane(self.env, car, sensors["bottom"], self.config.LANE_EDGE)

    def stop_line_detected(self, bottom_frame):
        # TODO(1단계): 하단 프레임 아래쪽 ROI에서 가로로 긴 흰색 선 비율로 판정
        # (힌트: cv2.inRange 흰색 → 행별 픽셀 합 → 임계 초과 행이 연속되면 정지선)
        return False
