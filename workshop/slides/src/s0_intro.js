// 오리엔테이션
const L = require('./lib');
const { C, text, box, circleIcon, pill, card, callout, code, bullets, arrow, img, table, step, flow, glossary, content } = L;
const SEC = '시작하기';

module.exports = function build() {
  let s;
  L.titleSlide(SEC, 'ROS 2 + MuJoCo로 만드는\n주행형 양팔로봇', '시뮬레이션 모델링부터 SLAM·Nav2, MoveIt, LLM 작업 계획까지\n2일 실습 강습회', 'FaRobot',
    '인사와 강사 소개. 이틀 동안 노트북 한 대로, 시뮬레이터 안의 주행형 양팔로봇을 처음부터 끝까지 움직여 봅니다. 실물 로봇, GPU, 가상머신은 필요 없습니다. 이 슬라이드는 강의 화면이자 복습용 교재입니다. 각 장 아래쪽의 "비유", "왜 그럴까?", "이렇게 나오면 성공" 상자를 눈여겨보라고 안내하세요.');

  s = content('이틀 뒤에 할 수 있게 되는 것', '시작하기',
    '최종 결과물을 먼저 보여 줍니다. 웹 대시보드에 한 문장을 쓰면 LLM이 계획을 세우고, 로봇이 주행과 집기·놓기를 스스로 이어서 합니다. 오른쪽 그림이 실제 실행 화면입니다(작업 진행 타임라인에 단계별 결과가 쌓임).');
  box(s, 0.6, 1.5, 6.0, 1.7, C.text1);
  text(s, '"공급 테이블로 가서 빨간 상자를 집고\n작업대로 옮겨"', { x: 0.9, y: 1.6, w: 5.5, h: 1.5, fontSize: 21, bold: true, color: C.background1, valign: 'middle' });
  bullets(s, [
    '브라우저에 위 문장 하나를 입력하면',
    '인공지능(Claude)이 무엇을 어떤 순서로 할지 계획하고',
    '로봇이 스스로 주행하고, 카메라로 상자를 찾아 집어서 옮깁니다',
    '그 과정이 단계별로 화면에 표시됩니다',
  ], 0.6, 3.5, 6.0, 3.0, 17);
  img(s, 'step7_dashboard.jpg', 7.0, 1.5, 5.7, 5.2, '완성된 웹 대시보드: 지도, 카메라, 명령창, 작업 진행 타임라인');

  s = content('로봇이 하는 일을 한 단계씩 보면', '시작하기',
    '한 문장 명령이 실제로는 여섯 단계의 일입니다. 강습회의 모듈이 이 단계들을 하나씩 가능하게 만든다는 점을 연결해 주세요: 주행(모듈 2), 찾기·집기·놓기(모듈 3), 이해·계획(모듈 4), 그리고 이 모든 것이 돌아가는 세계(모듈 1).');
  const steps6 = [['FaComments', '명령 이해', '무엇을 해야 하나?'], ['FaRoute', '공급 테이블로', '지도를 보고 주행'], ['FaCamera', '상자 찾기', '카메라로 마커 인식'], ['FaHandPaper', '집기', '팔을 뻗어 잡고 들기'], ['FaRoute', '작업대로', '들고 주행'], ['FaBox', '놓기', '표시된 자리에 내려놓기']];
  steps6.forEach(([ic, h, b], i) => {
    const x = 0.6 + i * 2.05;
    circleIcon(s, ic, x + 0.45, 1.5, 0.9, [C.text1, C.accent2, C.accent3, C.accent1, C.accent2, C.accent1][i]);
    text(s, `${i + 1}. ${h}`, { x, y: 2.5, w: 1.9, h: 0.45, fontSize: 16, bold: true, align: 'center' });
    text(s, b, { x, y: 2.95, w: 1.9, h: 0.6, fontSize: 13, color: C.text2, align: 'center' });
    if (i < 5) arrow(s, x + 1.45, 1.95, x + 2.4, 1.95);
  });
  img(s, 'at_supply_table.png', 0.6, 3.75, 5.95, 3.0, '공급 테이블 앞에 선 로봇과 빨간 상자');
  img(s, 'at_work_table.png', 6.75, 3.75, 5.95, 3.0, '작업대 옆의 로봇과 놓을 자리 마커');

  s = content('전체 구조: 아래에서 위로 쌓는다', '시작하기',
    '이 그림이 이틀의 지도입니다. 모듈 1은 맨 아래 두 층(물리 엔진과 브리지), 모듈 2와 3은 스킬, 모듈 4가 LLM 계획기입니다. 위층은 아래층이 제대로 동작한다고 믿고 만들어집니다. 다음 장에서 이것을 회사에 비유합니다.');
  const layers = [
    ['자연어 명령', '사람 → 웹 대시보드 / 터미널', C.accent5, C.text1, ''],
    ['LLM 작업 계획', 'Claude가 도구를 고른다: navigate_to · pick_object · place_object', C.accent1, C.background1, '모듈 4'],
    ['로봇 스킬', 'Nav2 주행 · ArUco 정밀 접근 · MoveIt 2 양팔', C.accent2, C.background1, '모듈 2 · 3'],
    ['MuJoCo ↔ ROS 2 브리지', '/clock · /joint_states · /odom · /scan · /tf · /camera', C.accent3, C.background1, '모듈 1'],
    ['MuJoCo 물리 엔진', '접촉 · 마찰 · 모터 · 카메라 렌더링', C.text1, C.background1, '모듈 1'],
  ];
  layers.forEach(([h, b, fill, col, tag], i) => {
    const y = 1.45 + i * 1.07;
    box(s, 0.6, y, 10.0, 0.8, fill);
    text(s, h, { x: 0.85, y, w: 3.4, h: 0.8, fontSize: 18, bold: true, color: col, valign: 'middle' });
    text(s, b, { x: 4.3, y, w: 6.2, h: 0.8, fontSize: 15, color: col, valign: 'middle' });
    if (tag) pill(s, tag, 10.9, y + 0.22, 1.8, C.background2, C.text1);
    if (i < layers.length - 1) arrow(s, 5.6, y + 0.8, 5.6, y + 1.07);
  });

  s = content('비유: 로봇은 작은 회사처럼 일한다', '시작하기',
    '학생들이 구조를 기억하기 쉽게 하는 비유입니다. 사장님(LLM)은 "무엇을"만 정하고, 팀장(작업 관리자)이 지금 할 수 있는 일인지 확인하고, 기술자(스킬)가 "어떻게"를 실행합니다. 모든 일은 물리 법칙이 있는 공장(시뮬레이터) 안에서 일어납니다. 사장님이 기술자의 일을 직접 하지 않듯, LLM은 모터를 직접 돌리지 않습니다.');
  const roles = [['FaBrain', '사장님 = LLM', '"빨간 상자를 작업대로" 같은 목표를 듣고, 무엇을 어떤 순서로 할지 정한다. 손을 직접 쓰지는 않는다.', C.accent1],
    ['FaListOl', '팀장 = 작업 관리자', '지시가 지금 가능한지 확인한다. "상자를 안 들었는데 놓으라고요?" 하고 되돌려 보낸다.', C.accent3],
    ['FaWrench', '기술자 = 로봇 스킬', '주행, 마커 찾기, 팔 움직이기를 실제로 해낸다. 빠르고 정확하다.', C.accent2],
    ['FaCogs', '공장 = MuJoCo 시뮬레이터', '중력, 마찰, 충돌이 있는 세계. 모든 일이 여기서 실제처럼 일어난다.', C.text1]];
  roles.forEach(([ic, h, b, a], i) => {
    const x = 0.6 + (i % 2) * 6.15, y = 1.5 + Math.floor(i / 2) * 2.65;
    card(s, { x, y, w: 5.95, h: 2.45, head: h, body: b, iconName: ic, accent: a, bodySize: 16 });
  });

  s = content('2일 일정', '시작하기',
    '오전 2시간, 오후 4시간입니다. 설치는 반드시 사전에 끝내고 오도록 공지했습니다. 1일차 08:30–09:30에는 설치를 못 끝낸 사람을 위한 헬프데스크가 있습니다.');
  pill(s, '사전: 집에서 설치 1~2시간 (다음 "설치" 장)', 0.6, 1.45, 5.2, C.accent2);
  const days = [
    ['1일차 오전', '09:30–11:30', '모듈 1', 'MuJoCo + ROS 2\n브리지', '시뮬레이터, 로봇 모델\n센서, 좌표계'],
    ['1일차 오후', '12:30–16:30', '모듈 2', 'SLAM + Nav2', '지도 만들기\n자율주행, 순찰'],
    ['2일차 오전', '09:30–11:30', '모듈 3', 'MoveIt 2 +\nPick & Place', '팔 제어, 카메라\n집기·놓기'],
    ['2일차 오후', '12:30–16:30', '모듈 4', 'LLM 작업 계획', '자연어 명령\n대시보드, 최종 미션'],
  ];
  days.forEach(([d, t, m, h, b], i) => {
    const x = 0.6 + i * 3.08;
    box(s, x, 2.1, 2.85, 4.5, C.background2);
    text(s, d, { x: x + 0.25, y: 2.3, w: 2.4, h: 0.4, fontSize: 15, bold: true, color: C.text2 });
    text(s, t, { x: x + 0.25, y: 2.7, w: 2.4, h: 0.4, fontSize: 15, color: C.text2 });
    pill(s, m, x + 0.25, 3.3, 1.2, [C.accent3, C.accent2, C.accent1, C.text1][i]);
    text(s, h, { x: x + 0.25, y: 3.85, w: 2.4, h: 1.0, fontSize: 18, bold: true });
    text(s, b, { x: x + 0.25, y: 4.95, w: 2.4, h: 1.3, fontSize: 15, color: C.text2 });
  });

  s = content('실습 환경', '시작하기',
    '모든 것이 노트북의 WSL 안에서 돕니다. WSLg 덕분에 MuJoCo와 RViz 창이 Windows 창처럼 뜹니다. 8 GB 노트북은 .wslconfig로 WSL 메모리를 6 GB로 올려야 합니다(설치 가이드 2-4). API 키가 없어도 모듈 4는 scripted 모드로 할 수 있습니다.');
  const stack = [['MuJoCo 3.12 · OpenArm v2 · UNBOLT 코드', C.accent1, C.background1], ['ROS 2 Humble · Nav2 · MoveIt 2', C.accent2, C.background1], ['Ubuntu 22.04', C.accent3, C.background1], ['WSL2 + WSLg (리눅스 GUI 창)', C.accent3, C.background1], ['Windows 10/11 노트북', C.accent5, C.text1]];
  stack.forEach(([t, f, col], i) => {
    const y = 1.5 + i * 1.0;
    box(s, 0.6, y, 6.4, 0.8, f);
    text(s, t, { x: 0.85, y, w: 6.0, h: 0.8, fontSize: 17, bold: true, color: col, valign: 'middle' });
  });
  [['FaMemory', '16 GB', 'RAM 권장 (최소 8 GB)'], ['FaHdd', '30 GB', 'C: 드라이브 여유'], ['FaMicrochip', '내장 그래픽', 'GPU·Docker·VM 불필요'], ['FaDollarSign', '$5 이내', 'Claude API (선택)']].forEach(([ic, big, small], i) => {
    const x = 7.4 + (i % 2) * 2.7, y = 1.5 + Math.floor(i / 2) * 2.5;
    box(s, x, y, 2.5, 2.3, C.background2);
    circleIcon(s, ic, x + 0.25, y + 0.25, 0.6, C.accent1);
    text(s, big, { x: x + 0.2, y: y + 1.0, w: 2.1, h: 0.6, fontSize: 24, bold: true });
    text(s, small, { x: x + 0.2, y: y + 1.6, w: 2.1, h: 0.6, fontSize: 14, color: C.text2 });
  });

  s = content('미리 알아 두기: ROS 2 용어', '시작하기',
    'ROS 2를 처음 쓰는 학생을 위한 장입니다. 노드는 사람, 토픽은 단체 채팅방, 서비스는 전화로 묻고 답 듣기, 액션은 택배 주문(진행 상황을 계속 알려 주고 취소도 됨)으로 비유하면 쉽습니다. 이 강습회에서 각각을 어디서 쓰는지 오른쪽 열의 예와 함께 짚어 주세요.');
  glossary(s, [
    ['노드 (node)', '한 가지 일을 맡은 프로그램. 예: mujoco_bridge, slam_toolbox', '회사의 직원 한 명'],
    ['토픽 (topic)', '이름이 붙은 메시지 통로. 보내는 쪽(publisher)과 받는 쪽(subscriber)이 서로 몰라도 됨. 예: /scan', '단체 채팅방'],
    ['메시지 (message)', '토픽으로 오가는 데이터의 형식. 예: sensor_msgs/LaserScan', '정해진 양식의 서류'],
    ['서비스 (service)', '요청 한 번에 응답 한 번. 예: /mujoco_bridge/reset', '전화로 묻고 바로 답 듣기'],
    ['액션 (action)', '오래 걸리는 일. 진행 상황(feedback)을 받고 중간에 취소 가능. 예: 주행, 팔 궤적', '택배 주문 + 배송 조회'],
    ['파라미터', '노드의 설정값. 예: lidar_samples, use_sim_time', '직원의 업무 설정'],
    ['launch 파일', '여러 노드를 한 번에 켜는 스크립트. 예: bringup.launch.py', '출근 명단'],
  ], [2.3, 6.3, 3.5], 16);

  s = content('미리 알아 두기: 로봇·시뮬레이션 용어', '시작하기',
    '각 용어는 해당 모듈에서 자세히 다룹니다. 지금은 "들어 본 적 있다" 정도면 충분하다고 말해 주세요.');
  glossary(s, [
    ['MJCF', 'MuJoCo가 읽는 로봇·세계 설명 파일 (XML). 질량, 모터, 충돌 모양', '게임 속 물체의 설계도'],
    ['URDF', 'ROS가 읽는 로봇 설명 파일. 링크와 관절의 연결', 'ROS용 로봇 신분증'],
    ['TF', '좌표계들 사이의 위치 관계를 알려 주는 시스템', '"어디서 보느냐"를 바꿔 주는 번역기'],
    ['오도메트리', '바퀴가 굴러간 양으로 계산한 위치', '걸음 수로 거리 짐작하기'],
    ['LiDAR', '레이저를 360° 쏘아 주변까지의 거리를 재는 센서', '박쥐의 초음파'],
    ['SLAM', '움직이면서 지도를 만들고 동시에 내 위치를 찾는 기술', '처음 간 건물에서 약도 그리며 걷기'],
    ['costmap', '"여기는 가면 위험" 정도를 칸마다 적은 지도', '등산로의 위험 구역 표시'],
    ['IK (역기구학)', '손을 어디에 두고 싶을 때 각 관절 각도를 거꾸로 계산', '컵을 잡으려 팔꿈치 각도 정하기'],
  ], [2.3, 6.3, 3.5], 16);

  s = content('토픽 통신은 이렇게 생겼다', '시작하기',
    'publish/subscribe 구조를 그림으로 설명합니다. 브리지가 /scan을 한 번 내보내면 SLAM, Nav2, RViz, 대시보드가 동시에 받습니다. 보내는 쪽은 누가 받는지 모릅니다. 그래서 새 기능(예: 대시보드)을 붙여도 브리지를 고칠 필요가 없습니다. ros2 topic list / echo / hz로 언제든 들여다볼 수 있습니다.');
  box(s, 0.6, 2.6, 3.0, 1.4, C.accent3);
  text(s, 'mujoco_bridge\n(publisher)', { x: 0.6, y: 2.6, w: 3.0, h: 1.4, fontSize: 16, bold: true, color: C.background1, align: 'center', valign: 'middle' });
  box(s, 4.4, 2.85, 2.6, 0.9, C.accent1);
  text(s, '/scan', { x: 4.4, y: 2.85, w: 2.6, h: 0.9, fontSize: 20, bold: true, fontFace: L.MONO, color: C.background1, align: 'center', valign: 'middle' });
  arrow(s, 3.65, 3.3, 4.35, 3.3);
  const subs = ['slam_toolbox', 'Nav2 costmap', 'RViz', '웹 대시보드'];
  subs.forEach((t, i) => {
    const y = 1.5 + i * 0.95;
    box(s, 8.0, y, 3.0, 0.75, C.background2);
    text(s, t, { x: 8.0, y, w: 3.0, h: 0.75, fontSize: 15, bold: true, align: 'center', valign: 'middle' });
    arrow(s, 7.05, 3.3, 7.95, y + 0.37);
  });
  text(s, '← 받는 쪽\n(subscriber)\n여럿이어도 됨', { x: 11.15, y: 2.55, w: 1.6, h: 1.2, fontSize: 13, color: C.text2 });
  code(s, '$ ros2 topic list          # 지금 있는 토픽 목록\n$ ros2 topic hz /scan      # 1초에 몇 번 오나\n$ ros2 topic echo /odom --once   # 내용 한 번 보기', 0.6, 5.3, 7.2, 1.4, 13);
  callout(s, 'analogy', 8.0, 5.3, 4.7, 1.4, '단체 채팅방: 한 명이 올리면 모두가 본다', '비유');

  s = content('터미널 쓰는 법 (처음이라면)', '시작하기',
    '실습에서는 터미널을 3~4개 동시에 씁니다. 터미널 1은 시뮬레이터(켜 두기), 터미널 2부터 명령을 칩니다. 붙여넣기 단축키(Ctrl+Shift+V)와 Ctrl+C의 의미(실행 중인 프로그램 멈추기)를 꼭 짚어 주세요. Ctrl+C로 시뮬레이터를 끄면 다른 실습도 다 멈춘다는 점도요.');
  [['FaTerminal', '터미널 여러 개', 'Windows Terminal의 탭 옆 ∨ → Ubuntu-22.04. 터미널 1은 시뮬레이터용으로 켜 두고, 2번부터 명령을 칩니다.'],
    ['FaKeyboard', '붙여넣기', 'Ctrl + Shift + V 또는 마우스 오른쪽 클릭. Ctrl + V는 안 됩니다. 명령 앞의 $ 는 치지 않습니다.'],
    ['FaStopCircle', 'Ctrl + C = 멈추기', '실행 중인 프로그램을 끕니다. 시뮬레이터 터미널에서 누르면 모든 실습이 멈추니 주의.'],
    ['FaRedo', '새 터미널은 준비 완료', '설치 스크립트가 ~/.bashrc에 ROS 설정을 넣어 두어, 새 터미널은 바로 ros2 명령을 쓸 수 있습니다.']].forEach(([ic, h, b], i) => {
    const x = 0.6 + (i % 2) * 6.15, y = 1.5 + Math.floor(i / 2) * 2.65;
    card(s, { x, y, w: 5.95, h: 2.45, head: h, body: b, iconName: ic, accent: [C.text1, C.accent3, C.accent6, C.accent2][i], bodySize: 15 });
  });

  s = content('진행 방식', '시작하기',
    '체크포인트 카드는 조교가 강의실을 한눈에 보는 수단입니다. 늦어진 학생도 각 모듈을 독립적으로 시작할 수 있게 되어 있으니 불안해하지 않아도 된다고 말해 주세요.');
  [['개념', '20~30%', '왜 그렇게 만드는지'], ['따라 하기', '50%', '명령 복사 → 결과 확인'], ['과제', '20~30%', '바꿔 보고 설명하기']].forEach(([h, p, b], i) => {
    const x = 0.6 + i * 4.15;
    box(s, x, 1.5, 3.7, 2.1, i === 1 ? C.accent1 : C.background2);
    const col = i === 1 ? C.background1 : C.text1;
    text(s, h, { x: x + 0.3, y: 1.65, w: 3.1, h: 0.5, fontSize: 20, bold: true, color: col });
    text(s, p, { x: x + 0.3, y: 2.2, w: 3.1, h: 0.7, fontSize: 30, bold: true, color: col });
    text(s, b, { x: x + 0.3, y: 2.95, w: 3.1, h: 0.5, fontSize: 15, color: col });
    if (i < 2) arrow(s, x + 3.75, 2.55, x + 4.1, 2.55);
  });
  card(s, { x: 0.6, y: 4.0, w: 6.0, h: 2.6, head: '체크포인트 카드', iconName: 'FaCheckCircle', accent: C.accent2, body: '노트북 뒤에 포스트잇을 붙입니다.\n초록 = 통과, 빨강 = 도움 필요.\n절반 이상이 통과하면 다음으로 넘어갑니다.' });
  card(s, { x: 6.75, y: 4.0, w: 5.95, h: 2.6, head: '슬라이드 읽는 법', iconName: 'FaBook', accent: C.accent4, body: '노란 전구 = 비유, 파란 물음표 = 왜 그럴까?\n초록 체크 = 이렇게 나오면 성공\n빨간 렌치 = 안 되면 이렇게' });

  s = content('막혔을 때는 이 순서로', '시작하기',
    '대부분의 문제는 1~3단계에서 풀립니다. 특히 3번(깨끗하게 종료 후 다시 시작)이 생각보다 자주 통합니다. 오류는 스크린샷보다 텍스트로 받는 것이 좋고, API 키가 섞여 있지 않은지 확인하라고 말해 주세요.');
  [['오류 메시지를 끝까지 읽기', '빨간 줄의 마지막 문장에 원인이 있는 경우가 많다. 예: No module named …, Address already in use'],
    ['troubleshooting.md 검색', '오류의 일부를 Ctrl + F로 찾는다. 증상별로 원인과 해결이 표로 정리되어 있다'],
    ['깨끗하게 종료하고 다시 시작', '모든 터미널 Ctrl + C → 남은 프로세스 종료 → 다시 launch. 그래도 안 되면 wsl --shutdown'],
    ['빨간 카드 올리기', '조교에게 오류 텍스트를 보여 준다 (API 키가 들어 있지 않은지 확인)']].forEach(([h, b], i) => step(s, i + 1, h, b, 0.6 + (i % 2) * 6.15, 1.6 + Math.floor(i / 2) * 2.4, 5.9, 1.2));
};
