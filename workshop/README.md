# UNBOLT 강습회: ROS 2 + MuJoCo로 만드는 주행형 양팔로봇

**시뮬레이션 모델링부터 SLAM·Nav2 주행, MoveIt 양팔 조작, LLM 자연어 작업 계획까지 2일 완성**

> 노트북 한 대(Windows)로 따라 하는 실습형 강습회.
> WSL조차 설치되지 않은 노트북에서 시작해, 마지막에는 웹 브라우저에
> "공급 테이블로 가서 빨간 상자를 집고 작업대로 옮겨"라고 입력하면 로봇이 스스로 계획해서 수행합니다.

![최종 결과: 웹 대시보드](../docs/step7_dashboard.jpg)

---

## 이 강습회에서 만드는 것

```
  자연어 명령 ─▶ LLM 작업 계획 (Claude, 도구 호출)
                     │ navigate_to / pick_object / place_object
                     ▼
  ┌──────────── 로봇 스킬 (Python) ────────────┐
  │ Nav2 주행   ArUco 정밀 접근   MoveIt 2 양팔 │
  └─────┬──────────────┬───────────────┬────────┘
        │ /cmd_vel     │ /camera       │ FollowJointTrajectory
        ▼              ▼               ▼
  ┌──────── MuJoCo ↔ ROS 2 브리지 (직접 작성) ────────┐
  │ /clock /joint_states /odom /scan /tf /camera      │
  └─────────────────── MuJoCo 물리 엔진 ──────────────┘
```

| 모듈 | 핵심 기술 | 끝나면 할 수 있는 것 |
|---|---|---|
| 1. 시뮬레이터와 브리지 | MuJoCo, MJCF/URDF, TF, LiDAR 레이캐스트, 오도메트리 | 직접 만든 브리지로 로봇을 키보드로 몰고 RViz에서 센서를 본다 |
| 2. SLAM과 자율주행 | slam_toolbox, Nav2 (AMCL, costmap, planner/controller) | 방 지도를 만들고 목표점을 찍어 자율주행한다 |
| 3. 양팔 조작과 Pick & Place | MoveIt 2, IK, Cartesian path, ArUco, planning scene | 카메라로 상자를 찾아 집어서 다른 테이블에 놓는다 |
| 4. LLM 작업 계획 | Claude 도구 호출, strict schema, 작업 관리자, 웹 대시보드 | 자연어 한 문장으로 주행+조작 전체를 시킨다 |

## 대상과 선수 지식

- 로봇공학·AI·컴퓨터공학 전공 학부 3~4학년, 대학원 신입생
- **필요**: 리눅스 터미널 기본 명령(`cd`, `ls`, 파일 편집), Python 기초
- **있으면 좋음**: ROS 2 기본 개념(노드, 토픽, 메시지). 처음이라면 [사전 학습 자료](#사전-학습-권장)를 1~2시간 보고 오세요.
- 로봇 실물, GPU, Docker, 가상머신 **필요 없음**

## 시간표

| 일차 | 시간 | 모듈 | 자료 |
|---|---|---|---|
| 사전 | 집에서 1~2시간 | **설치** (WSL → Ubuntu → ROS 2 → 실습 코드) | [00_install.md](00_install.md) |
| 1일차 | 08:30–09:30 | 설치 헬프데스크 (사전 설치를 못 끝낸 사람) | [troubleshooting.md](troubleshooting.md) |
|  | 09:30–11:30 | **모듈 1** MuJoCo + ROS 2 브리지, 주행형 양팔로봇 모델링 | [01_mujoco_ros2_bridge.md](01_mujoco_ros2_bridge.md) |
|  | 11:30–12:30 | 점심 | |
|  | 12:30–16:30 | **모듈 2** SLAM Toolbox + Nav2 실내 자율주행, 전반부 통합 데모 | [02_slam_nav2.md](02_slam_nav2.md) |
| 2일차 | 09:30–11:30 | **모듈 3** MoveIt 2 양팔 제어, 마커 기반 모바일 매니퓰레이션 | [03_moveit_pick_place.md](03_moveit_pick_place.md) |
|  | 11:30–12:30 | 점심 | |
|  | 12:30–16:30 | **모듈 4** LLM 작업 계획, 웹 대시보드, **최종 미션** | [04_llm_dashboard.md](04_llm_dashboard.md) |

각 모듈은 **개념 설명(20~30%) → 따라 하기(50%) → 과제(20~30%)** 순서이고,
중간중간 ✅ **체크포인트**가 있습니다. 체크포인트를 통과하면 다음으로 넘어가세요.
막히면 손을 들거나 [문제 해결 문서](troubleshooting.md)를 먼저 찾아보세요.

## 준비물

| 항목 | 최소 | 권장 |
|---|---|---|
| 운영체제 | Windows 10 21H2 (빌드 19044) 이상 | **Windows 11** |
| CPU | 4코어 | 8스레드 이상 |
| RAM | 8 GB | **16 GB** |
| 디스크 | C: 여유 30 GB | 50 GB |
| 그래픽 | 내장 그래픽 가능 (Intel Iris Xe / Arc, AMD Radeon) | 최신 그래픽 드라이버 |
| 네트워크 | 설치 때 약 4 GB 다운로드 | **집에서 미리 설치** |
| 계정 | GitHub 계정 (선택) | Anthropic Console 계정 + API 키 (모듈 4, 5달러 이내) |

- **macOS / Linux 노트북**: Ubuntu 22.04 노트북이면 [설치 가이드](00_install.md)의 3단계부터 그대로 됩니다.
  macOS(Apple Silicon)는 공식 지원하지 않으니 강사에게 미리 문의하세요.
- API 키가 없어도 모듈 4의 로봇 쪽은 `llm:=scripted`(정해진 순서를 재생하는 대역)로 실습할 수 있습니다.

## 소프트웨어 구성

| 구성 | 버전 | 비고 |
|---|---|---|
| WSL2 + WSLg | 2.x | 리눅스 GUI 창(MuJoCo, RViz)이 Windows 바탕화면에 뜬다 |
| Ubuntu | 22.04 LTS | |
| ROS 2 | Humble | Nav2, slam_toolbox, MoveIt 2, rosbridge |
| MuJoCo | 3.12.0 (Python) | pip, `~/.local` |
| 로봇 모델 | OpenArm v2 (Enactic, Apache-2.0) | 양팔 7자유도 × 2 + 그리퍼 |
| LLM | Claude (`claude-opus-5-5`), anthropic SDK 2.3.0 | 모듈 4 |

## 자료 목록

| 파일 | 내용 |
|---|---|
| [00_install.md](00_install.md) | 설치 가이드: WSL이 없는 노트북에서 실습 준비 완료까지 |
| [01_mujoco_ros2_bridge.md](01_mujoco_ros2_bridge.md) | 모듈 1 실습 교재 |
| [02_slam_nav2.md](02_slam_nav2.md) | 모듈 2 실습 교재 |
| [03_moveit_pick_place.md](03_moveit_pick_place.md) | 모듈 3 실습 교재 |
| [04_llm_dashboard.md](04_llm_dashboard.md) | 모듈 4 실습 교재 + 최종 미션 |
| [troubleshooting.md](troubleshooting.md) | 증상별 문제 해결 |
| [instructor_guide.md](instructor_guide.md) | 강사·조교용 운영 가이드 (사전 공지, 점검표, 시간 배분) |
| [slides/UNBOLT_workshop.pptx](slides/UNBOLT_workshop.pptx) | 강의 슬라이드 128장: 모듈마다 비유·용어·따라 하기(성공 화면/안 되면)·요약·셀프 체크 퀴즈·과제, 부록(오류 TOP 8, 명령 모음). 슬라이드마다 발표자 노트(퀴즈 정답 포함). 생성 코드는 [slides/src](slides/src/README.md) |
| `setup/check_windows.ps1` | Windows 사전 점검 (+ WSL 설치) |
| `setup/install_unbolt.sh` | Ubuntu 안에서 ROS 2부터 빌드까지 한 번에 |
| `setup/check_env.sh` | 설치 결과 점검 (✔/!/✘) |
| `setup/setup_api_key.sh` | Claude API 키 저장 + 연결 확인 |

## 사전 학습 (권장)

ROS 2가 처음이라면 강습회 전에 아래 공식 튜토리얼 중 앞의 네 개만 해 보세요 (설치 후 1~2시간).

- ROS 2 Humble 튜토리얼 – Beginner: CLI tools
  (`Configuring environment`, `Using turtlesim`, `Understanding nodes`, `Understanding topics`)
  <https://docs.ros.org/en/humble/Tutorials/Beginner-CLI-Tools.html>
- MuJoCo 문서 – Overview, XML Reference 훑어보기 <https://mujoco.readthedocs.io/>

## 수료 기준

- 모듈 1~4의 ✅ 체크포인트 통과
- 최종 미션 성공 (자연어 명령으로 빨간 상자를 공급 테이블 → 작업대로 옮기기)
- 과제 중 1개 이상 제출 (기본 과제 또는 도전 과제)
