// 설치: WSL → Ubuntu → ROS 2 → 실습 코드, 환경 설정(~/.bashrc), 첫 실행
const L = require('./lib');
const { C, text, box, circleIcon, pill, card, callout, code, bullets, arrow, img, table, step, lab, quiz, summary, content } = L;
const TAG = '설치';

module.exports = function build() {
  let s;
  L.section('설치', '사전 준비 · 집에서 1~2시간', 'WSL · ROS 2 설치와\n실습 환경 설정', [
    'WSL2와 Ubuntu 22.04를 설치하고 리눅스 GUI 창을 띄운다',
    'ROS 2 Humble과 실습 패키지를 설치 스크립트 한 줄로 설치한다',
    '환경 설정(source, ~/.bashrc)이 무엇인지 알고 직접 확인·수정한다',
    '점검 스크립트로 "0 실패"를 확인하고 로봇과 대시보드를 처음 켜 본다',
  ], '이 장은 강습회 전에 집에서 따라 하는 설치 가이드(00_install.md)를 슬라이드로 옮긴 것입니다. 사전 공지와 함께 이 장을 나눠 주고, 1일차 08:30 헬프데스크에서도 이 순서로 도와줍니다. WSL이 아예 없는 노트북에서 시작한다고 가정합니다.');

  s = content('설치는 6단계, 집에서 1~2시간', TAG,
    '전체 흐름입니다. 시간이 가장 오래 걸리는 것은 4단계의 ROS 2 패키지 다운로드(약 4 GB)라서, 강의실 와이파이로 40명이 동시에 하면 몇 시간이 걸립니다. 그래서 집에서 끝내고 오게 합니다. 명령 앞의 PS>와 $를 구분하는 법을 꼭 짚어 주세요. 학생들이 가장 많이 헷갈리는 부분입니다.');
  const steps = [['FaWindows', 'Windows 점검', '10분'], ['FaLinux', 'WSL + Ubuntu', '20분 · 재부팅'], ['FaDownload', '실습 코드 받기', '5분'], ['FaTools', '설치 스크립트', '10~60분'], ['FaClipboardCheck', '환경 설정·점검', '5분'], ['FaPlay', '첫 실행', '5분']];
  steps.forEach(([ic, h, t], i) => {
    const x = 0.6 + i * 2.05;
    circleIcon(s, ic, x + 0.45, 1.5, 0.9, [C.accent5, C.accent3, C.accent2, C.accent1, C.text1, C.accent2][i]);
    text(s, `${i + 1}. ${h}`, { x, y: 2.5, w: 1.9, h: 0.45, fontSize: 15, bold: true, align: 'center' });
    text(s, t, { x, y: 2.95, w: 1.9, h: 0.4, fontSize: 13, color: C.text2, align: 'center' });
    if (i < 5) arrow(s, x + 1.45, 1.95, x + 2.4, 1.95);
  });
  text(s, '명령 앞의 표시로 어디에서 칠지 구분합니다', { x: 0.6, y: 3.6, w: 12.1, h: 0.45, fontSize: 17, bold: true });
  text(s, 'Windows PowerShell', { x: 0.6, y: 4.1, w: 5.95, h: 0.4, fontSize: 15, bold: true, color: C.accent3 });
  code(s, 'PS> wsl -l -v', 0.6, 4.5, 5.95, 0.6, 15);
  text(s, 'Ubuntu 터미널 ($는 치지 않는다)', { x: 6.75, y: 4.1, w: 5.95, h: 0.4, fontSize: 15, bold: true, color: C.accent2 });
  code(s, '$ ros2 node list', 6.75, 4.5, 5.95, 0.6, 15);
  callout(s, 'warn', 0.6, 5.35, 12.1, 1.35, '강의실 와이파이로 40명이 동시에 받으면 몇 시간 걸린다. 꼭 집에서 끝내고, 마지막 점검 화면("0 실패")을 캡처해 제출하기.');

  s = content('WSL이란? Windows 안의 진짜 리눅스', TAG,
    'WSL2는 Windows 안에서 진짜 리눅스 커널을 돌립니다. 가상머신처럼 화면을 따로 띄우지 않고, 리눅스 프로그램의 창(MuJoCo, RViz)이 WSLg를 통해 Windows 창처럼 뜹니다. 두 세계는 파일(/mnt/c)과 네트워크(localhost)로 연결되어 있어서, Ubuntu에서 켠 대시보드를 Windows 브라우저로 볼 수 있습니다.');
  [['ROS 2 · MuJoCo · UNBOLT 코드', C.accent1, C.background1], ['Ubuntu 22.04 (리눅스)', C.accent2, C.background1], ['WSL2: 진짜 리눅스 커널 + WSLg', C.accent3, C.background1], ['Windows 10 / 11', C.accent5, C.text1]].forEach(([t, f, col], i) => {
    const y = 1.5 + i * 0.95;
    box(s, 0.6, y, 6.0, 0.78, f);
    text(s, t, { x: 0.85, y, w: 5.6, h: 0.78, fontSize: 17, bold: true, color: col, valign: 'middle' });
  });
  callout(s, 'analogy', 0.6, 5.45, 6.0, 1.25, 'Windows라는 집 안에 리눅스 방을 하나 들인 것. 방 사이에 문(파일, localhost)이 있다.');
  [['FaBolt', '가상머신보다 가볍다', '몇 초 만에 켜지고, 메모리는 필요한 만큼만 쓴다. GPU·Docker·VM 설정이 필요 없다.'],
    ['FaDesktop', '리눅스 창이 Windows에 뜬다 (WSLg)', 'MuJoCo 뷰어와 RViz가 일반 Windows 창처럼 작업 표시줄에 나타난다.'],
    ['FaGlobe', '파일과 네트워크가 이어져 있다', 'Ubuntu에서 Windows C: 드라이브는 /mnt/c. Ubuntu에서 켠 서버는 Windows 브라우저의 localhost로 열린다.']].forEach(([ic, h, b], i) => {
    card(s, { x: 6.9, y: 1.5 + i * 1.77, w: 5.8, h: 1.6, head: h, body: b, iconName: ic, accent: [C.accent1, C.accent3, C.accent2][i], headSize: 16, bodySize: 14 });
  });

  s = content('1단계. Windows 점검 (10분)', TAG,
    'WSL 설치가 실패하는 원인 1위는 밀린 Windows 업데이트, 2위는 꺼진 가상화입니다. 세 가지를 먼저 확인하게 하세요. 코드를 ZIP으로 받았다면 check_windows.ps1로 한 번에 점검할 수 있습니다(PowerShell 실행 정책 때문에 -ExecutionPolicy Bypass가 필요).');
  [['FaWindows', 'Windows 버전', 'Win + R → winver\nWindows 11, 또는 Windows 10 21H2 (빌드 19044) 이상\n아니면 Windows 업데이트부터'],
    ['FaMicrochip', '가상화: 사용', 'Ctrl + Shift + Esc → 성능 → CPU\n"가상화: 사용"이면 통과\n"사용 안 함"이면 다음 장 (BIOS)'],
    ['FaMemory', '메모리 · 디스크', 'RAM 16 GB 권장\n(8 GB면 WSL 메모리 설정 필요)\nC: 드라이브 여유 30 GB 이상']].forEach(([ic, h, b], i) => {
    card(s, { x: 0.6 + i * 4.13, y: 1.5, w: 3.85, h: 2.45, head: h, body: b, iconName: ic, accent: [C.accent3, C.accent1, C.accent2][i], bodySize: 14 });
  });
  code(s, 'PS> powershell -ExecutionPolicy Bypass -File .\\check_windows.ps1\n== Windows\n  [OK]   Microsoft Windows 11 Home (빌드 26200)\n== 하드웨어\n  [OK]   RAM 32GB      [OK] C: 여유 216GB\n  [OK]   가상화 사용 중 (하이퍼바이저 동작)\n== WSL\n  [주의] WSL이 아직 설치되지 않았습니다 (정상)\n결과: 실습 가능 (주의 1개)', 0.6, 4.2, 7.8, 2.5, 12);
  callout(s, 'tip', 8.7, 4.2, 4.0, 2.5, '자동 점검 (선택): 압축을 푼 폴더의 workshop/setup에서 실행. [실패] 줄이 있으면 그 안내부터 해결한다.');

  s = content('가상화가 꺼져 있다면: BIOS에서 켜기', TAG,
    '작업 관리자에 "가상화: 사용 안 함"이 나오는 학생만 합니다. BIOS 화면은 제조사마다 다르니 메뉴 이름(Virtualization, VT-x, SVM)으로 찾으라고 하세요. 다른 설정은 건드리지 않게 주의시킵니다.');
  table(s, [['제조사', 'BIOS 키 (로고가 보일 때 연타)'], ['삼성 · LG · Dell · Acer', 'F2'], ['Lenovo', 'F1 또는 F2 (일부는 옆면 Novo 버튼)'], ['HP', 'Esc → F10'], ['ASUS', 'F2 또는 Del'], ['MSI', 'Del']], 0.6, 1.5, 5.4, [2.3, 3.1], 14);
  callout(s, 'tip', 0.6, 4.4, 5.4, 2.3, '키를 모르겠으면 Windows에서: 설정 → 시스템 → 복구 → 고급 시작 → 지금 다시 시작 → 문제 해결 → 고급 옵션 → UEFI 펌웨어 설정');
  [['BIOS 들어가기', '재부팅하면서 왼쪽 표의 키를 연타'],
    ['가상화 항목 찾기', 'Advanced / Configuration / Security 메뉴에서\nIntel: Virtualization Technology, VT-x  ·  AMD: SVM Mode'],
    ['Enabled로 바꾸고 저장', 'Save & Exit (보통 F10) → 재부팅'],
    ['다시 확인', '작업 관리자 → 성능 → CPU → "가상화: 사용"']].forEach(([h, b], i) => step(s, i + 1, h, b, 6.4, 1.55 + i * 1.3, 6.3, 0.75));

  s = content('2단계. WSL + Ubuntu 22.04 설치 (20분)', TAG,
    '명령 한 줄이 WSL 기능, 리눅스 커널, Ubuntu 22.04를 모두 설치합니다. 반드시 관리자 권한 PowerShell에서 실행합니다. 재부팅 후 Ubuntu 창이 자동으로 열리며 설치가 이어지는데, 이때 몇 분 걸리니 창을 닫지 말라고 하세요.');
  lab(s, {
    cmd: '# 시작 메뉴 → PowerShell 검색 → "관리자 권한으로 실행"\nPS> wsl --install -d Ubuntu-22.04\n\n요청한 작업이 성공했습니다.\n시스템을 다시 시작해야 변경 내용이 적용됩니다.\n\n# → 재부팅. Ubuntu 창이 저절로 열리고 설치가 이어진다\n#   (안 열리면 시작 메뉴 → Ubuntu 22.04)',
    cmdH: 2.9, cmdSize: 13,
    explain: ['WSL 기능 + 리눅스 커널 + Ubuntu 22.04를 한 번에 설치한다', '이미 다른 Ubuntu가 있어도 22.04가 추가로 설치된다. 기본으로 쓰려면: wsl --set-default Ubuntu-22.04', '설치 중 "Installing, this may take a few minutes..."가 10분 넘게 멈추면 창을 닫고 wsl --shutdown 후 다시 연다'],
    ok: 'Ubuntu 창에\n"Enter new UNIX username:"\n이 나온다 → 다음 장',
    fail: '도움말만 나옴 → 오래된 Windows 10. Windows 업데이트, 또는 Store에서 WSL과 Ubuntu 22.04.5 LTS 설치\n0x80370102 → BIOS 가상화',
  });

  s = content('리눅스 사용자 만들기', TAG,
    '처음 한 번만 나오는 화면입니다. 비밀번호를 칠 때 화면에 아무것도 안 나와서 키보드가 고장 난 줄 아는 학생이 많습니다. 정상이라고 미리 말해 주세요. 이 비밀번호는 sudo(관리자 권한)에 계속 쓰입니다.');
  code(s, 'Installing, this may take a few minutes...\nPlease create a default UNIX user account.\n\nEnter new UNIX username: student\nNew password:             ← 입력해도 안 보임 (정상)\nRetype new password:\npasswd: password updated successfully\n\nstudent@my-laptop:~$      ← 이게 나오면 성공', 0.6, 1.5, 6.3, 3.05, 13);
  callout(s, 'why', 0.6, 4.8, 6.3, 1.9, 'sudo는 "관리자 권한으로 실행"이다. 프로그램 설치(apt install)처럼 시스템을 바꾸는 명령에 필요해서, 이 비밀번호를 설치 중에 여러 번 묻는다.');
  card(s, { x: 7.2, y: 1.5, w: 5.5, h: 1.6, head: '사용자 이름', body: '영어 소문자로 (예: student, hong)\n한글 · 공백 · 대문자는 안 된다', iconName: 'FaUserPlus', accent: C.accent3, headSize: 16, bodySize: 14 });
  card(s, { x: 7.2, y: 3.25, w: 5.5, h: 1.6, head: '비밀번호', body: '화면에 *조차 안 나오는 게 정상. 그대로 치고 Enter.\nWindows 비밀번호와 달라도 된다. 꼭 기억하기', iconName: 'FaKey', accent: C.accent1, headSize: 16, bodySize: 14 });
  callout(s, 'fail', 7.2, 5.0, 5.5, 1.7, '비밀번호를 잊었다 → PowerShell에서 wsl -d Ubuntu-22.04 -u root 로 들어가 passwd <이름> 실행 후 exit');

  s = content('WSL 확인과 메모리 설정', TAG,
    'VERSION이 2인지 꼭 확인합니다. WSL1은 리눅스 커널이 없어 ROS가 제대로 돌지 않습니다. 8 GB 노트북은 WSL이 4 GB만 쓰게 되어 모듈 3~4에서 멈출 수 있으니 .wslconfig로 6 GB로 올립니다. 메모장이 .txt를 붙이지 않게 "파일 형식: 모든 파일"로 저장하라고 하세요.');
  code(s, 'PS> wsl --update\nPS> wsl -l -v\n  NAME            STATE           VERSION\n* Ubuntu-22.04    Running         2', 0.6, 1.5, 6.0, 1.75, 14);
  callout(s, 'ok', 0.6, 3.45, 6.0, 1.3, 'VERSION이 2. (1이면 PS> wsl --set-version Ubuntu-22.04 2)');
  callout(s, 'tip', 0.6, 4.95, 6.0, 1.75, 'Ubuntu 다시 열기: 시작 메뉴 → Ubuntu 22.04, 또는 Windows Terminal의 탭 옆 ∨ → Ubuntu-22.04');
  text(s, '메모리가 8 GB인 노트북만', { x: 6.9, y: 1.45, w: 5.8, h: 0.45, fontSize: 17, bold: true });
  code(s, '# 메모장으로 만들기 (.txt가 붙지 않게)\n# C:\\Users\\<윈도우사용자>\\.wslconfig\n[wsl2]\nmemory=6GB\nswap=8GB\n\nPS> wsl --shutdown    # 적용 → Ubuntu 다시 열기', 6.9, 1.95, 5.8, 2.8, 13);
  callout(s, 'why', 6.9, 4.95, 5.8, 1.75, 'WSL은 기본으로 Windows 메모리의 절반만 쓴다. 8 GB면 4 GB라 Nav2와 MoveIt을 함께 켤 때 멈출 수 있다. 16 GB 이상이면 건너뛴다.');

  s = content('GUI 창이 뜨는지 확인: xeyes', TAG,
    'WSLg가 제대로 동작하는지 가장 간단하게 확인하는 방법입니다. 여기서 창이 뜨면 MuJoCo와 RViz도 뜹니다. 창이 검거나 깨지면 대부분 그래픽 드라이버 문제입니다. 체크포인트 1.');
  lab(s, {
    cmd: '$ sudo apt update && sudo apt install -y x11-apps\n$ xeyes\n\n# 끄기: 창을 닫거나 터미널에서 Ctrl + C',
    cmdH: 1.7, cmdSize: 14,
    explain: ['WSLg는 리눅스 프로그램의 창을 Windows 바탕화면에 띄워 준다', 'MuJoCo 뷰어와 RViz도 같은 길로 뜬다', '처음 sudo를 쓰면 2단계에서 만든 비밀번호를 묻는다'],
    ok: '눈알 두 개가 마우스를 따라다니는 창이 뜬다\n\n✅ 체크포인트 1\nwsl -l -v에 VERSION 2, xeyes 창이 뜬다',
    fail: '창이 안 뜨거나 검다 → Windows에서 그래픽 드라이버 업데이트 → PS> wsl --shutdown → 다시. troubleshooting.md "GUI 창이 안 뜬다"',
  });

  s = content('3단계. 실습 코드 받기 (5분)', TAG,
    '코드 위치가 중요합니다. Windows 드라이브(/mnt/c)에 두면 리눅스와 Windows 파일 시스템을 오가느라 빌드와 실행이 몇 배 느려집니다. 교재의 모든 명령이 ~/unbolt를 쓰므로 이름도 그대로 맞추게 하세요.');
  text(s, '방법 A. git clone (권장)', { x: 0.6, y: 1.45, w: 7.4, h: 0.4, fontSize: 16, bold: true });
  code(s, '$ sudo apt install -y git\n$ git clone <강사가 안내한 저장소 주소> ~/unbolt', 0.6, 1.9, 7.4, 0.95, 13);
  text(s, '방법 B. ZIP 파일 (Windows 다운로드 폴더에 풀었다면)', { x: 0.6, y: 3.0, w: 7.4, h: 0.4, fontSize: 16, bold: true });
  code(s, '$ ls /mnt/c/Users                  # 윈도우 사용자 이름 확인\n$ cp -r /mnt/c/Users/<윈도우사용자>/Downloads/<폴더> ~/unbolt\n$ ls ~/unbolt\nREADME.md  docs  models  ros2_ws  workshop', 0.6, 3.45, 7.4, 1.4, 12);
  code(s, '# 두 세계 사이 오가기\nUbuntu에서 본 Windows C:  →  /mnt/c\nWindows 탐색기에서 Ubuntu →  \\\\wsl$\\Ubuntu-22.04\\home\\<이름>\n지금 폴더를 탐색기로 열기 →  $ explorer.exe .', 0.6, 5.05, 7.4, 1.65, 12);
  callout(s, 'why', 8.3, 1.5, 4.4, 2.6, '코드는 Ubuntu 홈의 ~/unbolt에 둔다. /mnt/c(Windows 드라이브)에 두면 빌드와 실행이 몇 배 느려진다.');
  callout(s, 'warn', 8.3, 4.3, 4.4, 2.4, '폴더 이름은 ~/unbolt로. 교재의 명령이 모두 이 경로를 쓴다. 다른 곳에 두었다면 "환경 설정" 장의 직접 넣기를 따른다.');

  s = content('4단계. 설치 스크립트 한 줄 (10~60분)', TAG,
    '설치 스크립트가 ROS 2부터 빌드, 환경 설정까지 한 번에 합니다. 처음에 sudo 비밀번호를 한 번 묻고, 그다음은 기다리면 됩니다. 새로 설치한 Ubuntu 22.04에서 빠른 유선망 기준 약 10분(apt 패키지 1,300여 개)이었습니다. 끊기면 같은 명령을 다시 치면 이어서 합니다.');
  code(s, '$ bash ~/unbolt/workshop/setup/install_unbolt.sh\n[sudo] password for student:        ← 2단계에서 만든 비밀번호', 0.6, 1.5, 12.1, 0.95, 14);
  table(s, [['단계', '하는 일', '시간'],
    ['0', 'Ubuntu 22.04인지, 디스크 여유, 코드 위치 확인', ''],
    ['1', '로캘(en_US.UTF-8), curl · git · pip 같은 기본 도구', '1분'],
    ['2', 'ROS 2 apt 저장소 등록 (ros2-apt-source)', '1분'],
    ['3', 'ROS 2 Humble Desktop, Nav2, slam_toolbox, MoveIt 2, rosbridge', '20~50분'],
    ['4', 'Python 패키지: mujoco, anthropic, Brotli, numpy<2', '2분'],
    ['5', 'OpenArm 로봇 모델 받기 (고정 커밋)', '2분'],
    ['6', 'colcon build, ~/.bashrc에 환경 설정 추가', '1분'],
    ['7', '점검 (check_env.sh)', '1분']], 0.6, 2.7, 8.0, [0.8, 5.8, 1.4], 13);
  callout(s, 'tip', 8.9, 2.7, 3.8, 1.95, '중간에 끊겨도 같은 명령을 다시 실행하면 이어서 한다 (끝난 단계는 건너뜀).');
  callout(s, 'warn', 8.9, 4.85, 3.8, 1.85, '전원을 연결하고 절전 모드를 끄기. 빨간 ✘로 멈추면 그 메시지로 troubleshooting.md 검색.');

  s = content('ROS 2는 이렇게 설치된다 (스크립트 속 명령)', TAG,
    '스크립트가 실제로 하는 일을 줄여서 보여 줍니다. ROS 2 공식 문서의 Ubuntu 설치 방법과 같습니다. 직접 따라 치고 싶은 학생이나 스크립트가 실패한 학생은 00_install.md 4장의 "실제로 실행하는 명령"을 그대로 따라 하면 됩니다. 마지막 talker 예제로 ROS 2가 동작하는지 확인할 수 있습니다(Ctrl+C로 종료).');
  code(s, '# 1) 로캘과 기본 도구\n$ sudo apt update\n$ sudo apt install -y locales software-properties-common curl git python3-pip\n$ sudo locale-gen en_US en_US.UTF-8\n$ sudo add-apt-repository -y universe\n\n# 2) ROS 2 apt 저장소 등록 (curl로 받은 ros2-apt-source 패키지)\n$ sudo dpkg -i /tmp/ros2-apt-source.deb\n\n# 3) ROS 2 Humble + 실습 패키지\n$ sudo apt update && sudo apt upgrade -y\n$ sudo apt install -y ros-humble-desktop ros-dev-tools \\\n    ros-humble-navigation2 ros-humble-nav2-bringup ros-humble-slam-toolbox \\\n    ros-humble-moveit ros-humble-rosbridge-server ...\n\n# 4) 동작 확인\n$ source /opt/ros/humble/setup.bash\n$ ros2 run demo_nodes_cpp talker      # Publishing: "Hello World: 1" ...', 0.6, 1.5, 8.1, 5.2, 12);
  [['FaBook', 'apt 저장소', 'Ubuntu에게 "ROS 패키지는 여기서 받아"라고 알려 준다. 없으면 Unable to locate package'],
    ['FaCube', 'ros-humble-desktop', 'ROS 2 핵심 + RViz + 예제. 실습용 Nav2 · MoveIt · rosbridge를 함께 설치'],
    ['FaFolderOpen', '/opt/ros/humble', '설치되는 위치. source해야 ros2 명령이 생긴다 (다음 장)']].forEach(([ic, h, b], i) => {
    card(s, { x: 9.0, y: 1.5 + i * 1.77, w: 3.7, h: 1.6, head: h, body: b, iconName: ic, accent: [C.accent3, C.accent1, C.accent2][i], headSize: 15, bodySize: 13 });
  });

  s = content('Python 패키지: 버전을 고정하는 이유', TAG,
    '버전 고정은 "왜 최신으로 안 깔아요?"라는 질문에 대한 답입니다. 특히 numpy 2와 conda가 실제 강습회에서 자주 문제를 일으킵니다. conda가 있는 학생은 auto_activate_base를 끄게 하면 이후 문제가 거의 사라집니다.');
  code(s, '$ pip3 install --user "mujoco==3.12.0" "anthropic==2.3.0" "Brotli>=1.1" "numpy<2"', 0.6, 1.5, 12.1, 0.65, 14);
  table(s, [['패키지', '고정', '이유'],
    ['mujoco', '3.12.0', '교재·코드와 같은 버전. 뷰어와 API 동작이 같다'],
    ['anthropic', '2.3.0', '모듈 4의 LLM 코드가 쓰는 SDK 버전'],
    ['Brotli', '1.1 이상', 'Ubuntu 기본 1.0.9는 SDK의 HTTP 라이브러리와 맞지 않아 모든 API 호출이 APIConnectionError'],
    ['numpy', '2 미만', 'ROS Humble의 cv_bridge는 numpy 1.x로 빌드됨. 2.x가 깔리면 카메라 노드가 import 오류'],
    ['OpenArm 모델', '고정 커밋', '원본 저장소가 바뀌어도 관절 이름·메시 경로가 그대로']], 0.6, 2.4, 12.1, [2.0, 1.6, 8.5], 14);
  callout(s, 'why', 0.6, 5.0, 5.95, 1.7, '--user: sudo 없이 내 홈(~/.local)에 설치한다. Ubuntu 시스템 파이썬은 건드리지 않는다.');
  callout(s, 'warn', 6.75, 5.0, 5.95, 1.7, 'conda가 켜져 있으면(프롬프트 앞 (base)) ROS가 깨진다 → conda deactivate. 아예 끄기: auto_activate_base false');

  s = content('환경 설정: source와 ~/.bashrc', TAG,
    '"Package not found"의 원인을 이해시키는 장입니다. ros2 명령은 source로 불러온 곳의 패키지만 압니다. ROS 기본 패키지(/opt/ros/humble)와 우리가 빌드한 패키지(ros2_ws/install)를 둘 다 불러와야 합니다. ~/.bashrc는 새 터미널이 열릴 때마다 자동으로 실행되므로, 여기에 넣어 두면 매번 칠 필요가 없습니다. 실제 파일에는 ~/unbolt 대신 /home/<이름>/unbolt 같은 전체 경로가 들어갑니다.');
  table(s, [['불러오는 것', '그러면 생기는 것', '없으면'],
    ['source /opt/ros/humble/setup.bash', 'ros2 명령, ROS 기본 패키지 (Nav2, MoveIt, RViz)', 'ros2: command not found'],
    ['source ~/unbolt/ros2_ws/install/setup.bash', '우리가 빌드한 패키지 (unbolt_dashboard 등)', "Package 'unbolt_…' not found"],
    ['export UNBOLT_ROOT=~/unbolt', '모델 파일(models/) 위치', '로봇 모델을 못 찾음']], 0.6, 1.5, 12.1, [4.7, 4.4, 3.0], 14);
  code(s, '# ~/.bashrc 맨 끝 (설치 스크립트가 넣어 준다)\n# >>> unbolt >>>\nsource /opt/ros/humble/setup.bash\nsource ~/unbolt/ros2_ws/install/setup.bash\nexport UNBOLT_ROOT=~/unbolt\nexport ROS_DOMAIN_ID=${ROS_DOMAIN_ID:-0}\n[ -f ~/.unbolt_key ] && source ~/.unbolt_key   # API 키\n# <<< unbolt <<<', 0.6, 3.75, 7.2, 2.95, 13);
  callout(s, 'why', 8.1, 3.75, 4.6, 1.4, '~/.bashrc는 새 터미널이 열릴 때마다 자동으로 실행되는 파일이다.');
  callout(s, 'analogy', 8.1, 5.3, 4.6, 1.4, '주소록에 등록하기: 등록한 곳의 이름만 찾을 수 있다.');

  s = content('환경 설정 확인하고, 없으면 직접 넣기', TAG,
    '설치 스크립트를 썼다면 확인만 하면 됩니다. 코드를 ~/unbolt가 아닌 곳에 두었거나 스크립트 없이 설치했다면 아래처럼 직접 넣습니다. REPO에 실제 코드 위치를 넣으세요. 가장 흔한 실수는 이미 열려 있던 터미널에서 바로 실행하는 것입니다. .bashrc는 터미널이 열릴 때만 읽으므로 source ~/.bashrc를 하거나 새 터미널을 엽니다.');
  text(s, '확인 (새 터미널에서)', { x: 0.6, y: 1.45, w: 7.6, h: 0.4, fontSize: 16, bold: true });
  code(s, '$ grep -A5 ">>> unbolt" ~/.bashrc       # 블록이 있나\n$ ros2 pkg prefix unbolt_dashboard       # 패키지를 찾나\n/home/student/unbolt/ros2_ws/install/unbolt_dashboard\n$ echo $UNBOLT_ROOT\n/home/student/unbolt', 0.6, 1.9, 7.6, 1.55, 12);
  text(s, '없거나 코드를 다른 곳에 두었다면: 직접 넣기', { x: 0.6, y: 3.6, w: 7.6, h: 0.4, fontSize: 16, bold: true });
  code(s, '$ REPO=~/unbolt          # 실제 코드 위치로 바꾸기\n$ cat >> ~/.bashrc <<EOF\n# >>> unbolt >>>\nsource /opt/ros/humble/setup.bash\nsource $REPO/ros2_ws/install/setup.bash\nexport UNBOLT_ROOT=$REPO\n# <<< unbolt <<<\nEOF\n$ source ~/.bashrc       # 지금 열린 터미널에도 적용', 0.6, 4.05, 7.6, 2.65, 12);
  callout(s, 'fail', 8.5, 1.5, 4.2, 1.95, "Package 'unbolt_dashboard' not found → 이 블록이 없거나, 블록을 넣기 전에 연 터미널");
  callout(s, 'tip', 8.5, 3.6, 4.2, 1.65, '가장 쉬운 방법: 설치 스크립트를 다시 실행하면 블록을 새로 써 준다 (두 번 들어가지 않음)');
  callout(s, 'warn', 8.5, 5.4, 4.2, 1.3, '이미 열린 터미널은 .bashrc를 다시 읽지 않는다');

  s = content('빌드: colcon build는 언제 다시 하나', TAG,
    '설치 스크립트가 한 번 빌드해 두었으므로 평소에는 다시 빌드할 일이 거의 없습니다. --symlink-install 덕분에 기존 파이썬·launch·설정 파일을 고치면 바로 반영됩니다. 새 파일이나 새 실행 이름(setup.py의 entry point)을 추가했을 때만 다시 빌드하고 source합니다.');
  code(s, '$ cd ~/unbolt/ros2_ws\n$ colcon build --symlink-install\nSummary: 7 packages finished [40s]\n$ source install/setup.bash     # 새 패키지·새 실행 이름이 생겼을 때', 0.6, 1.5, 12.1, 1.5, 14);
  table(s, [['이럴 때', '다시 빌드?'],
    ['기존 Python 코드, launch, config, 웹 파일을 고침', '필요 없음 (바로 반영)'],
    ['새 파일(노드, launch 파일)을 추가함', '빌드'],
    ['setup.py에 실행 이름(entry point)을 추가함', '빌드 + source'],
    ['새 패키지를 만듦', '빌드 + source (또는 새 터미널)']], 0.6, 3.25, 7.6, [5.0, 2.6], 14);
  callout(s, 'analogy', 8.5, 3.25, 4.2, 1.65, '--symlink-install = 원본으로 가는 바로가기. 복사본이 아니라서 원본을 고치면 바로 반영된다.');
  callout(s, 'fail', 8.5, 5.05, 4.2, 1.65, 'colcon: command not found → ros-dev-tools가 없음. 설치 스크립트를 다시 실행');

  s = content('5단계. 설치 점검', TAG,
    '새 터미널에서 실행합니다(또는 source ~/.bashrc 후). 수업 시작 전에도 모두 이 명령을 실행하게 합니다. API 키 없음 경고는 정상입니다. python3가 conda를 가리키면 실패로 나오는데, conda deactivate로 해결됩니다. ~/.bashrc 설정 경고가 나오면 환경 설정 장을 보게 하세요. 실패가 있는 학생은 조교가 바로 붙습니다.');
  code(s, '$ bash ~/unbolt/workshop/setup/check_env.sh\n\n시스템\n  ✔ Ubuntu 22.04.5 LTS\n  ✔ python3 = /usr/bin/python3\n화면 (WSLg)\n  ✔ GPU 가속 OpenGL: D3D12 (...)\nROS 2\n  ✔ ROS 2 Humble 설치됨  ✔ slam_toolbox  ✔ moveit ...\nPython\n  ✔ mujoco 3.12.0   ✔ numpy 1.21.5   ✔ anthropic 2.3.0\nUNBOLT 코드\n  ✔ 워크스페이스 빌드됨   ✔ ~/.bashrc 설정\n  ✔ MuJoCo 월드 로드 + 오프스크린 렌더링\n\n결과: 28 통과, 1 경고, 0 실패', 0.6, 1.5, 7.3, 5.2, 14);
  callout(s, 'ok', 8.2, 1.5, 4.5, 1.6, '마지막 줄이 "0 실패". 이 화면을 캡처해서 제출');
  callout(s, 'tip', 8.2, 3.3, 4.5, 1.6, '! 경고는 괜찮다 (API 키 없음 등)');
  callout(s, 'fail', 8.2, 5.1, 4.5, 1.6, '✘ 줄의 안내대로. conda면 conda deactivate, ~/.bashrc 설정 없음이면 환경 설정 장');

  s = content('6단계. 첫 실행: 로봇 몰아 보기', TAG,
    '설치가 끝났는지 마지막으로 확인합니다. 터미널 두 개가 필요합니다. teleop은 그 터미널 창을 클릭해 선택한 상태에서 키를 눌러야 합니다. 로봇이 움직이고 RViz의 LiDAR 점이 따라 바뀌면 설치가 모두 끝난 것입니다. 두 터미널 모두 Ctrl+C로 끕니다. 체크포인트 3.');
  code(s, '# 터미널 1 (켜 두기)\n$ ros2 launch unbolt_mujoco_bridge sim.launch.py\n\n# 터미널 2\n$ ros2 run teleop_twist_keyboard teleop_twist_keyboard\n#   i 앞   , 뒤   j / l 회전   k 정지', 0.6, 1.5, 6.6, 2.4, 13);
  callout(s, 'ok', 0.6, 4.1, 6.6, 1.25, 'MuJoCo 뷰어의 로봇이 움직이고 RViz의 빨간 LiDAR 점이 따라 바뀐다. ✅ 체크포인트 3');
  callout(s, 'fail', 0.6, 5.5, 6.6, 1.2, 'Package not found → 환경 설정 장. 키가 안 먹음 → teleop 터미널을 클릭한 뒤 누르기');
  img(s, 'step2_rviz.jpg', 7.5, 1.5, 5.2, 5.2, 'RViz에 보이는 로봇 모델과 LiDAR 점');

  s = content('대시보드도 미리 열어 보기', TAG,
    '모듈 4에서 쓰는 웹 대시보드를 설치 확인용으로 미리 열어 봅니다. 런처를 켜 두면 ROS가 꺼져 있어도 페이지가 뜨고, 연결 버튼으로 전체 시스템을 켭니다. 처음 켤 때는 Nav2와 MoveIt이 함께 떠서 25~60초 걸립니다. 런처 터미널은 끄지 않고 둡니다. API 키가 없으면 LLM 옵션을 대역(scripted)으로 고릅니다.');
  img(s, 'dashboard_off.png', 0.6, 1.5, 6.4, 4.0, 'ROS가 꺼져 있을 때의 대시보드: 연결 버튼과 시작 옵션');
  code(s, '$ ros2 run unbolt_dashboard dashboard_launcher\n# Windows 브라우저 → http://localhost:8080', 0.6, 5.7, 6.4, 1.0, 13);
  card(s, { x: 7.3, y: 1.5, w: 5.4, h: 2.05, head: '방법 1. 런처 (추천)', body: '런처를 켜 두고 브라우저에서 모드(작업 / 지도 만들기) 고르기 → 연결 → 25초쯤 뒤 "ROS 연결됨". 끌 때는 시스템 종료', iconName: 'FaPowerOff', accent: C.accent2, headSize: 16, bodySize: 14 });
  card(s, { x: 7.3, y: 3.7, w: 5.4, h: 1.65, head: '방법 2. launch로 직접', body: 'bringup.launch.py planner:=true dashboard:=true (키가 없으면 llm:=scripted)', iconName: 'FaTerminal', accent: C.accent3, headSize: 16, bodySize: 14 });
  callout(s, 'fail', 7.3, 5.5, 5.4, 1.2, '페이지가 안 열림 → 런처 터미널이 살아 있나. Package not found → 환경 설정');

  s = content('Claude API 키 (모듈 4 전까지, 선택)', TAG,
    '강사가 키를 나눠 주는 방식이면 4번만 합니다. 키는 setup_api_key.sh로 넣기 때문에 화면이나 셸 기록에 남지 않습니다. 키가 없어도 모듈 4의 로봇 동작은 llm:=scripted로 똑같이 실습할 수 있습니다.');
  [['Console 가입, 크레딧 5달러', 'console.anthropic.com → Billing (강습회 전체에 1~3달러 정도)'],
    ['월 사용 한도 5달러', 'Settings → Limits (실수로 많이 쓰는 것 방지)'],
    ['키 만들기', 'API Keys → Create Key → 복사 (sk-ant-로 시작, 이 화면에서만 보임)'],
    ['Ubuntu에 넣기', '오른쪽 명령. 붙여넣기는 Ctrl + Shift + V']].forEach(([h, b], i) => step(s, i + 1, h, b, 0.6, 1.55 + i * 1.3, 6.4, 0.7));
  code(s, '$ bash ~/unbolt/workshop/setup/setup_api_key.sh\nAPI 키:          ← 붙여넣고 Enter\n                    (화면에 안 보이는 게 정상)\n✔ ~/.unbolt_key 에 저장 (본인만 읽기 가능)\n✔ API 연결 확인', 7.3, 1.5, 5.4, 2.2, 13);
  callout(s, 'warn', 7.3, 3.9, 5.4, 1.6, 'API 키는 비밀번호다. 채팅방·과제·GitHub·스크린샷에 올리지 않기. 노출되면 Console에서 바로 Delete');
  callout(s, 'tip', 7.3, 5.65, 5.4, 1.05, '키가 없으면 llm:=scripted로 실습');

  s = content('설치에서 자주 막히는 곳', TAG,
    '설치 헬프데스크에서 실제로 자주 나오는 순서입니다. 자세한 것은 troubleshooting.md의 "Windows / WSL 설치", "설치 스크립트", "실행 공통" 표에 있습니다.');
  table(s, [['증상', '해결'],
    ['wsl --install이 도움말만 출력', 'Windows 업데이트, 또는 Store에서 WSL + Ubuntu 22.04 설치'],
    ['0x80370102 "가상 머신을 시작할 수 없습니다"', 'BIOS에서 가상화 켜기'],
    ['wsl -l -v에 VERSION 1', 'wsl --set-version Ubuntu-22.04 2'],
    ['xeyes · RViz 창이 안 뜨거나 검다', '그래픽 드라이버 업데이트 → wsl --shutdown'],
    ['Could not get lock /var/lib/dpkg/lock-frontend', 'Ubuntu 자동 업데이트 중. 5분 뒤 다시'],
    ['/bin/bash^M: bad interpreter', '스크립트 줄바꿈이 Windows 형식. git clone으로 다시 받기'],
    ['ros2: command not found', '새 터미널, 또는 source ~/.bashrc'],
    ["Package 'unbolt_…' not found", '~/.bashrc의 unbolt 블록 확인 (환경 설정 장)'],
    ['프롬프트 앞 (base), rclpy 오류', 'conda deactivate, conda config --set auto_activate_base false']], 0.6, 1.5, 12.1, [5.6, 6.5], 14);
  s.addNotes('^M(또는 $\'\\r\') 오류는 ZIP을 Windows 도구로 풀었거나 git의 autocrlf 때문에 생깁니다. troubleshooting.md에 sed로 고치는 방법도 있습니다. 표의 순서는 설치 단계 순서입니다.');

  summary('설치 한 장 요약', TAG, [
    ['FaWindows', 'Windows 점검 → WSL + Ubuntu 22.04', 'winver · 가상화 · 메모리 확인 → 관리자 PowerShell에서 wsl --install -d Ubuntu-22.04 → VERSION 2, xeyes'],
    ['FaDownload', '코드는 ~/unbolt, 설치는 스크립트 한 줄', 'install_unbolt.sh가 ROS 2, Python 패키지, 로봇 모델, 빌드, 환경 설정까지 한다'],
    ['FaCogs', '환경 설정 = source 두 개 + UNBOLT_ROOT', '~/.bashrc의 unbolt 블록. 없으면 Package not found. 열려 있던 터미널은 source ~/.bashrc'],
    ['FaClipboardCheck', '점검 → 첫 실행', 'check_env.sh "0 실패" → sim.launch.py + 키보드 주행'],
    ['FaGlobe', '대시보드', 'dashboard_launcher를 켜 두고 http://localhost:8080 → 연결'],
  ], '설치 장을 한 장으로 정리합니다. 다섯 줄이 모두 되면 1일차를 시작할 준비가 끝난 것입니다.');

  quiz('설치 셀프 체크', TAG, [
    ['"PS> wsl -l -v"와 "$ ros2 node list"는 각각 어디에서 실행하나?', 'PS>는 Windows PowerShell, $는 Ubuntu 터미널. 앞의 PS>와 $는 입력하지 않는다.'],
    ['코드를 /mnt/c(Windows 드라이브)가 아니라 ~/unbolt에 두는 이유는?', 'Windows 드라이브의 파일은 리눅스에서 접근이 느려 빌드와 실행이 몇 배 느려진다.'],
    ["새로 연 터미널에서 Package 'unbolt_dashboard' not found가 나온다. 무엇을 확인하나?", '~/.bashrc에 워크스페이스 source가 있는지(# >>> unbolt >>> 블록). 블록을 넣기 전에 연 터미널이면 source ~/.bashrc.'],
    ['기존 Python 파일을 고쳤을 때와 새 노드 파일을 추가했을 때, colcon build가 필요한 쪽은?', '새 파일을 추가했을 때. --symlink-install이라 기존 파일 수정은 바로 반영된다.'],
    ['8 GB 노트북에서 Nav2와 MoveIt을 함께 켜면 멈춘다. 무엇을 하나?', '.wslconfig에 memory=6GB, swap=8GB를 쓰고 wsl --shutdown 후 다시 연다.'],
  ], '답은 이 장의 슬라이드에 있습니다.');
};
