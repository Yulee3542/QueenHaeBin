class Mission:
    """모든 미션의 베이스 클래스. main.py가 매 tick step()을 호출한다.

    sensors dict 키:
      top / bottom   : 카메라 프레임 (numpy BGR, 없으면 None)
      lidar_min_m    : 전방 섹터 최소 거리 m (없으면 None)
      lidar_scan     : 원본 스캔 [(quality, angle_deg, dist_mm), ...] (없으면 None)
      ultrasonic     : (left_mm, right_mm) — 측정 실패 시 None
      state          : 아두이노 상태 0 정지 / 1 전진 / 2 후진 (없으면 None)

    car: ArduinoNode — go() / drive(speed) / steer('F'|'L'|'R') / stop() 등
    """

    name = "base"

    def on_start(self, car, config):
        pass

    def step(self, sensors, car):
        pass

    def on_stop(self, car):
        car.stop()
