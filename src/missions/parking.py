from .base import Mission


class ParkingMission(Mission):
    """수직 주차: SEARCH → ALIGN → REVERSE → DONE 상태머신.

    상태 전이 골격은 완성돼 있고, 아래 감지 메서드 3개(slot_found / aligned /
    parked)를 실차 테스트하며 채우면 된다.
    """

    name = "parking"

    def on_start(self, car, config):
        self.config = config
        self.state = "SEARCH"
        car.go()

    def step(self, sensors, car):
        if self.state == "SEARCH":
            car.drive(self.config.SLOW_SPEED)
            car.steer("F")
            if self.slot_found(sensors):
                self.state = "ALIGN"

        elif self.state == "ALIGN":
            car.drive(0)
            # TODO: 슬롯 입구에 차체를 맞추는 조향 기동
            if self.aligned(sensors):
                self.state = "REVERSE"

        elif self.state == "REVERSE":
            car.drive(-self.config.SLOW_SPEED)
            car.steer("F")
            if self.parked(sensors):
                self.state = "DONE"

        else:  # DONE
            car.stop()

    # ---- 실차에서 채울 감지 로직 ----

    def slot_found(self, sensors):
        # TODO: 초음파/라이다로 주차 슬롯 입구 감지 (예: 측면 거리 급증)
        return False

    def aligned(self, sensors):
        # TODO: 슬롯과 차체 정렬 판정
        return False

    def parked(self, sensors):
        # TODO: 진입 완료 판정 (예: 좌우 초음파 거리 안정 + 목표 깊이 도달)
        return False
