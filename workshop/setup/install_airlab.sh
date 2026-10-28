#!/bin/bash
# AIRLAB 실습 환경 일괄 설치 (WSL2 Ubuntu 22.04 안에서 실행)
#
#   bash ~/airlab/workshop/setup/install_airlab.sh
#
# 하는 일 (여러 번 실행해도 안전하다. 이미 된 단계는 건너뛴다):
#   1. 로캘, 기본 도구         4. Python 패키지 (MuJoCo, anthropic)
#   2. ROS 2 Humble apt 저장소  5. OpenArm 모델 받기 (고정 커밋)
#   3. ROS 2 + Nav2 + MoveIt   6. 워크스페이스 빌드, ~/.bashrc 설정
#
# 옵션: --skip-system  apt 단계(1~3)를 건너뜀 (sudo 없이 4~6만)
#       --system-only  apt 단계만 (root로 실행할 때)
set -eo pipefail

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
ROS_DISTRO=humble
OPENARM_MUJOCO_COMMIT=a3c8a57ec15d385e3c1dbd3fd090ee486b7f258c
OPENARM_DESCRIPTION_COMMIT=206eb8a4cf2e5e564536b4f5366ef369843a4aa7
ROS_APT_SOURCE_FALLBACK=1.3.0

DO_SYSTEM=1; DO_USER=1
for a in "$@"; do
  case "$a" in
    --skip-system) DO_SYSTEM=0 ;;
    --system-only) DO_USER=0 ;;
    *) echo "알 수 없는 옵션: $a"; exit 2 ;;
  esac
done

step() { printf '\n\033[1;36m[%s] %s\033[0m\n' "$1" "$2"; }
ok()   { printf '  \033[32m✔\033[0m %s\n' "$1"; }
warn() { printf '  \033[33m!\033[0m %s\n' "$1"; }
die()  { printf '\n\033[1;31m✘ %s\033[0m\n' "$1"; exit 1; }

if [ "$(id -u)" -eq 0 ]; then SUDO=""; else SUDO="sudo"; fi

# --------------------------------------------------------------------------
step 0 "환경 확인"
. /etc/os-release
[ "$VERSION_ID" = "22.04" ] || die "Ubuntu 22.04가 아닙니다 ($PRETTY_NAME). 'wsl --install -d Ubuntu-22.04'로 설치하세요."
ok "$PRETTY_NAME"
if grep -qi microsoft /proc/version; then ok "WSL 커널"; else warn "WSL이 아닌 것 같습니다 (네이티브 Ubuntu도 동작은 합니다)"; fi
case "$REPO" in
  /mnt/*) warn "코드가 Windows 드라이브($REPO)에 있습니다. 빌드/실행이 느려지니 ~/airlab 로 복사해서 쓰세요:
      cp -r \"$REPO\" ~/airlab && bash ~/airlab/workshop/setup/install_airlab.sh" ;;
  *) ok "코드 위치: $REPO" ;;
esac
[ -f "$REPO/models/scene.xml" ] || die "$REPO 에 models/scene.xml 이 없습니다. 저장소 전체를 받았는지 확인하세요."
avail_gb=$(df -BG --output=avail "$HOME" | tail -1 | tr -dc 0-9)
[ "$avail_gb" -ge 15 ] || die "디스크 여유 공간이 ${avail_gb}GB 입니다. 15GB 이상 필요합니다."
ok "디스크 여유 ${avail_gb}GB"

if [ "$DO_SYSTEM" = 1 ]; then
  if [ -n "$SUDO" ]; then
    echo "  (apt 설치에 sudo 비밀번호가 필요합니다. Ubuntu 처음 설치할 때 만든 비밀번호를 입력하세요.)"
    sudo -v || die "sudo 인증 실패"
  fi
  export DEBIAN_FRONTEND=noninteractive

  # ------------------------------------------------------------------------
  step 1 "로캘, 기본 도구"
  $SUDO apt-get update -q
  $SUDO apt-get install -y -q locales software-properties-common curl git ca-certificates \
    python3-pip mesa-utils
  if ! locale -a | grep -qi '^en_US.utf8$'; then
    $SUDO locale-gen en_US en_US.UTF-8
  fi
  $SUDO update-locale LC_ALL=en_US.UTF-8 LANG=en_US.UTF-8
  $SUDO add-apt-repository -y universe >/dev/null
  ok "로캘 en_US.UTF-8, universe 저장소"

  # ------------------------------------------------------------------------
  step 2 "ROS 2 apt 저장소"
  if dpkg -s ros2-apt-source >/dev/null 2>&1 || ls /etc/apt/sources.list.d/ros2*.list /etc/apt/sources.list.d/ros2*.sources >/dev/null 2>&1; then
    ok "이미 등록됨"
  else
    # ROS 공식 설치 문서 방식 (ros-apt-source 패키지가 키와 저장소를 함께 관리)
    ver=$(curl -fsSL https://api.github.com/repos/ros-infrastructure/ros-apt-source/releases/latest 2>/dev/null \
          | grep -F '"tag_name"' | awk -F'"' '{print $4}') || true
    [ -n "$ver" ] || { ver=$ROS_APT_SOURCE_FALLBACK; warn "최신 버전 조회 실패 (강의실 공유 IP의 GitHub API 제한일 수 있음) → $ver 사용"; }
    tmp=$(mktemp -d)
    curl -fL -o "$tmp/ros2-apt-source.deb" \
      "https://github.com/ros-infrastructure/ros-apt-source/releases/download/${ver}/ros2-apt-source_${ver}.${VERSION_CODENAME}_all.deb"
    $SUDO dpkg -i "$tmp/ros2-apt-source.deb"
    rm -rf "$tmp"
    ok "ros2-apt-source $ver"
  fi

  # ------------------------------------------------------------------------
  step 3 "ROS 2 $ROS_DISTRO + 실습 패키지 (10~30분, 약 3GB 다운로드)"
  $SUDO apt-get update -q
  $SUDO apt-get upgrade -y -q
  $SUDO apt-get install -y -q \
    ros-$ROS_DISTRO-desktop ros-dev-tools \
    ros-$ROS_DISTRO-xacro ros-$ROS_DISTRO-joint-state-publisher-gui ros-$ROS_DISTRO-teleop-twist-keyboard \
    ros-$ROS_DISTRO-slam-toolbox ros-$ROS_DISTRO-navigation2 ros-$ROS_DISTRO-nav2-bringup \
    ros-$ROS_DISTRO-moveit ros-$ROS_DISTRO-moveit-configs-utils ros-$ROS_DISTRO-control-msgs \
    ros-$ROS_DISTRO-rosbridge-server \
    python3-opencv python3-numpy python3-yaml
  ok "apt 패키지 설치 완료"
fi

if [ "$DO_USER" = 1 ]; then
  [ "$(id -u)" -ne 0 ] || die "4~6단계는 root가 아닌 일반 사용자로 실행하세요."
  [ -f /opt/ros/$ROS_DISTRO/setup.bash ] || die "ROS 2 $ROS_DISTRO 가 없습니다. --skip-system 없이 다시 실행하세요."

  # ------------------------------------------------------------------------
  step 4 "Python 패키지 (~/.local)"
  # numpy<2: ROS Humble의 cv_bridge 등은 시스템 numpy 1.x로 빌드되어 있다.
  # Brotli: Ubuntu 기본 1.0.9는 anthropic SDK와 충돌한다 (모든 호출이 연결 오류).
  pip3 install --user -q "mujoco==3.12.0" "anthropic==2.3.0" "Brotli>=1.1" "numpy<2"
  python3 -c "import mujoco, anthropic; print('  mujoco', mujoco.__version__, '/ anthropic', anthropic.__version__)"
  ok "Python 패키지"

  # ------------------------------------------------------------------------
  step 5 "OpenArm 모델 (third_party)"
  mkdir -p "$REPO/third_party"
  fetch() {  # fetch <dir> <url> <commit>
    local d="$REPO/third_party/$1"
    if [ ! -d "$d/.git" ]; then
      rm -rf "$d"
      git clone -q "$2" "$d"
    fi
    if [ "$(git -C "$d" rev-parse HEAD)" != "$3" ]; then
      git -C "$d" fetch -q origin
      git -C "$d" checkout -q "$3"
    fi
    ok "$1 @ ${3:0:8}"
  }
  fetch openarm_mujoco https://github.com/enactic/openarm_mujoco.git $OPENARM_MUJOCO_COMMIT
  fetch openarm_description https://github.com/enactic/openarm_description.git $OPENARM_DESCRIPTION_COMMIT
  # zip으로 받으면 심볼릭 링크가 일반 파일로 풀릴 수 있어 다시 만든다
  link="$REPO/ros2_ws/src/openarm_description"
  if [ ! -L "$link" ] || [ ! -e "$link/package.xml" ]; then
    rm -rf "$link"
    ln -s ../../third_party/openarm_description "$link"
  fi
  ok "ros2_ws/src/openarm_description -> third_party"

  # ------------------------------------------------------------------------
  step 6 "워크스페이스 빌드, ~/.bashrc"
  set +u
  source /opt/ros/$ROS_DISTRO/setup.bash
  (cd "$REPO/ros2_ws" && colcon build --symlink-install --event-handlers console_cohesion- 2>&1 | tail -5)
  [ -f "$REPO/ros2_ws/install/setup.bash" ] || die "colcon build 실패. 위 로그를 확인하세요."
  ok "colcon build"

  begin="# >>> airlab >>>"; end="# <<< airlab <<<"
  sed -i "/^$begin\$/,/^$end\$/d" ~/.bashrc
  cat >> ~/.bashrc <<EOF
$begin
source /opt/ros/$ROS_DISTRO/setup.bash
source "$REPO/ros2_ws/install/setup.bash"
export AIRLAB_ROOT="$REPO"
export ROS_DOMAIN_ID=\${ROS_DOMAIN_ID:-0}
[ -f ~/.airlab_key ] && source ~/.airlab_key   # ANTHROPIC_API_KEY (setup_api_key.sh)
$end
EOF
  ok "~/.bashrc 에 ROS/워크스페이스 설정 추가"

  step 7 "점검"
  AIRLAB_ROOT="$REPO" bash "$REPO/workshop/setup/check_env.sh" || true
  printf '\n\033[1;32m설치 끝.\033[0m 새 터미널을 열거나  source ~/.bashrc  를 실행한 뒤 실습을 시작하세요.\n'
fi
