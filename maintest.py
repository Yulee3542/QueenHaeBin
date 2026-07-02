import argparse
import time
import re

try:
    import serial
except ImportError:
    serial = None

try:
    import cv2
except ImportError:
    cv2 = None


class ArduinoCar:
    def __init__(self, port, baudrate=9600):
        if serial is None:
            raise RuntimeError("pyserial is not installed")
        self.ser = serial.Serial(port, baudrate, timeout=0.05)
        time.sleep(2)
        self.last = {}

    def send(self, key, value):
        if self.last.get(key) == value:
            return
        self.ser.write(value.encode("ascii"))
        self.last[key] = value

    def set_drive(self, enabled):
        self.send("drive", "G" if enabled else "S")

    def set_steer(self, steer):
        if steer not in ["F", "L", "R"]:
            steer = "F"
        self.send("steer", steer)

    def set_camera_obstacle(self, detected):
        self.send("camera", "C" if detected else "c")

    def set_lidar_obstacle(self, detected):
        self.send("lidar", "D" if detected else "d")

    def read_state(self):
        lines = []
        while self.ser.in_waiting > 0:
            line = self.ser.readline().decode("utf-8", errors="ignore").strip()
            if line:
                lines.append(line)
        return lines

    def close(self):
        self.set_drive(False)
        time.sleep(0.05)
        self.ser.close()


class CameraManager:
    def __init__(self, top_index=0, bottom_index=1, show=False):
        self.show = show and cv2 is not None
        self.top = None
        self.bottom = None

        if cv2 is not None:
            self.top = cv2.VideoCapture(top_index)
            self.bottom = cv2.VideoCapture(bottom_index)

    def read(self):
        top_frame = None
        bottom_frame = None

        if self.top is not None and self.top.isOpened():
            ok, frame = self.top.read()
            if ok:
                top_frame = frame

        if self.bottom is not None and self.bottom.isOpened():
            ok, frame = self.bottom.read()
            if ok:
                bottom_frame = frame

        return top_frame, bottom_frame

    def detect_obstacle_with_camera(self, top_frame, bottom_frame):
        return False

    def detect_steer_from_lane(self, bottom_frame):
        if cv2 is None or bottom_frame is None:
            return "F"

        h, w = bottom_frame.shape[:2]
        roi = bottom_frame[int(h * 0.55):h, :]

        gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
        blur = cv2.GaussianBlur(gray, (5, 5), 0)
        edges = cv2.Canny(blur, 60, 160)

        m = cv2.moments(edges)
        if m["m00"] == 0:
            return "F"

        cx = int(m["m10"] / m["m00"])
        center = w // 2
        error = cx - center

        if error < -50:
            return "L"
        if error > 50:
            return "R"
        return "F"

    def display(self, top_frame, bottom_frame):
        if not self.show or cv2 is None:
            return True

        if top_frame is not None:
            cv2.imshow("top_camera", top_frame)
        if bottom_frame is not None:
            cv2.imshow("bottom_camera", bottom_frame)

        key = cv2.waitKey(1) & 0xFF
        return key != ord("q")

    def close(self):
        if self.top is not None:
            self.top.release()
        if self.bottom is not None:
            self.bottom.release()
        if cv2 is not None:
            cv2.destroyAllWindows()


class LidarReader:
    def __init__(self, port=None, baudrate=115200):
        self.ser = None
        if port and serial is not None:
            self.ser = serial.Serial(port, baudrate, timeout=0.02)
            time.sleep(1)

    def read_min_distance_m(self):
        if self.ser is None:
            return None

        values = []

        while self.ser.in_waiting > 0:
            line = self.ser.readline().decode("utf-8", errors="ignore").strip()
            nums = re.findall(r"[-+]?\d*\.\d+|\d+", line)

            for item in nums:
                value = float(item)
                if value > 20:
                    values.append(value / 1000.0)
                else:
                    values.append(value)

        if not values:
            return None

        values = [v for v in values if 0.05 <= v <= 12.0]
        if not values:
            return None

        return min(values)

    def close(self):
        if self.ser is not None:
            self.ser.close()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--arduino", required=True)
    parser.add_argument("--arduino-baud", type=int, default=9600)
    parser.add_argument("--lidar", default=None)
    parser.add_argument("--lidar-baud", type=int, default=115200)
    parser.add_argument("--top-camera", type=int, default=0)
    parser.add_argument("--bottom-camera", type=int, default=1)
    parser.add_argument("--threshold-m", type=float, default=1.0)
    parser.add_argument("--show", action="store_true")
    args = parser.parse_args()

    car = ArduinoCar(args.arduino, args.arduino_baud)
    cameras = CameraManager(args.top_camera, args.bottom_camera, args.show)
    lidar = LidarReader(args.lidar, args.lidar_baud)

    try:
        car.set_drive(True)
        car.set_steer("F")
        car.set_camera_obstacle(False)
        car.set_lidar_obstacle(False)

        while True:
            top_frame, bottom_frame = cameras.read()

            camera_obstacle = cameras.detect_obstacle_with_camera(top_frame, bottom_frame)

            lidar_distance_m = lidar.read_min_distance_m()
            lidar_obstacle = lidar_distance_m is not None and lidar_distance_m <= args.threshold_m

            steer = cameras.detect_steer_from_lane(bottom_frame)

            car.set_camera_obstacle(camera_obstacle)
            car.set_lidar_obstacle(lidar_obstacle)
            car.set_steer(steer)

            for state in car.read_state():
                if state == "0":
                    print("Arduino state: 0 STOP")
                elif state == "1":
                    print("Arduino state: 1 FORWARD")
                elif state == "2":
                    print("Arduino state: 2 BACKWARD")
                else:
                    print("Arduino:", state)

            if not cameras.display(top_frame, bottom_frame):
                break

            time.sleep(0.03)

    except KeyboardInterrupt:
        pass

    finally:
        car.close()
        cameras.close()
        lidar.close()


if __name__ == "__main__":
    main()
