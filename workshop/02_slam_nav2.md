# 모듈 2. SLAM Toolbox + Nav2 실내 자율주행

**1일차 12:30–16:30 (4시간)**

| 시간 | 내용 |
|---|---|
| 12:30–13:00 | 개념: SLAM, `map → odom → base` TF, Nav2 구조 |
| 13:00–13:50 | 실습 1~2: SLAM으로 지도 만들기, 저장 |
| 13:50–14:40 | 실습 3~4: AMCL 위치 추정, 목표점 주행, costmap 읽기 |
| 14:40–14:50 | 휴식 |
| 14:50–15:40 | 실습 5~6: 파라미터 바꿔 보기, 지도에 없는 장애물 |
| 15:40–16:10 | 실습 7: Python으로 순찰 프로그램 (Nav2 Simple Commander), 실습 8: 자동 탐색으로 지도 만들기 (시간이 모자라면 강사 시연) |
| 16:10–16:30 | **전반부 통합 데모**, 과제 안내 |

## 학습 목표

1. SLAM이 `map → odom` 변환으로 오도메트리 오차를 보정한다는 것을 TF로 확인한다.
2. slam_toolbox로 방 지도를 만들고 저장한다.
3. Nav2의 구성 요소(AMCL, global/local costmap, planner, controller, behavior tree)가 하는 일을 말할 수 있다.
4. RViz와 Python(Simple Commander)으로 목표점 주행을 시키고, 실제 위치 오차를 잰다.
5. 파라미터(inflation, 속도)가 경로와 주행에 주는 영향을 실험으로 확인한다.

---

## 개념

### 세 개의 좌표계

```
 map ──────────▶ odom ──────────▶ base_footprint ──▶ base_link ──▶ ...
     SLAM/AMCL이 발행          브리지(휠 오도메트리)가 발행
     (LiDAR로 오차 보정,        (부드럽지만 시간이 갈수록 어긋남)
      가끔 뛸 수 있음)
```

- **odom**: 연속적이고 부드럽지만 누적 오차가 쌓인다 (모듈 1 실습 6에서 확인).
- **map**: 지도에 대해 정확하지만 보정할 때 위치가 툭 뛸 수 있다.
- SLAM/AMCL은 로봇 위치를 직접 바꾸지 않고 **`map → odom`을 조정**해서 둘의 장점을 합친다.

### SLAM Toolbox (지도 만들기)

LiDAR 스캔을 이어 붙여 지도를 만드는 그래프 기반 SLAM입니다.

1. **스캔 매칭**: 새 스캔을 지금까지의 지도에 맞춰서 오도메트리보다 정확한 위치를 구한다.
2. **포즈 그래프**: 일정 거리(0.2 m)/각도(0.2 rad)마다 노드를 추가한다.
3. **루프 클로저**: 예전에 왔던 곳에 돌아오면 알아보고, 그동안 쌓인 오차를 그래프 전체에 나눠 줄인다.

### Nav2 (주행)

```
  목표 (RViz 2D Goal Pose / Python)
        ▼
  bt_navigator ── 행동 트리: 계획 → 따라가기 → 막히면 복구(회전, 후진, 대기)
        │
        ├─▶ planner_server (NavFn)     global costmap 위에서 전체 경로
        │        static layer(지도) + obstacle layer(LiDAR) + inflation layer
        │
        └─▶ controller_server (Regulated Pure Pursuit)   local costmap(4×4 m) 위에서 속도 명령
                 │
                 ▼
           velocity_smoother ──▶ /cmd_vel ──▶ 브리지
  AMCL: 저장된 지도 + LiDAR + 오도메트리 ──▶ map → odom
```

이 로봇의 설정 (`unbolt_navigation/config/nav2_params.yaml`):

| 항목 | 값 | 이유 |
|---|---|---|
| footprint | 0.60 × 0.54 m 직사각형 | 섀시 + 바퀴. 원(robot_radius)보다 문 통과가 정확 |
| controller | Regulated Pure Pursuit, 0.35 m/s | 차동구동, 제자리 회전 가능 |
| inflation_radius | 0.6 m | 벽에서 여유 |
| local costmap | 4 × 4 m, 0.05 m | LiDAR 장애물만 |
| goal tolerance | xy 0.15 m, yaw 0.2 rad | |

---

## 실습 1. SLAM으로 지도 만들기

터미널 1:

```bash
$ ros2 launch unbolt_navigation slam.launch.py
```

RViz에서 회색 지도가 조금씩 생깁니다. 터미널 2에서 키보드로 방을 돌아다니세요:

```bash
$ ros2 run teleop_twist_keyboard teleop_twist_keyboard
```

- **천천히** 다니세요 (`x`로 속도 줄이기). 빠르게 돌면 스캔 매칭이 실패해 지도가 겹쳐 보입니다.
- 칸막이벽의 문(가운데 y = −0.4~0.8 m)을 지나 서쪽 방까지 다녀오세요.
- 처음 자리로 돌아오면 루프 클로저로 지도가 살짝 "정리"되는 것을 볼 수 있습니다.

시간이 부족하면 자동 탐색 (약 2분):

```bash
$ ros2 run unbolt_navigation explore_waypoints.py --ros-args -p use_sim_time:=true
```

> `explore_waypoints.py`는 실제 위치(`/ground_truth/odom`)로 정해진 경로를 도는 **지도 작성 도우미**입니다.
> Nav2가 아닙니다. 지도가 없으면 Nav2를 쓸 수 없으니까요.

✅ **체크포인트 2-1**: 벽이 이중으로 겹치지 않은 방 전체 지도가 보인다.

## 실습 2. map → odom 관찰과 지도 저장

```bash
$ ros2 run tf2_ros tf2_echo map odom --ros-args -p use_sim_time:=true
```

로봇을 몰면서 이 값이 **조금씩 변하는 것**을 보세요. 오도메트리 오차를 SLAM이 보정하는 양입니다.

지도 저장 (src 폴더가 아니라 홈의 `maps`에):

```bash
$ mkdir -p ~/maps
$ ros2 run nav2_map_server map_saver_cli -f ~/maps/my_room --ros-args -p use_sim_time:=true
$ ls ~/maps            # my_room.pgm  my_room.yaml
$ explorer.exe ~/maps  # Windows에서 그림 보기 (pgm은 GIMP 등으로)
```

`my_room.yaml`의 `resolution`(칸 크기)과 `origin`(지도 왼쪽 아래 칸의 월드 좌표)을 확인하세요.

✅ **체크포인트 2-2**: `~/maps/my_room.yaml` 저장. 모든 터미널 `Ctrl + C`.

## 실습 3. 저장된 지도로 주행

미리 만들어 둔 지도(`unbolt_room`)로 시작합니다:

```bash
$ ros2 launch unbolt_navigation navigation.launch.py
```

![Nav2 in RViz](../docs/step3_nav_rviz.jpg)

1. AMCL은 지도 원점에서 시작하도록 설정되어 있습니다. 초록 파티클(화살표 구름)이 로봇 주변에 모여 있는지 확인.
   어긋나 있으면 RViz 위쪽 **2D Pose Estimate**로 실제 위치·방향을 드래그해 알려 줍니다.
2. **2D Goal Pose**로 동쪽 방 아무 데나 목표를 드래그 (화살표 방향 = 도착했을 때 바라볼 방향).
3. 보이는 것:
   - 초록/분홍 선: global plan (NavFn)
   - 로봇 주변 색 사각형: local costmap
   - 벽 주변 하늘색 띠: inflation (가까울수록 비용이 높음)
4. 서쪽 방의 목표도 찍어서 칸막이 문을 통과하는지 보세요.

✅ **체크포인트 2-3**: 목표 두 개(동쪽 방, 서쪽 방)를 연속으로 도착했다.

## 실습 4. 내 지도로 주행 + 위치 오차 재기

```bash
$ ros2 launch unbolt_navigation navigation.launch.py map:=$HOME/maps/my_room.yaml
```

다른 터미널에서 자동 시험 (목표 3개를 차례로 가고 실제 위치와 비교):

```bash
$ ros2 run unbolt_navigation nav_goal_test.py --ros-args -p use_sim_time:=true
```

결과를 표로 적으세요:

| 목표 | 걸린 시간 | 위치 오차 (cm) | 방향 오차 (°) |
|---|---|---|---|
| (3.0, −1.4) | | | |
| (−1.9, 1.6) | | | |
| (0.0, 0.0) | | | |

✅ **체크포인트 2-4**: 3/3 도착, 위치 오차 15 cm 이내 (goal tolerance).

## 실습 5. 파라미터 실험

설정 파일을 복사해서 고칩니다 (원본은 그대로 두기):

```bash
$ cp $(ros2 pkg prefix unbolt_navigation)/share/unbolt_navigation/config/nav2_params.yaml ~/my_nav2.yaml
$ code ~/my_nav2.yaml
$ ros2 launch unbolt_navigation navigation.launch.py params_file:=$HOME/my_nav2.yaml
```

하나씩 바꿔 보고 같은 목표로 비교하세요.

| 실험 | 바꿀 곳 | 예상 | 관찰 |
|---|---|---|---|
| A | `inflation_radius` 0.6 → 0.25 (global·local 둘 다) | 벽에 바짝 붙는 경로 | |
| B | `inflation_radius` 0.6 → 1.2 | 문을 통과하지 못할 수도 | |
| C | `desired_linear_vel` 0.35 → 0.6 | 빨라지지만 코너에서? | |
| D | `xy_goal_tolerance` 0.15 → 0.05 | 도착 판정이 엄격해져 오래 걸림 | |

> 실행 중에 바꿔 볼 수도 있습니다 (일부 파라미터만):
> `ros2 param set /global_costmap/global_costmap inflation_layer.inflation_radius 0.3`

## 실습 6. 지도에 없는 장애물

모듈 1 과제 A의 `my_scene.xml`(상자 추가)을 쓰거나, 지금 만듭니다. 상자를 **주행 경로 위**에 두세요:

```xml
<geom name="surprise" type="box" size="0.2 0.2 0.3" pos="2.0 -1.0 0.3" rgba="0.2 0.6 0.2 1"/>
```

**옛 지도**(상자 없음)로 주행:

```bash
$ ros2 launch unbolt_navigation navigation.launch.py model_path:=$UNBOLT_ROOT/models/my_scene.xml
```

처음 위치(원점)에서 `(3.0, −1.4)` 쪽으로 목표를 주고, 상자가 없는 원래 월드(`model_path` 없이)와 비교하세요.
(강사 노트북 기준: 상자가 없으면 작업대와 기둥 사이 남쪽 길로 약 12초, 상자가 있으면 작업대 북쪽으로 돌아 약 18초)

관찰할 것:

- 상자가 LiDAR에 보이면 **obstacle layer**가 costmap에 표시하고 → planner가 경로를 다시 계산합니다.
- 너무 가까이 와서야 보이면 controller가 멈추고 behavior tree의 **복구 동작**(회전·후진·대기)이 나옵니다.
  터미널 로그에서 `Running spin`, `Running backup` 같은 줄을 찾아보세요.

✅ **체크포인트 2-5**: 지도에 없는 상자를 돌아서 목표에 도착했다.

## 실습 7. Python으로 순찰 프로그램

`~/patrol.py`를 만듭니다:

```python
#!/usr/bin/env python3
"""방 네 곳을 차례로 순찰하고 걸린 시간을 출력한다."""
import math
import time

import rclpy
from geometry_msgs.msg import PoseStamped
from nav2_simple_commander.robot_navigator import BasicNavigator, TaskResult

POINTS = [(3.2, 1.2, 0.0), (3.0, -1.4, -math.pi / 2), (-1.9, 1.6, math.pi / 2), (0.0, 0.0, 0.0)]


def pose(nav, x, y, yaw):
    p = PoseStamped()
    p.header.frame_id = 'map'
    p.header.stamp = nav.get_clock().now().to_msg()
    p.pose.position.x, p.pose.position.y = x, y
    p.pose.orientation.z, p.pose.orientation.w = math.sin(yaw / 2), math.cos(yaw / 2)
    return p


def main():
    rclpy.init()
    nav = BasicNavigator()
    nav.waitUntilNav2Active()
    for x, y, yaw in POINTS:
        t0 = time.time()
        nav.goToPose(pose(nav, x, y, yaw))
        while not nav.isTaskComplete():
            fb = nav.getFeedback()
            if fb:
                print(f'  ({x:.1f}, {y:.1f})까지 {fb.distance_remaining:.2f} m', end='\r')
        result = nav.getResult()
        print(f'({x:.1f}, {y:.1f}): {"도착" if result == TaskResult.SUCCEEDED else "실패"}, {time.time() - t0:.1f} s')
    rclpy.shutdown()


if __name__ == '__main__':
    main()
```

```bash
$ python3 ~/patrol.py --ros-args -p use_sim_time:=true
```

> `goToPose` 대신 `followWaypoints([pose, pose, ...])`를 쓰면 한 번에 넘길 수 있습니다. 차이는? (중간 지점에서 방향 맞추기)

✅ **체크포인트 2-6**: 네 곳 순찰 성공.

## 실습 8. 자동 탐색으로 지도 만들기 (대시보드)

실습 1에서는 사람이 키보드로 몰면서 지도를 만들었습니다. 이번에는 **로봇이 스스로** 돌아다니며 지도를 만듭니다.
이것을 능동 탐색(active exploration)이라고 하고, 가장 널리 쓰는 방법이 **프론티어(frontier) 탐색**입니다.

**프론티어**는 "아는 빈 곳"과 "모르는 곳"의 경계입니다. SLAM 지도에서 빈 칸(흰색)인데 바로 옆이 미지(회색)인 칸들이죠.
프론티어에 가서 보면 그 너머가 지도에 채워지고, 새 프론티어가 생깁니다. 이것을 프론티어가 없어질 때까지 반복합니다.

```
 ┌─ /map (slam_toolbox) ─┐   ① 프론티어 칸 찾기: 빈 칸 + 옆이 미지
 │                       │   ② 붙어 있는 칸끼리 묶기 (길이 0.3 m 미만은 무시)
 │  frontier_explorer    │   ③ 묶음마다 "설 자리" 고르기: costmap 비용이 낮고(벽에서 0.55 m 이상),
 │                       │      로봇이 갈 수 있고, 프론티어에서 1 m 안 (벽 너머 말고 같은 쪽)
 └──────────┬────────────┘   ④ 점수 = 가는 거리 − 프론티어 길이 보너스 → 가장 좋은 곳으로
            │ NavigateToPose  ⑤ 가는 동안 LiDAR가 프론티어를 지우면 바로 다음 곳으로
            ▼                 ⑥ 갈 수 있는 프론티어가 없으면 끝 → 지도 자동 저장 (~/maps)
          Nav2 → /cmd_vel → 로봇
```

코드는 `unbolt_navigation/scripts/frontier_explorer.py` 하나(약 350줄)입니다. 프론티어 찾기는 OpenCV 몇 줄입니다:

```python
free = (grid >= 0) & (grid < 25)          # 빈 칸
unknown = grid < 0                          # 미지
frontier = free & (cv2.dilate(unknown.astype(np.uint8), cross) > 0)   # 빈 칸 중 옆이 미지
n, labels, stats, _ = cv2.connectedComponentsWithStats(frontier.astype(np.uint8), connectivity=8)
```

**대시보드로 하기** (런처 사용, [실습 5 웹 대시보드](04_llm_dashboard.md#실습-5-웹-대시보드) 참고):

```bash
$ ros2 run unbolt_dashboard dashboard_launcher
```

1. 브라우저에서 <http://localhost:8080> → 모드 **지도 만들기 (SLAM + 자동 탐색)** → **연결**
2. 20~40초 뒤 탐색이 저절로 시작됩니다. 지도 카드에서 지도가 자라는 것, 하늘색 프론티어, 파란 탐색 목표를 보세요.
3. 2~4분 뒤 **탐색 완료** → 지도가 `~/maps/unbolt_explored_<날짜>_<시간>.yaml`로 저장됩니다.
4. 이제 **키보드 조종**: 브라우저 창을 클릭하고 `W A S D` 또는 방향키 (스페이스 = 정지).
   누르고 있는 동안만 움직이고, 장애물이 가까우면 그쪽으로는 가지 않습니다. 몰고 다니는 동안에도 SLAM이 지도를 계속 고치니,
   빈 곳이 남았으면 직접 가서 채우고 **지도 저장**을 다시 누르세요.
5. **시스템 종료** → 모드 **작업**, 지도 목록에서 방금 저장한 지도를 고르고 **연결**하면 그 지도로 작업 모드가 켜집니다.

**터미널로 하기** (대시보드 없이, RViz로 보기):

```bash
$ ros2 launch unbolt_navigation explore.launch.py
$ ros2 topic echo /explore/status --field data            # 상태 (JSON)
$ ros2 topic pub --once /explore/control std_msgs/msg/String "{data: stop}"    # start / stop / save
$ ros2 launch unbolt_navigation navigation.launch.py map:=$HOME/maps/unbolt_explored_<...>.yaml
```

✅ **체크포인트 2-7**: 자동 탐색이 끝나고 `~/maps`에 지도가 저장됐다. 키보드로 로봇을 몰 수 있다.

> **실제로 겪은 문제: 지도가 비스듬히 두 번 그려진다.** 처음 만든 탐색은 실행 절반 정도에서 방을 비스듬히 겹쳐 그렸습니다.
> 실제 위치와 SLAM 위치, 오도메트리를 같이 기록해 보니 로봇이 공급 테이블의 4 cm 다리에 걸려 **바퀴만 헛돌았고**, 오도메트리가
> 수십 도 틀어지자 오도메트리에서 출발해 스캔을 맞추는 SLAM이 틀린 각도로 지도를 이었습니다. 왜 다리를 못 피했을까요?
> 시뮬레이터의 LiDAR가 그 다리를 **아예 못 봤습니다**: 브리지가 쓰던 `mj_multiRay`가 다리 두 개를 건너뛰었고(같은 광선을 `mj_ray`로
> 쏘면 맞음), 지금은 광선마다 `mj_ray`를 씁니다([모듈 1 실습 5](01_mujoco_ros2_bridge.md#실습-5-lidar--광선-360개)).
> 덤으로 탐색 모드의 Nav2는 로봇을 반지름 0.44 m 원으로 보고(회전 때 모서리가 쓰는 0.40 m + 여유), 가는 장애물을 한 번 보면
> 놓치지 않게 설정했습니다(720개 광선, footprint clearing 끔, 전역 costmap 20 × 20 m 이동 창). 자세한 내용은
> `explore.launch.py`의 `_nav2()` 주석에 있습니다. 증상(겹친 지도)에서 원인(센서 버그)까지 측정으로 좁혀 가는 과정 자체가 좋은 공부거리입니다.

> **생각해 보기.** 칸막이 문 너머 서쪽 방에는 벽 그림자처럼 비스듬한 프론티어가 생깁니다. 문 앞에 서면 왜 그 너머가 잘 안 보일까요?
> `frontier_explorer.py`는 이 문제를 어떻게 피하나요? (힌트: `MID_WEIGHT`, `MAX_TRIES`)

## 전반부 통합 데모 (16:10–16:30)

지금까지 만든 것이 한 줄로 이어집니다:

```
ros2 launch  →  MuJoCo 물리  →  브리지(/scan, /odom, /clock)  →  SLAM 지도  →  AMCL 위치 추정  →  Nav2 경로·제어  →  /cmd_vel  →  MuJoCo
```

조별로 한 명씩: **내가 만든 지도로, 내 순찰 프로그램을** 돌리고 MuJoCo 화면과 RViz를 나란히 보여 주세요.

---

## 과제

**기본 과제.** 실습 5의 실험 A~D 중 두 개를 골라 결과(스크린샷 + 시간·오차 표 + 한 줄 해석)를 제출.

**도전 과제 1. 더 똑똑한 탐색.** `frontier_explorer.py`는 "가까운 곳 + 긴 프론티어"로 다음 목표를 고릅니다.
설 자리에서 LiDAR 광선을 쏘아 **새로 보이게 될 미지 칸의 수(정보 이득)**를 계산해 점수에 넣어 보고, 탐색 시간과 목표 수가
어떻게 바뀌는지 3번씩 재서 비교하세요.

**도전 과제 2. 출입 금지 구역.** Nav2의 keepout filter(`nav2_costmap_2d::KeepoutFilter`)로 방 한쪽을
출입 금지로 만들고, 그쪽 목표를 주면 계획이 실패하는 것을 보이세요.

## 정리 질문

1. SLAM으로 지도를 만들 때와 AMCL로 주행할 때, 각각 `map → odom`을 누가 발행할까?
2. inflation_radius를 footprint보다 작게 하면 어떤 일이 생길까?
3. 지도에 없는 장애물이 **global** costmap에도 나타나는 이유는? (힌트: obstacle_layer가 어디 있는지 파라미터 파일에서 찾기)
4. 실습 4의 위치 오차는 goal tolerance보다 작았나? 왜 그럴까?

## 참고

| 파일 | 내용 |
|---|---|
| `unbolt_navigation/config/slam_toolbox.yaml` | SLAM 설정 (해상도 0.05, 루프 클로저) |
| `unbolt_navigation/config/nav2_params.yaml` | Nav2 설정 (맨 위 주석에 공식 파일과 다른 점) |
| `unbolt_navigation/scripts/nav_goal_test.py` | BasicNavigator 사용 예 + 실제 위치 비교 |
| `unbolt_navigation/scripts/frontier_explorer.py` | 프론티어 자동 탐색 (실습 8) |
| `unbolt_navigation/launch/explore.launch.py` | 시뮬레이터 + SLAM + Nav2(지도 없이) + 자동 탐색 |
| Nav2 문서 | <https://docs.nav2.org/> (Humble 버전 선택) |
