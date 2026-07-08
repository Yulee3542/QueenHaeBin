from .base import Mission
from .track import steer_from_lane


class ObstacleMission(Mission):
    """장애물 회피: 차선 추종 + 라이다/초음파 장애물 정지."""

    name = "obstacle"

    def on_start(self, car, config):
        self.config = config
        car.go()
        car.drive(config.DRIVE_SPEED)

    def step(self, sensors, car):
        dist = sensors["lidar_min_m"]
        blocked = dist is not None and dist <= self.config.OBSTACLE_STOP_M
        car.set_lidar_obstacle(blocked)

        if blocked:
            car.drive(0)
            # TODO: 회피 기동 — 정지 후 조향해서 우회 (대회 코스 규격 확정 후 구현)
            return

        car.drive(self.config.DRIVE_SPEED)
        car.steer(steer_from_lane(sensors["bottom"], self.config.STEER_ERROR_PX))
