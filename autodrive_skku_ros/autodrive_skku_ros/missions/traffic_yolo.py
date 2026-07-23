"""신호등 색상 인식 — YOLO 검출기 (1순위, HSV 폴백은 traffic.py의 detect_light_color).

팀 저장소(HANLAB_auto, yeoeun_traffic 브랜치) 공용 4클래스(red/yellow/green/off)
YOLO11n 가중치를 쓴다 (`models/traffic_light.pt`, 출처는 models/README.md 참고).
`ultralytics`가 미설치거나 가중치 파일이 없으면 이 모듈은 절대 예외를 던지지
않고 None을 반환한다 — 호출부(traffic.py)가 HSV 검출로 자동 폴백한다.

ROS 없이 테스트: `python3 -m autodrive_skku_ros.missions.traffic_yolo --selftest`
"""
import sys
from pathlib import Path

try:
    from ultralytics import YOLO
except ImportError:
    YOLO = None

# yellow/off/미검출은 모두 None("초록 확정 아님") — HSV 경로와 동일한 안전 편향.
CLASS_TO_COLOR = {"red": "red", "green": "green"}

DEFAULT_MODEL_PATH = str(Path(__file__).resolve().parent.parent / "models" / "traffic_light.pt")

_model_cache = {}  # path -> YOLO 인스턴스 (또는 실패 기록용으로 캐시하지 않음)


def load_model(path=None):
    """YOLO(path) 지연 로드. ultralytics 미설치/가중치 없음/로드 실패 시 None
    (예외를 던지지 않음 — 호출부가 HSV로 폴백하도록).

    path가 이미 로드된 적 있으면 캐시된 인스턴스를 재사용한다(매 틱 재로드 방지).
    """
    path = path or DEFAULT_MODEL_PATH
    if path in _model_cache:
        return _model_cache[path]
    if YOLO is None:
        print("[traffic_yolo] ultralytics 미설치 — HSV 검출로 폴백")
        return None
    if not Path(path).is_file():
        print(f"[traffic_yolo] 가중치 파일 없음: {path} — HSV 검출로 폴백")
        return None
    try:
        model = YOLO(path)
    except Exception as e:
        print(f"[traffic_yolo] 모델 로드 실패: {e} — HSV 검출로 폴백")
        return None
    _model_cache[path] = model
    return model


def detect_light_color_yolo(model, frame, conf=0.35, debug=None):
    """model(load_model 반환값)로 frame에서 신호등 색 판정. 'red'/'green'/None.

    가장 높은 confidence의 검출 하나만 본다(teammate 구현과 동일 — 신호등은
    프레임에 하나만 있다고 가정). 추론 중 어떤 예외가 나도 이 함수는 None을
    반환한다 — 한 프레임의 추론 실패가 미션을 죽이면 안 되고, 호출부가 그
    틱만 HSV로 넘어가면 되기 때문.

    debug: dict를 넘기면 source/class_name/confidence/bbox/result를 채운다
    (debug_viz.draw_traffic_light 오버레이용).
    """
    if model is None or frame is None:
        return None
    try:
        results = model.predict(frame, conf=conf, verbose=False)
        boxes = results[0].boxes
        if boxes is None or len(boxes) == 0:
            if debug is not None:
                debug.update(source="yolo", class_name=None, confidence=None,
                             bbox=None, result=None)
            return None
        best_idx = int(boxes.conf.argmax())
        class_id = int(boxes.cls[best_idx])
        class_name = model.names[class_id]
        confidence = float(boxes.conf[best_idx])
        bbox = tuple(float(v) for v in boxes.xyxy[best_idx])
        result = CLASS_TO_COLOR.get(class_name)
        if debug is not None:
            debug.update(source="yolo", class_name=class_name,
                         confidence=confidence, bbox=bbox, result=result)
        return result
    except Exception as e:
        print(f"[traffic_yolo] 추론 실패, 이번 프레임 HSV로 폴백: {e}")
        if debug is not None:
            debug.update(source="yolo", class_name=None, confidence=None,
                         bbox=None, result=None, error=str(e))
        return None


def _selftest():
    import numpy as np

    ok = True

    def check(name, cond):
        nonlocal ok
        status = "OK" if cond else "X "
        print(f"  [{status}] {name}")
        ok = ok and bool(cond)
        return cond

    print("== traffic_yolo 안전 폴백 ==")
    check("존재하지 않는 경로 → None (예외 없음)",
          load_model("/no/such/path/traffic_light.pt") is None)
    check("model=None → detect는 None", detect_light_color_yolo(None, np.zeros((10, 10, 3))) is None)
    check("frame=None → detect는 None", detect_light_color_yolo("dummy-non-none-model", None) is None)

    print("== 기본 가중치 로드 (ultralytics/가중치 존재 시에만 추론 확인) ==")
    model = load_model()
    if model is None:
        print("  [OK] ultralytics 미설치 또는 가중치 없음 — 폴백 경로만 검증, 추론은 생략")
    else:
        blank = np.zeros((240, 320, 3), dtype=np.uint8)
        debug = {}
        result = detect_light_color_yolo(model, blank, debug=debug)
        check("검은 프레임 추론이 예외 없이 완료 (result는 무엇이든 가능)",
              result in (None, "red", "green"))
        check("debug dict에 source=yolo 기록", debug.get("source") == "yolo")

    return ok


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        sys.exit(0 if _selftest() else 1)
    print(__doc__)
