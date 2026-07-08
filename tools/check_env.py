#!/usr/bin/env python3
"""새 장비에서 가장 먼저 실행하는 환경 점검 스크립트.

사용법: python tools/check_env.py
"""
import glob
import os
import sys


def is_wsl():
    try:
        with open("/proc/version") as f:
            return "microsoft" in f.read().lower()
    except OSError:
        return False


def check_imports():
    print("== Python 패키지 ==")
    ok = True
    for name in ("cv2", "numpy", "serial", "rplidar"):
        try:
            __import__(name)
            print(f"  [OK] {name}")
        except ImportError:
            print(f"  [X ] {name} — pip install -r requirements.txt 필요")
            ok = False
    return ok


def check_cameras():
    print("\n== 카메라 (/dev/video*) ==")
    if not sys.platform.startswith("linux"):
        print("  (Linux가 아니므로 건너뜀)")
        return True
    devices = sorted(glob.glob("/dev/video*"))
    if not devices:
        print("  [X ] 카메라 장치 없음")
        return False
    for dev in devices:
        print(f"  [OK] {dev}")
    return True


def check_serial_ports():
    print("\n== 시리얼 포트 ==")
    try:
        from serial.tools import list_ports
    except ImportError:
        print("  [X ] pyserial 미설치")
        return False
    ports = list(list_ports.comports())
    if not ports:
        print("  [X ] 시리얼 포트 없음 (아두이노/라이다 미연결?)")
        return False
    for p in ports:
        print(f"  [OK] {p.device}: {p.description}")
        if sys.platform.startswith("linux") and not os.access(p.device, os.R_OK | os.W_OK):
            print(f"       [!] 권한 없음 — dialout 그룹 추가 후 재로그인 필요")
    return True


def main():
    print(f"Python {sys.version.split()[0]} / {sys.platform}"
          + (" (WSL2)" if is_wsl() else ""))
    ok = check_imports()
    cams = check_cameras()
    sers = check_serial_ports()

    if is_wsl() and not (cams and sers):
        print("\n[WSL2] 장치가 안 보이면 Windows PowerShell에서 usbipd로 연결:")
        print("  usbipd list")
        print("  usbipd bind --busid <ID>")
        print("  usbipd attach --wsl --busid <ID>")
        print("  (카메라 2개 + 아두이노 + 라이다 각각. README 'WSL2에서 실행' 절 참고)")

    print("\n결과:", "이상 없음" if (ok and cams and sers) else "위 [X]/[!] 항목 해결 필요")


if __name__ == "__main__":
    main()
