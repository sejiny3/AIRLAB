#!/bin/bash
# UNBOLT 실습 환경 점검. 모든 줄이 ✔ 또는 ! 이면 실습 가능, ✘ 가 있으면 문제 해결 문서를 보세요.
#   bash ~/unbolt/workshop/setup/check_env.sh
REPO="${UNBOLT_ROOT:-$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)}"
P=0; W=0; F=0
pass() { printf '  \033[32m✔\033[0m %s\n' "$1"; P=$((P+1)); }
warn() { printf '  \033[33m!\033[0m %s\n' "$1"; W=$((W+1)); }
fail() { printf '  \033[31m✘\033[0m %s\n' "$1"; F=$((F+1)); }
sec()  { printf '\n\033[1m%s\033[0m\n' "$1"; }

sec "시스템"
. /etc/os-release
[ "$VERSION_ID" = "22.04" ] && pass "$PRETTY_NAME" || fail "Ubuntu 22.04 필요 (현재 $PRETTY_NAME)"
grep -qi microsoft /proc/version && pass "WSL2 커널 $(uname -r)" || warn "WSL이 아님"
n=$(nproc); [ "$n" -ge 4 ] && pass "CPU ${n}코어" || warn "CPU ${n}코어 (4코어 이상 권장)"
mem=$(awk '/MemTotal/{printf "%d", $2/1024/1024+0.5}' /proc/meminfo)
[ "$mem" -ge 7 ] && pass "WSL 메모리 ${mem}GB" || warn "WSL 메모리 ${mem}GB (8GB 이상 권장, 설치 가이드의 .wslconfig 참고)"
case "$REPO" in /mnt/*) warn "코드가 Windows 드라이브에 있음 ($REPO) → ~/unbolt 권장" ;; *) pass "코드 위치 $REPO" ;; esac
# ROS Humble is built for the system Python 3.10; scripts with "#!/usr/bin/env python3"
# (rosbridge, several Nav2/MoveIt tools) die if conda or a venv puts another python3 first.
py3=$(command -v python3)
if [ "$py3" = /usr/bin/python3 ]; then pass "python3 = /usr/bin/python3"
else fail "python3가 $py3 (conda/venv) → rosbridge 등이 죽음. 'conda deactivate' 또는 'conda config --set auto_activate_base false'"; fi

sec "화면 (WSLg)"
if [ -n "$WAYLAND_DISPLAY$DISPLAY" ] && [ -d /mnt/wslg ]; then pass "WSLg DISPLAY=$DISPLAY"; else fail "WSLg 없음 (Windows 10 21H2 이하 또는 'wsl --update' 필요)"; fi
if command -v glxinfo >/dev/null; then
  r=$(glxinfo -B 2>/dev/null | awk -F': ' '/OpenGL renderer/{print $2}')
  case "$r" in
    *D3D12*) pass "GPU 가속 OpenGL: $r" ;;
    *llvmpipe*) warn "소프트웨어 렌더링: $r (동작은 하지만 느림, GPU 드라이버 업데이트 권장)" ;;
    "") fail "OpenGL 컨텍스트를 만들 수 없음" ;;
    *) pass "OpenGL: $r" ;;
  esac
else warn "glxinfo 없음 (sudo apt install mesa-utils)"; fi

sec "ROS 2"
if [ -f /opt/ros/humble/setup.bash ]; then
  pass "ROS 2 Humble 설치됨"
  set +u; source /opt/ros/humble/setup.bash
  [ -f "$REPO/ros2_ws/install/setup.bash" ] && source "$REPO/ros2_ws/install/setup.bash"
  for p in rviz2 slam_toolbox nav2_bringup moveit_ros_move_group moveit_configs_utils rosbridge_server xacro teleop_twist_keyboard cv_bridge; do
    ros2 pkg prefix "$p" >/dev/null 2>&1 && pass "$p" || fail "$p 없음 (install_unbolt.sh 다시 실행)"
  done
else
  fail "/opt/ros/humble 없음 (install_unbolt.sh 실행)"
fi

sec "Python"
py() { python3 -c "$1" 2>/dev/null; }
v=$(py 'import mujoco; print(mujoco.__version__)'); [ "$v" = "3.12.0" ] && pass "mujoco $v" || fail "mujoco 3.12.0 필요 (현재: ${v:-없음})"
v=$(py 'import numpy; print(numpy.__version__)'); case "$v" in 1.*) pass "numpy $v" ;; "") fail "numpy 없음" ;; *) fail "numpy $v → 2.x는 ROS Humble과 충돌 (pip3 install --user 'numpy<2')" ;; esac
v=$(py 'import cv2; cv2.aruco.Dictionary_get; print(cv2.__version__)'); [ -n "$v" ] && pass "OpenCV $v (aruco)" || fail "OpenCV aruco 모듈 없음 (pip opencv가 apt 버전을 가리는지 확인)"
v=$(py 'import anthropic; print(anthropic.__version__)'); [ -n "$v" ] && pass "anthropic $v" || fail "anthropic 없음"
v=$(py 'import brotli; print(brotli.__version__)'); case "$v" in 1.0.*|"") fail "Brotli ${v:-없음} → pip3 install --user --upgrade Brotli" ;; *) pass "Brotli $v" ;; esac
v=$(py 'import torch; print(torch.__version__)'); [ -n "$v" ] && pass "torch $v (심화 모듈 5)" || warn "torch 없음 (심화 모듈 5 VLA에만 필요: pip3 install --user torch --index-url https://download.pytorch.org/whl/cpu)"

sec "UNBOLT 코드"
for d in openarm_mujoco openarm_description; do
  [ -d "$REPO/third_party/$d/.git" ] && pass "third_party/$d @ $(git -C "$REPO/third_party/$d" rev-parse --short HEAD)" || fail "third_party/$d 없음"
done
if ros2 pkg prefix unbolt_mujoco_bridge >/dev/null 2>&1; then pass "워크스페이스 빌드됨"; else fail "워크스페이스 미빌드 (cd $REPO/ros2_ws && colcon build --symlink-install)"; fi
grep -q '# >>> unbolt >>>' ~/.bashrc && pass "~/.bashrc 설정" || warn "~/.bashrc 설정 없음"
out=$(cd /tmp && timeout 60 python3 - "$REPO/models/scene.xml" 2>&1 <<'EOF'
import sys, time, mujoco
m = mujoco.MjModel.from_xml_path(sys.argv[1]); d = mujoco.MjData(m)
t = time.time(); mujoco.mj_step(m, d, 500); sim = 500 * m.opt.timestep / (time.time() - t)
r = mujoco.Renderer(m, 240, 320); mujoco.mj_forward(m, d); r.update_scene(d); img = r.render()
print(f"OK nbody={m.nbody} sim={sim:.0f}x img_mean={img.mean():.0f}")
EOF
)
case "$out" in
  *OK*) pass "MuJoCo 월드 로드 + 오프스크린 렌더링 (${out#*OK })" ;;
  *) fail "MuJoCo 월드 로드/렌더링 실패: $(echo "$out" | tail -1)" ;;
esac

sec "LLM (모듈 4, 선택)"
if [ -f ~/.unbolt_key ]; then source ~/.unbolt_key; fi
k="${ANTHROPIC_API_KEY:-}"
if [ -z "$k" ]; then warn "ANTHROPIC_API_KEY 없음 → llm:=scripted 모드로 실습 가능 (setup_api_key.sh)"
elif [[ "$k" == sk-ant-* ]]; then pass "ANTHROPIC_API_KEY 설정됨 (${#k}자)"
else warn "ANTHROPIC_API_KEY 형식이 sk-ant- 로 시작하지 않음"; fi

printf '\n결과: \033[32m%d 통과\033[0m, \033[33m%d 경고\033[0m, \033[31m%d 실패\033[0m\n' $P $W $F
[ $F -eq 0 ]
