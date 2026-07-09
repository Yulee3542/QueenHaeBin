from .base import Mission


class TParkingMission(Mission):
    """3. T 주차

    목표:
      (1) 라이다 기반 맵 빌딩          — TODO: map_update() / map_complete()
      (2) 후방 카메라 기반 주차선 인식  — TODO: reverse_lane_steer()
      (3) 차선 인식 도로 주행 (후진)    — TODO: reverse_lane_steer()
      (4) T주차 알고리즘에 따른 주차    — TODO: PARK 상태 기동 시퀀스

    상태머신: MAP_BUILD → FIND_SLOT → REVERSE_ALIGN → PARK → DONE
    상태 전이 골격은 완성돼 있고, 각 TODO 메서드를 실차 테스트하며 채우면 된다.
    후방 카메라는 config.REAR_CAMERA 인덱스 지정 시 sensors["rear"]로 들어온다.
    """

    name = "t_parking"

    def on_start(self, car, config):
        self.config = config
        self.state = "MAP_BUILD"
        self.scans = []  # 맵 빌딩용 라이다 스캔 누적
        car.go()

    def step(self, sensors, car):
        if self.state == "MAP_BUILD":
            car.drive(self.config.SLOW_SPEED)
            car.steer("F")
            if sensors["lidar_scan"] is not None:
                self.map_update(sensors["lidar_scan"])
            if self.map_complete():
                self.state = "FIND_SLOT"

        elif self.state == "FIND_SLOT":
            car.drive(0)
            if self.slot_found(sensors):
                self.state = "REVERSE_ALIGN"

        elif self.state == "REVERSE_ALIGN":
            car.drive(-self.config.SLOW_SPEED)
            steer = self.reverse_lane_steer(sensors["rear"])
            if steer is not None:
                car.steer(steer)
            if self.aligned(sensors):
                self.state = "PARK"

        elif self.state == "PARK":
            # TODO(4단계): T주차 기동 시퀀스 — steer_pulse + drive(±SLOW_SPEED)
            # 조합으로 슬롯 진입. 완료 판정 후 DONE.
            if self.parked(sensors):
                self.state = "DONE"

        else:  # DONE
            car.stop()

    # ---- 실차에서 채울 로직 ----

    def map_update(self, scan):
        # TODO(1단계): 스캔을 점유 격자(occupancy grid)에 누적.
        # 오도메트리가 없으므로 저속 직진 가정 or 정지 상태 스캔 사용 권장.
        self.scans.append(scan)

    def map_complete(self):
        # TODO(1단계): 맵이 충분히 쌓였는지 판정 (예: 스캔 N회 누적)
        return False

    def slot_found(self, sensors):
        # TODO: 맵/스캔에서 T주차 슬롯 위치·방향 결정
        return False

    def reverse_lane_steer(self, rear_frame):
        # TODO(2,3단계): 후방 카메라에서 주차선 인식 → 'F'/'L'/'R' 반환.
        # 후진 시 조향 방향이 반대임에 주의. None이면 조향 유지.
        return None

    def aligned(self, sensors):
        # TODO: 슬롯 진입 각도 정렬 판정
        return False

    def parked(self, sensors):
        # TODO: 주차 완료 판정 (예: 라이다 후방 거리 + 주차선 위치)
        return False
