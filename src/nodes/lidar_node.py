import threading

try:
    from rplidar import RPLidar
except ImportError:
    RPLidar = None

# 기본 장착 파라미터 — config.LIDAR_MOUNT 미전달 시 폴백 (2026-07-09 실측과 동일)
DEFAULT_MOUNT = dict(yaw_offset_deg=0.0, invert=False, to_rear_m=0.075)


# ---- 후방 장착 지오메트리 (순수 함수, 하드웨어 불필요 — 스모크 테스트 대상) ----
#
# RP라이다는 차량 후방(후단 뒤 75mm, 지면 140mm)에 장착되고, T주차 후진용이라
# 각도 규약은 "원시 0도 = 차량 후방"이다. 아래 함수들은 원시 각도를
# 차량 전방 기준 bearing(-180..180, +가 좌측)으로 변환해 다룬다:
#   bearing = normalize(원시각도*(invert? -1:+1) + yaw_offset_deg + 180)
# 전방 |bearing| < self_mask_deg 는 자차 차체 반사(전방이 차체에 막힘)로 제거한다.

def vehicle_bearing_deg(raw_angle_deg, mount):
    """라이다 원시 각도 → 차량 전방 기준 bearing (-180..180, +좌측)."""
    a = -raw_angle_deg if mount.get("invert") else raw_angle_deg
    a = a + mount.get("yaw_offset_deg", 0.0) + 180.0
    return (a + 180.0) % 360.0 - 180.0


def filter_self(scan, mount, self_mask_deg=75.0):
    """유효 스캔점만 남긴다: [(bearing_deg, dist_mm), ...].

    - 거리 게이트 50~12000mm (노이즈/최대거리)
    - 전방 |bearing| < self_mask_deg 제거 — 자차 차체가 전방 wedge를 가려
      해당 각도의 반사는 전부 자차 자신이다.
    """
    out = []
    for _quality, angle, dist_mm in scan:
        if not (50 <= dist_mm <= 12000):
            continue
        b = vehicle_bearing_deg(angle, mount)
        if abs(b) < self_mask_deg:
            continue
        out.append((b, dist_mm))
    return out


def rear_min_m(scan, mount, sector_deg=30, self_mask_deg=75.0):
    """후방 ±sector_deg 내 최소 거리 — 뒤 범퍼 기준 m. 스캔 없으면 None.

    라이다 축이 뒤 범퍼보다 75mm 뒤에 있으므로 뒤 범퍼 기준 거리는
    라이다 거리 + to_rear_m 이다.
    """
    if not scan:
        return None
    to_rear = mount.get("to_rear_m", 0.075)
    dists = [d for b, d in filter_self(scan, mount, self_mask_deg)
             if abs(b) >= 180.0 - sector_deg]
    return (min(dists) / 1000.0 + to_rear) if dists else None


def side_clearance_m(scan, side, mount, window_deg=(75.0, 100.0), self_mask_deg=75.0,
                     min_m=0.30):
    """좌('L')/우('R') 측면 여유 거리 m. 스캔 없거나 반사 없으면 None.

    자차 실루엣을 벗어나는 abeam 창(기본 전방 기준 75~100도)만 사용 —
    이보다 전방 쪽 각도는 차체에 가려 자차 반사만 잡힌다.
    min_m: 시뮬 실측(2026-07-09)에서 자차 "코너" 반사가 bearing ~75-82도,
    0.20~0.26m에 남는 것이 확인됨 — self_mask 각도만으로는 못 거르므로
    이 근거리 게이트로 함께 제거한다 (실차 장착 후 재보정 대상).
    """
    if not scan:
        return None
    lo, hi = window_deg
    sign = 1.0 if side == "L" else -1.0
    dists = [d for b, d in filter_self(scan, mount, self_mask_deg)
             if lo <= sign * b <= hi and d / 1000.0 >= min_m]
    return (min(dists) / 1000.0) if dists else None


class LidarNode:
    """RPLidar 스캔을 백그라운드 스레드로 수신해 최신 스캔을 유지한다.

    2026-07-09: 후방 장착(0도=차량 후방) 반영 — min_distance_m()은 이제
    "후방" 섹터의 뒤 범퍼 기준 최소 거리를 반환한다 (T주차 후진용).
    전방은 자차 차체에 막혀 라이다로 볼 수 없다.
    """

    def __init__(self, port, baud=115200, mount=None, self_mask_deg=75.0):
        self.scan = None  # [(quality, angle_deg, dist_mm), ...]
        self.mount = mount or DEFAULT_MOUNT
        self.self_mask_deg = self_mask_deg
        self._lidar = None
        self._running = False

        if RPLidar is None:
            print("[lidar] rplidar 패키지 미설치 — 라이다 없이 실행")
            return
        if port is None:
            print("[lidar] 포트를 찾지 못함 (--lidar 로 지정) — 라이다 없이 실행")
            return
        try:
            self._lidar = RPLidar(port, baudrate=baud)
        except Exception as e:
            print(f"[lidar] {port} 열기 실패: {e} — 라이다 없이 실행")
            self._lidar = None
            return

        self._running = True
        threading.Thread(target=self._loop, daemon=True).start()
        print(f"[lidar] {port} 연결됨")

    def _loop(self):
        try:
            for scan in self._lidar.iter_scans(max_buf_meas=3000):
                if not self._running:
                    break
                self.scan = scan
        except Exception as e:
            if self._running:
                print(f"[lidar] 수신 중단: {e}")
            self.scan = None

    def min_distance_m(self, sector_deg=30):
        """후방 ±sector_deg 내 최소 거리(m, 뒤 범퍼 기준). 스캔 없으면 None."""
        return rear_min_m(self.scan, self.mount, sector_deg, self.self_mask_deg)

    def side_clearance_m(self, side, window_deg=(75.0, 100.0)):
        """좌('L')/우('R') 측면 여유 거리(m). 회피 방향 결정용."""
        return side_clearance_m(self.scan, side, self.mount, window_deg, self.self_mask_deg)

    def close(self):
        self._running = False
        if self._lidar is not None:
            try:
                self._lidar.stop()
                self._lidar.stop_motor()
                self._lidar.disconnect()
            except Exception:
                pass
