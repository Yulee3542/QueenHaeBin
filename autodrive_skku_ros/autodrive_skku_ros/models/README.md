# traffic_light.pt

YOLO11n 4-class 신호등 색상 분류기 (`red`/`yellow`/`green`/`off`) — 팀 저장소
[HANLAB_auto](https://github.com/yeoeun0402/HANLAB_auto) `yeoeun_traffic` 브랜치의
`challenge_layout/mission2_TrafficLight/best.pt`에서 가져온 공용 학습 가중치.

**주의(팀원 노트 그대로 유지)**: 이 HANLAB 실내 트랙/조명/신호등 하드웨어 기준으로
학습됨 — 카메라, 조명, 트랙, 신호등 장비가 바뀌면 재검증 필요. 자체 재학습한
가중치로 교체하려면 이 파일을 같은 이름(`traffic_light.pt`)으로 덮어쓰면 된다
(경로는 `missions/traffic_yolo.py`의 `DEFAULT_MODEL_PATH` 단일 소스).
