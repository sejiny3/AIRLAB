# 모듈 3. MoveIt 2 양팔 제어와 마커 기반 모바일 매니퓰레이션

**2일차 09:30–11:30 (2시간)**

| 시간 | 내용 |
|---|---|
| 09:30–09:50 | 개념: MoveIt 2 구조, MoveIt ↔ MuJoCo 연결, 파지 기하 |
| 09:50–10:20 | 실습 1~2: RViz MotionPlanning, 자동 테스트 |
| 10:20–10:45 | 실습 3: Python으로 팔 움직이기 (pose goal, Cartesian path, 그리퍼) |
| 10:45–11:15 | 실습 4~5: ArUco 검출, Pick & Place 전체 흐름 |
| 11:15–11:30 | 과제 안내, 정리 |

## 학습 목표

1. MoveIt 2의 planning group, named state, planning scene, IK가 무엇인지 설명한다.
2. MoveIt이 계획한 궤적이 `FollowJointTrajectory` 액션으로 MuJoCo 액추에이터까지 가는 길을 따라간다.
3. Pose goal, Cartesian path, 그리퍼 명령을 Python에서 보낸다.
4. 카메라로 마커를 찾아 **주행 → 정밀 접근 → 집기 → 들기 → 운반 → 놓기**를 잇는 상태 기계를 읽고 바꾼다.

---

## 개념

### MoveIt 2 구조

```
 RViz MotionPlanning / Python (MoveGroup 액션, GetCartesianPath 서비스)
          ▼
   move_group ───────────────────────────────────────────────┐
   │ URDF + SRDF (그룹, 자세, 자기충돌 행렬)                   │
   │ KDL IK (kinematics.yaml), OMPL 계획기, 궤적 시간 매개화     │
   │ planning scene: 로봇 + 충돌 물체(테이블 상판 등)           │
   └──▶ moveit_simple_controller_manager ─────────────────────┘
              │ FollowJointTrajectory (left_arm / right_arm / left_gripper / right_gripper)
              ▼
   브리지의 trajectory_server: 궤적을 시간에 맞춰 보간 → MuJoCo 위치 액추에이터 목표
```

- **ros2_control을 쓰지 않습니다.** 브리지가 `FollowJointTrajectory` 액션 서버 4개를 직접 제공합니다
  (`unbolt_mujoco_bridge/trajectory_server.py`). MoveIt 입장에서는 실제 로봇 컨트롤러와 똑같이 보입니다.
- 팔은 MuJoCo의 **중력 보상**(`gravcomp`)을 켜서 위치 목표에 처짐 없이 도달합니다. 실제 로봇 팔의 중력 피드포워드와 같은 역할.

| SRDF 그룹 | 관절 | 용도 |
|---|---|---|
| `left_arm`, `right_arm` | `openarm_*_joint1..7` | 한 팔 계획, 끝점 `openarm_*_grasp_frame` (손가락 끝) |
| `both_arms` | 14개 | 두 팔 동시 (`home`, `ready`, `tuck`) |
| `left_gripper`, `right_gripper` | `openarm_*_finger_joint1` | `open` / `closed` |

### 이 로봇에서 집기가 어려운 이유와 해결

| 문제 | 해결 (`skills.py`) |
|---|---|
| OpenArm은 팔이 아래로 늘어진 구조라 앞쪽 도달 범위가 base 기준 x 0.30~0.45 m | 테이블 높이 0.65 m, 섀시가 상판 아래로 들어가게. 상자를 base 기준 `GRASP_XY` (0.38, ±0.15)에 오게 정밀 접근 |
| 테이블 상판과 손이 충돌 | 계획할 때 상판을 planning scene에 충돌 물체로 추가 (`set_support_surface`), 15° 아래로 접근, 상자 중심보다 1.5 cm 위를 집기 |
| 가까이 가면 상자가 손에 가려 마커가 안 보임 | 마지막으로 본 마커 위치를 **odom 좌표로 기억**해 두고 오도메트리로 이어서 씀 |
| 놓을 자리 높이 추정이 몇 cm 틀림 | 직선으로 내리다 막히면(3 cm 이상 내려간 뒤) 닿은 것으로 판단: **guarded move** (`lower_until_contact`) |

---

## 실습 1. RViz MotionPlanning

```bash
$ ros2 launch unbolt_moveit_config moveit.launch.py
```

![MoveIt in RViz](../docs/step4_moveit_rviz.jpg)

1. 왼쪽 **MotionPlanning → Planning** 탭 → **Planning Group: right_arm**
2. **Goal State: tuck** → **Plan** → 궤적 미리보기 → **Execute**. MuJoCo 뷰어의 팔이 똑같이 움직입니다. 다시 **home**.
3. 손끝의 interactive marker(화살표·고리)를 드래그 → **Plan & Execute**. 손이 닿지 않는 곳에서는 계획이 실패하는 것을 보세요 (IK 해 없음).
4. **Planning Group: both_arms**, **Goal State: ready** / **tuck** → 두 팔 동시 계획 (tuck은 주행할 때 쓰는 접힌 자세)
5. **right_gripper** → `open` / `closed`

✅ **체크포인트 3-1**: RViz에서 계획한 동작이 MuJoCo에서 실행된다.

## 실습 2. 자동 테스트와 궤적 흐름

같은 launch를 켜 둔 채 다른 터미널에서:

```bash
$ ros2 run unbolt_moveit_config moveit_test.py --ros-args -p use_sim_time:=true
```

6개 동작(관절 목표, 자세 목표, 그리퍼)을 계획·실행하고 목표와 실제 관절 각도 오차를 출력합니다. 실행 중에:

```bash
$ ros2 action list                       # /right_arm_controller/follow_joint_trajectory 등
$ ros2 topic echo /joint_states --field position --once
```

✅ **체크포인트 3-2**: 6/6 성공.

## 실습 3. Python으로 팔 움직이기

`RobotSkills`(`unbolt_manipulation/skills.py`)는 MoveIt 호출을 감싼 클래스입니다.
moveit.launch를 끄고, 주행·카메라까지 한 번에 켜는 bringup을 씁니다:

```bash
$ ros2 launch unbolt_manipulation bringup.launch.py
```

`~/arm_play.py`:

```python
#!/usr/bin/env python3
import math, time
import numpy as np
import rclpy
from unbolt_manipulation.skills import RobotSkills, grasp_rotation

rclpy.init()
s = RobotSkills()
s.wait_ready()

s.move_arms('home')                                  # 1. named posture (관절 목표)
s.set_gripper('right', -0.6)                         # 2. 그리퍼 열기 (오른쪽 열림 = 음수)

R = grasp_rotation(0.0)                              # 3. pose goal: 앞으로 15° 숙인 손
s.move_to_pose('right', (0.38, -0.15, 0.80), R, 'pose goal')

for dz in (-0.05, +0.05):                            # 4. Cartesian path: 손 방향 유지, 직선 5 cm 아래/위
    s.move_linear('right', (0.0, 0.0, dz), f'linear {dz:+.2f}')

s.set_gripper('right', 0.0)                          # 5. 닫기
s.move_arms('tuck')
s.shutdown(); rclpy.shutdown()
```

```bash
$ python3 ~/arm_play.py --ros-args -p use_sim_time:=true
```

- `move_to_pose`는 **목표 자세 하나**만 주고 경로는 OMPL이 찾습니다 (중간 경로가 휘어질 수 있음).
- `move_linear`는 **끝점이 직선으로** 움직이는 경로를 MoveIt의 `GetCartesianPath`로 만듭니다. 집기 직전 접근,
  들어 올리기처럼 경로 자체가 중요할 때 씁니다. 경로의 98% 이상을 만들지 못하면 실패로 처리합니다.

**해 보기**: z를 0.70, 0.60으로 낮춰 보세요. 어디서부터 실패하나요? 그 이유는? (도달 범위 / 섀시와 충돌)

✅ **체크포인트 3-3**: pose goal과 직선 이동이 모두 성공했다.

## 실습 4. 마커 검출 (ArUco)

bringup이 켜진 상태에서:

```bash
$ ros2 run rqt_image_view rqt_image_view /aruco/debug_image
```

키보드로 로봇을 공급 테이블(남쪽, 하늘색 상판) 쪽으로 돌려 보세요 (`ros2 run teleop_twist_keyboard teleop_twist_keyboard`).
빨간 상자 위의 마커 7, 테이블의 마커 5가 초록 테두리와 좌표축으로 표시됩니다.

```bash
$ ros2 run tf2_ros tf2_echo base_footprint aruco_7 --ros-args -p use_sim_time:=true
```

`aruco_detector.py`가 하는 일:

1. `cv2.aruco.detectMarkers` (DICT_4X4_50)로 마커 네 꼭짓점 찾기
2. 마커 크기(상자 3.75 cm, 놓을 자리 7.5 cm)와 `camera_info`로 `solvePnP` → 카메라 기준 위치·자세
3. TF `camera_optical_frame → aruco_<id>` 발행 → 스킬은 `base_footprint` 기준으로 읽기

✅ **체크포인트 3-4**: `tf2_echo`로 상자까지의 거리를 읽었다.

## 실습 5. Pick & Place 전체 흐름

월드를 리셋하고, AMCL에 로봇이 원점에 있다고 다시 알려 준 뒤 데모를 실행합니다:

```bash
$ ros2 service call /mujoco_bridge/reset std_srvs/srv/Trigger
$ ros2 topic pub --once /initialpose geometry_msgs/msg/PoseWithCovarianceStamped \
    "{header: {frame_id: map}, pose: {pose: {orientation: {w: 1.0}}}}"
$ ros2 run unbolt_manipulation pick_place_demo --ros-args -p use_sim_time:=true
```

> 시뮬레이터 리셋은 로봇을 원점으로 옮기지만 AMCL은 그 사실을 모릅니다. 실습 4에서 로봇을 몰았다면
> 지도 위 위치가 수십 cm 어긋난 채로 남아 주행이 틀어지므로 `/initialpose`로 원점을 다시 알려 줍니다
> (RViz의 **2D Pose Estimate**로 원점을 찍어도 같습니다). 모듈 4의 플래너를 켜면 `/task_reset` 하나로 둘 다 합니다.

![Pick & Place](../docs/step5_pick_place.jpg)

`pick_place_demo.py`는 스킬을 순서대로 잇는 **상태 기계**입니다. 하나라도 실패하면 거기서 멈춥니다:

```
 arms tuck ─▶ navigate(공급 테이블 앞) ─▶ servo_to_marker(7) ─▶ pick(7) ─▶ back off
     ─▶ navigate(작업대 앞) ─▶ servo_to_marker(3) ─▶ place(3) ─▶ back off
```

`pick()` 안에서는 (`skills.py`):

```
 상자 중심 = 마커 위치 − 2.5 cm × 마커 z축       (마커는 윗면에 붙어 있다)
 팔 선택  = 상자가 왼쪽(y > 0)이면 왼팔, 아니면 오른팔
 손 회전  = 상자 yaw에 맞춰 ±45° 안에서
 planning scene에 상판 추가 → 그리퍼 열기 → pre-grasp(10 cm 뒤, 4 cm 위) → 직선 접근 → 닫기
 → 닫은 뒤에도 손가락이 0.06 rad 이상 벌어져 있으면 "잡았다" (사이에 상자가 있다) → 직선으로 8 cm 들기 → tuck → 상판 제거
```

마지막 로그의 `red box ends at (...); N cm from the pad centre`를 적으세요.

✅ **체크포인트 3-5**: 상자가 작업대의 마커 3 위에 놓였다 (패드 중심에서 3 cm 이내).

---

## 과제

**기본 과제 A. 되돌려 놓기.** `pick_place_demo.py`를 복사해서 상자를 **작업대 → 공급 테이블**(놓을 자리 마커 5)로
되돌리는 `put_back.py`를 만드세요. 공급 테이블 앞 위치는 `SUPPLY_STAGING`, 작업대 앞은 `WORK_STAGING`입니다.

**기본 과제 B. 파지 파라미터.** `skills.py`의 `PRE_GRASP_UP`(0.04)을 0으로, `GRASP_HEIGHT`(0.015)를 0으로 바꿔
각각 데모를 돌려 보고 무엇이 실패하는지 로그로 설명하세요. (끝나면 원래 값으로)

**도전 과제. Attach / Detach.** 지금은 잡은 상자를 planning scene에 넣지 않아서, 상자를 든 채 팔을 움직일 때
MoveIt이 상자의 충돌을 모릅니다. 잡은 직후 상자를 `AttachedCollisionObject`(5 cm 상자, 손 링크 `openarm_*_ee_base_link`에
붙이고 손가락 링크와의 충돌은 `touch_links`로 허용)로 추가하고, 놓은 뒤 떼어 내도록 `pick()`/`place()`를 고치세요. RViz MotionPlanning의 **Scene Objects**에서 확인합니다.

## 정리 질문

1. `move_to_pose`와 `move_linear`를 각각 언제 쓰나? 집기 직전 접근에 `move_to_pose`를 쓰면 어떤 위험이 있나?
2. 계획할 때만 상판을 planning scene에 넣고 끝나면 빼는 이유는? (힌트: 주행 중 planning scene의 상판 위치는 맞을까?)
3. 마커가 가려졌을 때 "기억한 위치 + 오도메트리"를 쓴다. 이 방법이 틀어지는 경우는?
4. 손가락 각도로 "잡았다"를 판단한다. 실제 로봇에서는 무엇으로 판단할 수 있을까?

## 참고

| 파일 | 내용 |
|---|---|
| `unbolt_moveit_config/config/unbolt.srdf.base` | 그룹, named state |
| `unbolt_moveit_config/scripts/generate_collision_matrix.py` | MuJoCo로 자기충돌 행렬 계산 (Setup Assistant 대신) |
| `unbolt_mujoco_bridge/trajectory_server.py` | `FollowJointTrajectory` → MuJoCo |
| `unbolt_manipulation/skills.py` | `navigate`, `servo_to_marker`, `move_to_pose`, `move_linear`, `lower_until_contact`, `pick`, `place` |
| `unbolt_manipulation/aruco_detector.py` | ArUco → TF |
| MoveIt 2 문서 | <https://moveit.picknik.ai/humble/> |
