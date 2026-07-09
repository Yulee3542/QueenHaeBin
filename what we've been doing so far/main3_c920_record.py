import argparse
from datetime import datetime
from pathlib import Path

import cv2
import Function_Library as fl

try:
    import Lib_LiDAR as LiDAR
except ImportError:
    LiDAR = None


EPOCH = 500000
DEFAULT_ARDUINO_PORT = "COM4"
DEFAULT_LIDAR_PORT = ""
DEFAULT_CAMERA_INDEX = 0
BAUDRATE = 9600
STOP_DISTANCE = 700
RECORD_DIR = "recordings"


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--arduino", default=DEFAULT_ARDUINO_PORT)
    parser.add_argument("--lidar", default=DEFAULT_LIDAR_PORT)
    parser.add_argument("--baudrate", type=int, default=BAUDRATE)
    parser.add_argument("--stop-distance", type=int, default=STOP_DISTANCE)
    parser.add_argument("--camera", type=int, default=DEFAULT_CAMERA_INDEX)
    parser.add_argument("--camera2", type=int, default=-1)
    parser.add_argument("--no-split", action="store_true")
    parser.add_argument("--list-cameras", action="store_true")
    parser.add_argument("--no-record", action="store_true")
    parser.add_argument("--record-dir", default=RECORD_DIR)
    parser.add_argument("--fps", type=float, default=20.0)
    return parser.parse_args()


def try_open_camera(index):
    backends = [
        ("CAP_MSMF", cv2.CAP_MSMF),
        ("CAP_DSHOW", cv2.CAP_DSHOW),
        ("CAP_ANY", cv2.CAP_ANY),
    ]

    for name, backend in backends:
        cap = cv2.VideoCapture(index, backend)
        if cap.isOpened():
            ok, frame = cap.read()
            if ok and frame is not None:
                return cap, name
        cap.release()

    return None, None


def list_cameras(max_index=10):
    found = []

    for index in range(max_index):
        cap, backend = try_open_camera(index)
        if cap is not None:
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            found.append((index, backend, width, height))
            cap.release()

    return found


def open_camera(index):
    cap, backend = try_open_camera(index)

    if cap is None:
        available = list_cameras()
        raise RuntimeError(f"camera {index} open failed. available cameras: {available}")

    print(f"camera {index} opened with {backend}")
    return cap


def read_frames(cap0, cap1, split):
    ok0, full_frame = cap0.read()

    if not ok0 or full_frame is None:
        return None, None, None

    if split:
        h = full_frame.shape[0]
        return full_frame, full_frame[:h // 2, :], full_frame[h // 2:, :]

    if cap1 is None:
        return full_frame, full_frame, full_frame

    ok1, frame1 = cap1.read()

    if not ok1 or frame1 is None:
        return full_frame, full_frame, full_frame

    return full_frame, full_frame, frame1


def create_writer(frame, record_dir, fps):
    Path(record_dir).mkdir(parents=True, exist_ok=True)

    h, w = frame.shape[:2]
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = Path(record_dir) / f"c920_{timestamp}.avi"

    fourcc = cv2.VideoWriter_fourcc(*"XVID")
    writer = cv2.VideoWriter(str(path), fourcc, fps, (w, h))

    if not writer.isOpened():
        raise RuntimeError(f"video writer open failed: {path}")

    print(f"recording: {path}")
    return writer, path


def draw_record_overlay(frame, color, obstacle, go):
    output = frame.copy()
    text = f"color={color} obstacle={obstacle} go={go}"
    cv2.putText(output, text, (20, 35), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
    return output


def init_lidar(port):
    if not port:
        return None, None

    if LiDAR is None:
        print("LiDAR library not found. Running without LiDAR.")
        return None, None

    try:
        lidar = LiDAR.libLidar(port)
        lidar.init()
        return lidar, lidar.scanning()
    except Exception as e:
        print(f"LiDAR init failed: {e}")
        print("Running without LiDAR.")
        return None, None


def check_lidar_obstacle(lidar, scanner, stop_distance):
    if lidar is None or scanner is None:
        return False

    try:
        scan = next(scanner)
        detected = lidar.getAngleDistanceRange(scan, 330, 350, 0, stop_distance)
        return len(detected) > 0
    except StopIteration:
        return False
    except Exception as e:
        print(f"LiDAR read failed: {e}")
        return False


def main():
    args = parse_args()

    if args.list_cameras:
        cameras = list_cameras()
        print("available cameras:")
        for index, backend, width, height in cameras:
            print(f"  index={index}, backend={backend}, size={width}x{height}")
        return

    env = fl.libCAMERA()
    arduino = fl.libARDUINO()
    ser = arduino.init(port=args.arduino, baudrate=args.baudrate)

    lidar, lidar_scanner = init_lidar(args.lidar)

    cap0 = open_camera(args.camera)

    cap1 = None
    if args.camera2 >= 0 and args.camera2 != args.camera:
        cap1 = open_camera(args.camera2)

    split = not args.no_split
    prev_go = None
    prev_steer = None
    writer = None
    record_path = None

    try:
        for _ in range(EPOCH):
            full_frame, frame0, frame1 = read_frames(cap0, cap1, split)

            if full_frame is None or frame0 is None or frame1 is None:
                print("camera read failed")
                ser.write(b"S")
                continue

            env.image_show(frame0, frame1)

            color = env.object_detection(frame0, sample=16, print_enable=True)

            direction = env.edge_detection(
                frame1,
                width=500,
                height=120,
                gap=40,
                threshold=150,
                print_enable=True
            )

            obstacle = check_lidar_obstacle(lidar, lidar_scanner, args.stop_distance)

            color_str = str(color).strip().lower()

            if color_str == "red":
                go = False
            elif color_str == "green":
                go = not obstacle
            else:
                go = False

            if go != prev_go:
                ser.write(b"G" if go else b"S")
                prev_go = go

            if go:
                if direction == fl.FORWARD:
                    steer = b"F"
                elif direction == fl.LEFT:
                    steer = b"L"
                elif direction == fl.RIGHT:
                    steer = b"R"
                else:
                    steer = None

                if steer is not None and steer != prev_steer:
                    ser.write(steer)
                    prev_steer = steer
            else:
                prev_steer = None

            if not args.no_record:
                if writer is None:
                    writer, record_path = create_writer(full_frame, args.record_dir, args.fps)

                record_frame = draw_record_overlay(full_frame, color, obstacle, go)
                writer.write(record_frame)

            print(f"camera: {args.camera}  color: {repr(color)}  obstacle: {obstacle}  go: {go}")

            if env.loop_break():
                break

    finally:
        if lidar is not None:
            try:
                lidar.stop()
            except Exception:
                pass

        try:
            ser.write(b"S")
        except Exception:
            pass

        cap0.release()

        if cap1 is not None:
            cap1.release()

        if writer is not None:
            writer.release()
            print(f"saved: {record_path}")

        cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
