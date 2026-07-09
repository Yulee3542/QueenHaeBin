from .base import Mission
from .lane_follow import follow_lane

try:
    from ..vendor import Function_Library as fl
except ImportError:  # 패키지 미설치 개발 환경 — 차선 인식 없이 골격만 동작
    fl = None


class RoadMission(Mission):
    """1. 도로 주행

    단계별 목표:
      (1) 직진, 스티어링          — 동작
      (2) 차선 인식 도로 주행      — 동작 (팀 검증 edge_detection 사용, lane_follow.py 공유)
      (3) 차선 변경하며 도로 주행  — TODO: lane_change()
      (4) 장애물 피해 차선 변경    — TODO: 회피 방향 결정 + lane_change 연결
    """

    name = "road"

    def on_start(self, car, config):
        assert set(config.LANE_EDGE) == {"width", "height", "gap", "threshold"}, \
            f"config.LANE_EDGE 키가 예상과 다름: {set(config.LANE_EDGE)}"
        self.config = config
        self.env = fl.libCAMERA() if fl is not None else None
        car.go()
        car.drive(config.DRIVE_SPEED)

    def step(self, sensors, car):
        # (4) 장애물 감지 → 차선 변경으로 회피
        dist = sensors["lidar_min_m"]
        if dist is not None and dist <= self.config.OBSTACLE_STOP_M:
            self.lane_change(car, "L")  # TODO: 라이다 좌우 여유로 회피 방향 결정
            return

        # (2) 차선 인식 주행 — 검증된 파라미터는 config.LANE_EDGE
        follow_lane(self.env, car, sensors["bottom"], self.config.LANE_EDGE)

    def lane_change(self, car, direction):
        # TODO(3단계): 차선 변경 기동 — steer_pulse 시퀀스로 옆 차선 진입 후 복귀.
        # 구현 전에는 안전하게 정지.
        car.drive(0)
