# autodrive_for_skku

국민 AI 자율주행 경진대회 차량 코드. 아두이노 메가(모터/조향/초음파) + USB 카메라 2대(상/하단) + RPLidar 구성이며, `main.py` 한 번 실행으로 모든 센서 노드가 뜨고 미션을 선택해 주행한다.

주 실행 환경은 **Ubuntu**, 개발용으로 **WSL2**도 지원한다 (카메라/시리얼은 usbipd 연결 필요 — 아래 [WSL2에서 실행](#wsl2에서-실행) 참고).

## 빠른 시작 (Ubuntu / WSL2)

```bash
git clone https://github.com/Yulee3542/autodrive_for_skku.git
cd autodrive_for_skku
./setup.sh                     # apt + venv + 패키지 + 시리얼 권한 자동 설정
source .venv/bin/activate
python tools/check_env.py      # 카메라/시리얼/패키지 점검
python main.py                 # 미션 메뉴가 뜬다
```

미션을 미리 정해서 바로 실행할 수도 있다:

```bash
python main.py --mission track --show
```

| 인자 | 설명 |
|------|------|
| `--mission {track,obstacle,parking,escape}` | 생략하면 메뉴에서 선택 |
| `--arduino /dev/ttyACM0` | 아두이노 포트 (기본: 자동 감지) |
| `--lidar /dev/ttyUSB0` | 라이다 포트 (기본: 자동 감지) |
| `--top-camera 0` / `--bottom-camera 1` | 카메라 인덱스 |
| `--show` | 카메라 창 표시 (`q`로 종료) |

기본값(속도, 정지 거리, 카메라 해상도 등)은 전부 `config.py`에 있다.

## 미션

| 이름 | 내용 | 상태 |
|------|------|------|
| `track` | 트랙 주행 — 하단 카메라 차선 추종 | 동작 |
| `obstacle` | 장애물 회피 — 차선 추종 + 라이다 정지 | 동작 (회피 기동 TODO) |
| `parking` | 수직 주차 — SEARCH→ALIGN→REVERSE 상태머신 | 골격 (감지 로직 TODO) |
| `escape` | 탈출 — REVERSE→TURN→FORWARD 상태머신 | 골격 (판정 로직 TODO) |

새 미션 추가: `src/missions/`에 `Mission`을 상속한 클래스를 만들고 `src/missions/__init__.py`의 `MISSIONS`에 등록하면 메뉴에 자동으로 나타난다. `parking.py`/`escape.py`의 `TODO` 메서드가 실차 테스트에서 채워야 할 지점이다.

## 폴더 구조

```
├── main.py                  # 진입점: 미션 선택 + 모든 노드 기동
├── config.py                # 포트/속도/임계값 등 튜닝 값
├── setup.sh                 # 새 환경 자동 설정
├── arduino/car_controller/  # 차량 펌웨어 (.ino)
├── src/
│   ├── nodes/               # 센서/액추에이터 스레드 (arduino, camera, lidar)
│   └── missions/            # 미션 로직 (base 상속)
└── tools/check_env.py       # 환경 점검
```

## 펌웨어 (아두이노 메가)

`arduino/car_controller/car_controller.ino`를 Arduino IDE로 업로드한다 (외부 라이브러리 불필요). 보드: Arduino Mega 2560.

### 시리얼 프로토콜 (9600bps)

| 방향 | 명령 | 의미 |
|------|------|------|
| PC→차량 | `G` / `S` | 주행 허용 / 정지 |
| PC→차량 | `F` / `L` / `R` | 조향 (차동 구동) |
| PC→차량 | `V<int>\n` | 속도 -255..255, **음수 = 후진** |
| PC→차량 | `C`/`c`, `D`/`d` | 카메라/라이다 장애물 플래그 |
| 차량→PC | `0`/`1`/`2` | 정지 / 전진 / 후진 |
| 차량→PC | `U,<left>,<right>` | 좌우 초음파 거리(mm), 실패 시 -1 |

안전 장치:
- **워치독**: `V` 명령 수신 후 500ms 이상 시리얼이 끊기면 자동 정지 (파이썬 쪽은 200ms마다 keepalive 전송)
- **초음파 자동 정지**: 전진 중에만 적용 — 후진 주차가 측면 센서에 막히지 않음
- `V`를 한 번도 받지 못하면 기존 포텐셔미터 속도 제어로 동작 (구버전 호환)

## WSL2에서 실행

WSL2는 USB 장치가 기본적으로 안 보이므로 **카메라 2대 + 아두이노 + 라이다를 usbipd로 붙여야 한다.**

1. Windows PowerShell(관리자):
   ```powershell
   winget install usbipd
   usbipd list                        # 장치 BUSID 확인
   usbipd bind --busid <ID>           # 장치마다 1회
   usbipd attach --wsl --busid <ID>   # WSL 재시작/장치 재연결 시마다
   ```
2. WSL 안에서 확인:
   ```bash
   ls /dev/video*                     # 카메라
   ls /dev/ttyACM* /dev/ttyUSB*       # 아두이노/라이다
   python tools/check_env.py
   ```

- 카메라가 attach돼도 `/dev/video*`가 안 생기면 WSL 커널이 UVC를 지원하는지 확인 (`uname -r` 5.15+ 권장, `wsl --update`).
- `--show` 카메라 창은 WSLg(Windows 11 기본)로 그대로 뜬다.
- 장치가 없어도 `main.py`는 경고만 내고 실행된다 — 로직 개발은 하드웨어 없이 가능.

## 문제 해결

| 증상 | 해결 |
|------|------|
| `/dev/ttyUSB0` permission denied | `./setup.sh`가 dialout 그룹에 추가함 — **재로그인** 필요 |
| 카메라 열기 실패 | 다른 프로그램이 점유 중인지 확인, WSL2면 usbipd attach |
| 아두이노/라이다 포트 뒤바뀜 | `config.py`의 `ARDUINO_PORT`/`LIDAR_PORT` 직접 지정 |
| 차가 안 움직임 | 미션이 `car.go()`를 호출했는지, 펌웨어 업로드 여부, 초음파 1m 이내 장애물 확인 |

## 실차 첫 주행 체크리스트

1. `car_controller.ino` 업로드 (기존 test5.ino 대체)
2. `python tools/check_env.py` — 장치 4개 모두 인식 확인
3. 바퀴를 띄운 상태에서 `python main.py --mission track --show` — 전진/조향 확인
4. `V-100` 후진 동작 확인 (parking/escape 미션이 사용)
5. 초음파 앞 1m에 장애물을 두고 자동 정지 확인
6. 시리얼 케이블을 뽑아 500ms 내 정지(워치독) 확인
