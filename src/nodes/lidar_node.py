import threading

try:
    from rplidar import RPLidar
except ImportError:
    RPLidar = None


class LidarNode:
    """RPLidar 스캔을 백그라운드 스레드로 수신해 최신 스캔을 유지한다."""

    def __init__(self, port, baud=115200):
        self.scan = None  # [(quality, angle_deg, dist_mm), ...]
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
        """전방 ±sector_deg 내 최소 거리(m). 스캔 없으면 None."""
        scan = self.scan
        if not scan:
            return None
        dists = []
        for _quality, angle, dist_mm in scan:
            a = (angle + 180.0) % 360.0 - 180.0  # 0도=전방 기준 -180..180
            if abs(a) <= sector_deg and 50 <= dist_mm <= 12000:
                dists.append(dist_mm / 1000.0)
        return min(dists) if dists else None

    def close(self):
        self._running = False
        if self._lidar is not None:
            try:
                self._lidar.stop()
                self._lidar.stop_motor()
                self._lidar.disconnect()
            except Exception:
                pass
