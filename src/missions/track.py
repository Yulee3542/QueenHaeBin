try:
    import cv2
except ImportError:
    cv2 = None

from .base import Mission


def steer_from_lane(frame, error_px=50):
    """하단 카메라 프레임에서 차선 에지 중심(centroid)으로 F/L/R 판단."""
    if cv2 is None or frame is None:
        return "F"

    h, w = frame.shape[:2]
    roi = frame[int(h * 0.55):h, :]

    gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
    blur = cv2.GaussianBlur(gray, (5, 5), 0)
    edges = cv2.Canny(blur, 60, 160)

    m = cv2.moments(edges)
    if m["m00"] == 0:
        return "F"

    cx = int(m["m10"] / m["m00"])
    error = cx - w // 2

    if error < -error_px:
        return "L"
    if error > error_px:
        return "R"
    return "F"


class TrackMission(Mission):
    """트랙 주행: 차선 추종으로 트랙을 돈다."""

    name = "track"

    def on_start(self, car, config):
        self.config = config
        car.go()
        car.drive(config.DRIVE_SPEED)

    def step(self, sensors, car):
        car.steer(steer_from_lane(sensors["bottom"], self.config.STEER_ERROR_PX))
