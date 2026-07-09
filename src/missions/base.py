class Mission:
    """모든 미션의 베이스 클래스. main.py가 매 tick step()을 호출한다.

    sensors dict 키:
      top / bottom   : 전방 카메라 상/하 프레임 (C920 분할, 없으면 None)
                       top=신호등·표지판용, bottom=차선용
      rear           : 후방 카메라 프레임 (T주차용, 없으면 None)
      lidar_min_m    : 전방 섹터 최소 거리 m (없으면 None)
      lidar_scan     : 원본 스캔 [(quality, angle_deg, dist_mm), ...] (없으면 None)
      state          : 아두이노 상태 0 정지 / 1 전진 / 2 후진 (없으면 None)

    car: ArduinoNode
      go() / stop() / drive(speed: -255..255, 음수=후진)
      steer('F'|'L'|'R')  — 스티어링 모터 펄스 (같은 값 연속 호출 무시)
      steer_pulse(d)      — 펄스 강제 반복 전송 (주차 기동용)
    """

    name = "base"

    def on_start(self, car, config):
        pass

    def step(self, sensors, car):
        pass

    def on_stop(self, car):
        car.stop()
