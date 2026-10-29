# AIRLAB — ROS 2 + MuJoCo 주행형 양팔로봇

PinkLAB 영상(ROS 2 + MuJoCo 양팔로봇)을 참고해 오픈소스로 재구성하는 프로젝트.

> **강습회 자료**: [workshop/](workshop/README.md) — 2일 과정 실습 교재, WSL이 없는 Windows 노트북부터 시작하는
> [설치 가이드](workshop/00_install.md)와 일괄 설치 스크립트(`workshop/setup/install_airlab.sh`).

- 환경: WSL2 Ubuntu 22.04, ROS 2 Humble, MuJoCo 3.12 (Python)
- 로봇: 차동구동 베이스 + 기둥 + [OpenArm v2](https://github.com/enactic/openarm_mujoco) 양팔 (7DoF x 2 + 그리퍼)

## 폴더 구조

```
models/
  airlab_robot.xml   로봇 (차동구동 베이스 + OpenArm 받침대 + 양팔 attach)
  scene.xml          월드 (10x8.5 m 방, 칸막이벽, 장애물, 공급 테이블 3개, 작업대, 빨강·초록·파랑 상자, 마커 1-3/7-9/11-32)
third_party/
  openarm_mujoco/        OpenArm 공식 MJCF (git clone)
  openarm_description/   OpenArm 공식 URDF/xacro (git clone, ros2_ws/src에 심볼릭 링크)
ros2_ws/src/
  airlab_mujoco_bridge/
    mujoco_bridge_node.py   MuJoCo <-> ROS 2 브리지 (+ 2D LiDAR)
    arm_demo.py             팔/그리퍼 동작 확인용 데모
    launch/bridge.launch.py 시뮬레이터만
    launch/sim.launch.py    시뮬레이터 + robot_state_publisher + RViz
  airlab_navigation/
    config/slam_toolbox.yaml     slam_toolbox (online async) 설정
    config/nav2_params.yaml      Nav2 (Humble 공식 파일 기반, RPP 컨트롤러, 직사각형 footprint)
    maps/airlab_room.yaml/.pgm   SLAM으로 만든 지도
    scripts/explore_waypoints.py 지도 작성용 자동 탐색 (ground truth 기반 웨이포인트 주행)
    scripts/nav_goal_test.py     Nav2 목표 3개 연속 주행 + 실제 위치 오차 측정
    scripts/frontier_explorer.py 프론티어 기반 능동 탐색 (SLAM 지도만 사용, Nav2로 주행, 끝나면 ~/maps에 저장)
    launch/slam.launch.py, navigation.launch.py
    launch/explore.launch.py     시뮬레이터 + slam_toolbox + Nav2(지도 없이) + frontier_explorer
  airlab_moveit_config/
    config/airlab.srdf.base      그룹(left_arm/right_arm/both_arms/그리퍼), 자세(home/ready/open/closed)
    config/airlab.srdf           = base + 자기충돌 행렬 (scripts/generate_srdf.sh로 생성)
    config/kinematics.yaml, joint_limits.yaml, moveit_controllers.yaml, moveit.rviz
    scripts/generate_collision_matrix.py  MuJoCo로 자기충돌 행렬 계산
    scripts/moveit_test.py       계획+실행 6개 동작 자동 테스트
    launch/moveit.launch.py
  airlab_manipulation/
    aruco_detector.py            카메라 영상 -> ArUco(DICT_4X4_50) -> TF aruco_<id>
    skills.py                    navigate / servo_to_marker / pick / place 스킬
    pick_place_demo.py           빨간 상자를 1번 공급 테이블 -> 작업대 가운데 자리로 옮기는 데모
    task_planner_core.py         Claude 도구 호출 루프 + 스킬을 감싼 도구 + 장소/물체 지식
    task_planner.py, ask.py      ROS 노드(/task_command -> /task_status), 명령 CLI
    launch/bringup.launch.py     sim + Nav2 + move_group + 마커 검출 한 번에
  airlab_dashboard/
    web/index.html               대시보드 (외부 라이브러리 없음, rosbridge v2 프로토콜 직접 구현)
    dashboard_server.py          웹 서버(:8080) + 지도 PNG/config + /dashboard/robot_pose(TF map->base)
    launcher.py                  dashboard_launcher: ROS가 꺼져 있어도 페이지를 띄우고 작업/VLA 집기/지도 만들기 모드를 켜고 끔
    launch/dashboard.launch.py   rosbridge_websocket(:9090) + 웹 서버
    launch/mapping.launch.py     explore.launch.py + 대시보드 (지도 만들기 모드)
  airlab_vla/                    VLA 집기 정책 (ROS 없이 학습·평가, PyTorch CPU)
    sim.py                       집기 전용 MuJoCo 장면 (테이블 앞 로봇, 상자 위치·각도 무작위)
    expert.py                    스크립트 전문가: MuJoCo IK로 집기 시연 (MoveIt 대신)
    record.py, train.py          시연 녹화 → 정책 학습 (~/airlab_vla/demos, ~/airlab_vla/policy.pt)
    model.py, runner.py          정책 (카메라 2대 + 명령 문장 + 관절 → 관절 목표 10개 묶음), 실행기
    evaluate.py                  처음 보는 배치에서 정책과 전문가의 성공률 비교
    vla_pick_node.py             ROS 노드: /vla/pick 명령 → /joint_commands 10 Hz → /vla/result
  airlab_description/
    urdf/airlab.urdf.xacro      베이스 + OpenArm xacro 매크로 (MJCF와 동일 기구학)
    config/openarm_preset.yaml  OpenArm preset (root를 베이스 위 openarm_body_mount로)
    rviz/airlab.rviz
    launch/rsp.launch.py, display.launch.py
```

로봇 모델은 MJCF(`models/airlab_robot.xml`)와 URDF(`airlab.urdf.xacro`) 두 벌이다.
치수를 바꿀 때는 양쪽을 같이 고쳐야 한다 (주요 값: 바퀴 반지름 0.08, 바퀴 간격 0.45,
받침대 장착 위치 base_link 기준 (-0.05, 0, 0.11), LiDAR (0.22, 0, 0.13)).

## 빌드

받기 (WSL Ubuntu 22.04 안에서):

```bash
git clone https://github.com/sejiny3/AIRLAB.git ~/airlab
```

처음 설치는 `bash ~/airlab/workshop/setup/install_airlab.sh` (ROS 2, 의존 패키지, OpenArm 모델, 빌드, `~/.bashrc`까지).
강습회 교재는 [workshop/README.md](workshop/README.md)에서 시작합니다.
코드를 고친 뒤 다시 빌드할 때:

```bash
source /opt/ros/humble/setup.bash
cd ~/airlab/ros2_ws
colcon build --symlink-install
source install/local_setup.bash
```

시뮬레이터는 월드 파일을 `$AIRLAB_ROOT/models/scene.xml`에서 찾는다. `AIRLAB_ROOT`가 없으면
`--symlink-install` 링크를 따라 저장소 위치를 알아낸다.

## 실행

```bash
ros2 launch airlab_mujoco_bridge sim.launch.py               # MuJoCo 뷰어 + RViz (권장)
ros2 launch airlab_mujoco_bridge sim.launch.py use_viewer:=false rviz:=false
ros2 launch airlab_mujoco_bridge bridge.launch.py            # 시뮬레이터만
ros2 launch airlab_description display.launch.py             # 시뮬레이터 없이 URDF만 (관절 슬라이더)
```

![RViz](docs/step2_rviz.jpg)

### SLAM과 Navigation (3단계)

`slam_toolbox`와 Nav2가 필요하다:

```bash
sudo apt-get install -y ros-humble-slam-toolbox ros-humble-navigation2 ros-humble-nav2-bringup
```

지도 만들기:

```bash
ros2 launch airlab_navigation slam.launch.py
# 다른 터미널: 키보드로 돌아다니거나 자동 탐색 (약 3분)
ros2 run airlab_navigation explore_waypoints.py --ros-args -p use_sim_time:=true
# 지도 저장 (src 쪽에 저장한 뒤 colcon build 다시)
ros2 run nav2_map_server map_saver_cli -f $AIRLAB_ROOT/ros2_ws/src/airlab_navigation/maps/airlab_room --ros-args -p use_sim_time:=true
```

실제 위치를 쓰지 않는 자동 탐색 (프론티어 탐색, 끝나면 `~/maps/airlab_explored_<날짜>_<시간>.yaml`로 저장):

```bash
ros2 launch airlab_navigation explore.launch.py
ros2 topic echo /explore/status --field data       # 상태 JSON
ros2 launch airlab_navigation navigation.launch.py map:=$HOME/maps/airlab_explored_<...>.yaml
```

저장된 지도로 주행 (RViz의 "2D Goal Pose"로 목표 지정):

```bash
ros2 launch airlab_navigation navigation.launch.py
ros2 run airlab_navigation nav_goal_test.py --ros-args -p use_sim_time:=true   # 자동 테스트
```

![Nav2](docs/step3_nav_rviz.jpg)

### MoveIt 2 양팔 제어 (4단계)

```bash
sudo apt-get install -y ros-humble-moveit ros-humble-moveit-configs-utils ros-humble-control-msgs
```

```bash
ros2 launch airlab_moveit_config moveit.launch.py      # MuJoCo + move_group + RViz MotionPlanning
ros2 run airlab_moveit_config moveit_test.py --ros-args -p use_sim_time:=true   # 자동 테스트
```

- MoveIt은 브리지의 `FollowJointTrajectory` 액션 서버 4개(`left_arm_controller`,
  `right_arm_controller`, `left_gripper_controller`, `right_gripper_controller`)로 궤적을 실행한다.
  ros2_control은 쓰지 않는다.
- 팔은 MuJoCo 액추에이터 중력 보상(`gravcomp` + `actuatorgravcomp`)을 켜서 처짐 없이 목표 각도에 도달한다
  (브리지 파라미터 `arm_gravity_compensation`).
- 끝점(tip)은 손가락 끝의 `openarm_{left,right}_grasp_frame`.
- 그리퍼: `finger_joint1` 0 = 닫힘(끝 간격 3.6 cm), 왼쪽 +0.6 / 오른쪽 −0.6 = 열림(11.5 cm).
- URDF나 SRDF 그룹을 바꾸면 자기충돌 행렬을 다시 만든다:
  `bash src/airlab_moveit_config/scripts/generate_srdf.sh` 후 `colcon build`.
  (MoveIt Setup Assistant의 `collisions_updater`는 이 로봇에서 멈춰서 MuJoCo로 계산한다.)

![MoveIt](docs/step4_moveit_rviz.jpg)

### 마커 기반 Pick & Place (5단계)

```bash
ros2 launch airlab_manipulation bringup.launch.py
ros2 run airlab_manipulation pick_place_demo --ros-args -p use_sim_time:=true
```

흐름: 팔 `tuck` → Nav2로 1번 공급 테이블 앞 → 마커 7(상자 윗면)로 정밀 접근 → 집기 → 후진 →
Nav2로 작업대 앞 → 마커 2(가운데 놓을 자리)로 정밀 접근 → 놓기 → 후진.

- 월드: 공급 테이블 3개(빨강·초록·파랑 상자가 하나씩, 자리 2칸: 마커 N1·N2)와 작업대(자리 3칸: 마커 1·2·3), 모두 상판 높이 0.65 m. 앞다리는 가장자리에서 약 20 cm 안쪽이라 끝자리에 비껴 서도 차체가 닿지 않는다.
  OpenArm은 팔이 아래로 늘어진 구조라 전방 파지 도달 범위가 base 기준 x 0.30~0.45 m뿐이어서,
  섀시(높이 0.19 m)가 상판 아래로 들어가는 높이로 정했다.
- 카메라: 받침대 위 헤드 카메라(1280×720, 5 Hz, 47° 하향). 마커 텍스처는 `models/make_markers.py`로 생성.
- 정밀 접근(`servo_to_marker`): 차동구동으로 마커까지의 거리와 방위각을 맞춰 base 기준 목표 위치
  (오른팔 (0.38, −0.15), 왼팔 (0.38, 0.15))에 1 cm 이내로 세운다. 가까이서 마커가 손/상자에 가려지면
  마지막으로 본 위치를 odom 좌표로 기억해 두었다가 오도메트리로 이어서 쓴다.
- 파지: 접근축 15° 하향, 손가락은 base y로 집는다(상자 yaw에 맞춰 ±45° 회전). MoveIt 계획 시 테이블 상판을
  충돌 물체로 넣는다. 운반·접근 중에는 손이 상판과 카메라 시야를 피하도록 팔을 `tuck` 자세로 둔다.

![Pick & Place](docs/step5_pick_place.jpg)

### LLM 작업 계획 (6단계)

자연어 명령 → Claude(`claude-opus-5-5`)가 계획 → 로봇 스킬을 도구로 하나씩 호출 → 결과를 보고 다음 단계 결정.

준비 (WSL, sudo 불필요):

```bash
pip3 install --user anthropic Brotli          # install_airlab.sh가 이미 설치함
bash workshop/setup/setup_api_key.sh          # 키를 ~/.airlab_key 에 저장 (~/.bashrc가 읽음), 연결 확인
```

비대화형 셸(스크립트, `bash -c`)에서는 `~/.bashrc`가 앞부분에서 빠져나가므로 `source ~/.airlab_key`를 직접 하거나
`~/.profile`에 키를 넣는다.

`Brotli`를 함께 올려야 한다: Ubuntu 22.04 기본 `python3-brotli` 1.0.9는 SDK의 HTTP 라이브러리(httpx2)와 맞지 않아
모든 요청이 `APIConnectionError`(원인: `process() takes no keyword arguments`)로 끝난다.

실행:

```bash
ros2 launch airlab_manipulation bringup.launch.py planner:=true
ros2 run airlab_manipulation ask "빨간 상자를 작업대로 옮겨줘"
ros2 run airlab_manipulation ask "초록 상자를 먼저 작업대 왼쪽에 놓고, 그다음 파란 상자를 오른쪽에 놓아줘"
ros2 run airlab_manipulation ask "작업대에 빨간 상자가 있으면 원래 자리로 돌려놓고, 없으면 그냥 원위치로 와"
```

- 도구: `get_world_state`, `navigate_to(location)`, `pick_object(object)`, `place_object(location, spot)`,
  `check_table(location)`, `set_arm_posture(posture)`, `wait(seconds)` — 모두 `strict` 스키마, 한 번에 하나씩 실행(`disable_parallel_tool_use`).
- 장소: `supply_1`~`supply_3`(자리 `right`/`left`, 마커 N1/N2), `work_table`(자리 `left`/`middle`/`right`, 마커 1/2/3), `home`.
  물체: `red_box`(마커 7), `green_box`(8), `blue_box`(9), 각각 1~3번 공급 테이블의 오른쪽 자리에서 시작.
- 자리 하나에 상자 하나. `place_object`의 `auto`는 그 상자의 처음 자리(그 테이블일 때), 아니면 첫 빈자리.
- `check_table`은 서 있는 테이블을 카메라로 보고(안 보이면 25 cm 다가가 다시) 보이는 상자의 자리를 고치고, 기억에 있는데
  안 보이는 상자는 `unknown`으로 바꾼다. 조건이 있는 명령("…이 없으면", "…이면")은 Claude가 기억 또는 이 도구로 판단한다.
- 진행 상황은 `/task_status`에 JSON 이벤트(command / tool_call / tool_result / thought / final / world)로 나온다.
- 모델이 요청을 거절하면 다른 모델로 자동 재시도하는 server-side fallback(`fallbacks: "default"`)을 켜 두었다.
- API 키 없이 로봇 쪽만 시험: `planner:=true llm:=scripted` (명령의 키워드로 정해진 순서를 재생하는 대역, 계획은 하지 않음).

실제 Claude 시험 (10 × 8.5 m 방, 연속 6개 명령, 한 번의 실행, 합계 약 $0.50):

| 명령 | Claude의 계획 | 결과 |
|---|---|---|
| 초록 상자를 먼저 작업대 왼쪽에 놓고, 그다음 파란 상자를 오른쪽에 놓아줘 | 상태 → 2번 → 집기 → 작업대 → 놓기(left) → 3번 → 집기 → 작업대 → 놓기(right) | 성공, 195 s |
| 작업대에 빨간 상자가 없으면 가져다 놔 | 상태(기억: 없음) → 1번 → 집기 → 작업대 → 놓기(auto → middle) | 성공, 99 s, 판단 근거("로봇 기억으로는")를 답에 밝힘 |
| 작업대에 뭐가 있는지 가서 확인해 줘 | (이미 작업대 앞) → check_table | 왼쪽 초록 · 가운데 빨강 · 오른쪽 파랑, 10 s |
| 작업대에 빨간 상자가 있으면 원래 자리로 돌려놓고, 없으면 그냥 원위치로 와 | 상태(있음) → 집기 → 1번 → 놓기(auto → 처음 자리) | 성공, 72 s, 원위치로는 가지 않음 |
| 노란 공 좀 가져다 줄래? | (도구 호출 없음) 모르는 물건이라 불가, 가능한 일 안내 | 3 s |
| 상자를 모두 원래 자리에 돌려놓고 원위치로 와 | 상태 → 초록·파랑을 처음 자리로 (빨강은 이미 제자리) → 원위치 | 성공, 208 s, 세 상자 모두 처음 자리에서 1.2 cm 이내 |

대역(`llm:=scripted`)으로 "상자를 모두 작업대에 모아" → "가서 확인해" → "모두 제자리로"를 돌리면 집기·놓기 12번이 모두 성공한다
(왼쪽 자리의 상자는 왼팔로, 나머지는 오른팔로).

실패한 시도에서도 Claude는 도구 결과를 읽고 한 번 재시도한 뒤, 상자를 들고 있는 현재 상태를 정확히 보고했다.

### 웹 대시보드 (7단계)

```bash
ros2 launch airlab_manipulation bringup.launch.py planner:=true dashboard:=true
# 브라우저(Windows에서도 가능): http://localhost:8080/
```

- 지도: SLAM 지도 위에 로봇(외곽선·방향), LiDAR 점, Nav2 경로, 테이블과 놓는 자리, 상자 세 개(시뮬레이터 실제 위치).
- 헤드 카메라: 마커 검출 결과가 그려진 영상(`/aruco/debug_image/compressed`, JPEG).
- 명령: 자연어 입력, 자주 쓰는 명령 버튼, 작업 취소(`/task_cancel` — 주행·정밀 접근은 즉시 멈추고,
  진행 중인 팔 동작은 마친 뒤 다음 단계를 시작하지 않는다).
- 연결(시스템 시작): `ros2 run airlab_dashboard dashboard_launcher`를 켜 두면 ROS가 꺼져 있어도 http://localhost:8080 이
  열리고 "ROS가 꺼져 있습니다" 화면의 **연결** 버튼(LLM Claude/대역, MuJoCo 창, RViz 선택)으로 bringup 전체를 켠다.
  런처가 페이지와 시작/종료 API(`/api/stack`)를 맡고, launch 안의 dashboard_server는 8080이 차 있으면 ROS 쪽 일만 한다.
  시작·종료 요청은 이 컴퓨터에서만 받는다(`--allow-remote`로 해제). 터미널에서 켠 스택이 있거나 이전 스택이 아직 꺼지는 중이면
  시작을 거절한다. 런처의 Ctrl+C는 자기가 켠 스택도 함께 끈다. 로그: `~/.ros/airlab_launcher.log`
  모드는 둘: **작업**(bringup, 지도는 기본 지도 또는 `~/maps`의 저장 지도 중 선택 → `bringup.launch.py map:=...`)과
  **지도 만들기**(`airlab_dashboard mapping.launch.py`).
- 지도 만들기 모드: 빈 지도에서 slam_toolbox + Nav2(map_server/AMCL 없이) + `frontier_explorer.py`가 프론티어
  (아는 빈 칸과 미지의 경계)를 따라 스스로 탐색하고, 갈 수 있는 프론티어가 없으면 지도를
  `~/maps/airlab_explored_<날짜>_<시간>.yaml`로 저장한다. 페이지는 `/map`을 실시간으로 그리고(프론티어는 하늘색,
  탐색 목표는 파란 원), 탐색 시작/멈춤/지도 저장(`/explore/control`)과 상태(`/explore/status`)를 보여 준다.
  탐색이 끝나거나 멈추면(작업 모드에서는 작업이 없을 때) **키보드 조종**(W A S D/방향키, 누르는 동안만 `/cmd_vel` 10 Hz, LiDAR로 앞뒤 장애물이 가까우면
  그 방향은 막음)을 쓸 수 있고, 그동안에도 SLAM이 지도를 고친다. 작업 모드에서 몰면 페이지가 `/task_manual_drive`를 보내고 플래너가
  로봇 위치를 "알 수 없음"으로 바꿔, 다음 명령은 주행부터 한다(엉뚱한 자리에서 집거나 놓지 않게). 터미널만으로는 `ros2 launch airlab_navigation explore.launch.py`.
  탐색 모드의 Nav2 설정은 작업 모드와 다르다(`explore.launch.py`의 `_nav2()`, 작업 모드는 테이블에 붙어야 해서 그대로):
  로봇을 직사각형 대신 반지름 0.44 m 원으로 보고(제자리 회전 때 모서리가 쓸고 지나가는 0.40 m + 여유), footprint clearing을 끄고,
  전역 costmap은 지도 크기를 따라가지 않는 20 × 20 m 이동 창이며, LiDAR는 720개 광선, 회전 0.5 rad/s·직진 0.25 m/s로 천천히 간다.
  처음에는 MuJoCo 창을 켠 실행의 절반 정도에서 방이 비스듬히 두 번 그려졌다. 추적해 보니 로봇이 공급 테이블 다리에 걸려 바퀴만
  헛돌았고(오도메트리가 수십 도 틀어짐), 오도메트리에서 출발해 스캔을 맞추는 slam_toolbox가 틀린 각도로 지도를 이었다. 다리에
  부딪힌 근본 원인은 시뮬레이터의 LiDAR: 브리지가 쓰던 `mj_multiRay`(MuJoCo 3.12)가 테이블 다리 두 개를 방 대부분에서 건너뛰었다
  (같은 방향의 `mj_ray`는 맞힘). 브리지는 이제 광선마다 `mj_ray`를 쓴다(360개에 약 1 ms). 위 탐색 설정은 가는 장애물을 한 번 보면
  놓치지 않게 하는 나머지 조치다. 고친 뒤 MuJoCo 창을 켠 채 6번 연속: 6번 모두 159~220초에 방 전체(41.4~41.8 m²) 완료,
  SLAM 위치 오차 3 cm·1° 이하, 실제 자세를 MuJoCo 충돌 검사로 다시 돌려 봐도 접촉 0.
- 시스템 종료(헤더 오른쪽, 두 번 눌러 확인): `/dashboard/shutdown` → dashboard_server가 정상 종료(코드 0)하면
  `dashboard.launch.py`가 launch 전체를 끈다(시뮬레이터, Nav2, MoveIt, 플래너, RViz). 서버가 비정상 종료(크래시)하면 끄지 않는다.
  페이지는 "종료했습니다"와 다시 시작 명령을 보여 주고, 다시 켜면 저절로 다시 연결된다.
- 초기화(`/task_reset`, 두 번 눌러 확인): 진행 중인 작업을 취소하고 → 시뮬레이터 리셋(로봇·팔·상자 세 개를
  처음 위치로) → AMCL을 원점으로 다시 맞추고 costmap 비움 → 플래너의 상태(위치·들고 있는 것·마커 기억)도 처음으로.
- 작업 진행: Claude가 호출한 단계마다 상태·걸린 시간·결과, Claude의 응답.
- 로봇 상태: 작업 기준 위치, 들고 있는 물체, 지도 위치, 속도, 양손 그리퍼 열림, 시뮬레이션 시간.
- 페이지를 새로 열면 `/task_world`로 현재 상태를 다시 받아 온다.

![Dashboard](docs/step7_dashboard.jpg)

대시보드에서 확인한 것: 명령 보내기 → 5단계 완료(76~80 s), 원래 자리로 되돌리기(4단계 완료),
주행 중·정밀 접근 중 취소, 페이지 새로 고침 후 상태 복원, 휴대폰 폭(375 px) 한 열 배치,
초기화(대기 중 2 s / 상자를 들고 주행 중 3 s → 같은 명령 다시 성공, 패드 중심에서 0.5 cm),
시스템 종료(누른 뒤 1.8 s에 페이지가 "종료했습니다", 모든 프로세스 종료, 다시 켜면 페이지 자동 재연결),
연결(런처로 시작 → 13 s에 rosbridge 연결, 25 s에 플래너 준비, 시작 3/6/10 s에 취소해도 남는 프로세스 0개).

다른 터미널에서:

```bash
# 키보드로 주행 (i/j/l/, 등)
ros2 run teleop_twist_keyboard teleop_twist_keyboard

# 팔/그리퍼 데모 (10초)
ros2 run airlab_mujoco_bridge arm_demo --ros-args -p use_sim_time:=true

# 관절 하나 직접 명령
ros2 topic pub --once /joint_commands sensor_msgs/msg/JointState \
  "{name: [openarm_left_joint1], position: [-0.8]}"

# 월드 리셋 (task_planner가 켜져 있으면: AMCL·플래너 상태까지 함께, 대시보드 초기화 버튼과 같음)
ros2 topic pub --once /task_reset std_msgs/msg/Empty
# 시뮬레이터만 리셋 (planner 없이 실행할 때. 로봇을 움직인 뒤라면 RViz 2D Pose Estimate로 원점을 다시 알려 줄 것)
ros2 service call /mujoco_bridge/reset std_srvs/srv/Trigger
```

브리지 리셋은 시뮬레이션 시간을 0으로 되돌리지 않는다. `/clock`이 뒤로 가면 모든 노드가 TF 버퍼를 비워
Nav2·AMCL·MoveIt이 상태를 잃기 때문이다.

### VLA 집기 (심화)

집기 한 단계만 학습된 정책으로 바꾼다. 계획(LLM)·주행(Nav2)·상자 앞 정렬(ArUco)·놓기(MoveIt)는 그대로다.
정책은 머리 카메라(128×72)·오른손 손목 카메라(96×96)·명령 문장·오른팔 관절각을 보고 0.1초마다 앞으로 1초(10단계)의
관절 목표를 낸다 (합성곱 + 공간 소프트맥스 + MLP, 60만 매개변수, CPU 추론 4 ms). PyTorch(CPU판)가 필요하다.

```bash
ros2 run airlab_vla record --episodes 1200  # MuJoCo만으로 스크립트 전문가 시연 녹화 (~40분, ~/airlab_vla/demos)
ros2 run airlab_vla train                   # CPU 학습 (20000단계 ~65분, ~/airlab_vla/policy.pt)
ros2 run airlab_vla evaluate --episodes 100 # 처음 보는 배치에서 정책 vs 전문가
ros2 run airlab_vla evaluate --ask-other --episodes 20   # 언어 확인: 옆 상자의 색을 말하면?
ros2 launch airlab_manipulation bringup.launch.py planner:=true dashboard:=true pick:=vla
```

- 전문가(`expert.py`)는 시뮬레이터가 아는 상자의 실제 위치로 감쇠 최소제곱 IK를 풀어 `pick()`과 같은 경유점(벌리며 다가가기 →
  15° 비스듬히 밀어 넣기 → 쥐기 → 들기)을 따라간다. 테이블 넷 · 자리 · 상자 색 셋, 상자 위치·방향, 로봇 정렬 오차를 시연마다 무작위로 하고
  (절반은 옆자리에 다른 색 상자),
  절반은 실행 목표에 천천히 변하는 잡음을 더한다(DART, 정답은 전문가 목표 그대로).
- `pick:=vla`: 브리지 헤드 카메라 10 Hz + 손목 카메라 `/wrist_camera/image_raw` 켜기, `vla_pick` 노드 시작,
  플래너 `pick_mode:=vla`(오른팔 기준으로 정렬한 뒤 `/vla/pick`에 문장을 보내고 `/vla/result`를 기다림).
  `vla_pick`은 정책이 "끝"이라고 해도 손을 닫으라고 명령했고 손가락이 물체에 걸려 덜 닫혔을 때만 성공으로 보고한다.
- 대시보드 런처의 **VLA 집기** 모드가 같은 것을 켠다(`~/airlab_vla/policy.pt`가 없으면 시작을 거절). 카드에 정책이 받는 머리(128×72, `/vla/head_input`)·손목 영상과 "끝" 확률. ArUco는 VLA 모드에서도 정렬·놓기·확인에 쓰고, 정책은 마커 좌표를 받지 않는다.
- 결과(10 × 8.5 m 방, 시연 1155개, 20000단계, CPU 약 65분, 검증 L1 0.0385): 처음 보는 배치 100개에서 정책 100/100
  (네 테이블 모두 100%, 옆에 다른 색 상자가 있던 43번 포함, 다른 상자를 든 적 없음), 전문가 100/100.
  그러나 `evaluate --ask-other`(정렬한 상자가 아닌 옆 상자의 색을 말함)에서는 20/20 정렬한 상자를 집었다. 정책은 색 낱말이 아니라
  "오른손 앞에 정렬된 상자"를 단서로 배웠다(shortcut learning). 작업 관리자가 집을 상자의 마커로 정렬하므로 실제 작업은 맞게 된다.
  ROS 전체에서 "상자를 모두 작업대에 모아" → "모두 제자리로"로 정책 집기 6/6 성공(74~88단계).
  방을 넓히기 전(테이블 둘) 실험: 공급 테이블 시연 297개만으로 학습한 정책은 공급 48/50, 작업대 0/20(2초 만에 "끝")이었다.

## 브리지 인터페이스

| 방향 | 토픽 | 타입 | 비고 |
|---|---|---|---|
| pub | `/clock` | rosgraph_msgs/Clock | 250 Hz, 시뮬레이션 시간 |
| pub | `/joint_states` | sensor_msgs/JointState | 100 Hz, 팔·그리퍼·바퀴 20개 관절 |
| pub | `/odom` + TF `odom→base_footprint` | nav_msgs/Odometry | 50 Hz, 바퀴 엔코더 적분 |
| pub | `/ground_truth/odom` | nav_msgs/Odometry | 50 Hz, 시뮬레이터 실제 위치 (`world` 프레임) |
| pub | `/imu` | sensor_msgs/Imu | 50 Hz |
| pub | `/scan` | sensor_msgs/LaserScan | 10 Hz, 360빔, 0.12~12 m, 노이즈 σ=1 cm, `lidar_link` 프레임 |
| pub | `/robot_description`, `/tf` | (robot_state_publisher) | URDF 30개 링크 TF |
| sub | `/cmd_vel` | geometry_msgs/Twist | 0.5 s 동안 명령이 없으면 정지 |
| sub | `/joint_commands` | sensor_msgs/JointState | 관절 이름별 위치 목표 (16개) |
| action | `/{left,right}_{arm,gripper}_controller/follow_joint_trajectory` | control_msgs/FollowJointTrajectory | MoveIt 궤적 실행 |
| pub | `/camera/image_raw`, `/camera/camera_info` | sensor_msgs/Image, CameraInfo | 헤드 카메라 5 Hz (그림자·반사 끔, `camera_rate`) |
| pub | `/wrist_camera/image_raw` | sensor_msgs/Image | 오른손 손목 카메라 96×96, 기본은 끔 (`wrist_camera_rate`, VLA 모드는 10 Hz) |
| pub | `/ground_truth/{red,green,blue}_box` | geometry_msgs/PoseStamped | 상자 실제 위치 (평가용, 스킬은 사용 안 함) |
| srv | `/mujoco_bridge/reset` | std_srvs/Trigger | home 자세로 리셋 (시뮬레이션 시간은 계속 흐름) |

관절 이름: `openarm_{left,right}_joint1..7`, `openarm_{left,right}_finger_joint1`
(finger_joint2는 equality로 joint1을 따라감), `{left,right}_wheel_joint`.

## 진행 상황

- [x] 1단계: MuJoCo 모델 + ROS 2 브리지
- [x] 2단계: URDF/TF, LiDAR, RViz
- [x] 3단계: SLAM + Nav2
- [x] 4단계: MoveIt 2 양팔 제어
- [x] 5단계: 마커 기반 Pick & Place
- [x] 6단계: LLM 작업 계획
- [x] 7단계: 웹 대시보드
- [x] 심화: VLA 집기 정책 (`airlab_vla`, 대시보드 **VLA 집기** 모드)
