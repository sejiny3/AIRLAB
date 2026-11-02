# π0.5: 두 번째 VLA 정책

첫 번째 VLA 정책(`ros2_ws/src/airlab_vla`)은 작은 모델을 노트북 CPU에서 처음부터 학습시켰습니다. 이 폴더는 두 번째 정책을 추가합니다. [π0.5](https://github.com/Physical-Intelligence/openpi)는 여러 로봇 데이터로 미리 학습된 큰 VLA 모델이고, 여기서는 같은 집기 시연으로 파인튜닝합니다. 노트북에 GPU가 없으므로 학습과 추론은 Google Colab(A100 또는 L4)에서 돌리고, 노트북은 데이터를 녹화하고 변환하는 일만 맡습니다.

| 단계 | 어디서 | 하는 일 |
| --- | --- | --- |
| 1 | 노트북 | 시연을 224 px로 녹화하고 LeRobot 데이터셋으로 변환 |
| 2 | Colab | openpi로 `pi05_base`를 LoRA 파인튜닝하고 MuJoCo에서 평가 |
| 3 | Colab + 노트북 | Colab에서 정책을 서빙하고, 대시보드의 **π0.5 집기** 모드로 실행 |

| 파일 | 내용 |
| --- | --- |
| `convert_to_lerobot.py` | 녹화한 npz를 LeRobot 데이터셋으로 변환 |
| `airlab_policy.py` | π0.5의 입출력 변환과 학습 설정 `pi05_airlab` |
| `run_openpi.py` | openpi 코드를 고치지 않고, 설정을 추가해 openpi 스크립트를 실행 |
| `download_base.py` | `pi05_base` 가중치를 CRC32C를 대조하며 받기 (Colab의 gsutil이 큰 파일을 거부함) |
| `assets/` | 전체 데이터로 계산해 둔 정규화 통계 `norm_stats.json` |
| `train_pi05.ipynb` | Colab 학습 노트북 |
| `evaluate_pi05.py` | 작은 정책과 같은 시험 장면에서 평가 |
| `serve_pi05.py` | 학습한 정책을 대시보드에 제공하는 서버 |

## 1. 시연과 데이터셋 (노트북)

π0.5는 224×224 영상을 보므로 시연을 그 크기로 다시 녹화합니다. 장면, 전문가, 명령 문장은 작은 정책과 같고(시드도 같음) 카메라 크기만 다릅니다.

```bash
ros2 run airlab_vla record --cameras pi05 --episodes 1200   # ~/airlab_vla/demos_pi05, 약 1.7 GB, 40분
```

| | 작은 정책 | π0.5 |
| --- | --- | --- |
| 머리 카메라 | 128×72 | 224×126, 위아래 검은 띠를 붙여 224×224 |
| 손목 카메라 | 96×96 | 224×224 |
| 상태 | 8 | 8 (오른팔 관절 1-7 + 손가락) |

변환은 openpi가 쓰는 LeRobot 버전이 있는 Python 3.11 환경에서 합니다. 스크립트 머리말에 의존성이 적혀 있어서 `uv`가 첫 실행 때 환경을 만듭니다(CPU용 torch, 약 1분).

```bash
uv run pi05/convert_to_lerobot.py --limit 5 --repo-id airlab/pick_pi05_test   # 빠른 시험
uv run pi05/convert_to_lerobot.py                                             # 전체, 약 20분
```

데이터셋은 `~/.cache/huggingface/lerobot/airlab/pick_pi05`에 생깁니다. 에피소드 1155개, 88,935 프레임, 명령 문장 21종, 2.1 GB, 초당 10프레임입니다.

| 항목 | 크기 | |
| --- | --- | --- |
| `image` | 224×224×3 | 머리 카메라 |
| `wrist_image` | 224×224×3 | 오른손목 카메라 |
| `state` | 8 | 측정한 관절각 |
| `actions` | 8 | 전문가의 관절 목표값 |
| `done` | 1 | 마지막 유지 구간에서 1 (집기 끝) |
| `task` | 문장 | 명령, 예: "pick up the red box" |

Drive에는 파일이 1155개 넘는 폴더 대신 tar 하나로 올립니다. Drive는 작은 파일이 많으면 아주 느립니다.

```bash
tar -cf ~/airlab_vla/pick_pi05.tar -C ~/.cache/huggingface/lerobot/airlab pick_pi05   # 2.2 GB
```

## 2. 파인튜닝과 평가 (Colab)

`내 드라이브/airlab_pi05/`에 `pick_pi05.tar`를 올린 뒤, Colab에서 [train_pi05.ipynb](train_pi05.ipynb)를 열어 A100 런타임으로 위에서부터 실행합니다.

학습 설정(`airlab_policy.py`)의 핵심은 다음과 같습니다.

- **LoRA 파인튜닝:** 34억 개 파라미터 중 4.7억 개만 학습합니다. 비전 인코더 전체, 언어 모델의 LoRA 추가분, 행동 입출력 층이 여기에 들어갑니다. GPU 메모리는 22.5 GB가 넘게 필요합니다.
- **행동 9개:** 관절 목표 8개에 `done`을 더했습니다. openpi는 원래 `actions`만 내보내므로, `done`을 행동의 일부로 학습시켜 작은 정책처럼 집기가 끝났는지 알 수 있게 했습니다.
- **상대 행동:** 팔 관절 7개는 청크 시작 시점의 상태에 대한 차이로 학습합니다. 손가락과 `done`은 절대값입니다.
- **상태 입력:** π0.5의 기본대로 상태를 숫자 토큰으로 바꿔 프롬프트에 넣습니다. openpi의 `pi05_libero` 예제는 상태를 넣지 않습니다.
- **청크:** 10스텝(1초)으로 작은 정책과 같습니다. 평가에서는 5스텝 실행하고 다시 추론합니다.

체크포인트는 하나에 약 11 GB로 예상합니다. 2500 스텝마다 Drive로 복사하고 복사가 끝나면 이전 것을 지우므로, 교체할 때는 Drive에 약 22 GB가 필요합니다. 지운 체크포인트는 휴지통으로 가서 비울 때까지 용량을 차지합니다. 공간이 모자라면 복사만 실패하고 이전 체크포인트는 남습니다.

정규화 통계는 노트북에서 계산해 `assets/`에 넣어 두었습니다. 데이터나 행동 정의가 바뀌면 다시 계산합니다.

```bash
cd ~/airlab_vla/openpi
.venv/bin/python /mnt/c/Claude-project/AIRLAB/pi05/run_openpi.py scripts/compute_norm_stats.py --config-name pi05_airlab
```

노트북에서 openpi를 설치할 때는 NVIDIA 패키지와 CUDA용 torch를 뺍니다. GPU 없이 코드를 시험하는 용도입니다. MuJoCo는 `mujoco==3.12.0`으로 올려야 하고, `uv run`을 쓰면 다시 내려가므로 `.venv/bin/python`으로 직접 실행합니다.

## 3. 대시보드에서 실행 (Colab + 노트북)

이동, 상자 앞 정렬, 놓기는 작업 모드 그대로이고 집는 동작만 Colab의 π0.5가 합니다.

```text
vla_pick (노트북) ── 영상 2장, 관절각, 명령 ──▶ Cloudflare 터널 ──▶ serve_pi05.py (Colab GPU)
                  ◀── 행동 10스텝 ───────────
```

노트북의 WSL에 통신 패키지를 한 번 설치합니다.

```bash
pip3 install --user websockets msgpack
```

1. Colab에서 1번과 2번 칸을 실행합니다. 체크포인트는 Drive에서 읽으므로 3번과 4번은 필요 없습니다.
2. 7번 칸을 실행합니다. 몇 분 뒤 `대시보드에 넣을 서버 주소`가 나옵니다. 칸은 끝나지 않으며, 켜 둔 동안 정책을 제공합니다.
3. 대시보드에서 모드를 **π0.5 집기**로 고르고 서버 주소를 넣은 뒤 **연결**을 누릅니다. 서버가 응답하지 않으면 시스템을 켜지 않고 이유를 알려 줍니다.
4. 다 쓰면 7번 칸을 중지하고 런타임을 해제합니다. 켜 둔 동안 GPU 요금이 계속 나갑니다.

터미널에서는 이렇게 실행합니다.

```bash
ros2 launch airlab_manipulation bringup.launch.py planner:=true pick:=pi05 policy_server:=https://<...>.trycloudflare.com
```

**작은 정책과 다른 점**

- **멈췄다 움직입니다.** 모델이 내는 5스텝을 실행하고, 다음 답이 올 때까지 팔은 마지막 목표에 멈춰 있습니다. 답을 기다리며 움직이면 모델이 본 자세와 실제 자세가 달라지기 때문입니다. 대시보드에 서버 응답 시간이 표시됩니다.
- **더 오래 걸립니다.** 추론을 0.3초로 흉내 낸 가짜 서버로 재면 75스텝 집기에 터널 없이 약 16초, Cloudflare 터널을 거쳐 약 20초가 걸렸습니다. 실제 Colab에서는 재지 않았습니다. 이 모드의 제한 시간은 시뮬레이션 시간 60초입니다.
- **카메라 설정이 다릅니다.** 손목 카메라를 96 대신 224로 렌더링하고, 머리 영상은 224×126으로 줄인 뒤 위아래에 검은 띠를 붙입니다.
- **서버가 끊기면 그 집기는 실패로 끝납니다.** 15초 안에 답이 없거나 연결이 끊기면 팔은 멈추고, 계획기는 평소의 집기 실패처럼 팔을 접습니다.

**주의할 점**

- 서버 주소를 아는 사람은 누구나 이 정책을 호출할 수 있습니다. 인증이 없으니 주소를 공유하지 말고 쓰고 나면 칸을 중지하세요.
- Colab FAQ는 대화형 작업과 관련 없는 웹 서비스를 금지합니다. 본인 노트북에서 잠깐 쓰는 이 방식이 여기에 걸리는지는 명확하지 않으니, 필요할 때만 켜고 다른 사람에게 제공하지 마세요. 런타임이 예고 없이 끊길 수 있습니다.
- 빠른 터널(trycloudflare)은 계정 없이 쓰는 시험용이라 가동 보장이 없습니다.
