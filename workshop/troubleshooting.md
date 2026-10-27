# 문제 해결

`Ctrl + F`로 오류 메시지의 일부를 검색하세요. 여기 없으면 오류 전체를 복사해 조교에게 보여 주세요
(스크린샷보다 텍스트가 좋습니다. 단, **API 키가 들어 있지 않은지** 확인).

- [Windows / WSL 설치](#windows--wsl-설치)
- [GUI 창이 안 뜬다 (WSLg)](#gui-창이-안-뜬다-wslg)
- [설치 스크립트](#설치-스크립트)
- [실행 공통](#실행-공통)
- [모듈 1~3: 시뮬레이터, Nav2, MoveIt](#모듈-13-시뮬레이터-nav2-moveit)
- [모듈 4: LLM, 대시보드](#모듈-4-llm-대시보드)
- [모든 것을 처음부터](#모든-것을-처음부터)

---

## Windows / WSL 설치

| 증상 | 원인 | 해결 |
|---|---|---|
| `0x80370102` "가상 머신을 시작할 수 없습니다" | BIOS 가상화 꺼짐 | [설치 가이드 부록 A](00_install.md#부록-a-bios에서-가상화-켜기) |
| `0x8007019e`, "WSL 옵션 구성 요소를 사용하도록 설정" | WSL 기능이 꺼져 있음 | 관리자 PowerShell: `dism.exe /online /enable-feature /featurename:Microsoft-Windows-Subsystem-Linux /all /norestart` 와 `dism.exe /online /enable-feature /featurename:VirtualMachinePlatform /all /norestart` → 재부팅 |
| `0x800701bc` "커널 구성 요소 업데이트 필요" | WSL 커널이 오래됨 | `wsl --update` |
| `wsl --install`이 도움말만 출력 | 오래된 Windows 10 | Windows 업데이트, 또는 Microsoft Store에서 "Windows Subsystem for Linux" + "Ubuntu 22.04.5 LTS" |
| "Installing, this may take a few minutes..."에서 10분 넘게 멈춤 | 다운로드/초기화 지연 | 창을 닫고 `wsl --shutdown` 후 시작 메뉴에서 Ubuntu 22.04 다시 실행 |
| 학교·회사 노트북에서 설치가 막힘 | 그룹 정책으로 Hyper-V/WSL 차단 | 관리 부서에 문의하거나 개인 노트북 사용. 강사에게 미리 알리기 |
| sudo 비밀번호를 잊었다 | | PowerShell: `wsl -d Ubuntu-22.04 -u root` → `passwd <리눅스사용자>` → `exit` |
| `wsl -l -v`에 VERSION 1 | WSL1으로 설치됨 | `wsl --set-version Ubuntu-22.04 2` |
| Windows Terminal에 Ubuntu-22.04 탭이 없음 | | Terminal 재시작, 또는 시작 메뉴의 Ubuntu 22.04 앱 사용 |

## GUI 창이 안 뜬다 (WSLg)

1. `$ ls /mnt/wslg` 에 파일이 있는지, `$ echo $DISPLAY` 가 `:0` 인지 확인
2. 없다면: PowerShell에서 `wsl --update` → `wsl --shutdown` → Ubuntu 다시 열기
3. Windows 10이면 빌드 19044 이상 + Store 버전 WSL이어야 WSLg가 됩니다 (`wsl --version`이 동작해야 함)

| 증상 | 해결 |
|---|---|
| 창은 뜨는데 검거나 깨짐, RViz가 바로 죽음 | Windows에서 **그래픽 드라이버 업데이트** (Intel/AMD/NVIDIA 공식 사이트) → `wsl --shutdown` |
| `check_env.sh`가 `소프트웨어 렌더링: llvmpipe` | 위와 같음. 그래도 안 되면 소프트웨어 렌더링으로 진행 가능 (느림) |
| 그래픽 오류가 계속 남 | 임시 우회: `export LIBGL_ALWAYS_SOFTWARE=1` 후 실행 (CPU 렌더링, 느림) |
| NVIDIA 외장 그래픽이 있는데 내장 그래픽을 씀 | `export MESA_D3D12_DEFAULT_ADAPTER_NAME=NVIDIA` 를 `~/.bashrc`에 추가 |
| 창이 화면 밖에 뜸 / 너무 작음 | 작업 표시줄의 창 아이콘 우클릭 → 최대화. 고해상도 화면은 Windows 배율 설정 영향 |

## 설치 스크립트

| 증상 | 원인 | 해결 |
|---|---|---|
| `Could not get lock /var/lib/dpkg/lock-frontend` | Ubuntu가 자동 업데이트 중 | 5분 기다렸다가 다시 실행 |
| `Unable to locate package ros-humble-desktop` | 2단계(ROS 저장소) 실패 | `ls /etc/apt/sources.list.d/` 에 `ros2.sources`가 있는지 확인 → 없으면 스크립트 다시 실행 |
| `NO_PUBKEY F42ED6FBAB17C654` 또는 `EXPKEYSIG` | 옛날 방식으로 등록한 ROS 저장소 키 만료 | `sudo rm /etc/apt/sources.list.d/ros2.list /usr/share/keyrings/ros-archive-keyring.gpg` 후 스크립트 다시 실행 |
| `최신 버전 조회 실패 (… GitHub API 제한 …)` | 같은 IP에서 GitHub API를 많이 부름 (강의실) | 경고일 뿐, 고정 버전으로 계속 진행됨 |
| `Temporary failure resolving 'archive.ubuntu.com'` | WSL DNS 문제 | `wsl --shutdown` 후 재시도. VPN을 끄기. 계속되면 아래 "DNS 고정" |
| `$'\r': command not found`, `/bin/bash^M: bad interpreter` | 스크립트 줄바꿈이 Windows(CRLF) 형식 (ZIP을 Windows 도구로 풀었거나 git `autocrlf`) | `sudo apt install -y dos2unix && find ~/unbolt -name '*.sh' -exec dos2unix {} +` |
| `코드가 Windows 드라이브(/mnt/c/...)에 있습니다` 경고 | 코드가 C: 드라이브에 있음 | `cp -r <그 폴더> ~/unbolt` 후 `~/unbolt`에서 다시 실행 |
| colcon: `Package 'openarm_description' not found` | ZIP으로 받아 심볼릭 링크가 깨짐 | 스크립트를 다시 실행 (5단계가 링크를 다시 만듦) |
| pip가 `numpy 2.x`를 깔았다 / `cv_bridge` import 오류 `numpy.core.multiarray failed to import` | pip numpy가 시스템 numpy를 가림 | `pip3 uninstall -y numpy` 후 `pip3 install --user "numpy<2"` |
| `module 'cv2' has no attribute 'aruco'` | pip의 `opencv-python`이 Ubuntu OpenCV를 가림 | `pip3 uninstall -y opencv-python opencv-contrib-python` |
| 디스크 여유 부족 | | Windows 디스크 정리. WSL 디스크는 쓴 만큼 커지고 저절로 줄지 않음 |

**DNS 고정** (`Temporary failure resolving`이 계속될 때):

```bash
$ sudo tee /etc/wsl.conf >/dev/null <<'EOF'
[network]
generateResolvConf = false
EOF
$ sudo rm -f /etc/resolv.conf && echo "nameserver 8.8.8.8" | sudo tee /etc/resolv.conf
```

PowerShell에서 `wsl --shutdown` 후 다시 엽니다.

## 실행 공통

| 증상 | 원인 | 해결 |
|---|---|---|
| `ros2: command not found` | 설치 전에 연 터미널 | 새 터미널을 열거나 `source ~/.bashrc` |
| `Package 'unbolt_mujoco_bridge' not found` (`unbolt_dashboard` 등도 같음) | 워크스페이스 환경 미적용: `~/.bashrc`에 unbolt 블록이 없거나, 블록을 넣기 전에 연 터미널 | `grep ">>> unbolt" ~/.bashrc`로 확인. 있으면 `source ~/.bashrc`, 없으면 설치 스크립트를 다시 실행하거나 [설치 가이드 4-1](00_install.md#4-1-환경-설정-bashrc가-하는-일)대로 직접 넣기 (코드를 `~/unbolt`가 아닌 곳에 두었을 때도) |
| 새로 만든 파일(노드, launch)이 안 보임 | `--symlink-install`이어도 **새 파일**은 빌드 필요 | `cd ~/unbolt/ros2_ws && colcon build --symlink-install` |
| `Lookup would require extrapolation into the future/past` | 그 노드가 시뮬레이션 시간을 안 씀 | `--ros-args -p use_sim_time:=true` 붙이기 |
| `simulation is slower than real_time_factor` 경고 | 노트북이 물리 계산을 못 따라감 | 다른 프로그램 끄기, 전원 연결, `use_viewer:=false` (MuJoCo 창 끄기), RViz 표시 줄이기. 동작은 느려질 뿐 결과는 같음 |
| 이전 실행이 안 꺼져서 이상하게 동작 (토픽 발행자가 2개, 로봇 두 대처럼) | `Ctrl + C` 뒤에도 남은 프로세스 | 아래 "깨끗하게 종료" |
| 다른 사람 로봇의 토픽이 보임 | 같은 네트워크·같은 `ROS_DOMAIN_ID` (WSL 네트워크를 mirrored로 바꾼 경우) | 강사가 정한 번호로 `export ROS_DOMAIN_ID=<번호>` 를 `~/.bashrc`의 unbolt 블록에 |

**conda를 쓰는 노트북**: 프롬프트 앞에 `(base)`가 보이면 conda가 켜져 있는 것입니다. ROS 2 Humble은 Ubuntu의
Python 3.10(`/usr/bin/python3`)용으로 만들어져 있어서, conda의 `python3`가 먼저 잡히면 `#!/usr/bin/env python3`로
시작하는 프로그램(rosbridge, Nav2·MoveIt 도구 일부, `python3 ~/patrol.py`)이 `No module named 'rclpy._rclpy_pybind11'`로
죽습니다. `check_env.sh`의 `python3 = ...` 줄에서 확인할 수 있습니다.

```bash
$ conda deactivate                              # 지금 터미널만
$ conda config --set auto_activate_base false   # 앞으로 새 터미널에서 자동으로 켜지지 않게 (conda는 필요할 때 conda activate)
```

**깨끗하게 종료**: 대시보드를 켰다면 오른쪽 위 **시스템 종료**(두 번 눌러 확인)가 가장 간단합니다. 모든 프로그램이
꺼지기까지 15초쯤 걸립니다 (Nav2 컨테이너가 SIGINT에 늦게 반응해 launch가 강제 종료할 때까지 기다림. 로그의
`escalating to 'SIGKILL'`, `move_group ... exit code -11`은 정상). 대시보드가 없거나 그래도 남은 프로세스가 있으면:

```bash
$ pkill -INT -f ros2; sleep 3
$ pkill -9 -f "mujoco_bridge|rviz2|move_group|nav2|slam_toolbox|rosbridge|task_planner|aruco_detector|dashboard_server"
$ ros2 daemon stop
```

그래도 이상하면 PowerShell에서 `wsl --shutdown` (Ubuntu 전체 재시작, 10초).

## 모듈 1~3: 시뮬레이터, Nav2, MoveIt

| 증상 | 해결 |
|---|---|
| 키보드로 눌러도 로봇이 안 움직임 | teleop 터미널 창을 클릭해서 선택한 상태로 키 누르기. `ros2 topic echo /cmd_vel`로 명령이 나가는지 확인 |
| 로봇이 제자리 회전을 잘 못함 | MJCF 캐스터의 `priority="2"`를 지웠는지 확인 ([모듈 1 실습 2](01_mujoco_ros2_bridge.md#실습-2-모델-파일-읽기)) |
| SLAM 지도가 겹쳐서(벽이 이중으로) 나옴 | 너무 빨리 회전했음. 처음부터 다시: 천천히(`x`로 감속), 특히 회전은 천천히 |
| `map_saver_cli` 가 `Failed to spin map subscription` | SLAM이 켜져 있는 동안 저장해야 함. `--ros-args -p use_sim_time:=true` 확인 |
| Nav2: 목표를 줘도 출발 안 함, `Failed to make progress` | AMCL 위치가 틀림 → RViz **2D Pose Estimate**로 실제 위치 알려 주기 |
| Nav2: 로봇이 제자리에서 계속 돎 (복구 동작 반복) | 목표가 장애물 안/벽 너무 가까이 → 다른 목표. 아래 "월드 리셋" |
| 월드 리셋 후 주행이 엉뚱한 곳으로 감 | 시뮬레이터 리셋(`/mujoco_bridge/reset`)만 해서 AMCL이 옛 위치를 기억 | 플래너가 켜져 있으면 대시보드 **초기화** 또는 `ros2 topic pub --once /task_reset std_msgs/msg/Empty`. 아니면 리셋 후 RViz **2D Pose Estimate**로 원점을 찍기 ([모듈 3 실습 5](03_moveit_pick_place.md#실습-5-pick--place-전체-흐름)) |
| Nav2 노드가 다 안 뜸 (`lifecycle` 관련 오류) | 이전 실행이 남아 있음 → "깨끗하게 종료" 후 다시 |
| MoveIt: `Unable to sample any valid states for goal tree`, `No IK solution` | 손이 닿지 않는 목표. 더 가까이/높이 조정 |
| MoveIt: `Start state appears to be in collision` | 팔이 테이블에 걸쳐 있음 → 월드 리셋 |
| `pick: marker 7 not visible` | 로봇이 공급 테이블을 보고 있지 않음, 또는 그리퍼가 열린 채로 시야를 가림 → 월드 리셋 후 다시 |
| `pick: gripper closed on nothing` | 정밀 접근 오차 → 월드 리셋 후 다시. 반복되면 `GRASP_*` 상수를 바꿨는지 확인 |
| `servo timed out` / `lost marker` | 마커가 시야 밖. 로봇이 테이블 정면을 보는지 확인 (`navigate`가 정확히 도착했는지) |

## 모듈 4: LLM, 대시보드

| 증상 | 원인 | 해결 |
|---|---|---|
| `APIConnectionError` + 원인 `process() takes no keyword arguments` | Ubuntu 기본 Brotli 1.0.9 | `pip3 install --user --upgrade Brotli` |
| `APIConnectionError` (다른 원인) | 인터넷 / 프록시 / 학교망 차단 | `curl -I https://api.anthropic.com` 로 확인. 휴대폰 핫스팟으로 시험 |
| `AuthenticationError` / 401 | 키가 틀림 또는 삭제됨 | `bash ~/unbolt/workshop/setup/setup_api_key.sh` 다시 |
| `Could not resolve authentication method` / 키가 없다고 함 | 키를 넣기 **전에** 연 터미널에서 실행 | 새 터미널에서 bringup 다시. 확인: `echo ${#ANTHROPIC_API_KEY}` (길이만 나와야 정상) |
| `credit balance is too low` | 크레딧 소진 | Console → Billing. 강의 중이면 `llm:=scripted`로 계속 |
| `429` / `rate_limit_error` | 짧은 시간에 너무 많이 호출 | 잠시 후 다시. SDK가 자동 재시도함 |
| `529` / `overloaded_error` | API 서버 혼잡 | 잠시 후 다시 |
| `ask`가 아무것도 안 하고 기다림 | `planner:=true` 없이 bringup을 켬 | `ros2 node list`에 `/task_planner` 있는지 확인 |
| `busy; ignored command: ...` | 이전 명령이 실행 중 | 끝날 때까지 기다리거나 `ros2 topic pub --once /task_cancel std_msgs/msg/Empty` |
| 브라우저에서 `localhost:8080`이 안 열림 | `dashboard:=true` 빠짐, 또는 WSL localhost 전달 문제 | Ubuntu에서 `curl -I localhost:8080` 확인 → 되면 `wsl --shutdown` 후 다시. 그래도 안 되면 `hostname -I`의 IP로 `http://<IP>:8080` |
| 대시보드에 "연결 끊김", 로그에 `rosbridge_websocket ... process has died ... exit code 1` | conda/venv가 켜져 있어 rosbridge가 ROS용이 아닌 Python으로 실행됨 (`No module named 'rclpy._rclpy_pybind11'`) | 아래 "conda를 쓰는 노트북" |
| 대시보드에 "연결 끊김" (그 밖의 경우) | rosbridge(:9090) 안 뜸 | bringup 로그에서 `rosbridge_websocket` 오류 확인. 9090 포트를 다른 프로그램이 쓰는지 |
| 대시보드에 **연결** 버튼이 없다 | 페이지를 런처가 아니라 bringup(dashboard_server)이 보여 주는 중 | `ros2 run unbolt_dashboard dashboard_launcher`를 켜고 페이지를 새로 고침 (bringup은 끈 상태에서) |
| 연결을 눌렀더니 "이전 프로그램이 아직 꺼지는 중입니다" | 방금 끈 시스템의 Nav2·MoveIt이 아직 종료 중 (최대 15초) | 10초쯤 뒤에 다시 연결 |
| 연결을 눌렀더니 "다른 곳에서 켠 ROS가 이미 실행 중입니다" | 터미널에서 켠 bringup이 있음 | 그대로 쓰면 됨 (페이지가 이미 연결됨). 런처로 켜고 싶으면 그 터미널을 Ctrl+C |
| "시스템이 멈췄습니다 (exit code …)" | 켜는 중 또는 실행 중에 launch가 종료됨 | 화면의 로그와 `~/.ros/unbolt_launcher.log`에서 `Traceback`, `has died` 찾기 |
| 지도 만들기: 1분이 넘도록 "준비 중" (지도와 Nav2를 기다리는 중) | slam_toolbox가 아직 지도를 안 냈거나 Nav2가 안 뜸 | `~/.ros/unbolt_launcher.log`에서 `slam_toolbox`, `bt_navigator` 오류 찾기. 시스템 종료 후 다시 연결 |
| 지도 만들기: "탐색 완료"인데 지도에 회색(미지)이 남음 | 장애물 뒤 그림자, 벽에 붙은 좁은 틈은 설 자리가 없어 포기함 (정상) | 키보드로 그쪽에 가서 보이게 한 뒤 **지도 저장**. 큰 방이 통째로 남았으면 **다시 탐색** |
| 지도 만들기: 방이 비스듬히 두 번 겹쳐 그려짐 | 로봇이 어딘가에 걸려 바퀴만 헛돌았고(오도메트리가 틀어짐), SLAM이 틀린 각도로 스캔을 맞춤 | 그 지도는 버리고 **시스템 종료** → 다시 **연결**. `explore.launch.py`의 `_nav2()` 설정(원 반지름 0.44 m, 720개 광선 등)이나 브리지의 LiDAR 코드(`mj_ray`)를 `nav2_params.yaml`을 바꿨다면 되돌리기 |
| 지도 만들기: 키보드가 안 먹음 | 탐색 중이거나, 페이지가 키 입력을 못 받음 | **멈춤**을 누르고, 브라우저 페이지를 한 번 클릭한 뒤 W A S D. "앞에 장애물" 표시는 일부러 막은 것 |
| 작업 모드 지도 목록에 만든 지도가 없음 | 지도가 `~/maps`에 없거나 목록이 예전 것 | `ls ~/maps/*.yaml` 확인 후 페이지 새로 고침. 런처를 다른 사용자(root 등)로 켜면 그 사용자의 `~/maps`를 봄 |
| 초기화 버튼을 눌렀는데 "초기화 요청에 응답이 없습니다" | `planner:=true` 없이 bringup을 켬 | `planner:=true`(키가 없으면 `llm:=scripted`도)로 다시 실행 |
| 카메라 화면이 안 나옴 | 마커 검출 노드 미실행 | `ros2 topic hz /aruco/debug_image/compressed` |

## 무시해도 되는 메시지

정상 동작 중에도 나오는 경고·오류입니다.

| 메시지 | 이유 |
|---|---|
| `[move_group] [ERROR] ... No 3D sensor plugin(s) defined for octomap updates` | 3D 센서(점구름)로 충돌 지도를 만들지 않으므로 |
| `[mujoco_bridge] [WARN] simulation is slower than real_time_factor` (시작할 때 한 번) | Nav2·MoveIt이 동시에 켜지는 동안 잠깐 느려짐. 계속 나오면 위 "실행 공통" 참고 |
| `[planner_server] [ERROR] Failed to create a plan from potential when a legal potential was found` (가끔 한 번) | NavFn이 다음 주기에 다시 계획함. 로봇이 계속 가면 무시 |
| `[rviz2] ... Message Filter dropping message` (시작 직후) | TF가 아직 다 안 들어옴 |
| `To run a command as administrator (user "root"), use "sudo <command>"` | Ubuntu 첫 로그인 안내 |

## 모든 것을 처음부터

설치가 꼬여서 처음부터 다시 하고 싶을 때. **Ubuntu 안의 모든 파일이 삭제됩니다** (필요한 파일은 먼저 `/mnt/c/...`로 복사).

```powershell
PS> wsl --unregister Ubuntu-22.04
PS> wsl --install -d Ubuntu-22.04
```

그리고 [설치 가이드 2-2](00_install.md#2-2-리눅스-사용자-만들기)부터 다시 합니다.
