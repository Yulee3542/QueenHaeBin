import time

from .base import Mission


class EscapeMission(Mission):
    """탈출: REVERSE → TURN → FORWARD → DONE 상태머신.

    상태 전이 골격은 완성돼 있고, 시간 기반 임시 판정을 실차 테스트하며
    센서 기반(초음파/라이다) 판정으로 바꾸면 된다.
    """

    name = "escape"

    def on_start(self, car, config):
        self.config = config
        self.state = "REVERSE"
        self.t0 = time.time()
        car.go()

    def step(self, sensors, car):
        elapsed = time.time() - self.t0

        if self.state == "REVERSE":
            car.drive(-self.config.SLOW_SPEED)
            car.steer("F")
            if self.reverse_done(sensors, elapsed):
                self._to("TURN")

        elif self.state == "TURN":
            car.drive(self.config.SLOW_SPEED)
            car.steer("L")  # TODO: 라이다로 열린 방향을 찾아 회전 방향 결정
            if self.turn_done(sensors, elapsed):
                self._to("FORWARD")

        elif self.state == "FORWARD":
            car.drive(self.config.DRIVE_SPEED)
            car.steer("F")
            if self.escaped(sensors, elapsed):
                self._to("DONE")

        else:  # DONE
            car.stop()

    def _to(self, state):
        self.state = state
        self.t0 = time.time()

    # ---- 실차에서 채울 판정 로직 ----

    def reverse_done(self, sensors, elapsed):
        # TODO: 시간 대신 후방 여유 공간 확보 판정으로 교체
        return elapsed > 2.0

    def turn_done(self, sensors, elapsed):
        # TODO: 전방이 열렸는지 라이다로 판정
        return elapsed > 1.5

    def escaped(self, sensors, elapsed):
        # TODO: 탈출 완료 판정 (코스 규격 확정 후)
        return False
