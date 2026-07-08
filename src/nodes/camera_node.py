import sys
import threading

try:
    import cv2
except ImportError:
    cv2 = None

WSL2_HINT = "WSL2라면 Windows에서 usbipd attach 필요 (README 'WSL2에서 실행' 절 참고)"


class CameraNode:
    """상/하단 USB 카메라를 백그라운드 스레드로 계속 읽어 최신 프레임을 유지한다."""

    def __init__(self, top_index, bottom_index, width=640, height=480):
        self._width = width
        self._height = height
        self._lock = threading.Lock()
        self._top_frame = None
        self._bottom_frame = None
        self._top = self._open(top_index, "top")
        self._bottom = self._open(bottom_index, "bottom")
        self._running = self._top is not None or self._bottom is not None
        if self._running:
            threading.Thread(target=self._loop, daemon=True).start()

    def _open(self, index, name):
        if cv2 is None:
            print("[camera] opencv 미설치 — 카메라 없이 실행")
            return None
        if sys.platform.startswith("linux"):
            cap = cv2.VideoCapture(index, cv2.CAP_V4L2)
        else:
            cap = cv2.VideoCapture(index)
        if not cap.isOpened():
            print(f"[camera] {name}({index}) 열기 실패 — {WSL2_HINT}")
            return None
        # USB 웹캠은 MJPG로 열어야 640x480@30fps가 안정적으로 나온다
        cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*"MJPG"))
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, self._width)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self._height)
        print(f"[camera] {name}({index}) 연결됨")
        return cap

    def _loop(self):
        while self._running:
            if self._top is not None:
                ok, frame = self._top.read()
                if ok:
                    with self._lock:
                        self._top_frame = frame
            if self._bottom is not None:
                ok, frame = self._bottom.read()
                if ok:
                    with self._lock:
                        self._bottom_frame = frame

    def latest(self):
        """(top_frame, bottom_frame). 없는 카메라는 None."""
        with self._lock:
            return self._top_frame, self._bottom_frame

    def close(self):
        self._running = False
        for cap in (self._top, self._bottom):
            if cap is not None:
                cap.release()
        if cv2 is not None:
            cv2.destroyAllWindows()
