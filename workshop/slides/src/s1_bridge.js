// 모듈 1: MuJoCo + ROS 2 브리지
const L = require('./lib');
const { C, MONO, text, box, circleIcon, pill, card, callout, code, bullets, arrow, img, marker, table, step, flow, lab, quiz, summary, content } = L;
const TAG = '모듈 1 · 브리지';

module.exports = function build() {
  let s;
  L.section('모듈 1: MuJoCo + ROS 2 브리지', '모듈 1 · 1일차 09:30–11:30', 'MuJoCo + ROS 2 브리지\n주행형 양팔로봇 모델링', [
    '시뮬레이터와 MuJoCo가 무엇인지, 왜 쓰는지 안다',
    '로봇 모델 파일(MJCF·URDF)을 읽을 수 있다',
    '브리지가 ROS에 시간·상태·센서를 어떻게 내보내는지 확인한다',
    'LiDAR와 휠 오도메트리가 어떻게 계산되는지 코드로 읽는다',
  ], '모듈 1의 목표 네 가지입니다. 시뮬레이터와 ROS 사이에 무엇이 오가야 하는지를 직접 만든 브리지 코드로 확인합니다.');

  s = content('오늘 오전에 할 일', TAG, '2시간 동안의 흐름입니다. 실습 1~2는 ROS 없이 MuJoCo만, 실습 3부터 ROS와 연결합니다. 체크포인트 번호(1-1 등)가 각 실습 끝에 있습니다.');
  const plan = [['09:30', '개념', '시뮬레이터, MuJoCo, 전체 구조'], ['09:50', '실습 1~2', 'MuJoCo 혼자 실행, 모델 파일 읽기'], ['10:20', '실습 3~4', '브리지 실행, 토픽·시간·TF'], ['10:50', '실습 5~6', 'LiDAR, 오도메트리 vs 실제 위치'], ['11:15', '정리', '요약, 퀴즈, 과제 안내']];
  plan.forEach(([t, h, b], i) => {
    const y = 1.5 + i * 1.03;
    pill(s, t, 0.6, y + 0.22, 1.2, i % 2 ? C.accent3 : C.text1);
    box(s, 2.1, y, 10.6, 0.82, C.background2);
    text(s, h, { x: 2.35, y, w: 2.2, h: 0.82, fontSize: 18, bold: true, valign: 'middle' });
    text(s, b, { x: 4.6, y, w: 8.0, h: 0.82, fontSize: 16, color: C.text2, valign: 'middle' });
  });

  s = content('시뮬레이터를 쓰는 이유', TAG, '실제 로봇 없이 시작하는 이유를 학생 눈높이로 설명합니다. 특히 "정답 정보"(ground truth)는 시뮬레이터만의 장점입니다. 이 강습회에서도 오도메트리 오차를 재거나 상자가 제대로 놓였는지 확인할 때 씁니다.');
  [['FaShieldAlt', '안전하다', '벽에 부딪혀도, 팔이 테이블에 걸려도 아무것도 부서지지 않는다. 마음껏 실패해 볼 수 있다.'],
    ['FaDollarSign', '돈이 들지 않는다', '양팔 모바일 로봇은 수천만 원. 시뮬레이터는 노트북 한 대면 된다. 40명이 동시에 실습할 수 있다.'],
    ['FaRedo', '몇 번이든 처음부터', '리셋 한 번이면 로봇과 상자가 처음 자리로. 같은 실험을 똑같이 반복할 수 있다.'],
    ['FaCrosshairs', '정답을 알 수 있다', '로봇과 물체의 "진짜" 위치를 언제든 알 수 있다 (/ground_truth). 내 알고리즘이 얼마나 틀렸는지 잴 수 있다.']].forEach(([ic, h, b], i) => {
    const x = 0.6 + (i % 2) * 6.15, y = 1.5 + Math.floor(i / 2) * 2.65;
    card(s, { x, y, w: 5.95, h: 2.45, head: h, body: b, iconName: ic, accent: [C.accent2, C.accent1, C.accent3, C.accent6][i], bodySize: 16 });
  });

  s = content('왜 Gazebo가 아니라 MuJoCo인가', TAG, '집기처럼 손가락과 물체가 닿는 일이 중요하면 MuJoCo가 유리합니다. 대신 ROS 쪽 연결을 우리가 씁니다. 이것이 이 강습회가 MuJoCo를 고른 이유이자 모듈 1의 학습 포인트입니다.');
  [['Gazebo', ['ROS 연동 플러그인이 이미 많다', '센서 종류가 많다', '모바일 로봇 시뮬레이션에 강함'], C.background2, C.text1], ['MuJoCo', ['접촉·마찰 계산이 정확하고 빠르다', '파이썬에서 바로 쓴다 (pip install mujoco)', '집기·강화학습처럼 접촉이 많은 일에 강함'], C.text1, C.background1]].forEach(([h, items, f, col], i) => {
    const x = 0.6 + i * 6.15;
    box(s, x, 1.5, 5.95, 3.3, f);
    text(s, h, { x: x + 0.35, y: 1.7, w: 5.2, h: 0.6, fontSize: 24, bold: true, color: col });
    bullets(s, items, x + 0.35, 2.5, 5.3, 2.2, 17, col);
  });
  callout(s, 'why', 0.6, 5.05, 12.1, 1.65, 'MuJoCo에는 ROS 연결 기능이 없어서 "브리지"를 직접 만든다. 직접 만들어 보면 시뮬레이터가 ROS에 무엇을 내줘야 하는지(시간, 관절, 센서, 명령)를 정확히 알게 된다.');

  s = content('MuJoCo의 기본: 설계도와 현재 상태', TAG, 'MjModel은 바뀌지 않는 설계도(질량, 모양, 모터), MjData는 매 순간 바뀌는 상태(관절 각도, 속도, 접촉, 센서값)입니다. mj_step 한 번이 시간을 1 ms 앞으로 보냅니다. 악보와 연주의 비유가 잘 통합니다.');
  box(s, 0.6, 1.5, 3.6, 2.0, C.accent3);
  text(s, 'MjModel\n설계도 (변하지 않음)\n질량 · 모양 · 관절 · 모터', { x: 0.7, y: 1.5, w: 3.4, h: 2.0, fontSize: 16, bold: true, color: C.background1, align: 'center', valign: 'middle' });
  box(s, 4.85, 1.5, 3.6, 2.0, C.accent1);
  text(s, 'mj_step(m, d)\n시간을 1 ms 앞으로\n(1초 = 1000번)', { x: 4.95, y: 1.5, w: 3.4, h: 2.0, fontSize: 16, bold: true, color: C.background1, align: 'center', valign: 'middle' });
  box(s, 9.1, 1.5, 3.6, 2.0, C.accent2);
  text(s, 'MjData\n현재 상태 (매 순간 변함)\n위치 · 속도 · 접촉 · 센서', { x: 9.2, y: 1.5, w: 3.4, h: 2.0, fontSize: 16, bold: true, color: C.background1, align: 'center', valign: 'middle' });
  arrow(s, 4.25, 2.5, 4.8, 2.5); arrow(s, 8.5, 2.5, 9.05, 2.5);
  code(s, 'import mujoco\nm = mujoco.MjModel.from_xml_path("models/scene.xml")  # 설계도 읽기\nd = mujoco.MjData(m)                                  # 상태 만들기\nfor _ in range(1000):\n    d.ctrl[:] = ...         # 모터에 명령\n    mujoco.mj_step(m, d)    # 물리 계산 1 ms\nprint(d.time, d.qpos[:3])   # 1초 뒤 시간과 위치', 0.6, 3.8, 7.6, 2.9, 13);
  callout(s, 'analogy', 8.5, 3.8, 4.2, 2.9, 'MjModel = 악보, MjData = 지금 연주 중인 마디. mj_step은 박자 하나를 넘기는 것.');

  s = content('MJCF 파일 읽는 법', TAG, 'models/unbolt_robot.xml의 일부를 줄여서 보여 줍니다. body 안에 body가 들어가며 나무 모양을 이루고, joint가 움직임을, geom이 모양과 충돌을, actuator가 모터를 정의합니다. 실습 2에서 실제 파일을 열어 이 태그들을 찾습니다.');
  code(s, '<worldbody>\n  <body name="base_link" pos="0 0 0.08">        <!-- 몸체 -->\n    <freejoint name="base_free"/>               <!-- 자유롭게 움직임 -->\n    <geom type="box" size="0.27 0.19 0.05"/>    <!-- 모양·충돌 -->\n    <body name="left_wheel" pos="0 0.225 0">\n      <joint name="left_wheel_joint" type="hinge" axis="0 1 0"/>\n      <geom type="sphere" size="0.08"/>         <!-- 바퀴 r=0.08 -->\n    </body>\n    <site name="lidar_link" pos="0.22 0 0.13"/> <!-- 센서 위치 -->\n    <camera name="head_camera" pos="0.05 0 0.97" fovy="60"/>\n  </body>\n</worldbody>\n<actuator>\n  <velocity name="left_wheel_vel" joint="left_wheel_joint" kv="8"/>\n</actuator>', 0.6, 1.5, 7.9, 5.2, 13);
  table(s, [['태그', '뜻'], ['body', '물체 하나. 안에 body를 넣으면 붙어서 같이 움직임'], ['joint', '움직일 수 있는 방향 (hinge = 회전)'], ['geom', '모양, 충돌, 마찰'], ['site / camera', '센서·카메라를 달 위치'], ['actuator', '모터. velocity = 속도 제어, position = 각도 제어']], 8.8, 1.5, 3.9, [1.3, 2.6], 13);
  s.addNotes('표시된 값은 실제 파일과 같은 값입니다(바퀴 반지름 0.08, 바퀴 간격 0.45 → y = ±0.225, LiDAR (0.22, 0, 0.13)). 코드는 이해를 돕기 위해 줄였습니다.');

  s = content('우리 로봇 해부도', TAG, '번호를 짚으며 설명합니다. 바퀴는 속도 모터, 캐스터는 바닥을 받치는 공, LiDAR는 앞쪽 검은 구, 카메라는 기둥 위(두 팔 사이)에서 47° 아래를 봅니다. 팔은 OpenArm v2(7자유도 + 그리퍼) 두 개입니다. 사진에는 오른팔만 잘 보입니다.');
  const r = img(s, 'robot_side_crop.png', 0.6, 1.5, 7.4, 5.2, '주행형 양팔로봇 옆모습');
  const P = (u, v) => [r.x + (u - 430) / 500 * r.w, r.y + (v - 160) / 500 * r.h];
  [[1, 645, 580], [2, 745, 602], [3, 728, 494], [4, 612, 190], [5, 735, 315], [6, 610, 420]].forEach(([n, u, v]) => marker(s, n, ...P(u, v)));
  table(s, [['번호', '부품', '하는 일'], ['1', '구동 바퀴 × 2', '좌우 속도를 다르게 → 회전 (차동구동)'], ['2', '캐스터 × 2', '앞뒤를 받치는 작은 공 (마찰 없음)'], ['3', '2D LiDAR', '360° 거리 측정, 10 Hz'], ['4', '헤드 카메라', '1280×720, 47° 아래, 마커 인식'], ['5', 'OpenArm 팔 × 2', '7자유도 + 그리퍼 (손가락 2개)'], ['6', '받침대', '팔을 받침대 위에 고정 (어깨 높이 약 0.9 m)']], 8.3, 1.5, 4.4, [0.7, 1.6, 2.1], 13);

  s = content('우리 월드: 7 × 6 m 방', TAG, '위에서 내려다본 MuJoCo 월드입니다. 번호를 짚으며 공급 테이블(빨간 상자가 있는 곳)과 작업대(상자를 옮길 곳)를 먼저 익히게 합니다. 칸막이벽의 문은 모듈 2에서 지도를 만들 때와 주행할 때 중요합니다.');
  const rt = img(s, 'room_top.png', 0.6, 1.5, 7.9, 5.2, '위에서 본 방: 벽, 칸막이, 테이블, 장애물');
  const W = (x, y) => [rt.x + (640 + (x - 1.0) * 96.6) / 1280 * rt.w, rt.y + (360 - y * 96.6) / 720 * rt.h];
  [[1, 0.0, 0.0], [2, -0.15, -2.45], [3, 2.2, 0.0], [4, -1.2, 0.2], [5, 1.0, -1.6]].forEach(([n, x, y]) => marker(s, n, ...W(x, y)));
  table(s, [['번호', '이름', '설명'], ['1', '시작 위치', '로봇이 처음 서 있는 곳 (0, 0)'], ['2', '공급 테이블', '빨간 상자가 있는 하늘색 테이블'], ['3', '작업대', '상자를 놓을 나무 테이블 (마커 3)'], ['4', '칸막이 문', '서쪽 방으로 가는 통로'], ['5', '기둥', '피해 가야 하는 장애물']], 8.8, 1.5, 3.9, [0.7, 1.3, 1.9], 13);

  s = content('실습 1. MuJoCo 혼자 실행하기', TAG, 'ROS 없이 MuJoCo만 띄워 봅니다. 아무 명령이 없으면 팔이 아래로 처지는 것을 보여 주세요. 브리지는 중력 보상(gravcomp)을 켜서 이를 막습니다. 체크포인트 1-1.');
  lab(s, {
    cmd: '$ cd ~/unbolt/models\n$ python3 -m mujoco.viewer --mjcf=scene.xml\n\n# 창이 뜨면\n#  스페이스바   시뮬레이션 시작/멈춤\n#  Backspace    처음으로 되돌리기\n#  오른쪽 패널  Control → 바퀴·팔 슬라이더',
    cmdH: 3.0,
    explain: ['python3 -m mujoco.viewer: MuJoCo에 들어 있는 3D 뷰어', '--mjcf=scene.xml: 방 + 로봇이 들어 있는 월드 파일', '슬라이더로 바퀴를 돌리면 로봇이 움직인다'],
    ok: 'MuJoCo 창에 방과 분홍색 로봇이 보이고, 바퀴 슬라이더를 움직이면 로봇이 굴러간다.\n\n✅ 체크포인트 1-1',
    fail: '창이 안 뜨면 WSLg 문제 → xeyes로 확인 (설치 가이드 2-6). python3가 conda면 conda deactivate',
  });

  s = content('MuJoCo 뷰어 조작법', TAG, '조작법은 자주 물어보는 부분이라 한 장으로 정리했습니다. 특히 Ctrl+오른쪽 드래그로 물체를 끄는 기능은 학생들이 재미있어합니다.');
  [['FaArrowsAlt', '시점 바꾸기', '왼쪽 드래그 = 회전\n오른쪽 드래그 = 이동\n휠 = 확대/축소'], ['FaHandPaper', '물체 끌기', '물체를 더블클릭해서 선택\nCtrl + 오른쪽 드래그 = 끌기\n빨간 상자를 굴려 보자'], ['FaEye', '보이는 것 바꾸기', '왼쪽 패널 Rendering →\nFrame: Body (좌표축)\nLabel: Body (이름표)'], ['FaPlay', '시간 조절', '스페이스바 = 시작/멈춤\nBackspace = 리셋\n오른쪽 패널 Simulation']].forEach(([ic, h, b], i) => {
    const x = 0.6 + (i % 2) * 6.15, y = 1.5 + Math.floor(i / 2) * 2.65;
    card(s, { x, y, w: 5.95, h: 2.45, head: h, body: b, iconName: ic, accent: [C.accent3, C.accent1, C.accent2, C.text1][i], bodySize: 16 });
  });

  s = content('브리지가 필요한 이유', TAG, 'MuJoCo는 물리를 알지만 ROS 토픽을 모르고, ROS 노드들은 토픽을 알지만 MuJoCo를 모릅니다. 브리지가 양쪽을 통역합니다. 왼쪽에서 오른쪽(상태·센서), 오른쪽에서 왼쪽(명령) 두 방향이 있다는 것을 강조하세요.');
  box(s, 0.6, 1.6, 3.4, 3.6, C.text1);
  text(s, 'MuJoCo\n\nqpos, qvel\n접촉, 렌더링\nd.ctrl (모터)', { x: 0.7, y: 1.6, w: 3.2, h: 3.6, fontSize: 16, bold: true, color: C.background1, align: 'center', valign: 'middle' });
  box(s, 4.95, 1.6, 3.4, 3.6, C.accent1);
  text(s, 'mujoco_bridge\n(우리가 만든 노드)\n\n상태·센서 → ROS\n명령 → MuJoCo\n시간 관리', { x: 5.05, y: 1.6, w: 3.2, h: 3.6, fontSize: 16, bold: true, color: C.background1, align: 'center', valign: 'middle' });
  box(s, 9.3, 1.6, 3.4, 3.6, C.accent3);
  text(s, 'ROS 2\n\n/joint_states, /odom\n/scan, /camera, /tf\n/cmd_vel (명령)', { x: 9.4, y: 1.6, w: 3.2, h: 3.6, fontSize: 16, bold: true, color: C.background1, align: 'center', valign: 'middle' });
  arrow(s, 4.05, 2.6, 4.9, 2.6); arrow(s, 8.4, 2.6, 9.25, 2.6);
  arrow(s, 9.25, 4.2, 8.4, 4.2); arrow(s, 4.9, 4.2, 4.05, 4.2);
  callout(s, 'analogy', 0.6, 5.45, 12.1, 1.25, '통역사: MuJoCo는 "물리 언어", ROS는 "토픽 언어"를 쓴다. 브리지가 양쪽 말을 실시간으로 옮겨 준다.');

  s = content('브리지의 한 바퀴', TAG, 'mujoco_bridge_node.py의 run() 루프입니다. 명령을 반영하고, 실제 시간만큼 물리 스텝을 밟고, 주기가 된 토픽만 냅니다. 노트북이 느리면 한 사이클에 50 ms까지만 따라잡고 "simulation is slower" 경고를 냅니다.');
  [['_apply_commands()', '/cmd_vel → 바퀴 속도, 관절 목표 → 모터'], ['mj_step() × N', '1 ms씩, 실제 시간을 따라잡을 때까지'], ['_publish_due()', '주기가 된 토픽만 발행 (아래 표)'], ['카메라 렌더링', '오프스크린으로 그려서 5 Hz 발행']].forEach(([h, b], i) => {
    const y = 1.5 + i * 1.3;
    box(s, 0.6, y, 6.3, 1.05, i === 1 ? C.accent3 : C.background2);
    const col = i === 1 ? C.background1 : C.text1;
    text(s, h, { x: 0.85, y: y + 0.08, w: 5.8, h: 0.45, fontSize: 17, bold: true, fontFace: MONO, color: col });
    text(s, b, { x: 0.85, y: y + 0.52, w: 5.8, h: 0.45, fontSize: 14, color: col });
    if (i < 3) arrow(s, 3.75, y + 1.05, 3.75, y + 1.3);
  });
  text(s, '↺ 이 네 단계를 계속 반복', { x: 0.6, y: 6.6, w: 6.3, h: 0.35, fontSize: 14, color: C.text2, align: 'center' });
  table(s, [['토픽', '주기', '내용'], ['/clock', '250 Hz', '시뮬레이션 시간'], ['/joint_states', '100 Hz', '관절 20개의 각도·속도'], ['/odom + TF', '50 Hz', '바퀴로 계산한 위치'], ['/imu', '50 Hz', '기울기·회전 속도'], ['/scan', '10 Hz', 'LiDAR 360빔'], ['/camera/*', '5 Hz', '헤드 카메라 영상 (camera_rate)'], ['/wrist_camera/*', '0 / 10 Hz', '손목 카메라, VLA 모드만 (모듈 5)'], ['/ground_truth/*', '10~50 Hz', '진짜 위치 (평가용)']], 7.3, 1.5, 5.4, [1.9, 1.2, 2.3], 13);

  s = content('시간의 주인은 시뮬레이터: /clock', TAG, 'use_sim_time을 빠뜨리면 TF가 "미래/과거 시간"이라며 거부하는 오류(Lookup would require extrapolation)가 납니다. 이 강습회의 모든 ros2 run에 --ros-args -p use_sim_time:=true를 붙이는 이유입니다. 게임 속 시계 비유를 쓰세요.');
  box(s, 0.6, 1.5, 5.9, 2.4, C.background2);
  text(s, '실제 시계 (벽시계)', { x: 0.9, y: 1.6, w: 5.3, h: 0.45, fontSize: 17, bold: true });
  text(s, '1792889000초 … (1970년부터 센 초)\n노트북이 느려도 똑같이 흐른다', { x: 0.9, y: 2.1, w: 5.3, h: 1.6, fontSize: 15, color: C.text2 });
  box(s, 6.8, 1.5, 5.9, 2.4, C.accent1);
  text(s, '시뮬레이션 시계 (/clock)', { x: 7.1, y: 1.6, w: 5.3, h: 0.45, fontSize: 17, bold: true, color: C.background1 });
  text(s, '0초부터 시작, 시뮬레이터가 계산한 만큼만 흐른다\n노트북이 느리면 천천히 간다', { x: 7.1, y: 2.1, w: 5.3, h: 1.6, fontSize: 15, color: C.background1 });
  callout(s, 'why', 0.6, 4.15, 6.0, 2.55, '센서 데이터에는 "시뮬레이션 시각"이 찍혀 있다. 다른 노드가 벽시계를 쓰면 시각이 50년쯤 어긋나서 데이터를 버린다. 그래서 모두 use_sim_time:=true.');
  callout(s, 'analogy', 6.8, 4.15, 5.9, 2.55, '게임 속 시계: 게임을 일시정지하면 게임 속 시간도 멈춘다. 로봇 프로그램들은 모두 이 게임 속 시계를 봐야 서로 맞는다.');

  s = content('실습 3. 브리지 실행하고 토픽 확인', TAG, 'sim.launch.py는 브리지 + robot_state_publisher + RViz를 함께 켭니다. 터미널 2에서 토픽을 확인합니다. 체크포인트 1-2: /clock 약 250 Hz, /scan 약 10 Hz.');
  lab(s, {
    cmd: '# 터미널 1 (켜 두기)\n$ ros2 launch unbolt_mujoco_bridge sim.launch.py\n\n# 터미널 2\n$ ros2 node list\n$ ros2 topic list\n$ ros2 topic hz /clock\n$ ros2 topic hz /scan\n$ ros2 topic echo /joint_states --once',
    cmdH: 3.6,
    explain: ['ros2 topic hz: 1초에 몇 번 오는지 (Ctrl+C로 멈춤)', 'echo --once: 메시지 하나만 출력'],
    ok: 'MuJoCo 창 + RViz 창이 뜬다.\n/clock 평균 약 250, /scan 약 10.\n\n✅ 체크포인트 1-2',
    fail: '"simulation is slower" 경고가 계속 나오면 다른 프로그램을 끄고 전원을 연결. 동작은 같고 느려질 뿐',
  });

  s = content('TF: "어디서 본 위치인가"를 바꿔 주는 나무', TAG, '카메라는 "내 앞 50 cm"라고 말하지만, 팔은 "로봇 몸 기준 어디"인지 알아야 합니다. TF는 좌표계들 사이의 관계를 나무로 관리해서 아무 두 좌표계 사이의 변환을 계산해 줍니다. odom→base_footprint는 브리지가, 몸 안의 링크는 robot_state_publisher가 URDF로 냅니다. map은 모듈 2에서 생깁니다.');
  const tf = [['map', 0.6, 1.6, C.accent5, C.text1, '모듈 2에서'], ['odom', 0.6, 2.75, C.accent3, C.background1, '브리지'], ['base_footprint', 0.6, 3.9, C.text1, C.background1, '브리지'], ['base_link', 0.6, 5.05, C.text1, C.background1, 'URDF']];
  tf.forEach(([n, x, y, f, col, who], i) => {
    box(s, x, y, 2.8, 0.75, f);
    text(s, n, { x, y, w: 2.8, h: 0.75, fontSize: 15, bold: true, fontFace: MONO, color: col, align: 'center', valign: 'middle' });
    if (i > 0) { arrow(s, x + 1.4, y - 0.4, x + 1.4, y - 0.02); text(s, who, { x: x + 1.5, y: y - 0.42, w: 1.6, h: 0.38, fontSize: 12, color: C.text2 }); }
  });
  [['lidar_link', 1.55], ['camera_link → camera_optical_frame', 2.55], ['openarm_left/right_… (팔 링크들)', 3.55], ['left/right_wheel_link', 4.55]].forEach(([n, y]) => {
    box(s, 4.3, y + 1.0, 4.2, 0.7, C.background2);
    text(s, n, { x: 4.35, y: y + 1.0, w: 4.1, h: 0.7, fontSize: 13, bold: true, fontFace: MONO, align: 'center', valign: 'middle' });
    arrow(s, 3.45, 5.42, 4.25, y + 1.35);
  });
  text(s, 'base_link에 붙은 것들 (URDF)', { x: 4.3, y: 1.95, w: 4.2, h: 0.45, fontSize: 14, color: C.text2, align: 'center' });
  callout(s, 'analogy', 8.8, 1.6, 3.9, 2.4, '"내 왼쪽 30 cm"와 "교실 앞문에서 3 m"는 같은 곳일 수 있다. TF는 이런 말을 서로 바꿔 준다.');
  callout(s, 'why', 8.8, 4.2, 3.9, 2.5, '카메라가 본 상자 위치(camera 기준)를 팔이 쓰려면 base 기준으로 바꿔야 한다. TF가 자동으로 계산한다.');

  s = content('실습 4. TF 트리와 RViz 보기', TAG, 'view_frames는 TF 나무를 PDF로 그려 줍니다. 홈 폴더에 frames_날짜.pdf가 생깁니다. RViz에서 TF 표시를 켜고, 관절 명령을 보내 MuJoCo와 RViz의 팔이 똑같이 움직이는지 확인시킵니다. 체크포인트 1-3.');
  code(s, '$ cd ~ && ros2 run tf2_tools view_frames \\\n    --ros-args -p use_sim_time:=true\n$ explorer.exe .          # frames_<날짜>.pdf 열기\n\n# 팔 관절 하나 움직이기\n$ ros2 topic pub --once /joint_commands \\\n    sensor_msgs/msg/JointState \\\n    "{name: [openarm_left_joint1], position: [-0.8]}"\n\n# 10초 팔 데모, 원위치\n$ ros2 run unbolt_mujoco_bridge arm_demo \\\n    --ros-args -p use_sim_time:=true\n$ ros2 service call /mujoco_bridge/reset std_srvs/srv/Trigger', 0.6, 1.5, 6.8, 5.2, 13);
  img(s, 'step2_rviz.jpg', 7.7, 1.5, 5.0, 3.2, 'RViz: 로봇 모델, LiDAR 점, TF 좌표축');
  callout(s, 'ok', 7.7, 4.9, 5.0, 1.8, 'PDF에 odom → base_footprint → base_link … 나무. MuJoCo와 RViz의 팔이 똑같이 움직인다. ✅ 1-3');

  s = content('로봇은 두 벌로 기술한다: MJCF와 URDF', TAG, '같은 로봇이 두 파일에 있습니다. RViz의 팔과 MuJoCo의 팔이 똑같이 움직이면 두 모델이 일치하는 것입니다. 개발 때 FK 비교 스크립트로 정확히 일치함을 확인했습니다. 치수를 바꿀 때는 꼭 둘 다 고쳐야 합니다.');
  card(s, { x: 0.6, y: 1.5, w: 5.6, h: 2.3, head: 'MJCF: models/unbolt_robot.xml', body: 'MuJoCo 물리용: 질량, 관성, 충돌, 모터. 팔은 OpenArm 공식 MJCF를 <attach>로 붙인다.', iconName: 'FaCube', accent: C.accent3, headSize: 17 });
  card(s, { x: 0.6, y: 4.0, w: 5.6, h: 2.3, head: 'URDF: unbolt.urdf.xacro', body: 'ROS용: TF, RViz, MoveIt, Nav2. 팔은 OpenArm xacro 매크로 + preset 파일.', iconName: 'FaSitemap', accent: C.accent2, headSize: 17 });
  img(s, 'robot_front.png', 6.5, 1.5, 6.2, 3.5, '주행형 양팔로봇 앞모습');
  text(s, '치수를 바꾸면 양쪽을 같이 고친다', { x: 6.5, y: 5.15, w: 6.2, h: 0.4, fontSize: 16, bold: true });
  ['바퀴 r 0.08', '간격 0.45', 'LiDAR (0.22, 0, 0.13)', '받침대 (-0.05, 0, 0.11)'].forEach((t, i) => pill(s, t, 6.5 + (i % 2) * 3.15, 5.65 + Math.floor(i / 2) * 0.48, 3.0, C.background2, C.text1, 13));

  s = content('알아 두면 좋은 함정: 접촉은 큰 값을 쓴다', TAG, '모델 파일을 읽을 때 함께 짚는 함정입니다. "제어가 안 된다"는 증상이 실제로는 물리 모델 때문인 경우가 많다는 교훈입니다. 실제로 Nav2가 제자리 회전을 하다 멈추는 증상으로 나타났던 버그입니다.');
  box(s, 0.6, 1.5, 3.4, 1.5, C.background2);
  text(s, '캐스터\ncondim = 1 (마찰 없음)', { x: 0.8, y: 1.6, w: 3.0, h: 1.3, fontSize: 16, bold: true, align: 'center', valign: 'middle' });
  text(s, '+', { x: 4.0, y: 1.5, w: 0.6, h: 1.5, fontSize: 30, bold: true, align: 'center', valign: 'middle', color: C.text2 });
  box(s, 4.6, 1.5, 3.4, 1.5, C.background2);
  text(s, '바닥\ncondim = 3 (마찰 있음)', { x: 4.8, y: 1.6, w: 3.0, h: 1.3, fontSize: 16, bold: true, align: 'center', valign: 'middle' });
  arrow(s, 8.1, 2.25, 8.7, 2.25);
  box(s, 8.8, 1.5, 3.9, 1.5, C.accent6);
  text(s, '실제 접촉 = 3 (큰 쪽)\n캐스터가 버텨서 회전 멈춤', { x: 9.0, y: 1.6, w: 3.5, h: 1.3, fontSize: 16, bold: true, align: 'center', valign: 'middle', color: C.background1 });
  text(s, '해결: priority를 주면 우선순위가 높은 쪽의 값을 쓴다', { x: 0.6, y: 3.35, w: 12.1, h: 0.5, fontSize: 18, bold: true });
  code(s, '<geom type="sphere" size="0.03" condim="1" priority="2" friction="0 0 0" .../>', 0.6, 3.95, 12.1, 0.75, 15);
  callout(s, 'why', 0.6, 4.95, 12.1, 1.75, 'MuJoCo는 두 물체가 닿을 때 둘 중 "더 끈끈한" 설정을 쓴다. 캐스터만 미끄럽게 해도 바닥이 끈끈하면 소용없다. 증상은 "제어기가 이상하다"처럼 보여서 찾기 어렵다.');

  s = content('LiDAR = 광선 360개', TAG, '_publish_scan()입니다. 실제 LiDAR는 한 바퀴 도는 동안 시간이 흐르지만 여기서는 한순간에 쏩니다. 로봇 자신의 몸은 다른 geom 그룹에 두어서 자기 팔을 장애물로 보지 않게 합니다.');
  const cx = 2.6, cy = 3.9;
  for (let k = 0; k < 24; k++) {
    const a = (k / 24) * 2 * Math.PI, rr = k % 6 === 2 ? 1.0 : 1.7;
    s.addShape(L.S.LINE, { x: Math.min(cx, cx + rr * Math.cos(a)), y: Math.min(cy, cy - rr * Math.sin(a)), w: Math.abs(rr * Math.cos(a)), h: Math.abs(rr * Math.sin(a)), flipH: Math.cos(a) < 0, flipV: Math.sin(a) > 0, line: { color: L.HEX.accent4, width: 1.25 } });
  }
  box(s, cx - 0.35, cy - 0.25, 0.7, 0.5, C.accent1);
  text(s, '로봇', { x: cx - 0.35, y: cy - 0.25, w: 0.7, h: 0.5, fontSize: 12, bold: true, color: C.background1, align: 'center', valign: 'middle', margin: 0 });
  box(s, cx + 0.55, cy - 1.35, 0.5, 0.9, C.text2);
  text(s, '광선 360개를 쏘아\n처음 맞는 곳까지의 거리', { x: 0.6, y: 5.85, w: 4.2, h: 0.8, fontSize: 14, color: C.text2, align: 'center' });
  code(s, 'origin = d.site_xpos[lidar_site].copy()   # LiDAR 위치\nvec = lidar_dirs @ R.T                    # 360방향 회전\nfor k in range(n):                        # 광선 하나씩\n    dist[k] = mujoco.mj_ray(m, d, origin, vec[k],\n        LIDAR_GEOMGROUP, 1, -1, geomid)   # 그룹 0,1만\nranges = dist.copy()\nhit = ranges >= 0.0\nranges[hit] += rng.normal(0, 0.01, hit.sum())  # 노이즈 1 cm\nranges[~hit] = math.inf                   # 안 맞으면 inf', 5.0, 1.5, 7.7, 3.3, 13);
  callout(s, 'analogy', 5.0, 5.0, 3.75, 1.7, '박쥐가 초음파로 벽까지 거리를 재는 것과 같다.');
  callout(s, 'why', 8.95, 5.0, 3.75, 1.7, '노이즈를 일부러 넣는다. 실제 센서도 1~2 cm 흔들린다.');

  s = content('실습 5. LiDAR 값 직접 보기', TAG, 'ranges는 한 줄짜리 배열이라 쉼표로 나눠서 봅니다. 0번 빔이 뒤쪽(-180°), 180번이 정면입니다. 키보드로 벽에 다가가며 정면 거리가 줄어드는지 확인시킵니다. RViz LaserScan의 Size를 0.05로 키우면 잘 보입니다.');
  lab(s, {
    cmd: '# 터미널 2: 키보드로 운전 (i 앞, , 뒤, j/l 회전, k 정지)\n$ ros2 run teleop_twist_keyboard teleop_twist_keyboard\n\n# 터미널 3: 정면(0°) 빔의 거리 [m]\n#  0번 빔 = 뒤쪽(-180°), 180번 = 정면\n#  i번 빔이 (i+2)번째 줄\n$ ros2 topic echo /scan --once --field ranges \\\n    | tr \',\' \'\\n\' | sed -n 182p',
    cmdH: 3.4,
    explain: ['teleop 터미널을 클릭한 상태에서 키를 눌러야 한다', '벽에 다가가면 RViz의 빨간 점도 가까워진다'],
    ok: '벽 쪽으로 가까이 갈수록 정면 거리 숫자가 작아진다 (예: 4.29 → 1.2).',
    fail: '로봇이 안 움직이면 teleop 창을 클릭했는지, ros2 topic echo /cmd_vel로 명령이 나가는지 확인',
  });

  s = content('휠 오도메트리: 바퀴로 위치 계산하기', TAG, '_update_odometry()입니다. 두 바퀴가 굴러간 거리의 평균이 앞으로 간 거리, 차이가 회전입니다. 예: 왼쪽 10 cm, 오른쪽 12 cm면 앞으로 11 cm, 회전 (12-10)/45 = 0.044 rad ≈ 2.5° 왼쪽.');
  box(s, 0.6, 1.5, 5.2, 3.2, C.background2);
  box(s, 2.3, 2.3, 1.8, 1.6, C.accent1);
  text(s, '로봇', { x: 2.3, y: 2.3, w: 1.8, h: 1.6, fontSize: 15, bold: true, color: C.background1, align: 'center', valign: 'middle' });
  box(s, 1.75, 2.0, 0.5, 0.35, C.text1); box(s, 1.75, 3.85, 0.5, 0.35, C.text1);
  text(s, '왼쪽 바퀴 dl', { x: 0.75, y: 1.6, w: 2.6, h: 0.4, fontSize: 13, bold: true });
  text(s, '오른쪽 바퀴 dr', { x: 0.75, y: 4.2, w: 2.6, h: 0.4, fontSize: 13, bold: true });
  text(s, '간격 0.45 m', { x: 4.2, y: 2.9, w: 1.5, h: 0.4, fontSize: 13, color: C.text2 });
  code(s, 'ds   = (dl + dr) / 2          # 앞으로 간 거리\ndyaw = (dr - dl) / 0.45       # 회전한 각도 [rad]\nmid  = yaw + dyaw / 2         # 중간 방향으로\nx   += ds * cos(mid)\ny   += ds * sin(mid)\nyaw += dyaw', 6.1, 1.5, 6.6, 3.2, 14);
  callout(s, 'analogy', 0.6, 4.95, 6.0, 1.75, '눈 감고 걸음 수로 거리 짐작하기. 처음엔 잘 맞지만 오래 걸을수록 틀어진다.');
  callout(s, 'why', 6.75, 4.95, 5.95, 1.75, '바퀴가 미끄러지거나 바닥이 고르지 않으면 계산이 실제와 어긋나고, 그 오차가 계속 쌓인다.');

  s = content('실습 6. 오도메트리 vs 진짜 위치', TAG, '키보드로 1~2분 돌아다닌 뒤 두 값을 비교해 cm 단위로 적게 합니다. 이 숫자는 모듈 2 도입에서 다시 꺼냅니다(SLAM/AMCL이 이 오차를 바로잡는다). 체크포인트 1-4.');
  lab(s, {
    cmd: '# 키보드로 방을 1~2분 돌아다닌 뒤\n$ ros2 topic echo /odom --field pose.pose.position --once\n$ ros2 topic echo /ground_truth/odom \\\n    --field pose.pose.position --once',
    cmdH: 2.0,
    explain: ['/odom: 바퀴로 계산한 위치 (실제 로봇에도 있음)', '/ground_truth/odom: 시뮬레이터가 아는 진짜 위치 (실제 로봇에는 없음)', '차이 = 오도메트리 오차. 급회전을 많이 할수록 커진다'],
    ok: '두 x, y 값이 몇 cm~수십 cm 다르다. 그 차이를 적는다.\n\n✅ 체크포인트 1-4',
    fail: '"does not appear to be published yet"이면 몇 초 뒤 다시 실행',
  });

  summary('모듈 1 한 장 요약', TAG, [
    ['FaCube', 'MuJoCo = 설계도(MjModel) + 현재 상태(MjData) + mj_step', 'MJCF 파일에 body, joint, geom, actuator로 로봇과 세계를 적는다'],
    ['FaLink', '브리지 = MuJoCo와 ROS 사이의 통역사', '상태·센서는 토픽으로 내보내고, /cmd_vel 같은 명령은 모터로 넣는다'],
    ['FaClock', '시간의 주인은 시뮬레이터', '/clock + use_sim_time:=true 를 모든 노드에'],
    ['FaSitemap', 'TF = 좌표계 나무', 'odom→base는 브리지, 몸 안은 robot_state_publisher(URDF)가 낸다'],
    ['FaSatelliteDish', '센서는 시뮬레이터 안에서 계산', 'LiDAR = 광선 360개, 오도메트리 = 바퀴 각도 적분 (오차가 쌓인다)'],
  ], '다섯 줄로 정리합니다. 퀴즈로 넘어가기 전에 학생에게 한 줄씩 읽게 해도 좋습니다.');

  quiz('모듈 1 셀프 체크', TAG, [
    ['MjModel과 MjData 중 시뮬레이션 중에 계속 바뀌는 것은?', 'MjData (위치, 속도, 접촉 등 현재 상태). MjModel은 설계도라 바뀌지 않는다.'],
    ['다른 노드에 use_sim_time:=true를 주지 않으면 어떤 문제가 생길까?', '벽시계(1970년 기준 초)를 써서 센서·TF의 시뮬레이션 시각과 어긋나 "extrapolation" 오류로 데이터를 버린다.'],
    ['/joint_states는 브리지가, 팔 링크의 TF는 robot_state_publisher가 낸다. 왜 나눴을까?', '물리 상태(관절각)는 시뮬레이터만 알고, 링크 사이 기하는 URDF에 있다. 나누면 실제 로봇에서도 같은 robot_state_publisher를 그대로 쓴다.'],
    ['URDF의 LiDAR 위치를 MJCF와 다르게 적으면 RViz의 LiDAR 점은 어떻게 보일까?', '실제 벽과 어긋난 위치에 찍힌다(적은 만큼 밀려 보임). SLAM 지도도 휘거나 겹친다.'],
    ['오도메트리 오차가 시간이 갈수록 커지는 이유는?', '매 순간의 작은 오차(미끄러짐 등)를 계속 더해 가는 적분이라 오차가 누적된다.'],
  ], '답은 발표자 노트에 있습니다. 옆 사람과 먼저 이야기해 보세요.');

  s = content('모듈 1 과제', TAG, '기본 과제 A의 my_scene.xml은 모듈 2 실습(지도에 없는 장애물)에서도 씁니다. group="3"을 주면 LiDAR에 안 보이는 이유도 질문해 보세요(LiDAR는 그룹 0, 1만 봄).');
  card(s, { x: 0.6, y: 1.5, w: 6.0, h: 2.55, head: '기본 A. 장애물 추가하기', iconName: 'FaCube', accent: C.accent3, body: 'scene.xml을 my_scene.xml로 복사하고 상자 하나 추가\n→ sim.launch.py model_path:=$UNBOLT_ROOT/models/my_scene.xml\n→ LiDAR에 보이는지 확인. group="3"이면?', bodySize: 14 });
  code(s, '<geom name="my_box" type="box" size="0.2 0.2 0.3"\n      pos="1.5 1.0 0.3" rgba="0.2 0.6 0.2 1"/>', 6.75, 1.5, 5.95, 1.2, 13);
  card(s, { x: 6.75, y: 2.85, w: 5.95, h: 1.2, head: '기본 B. LiDAR 파라미터 바꾸기', bodySize: 14, headSize: 16 });
  code(s, '$ ros2 run unbolt_mujoco_bridge mujoco_bridge --ros-args \\\n    -p model_path:=$UNBOLT_ROOT/models/scene.xml \\\n    -p lidar_samples:=720 -p lidar_noise_std:=0.05\n$ ros2 topic echo /scan --once --field angle_increment', 0.6, 4.3, 7.4, 1.6, 13);
  text(s, '빔 간격이 0.01745(360빔) → 0.00873(720빔)으로 바뀌는지, 노이즈 5 cm에서 점이 어떻게 보이는지 캡처', { x: 0.6, y: 6.0, w: 7.4, h: 0.7, fontSize: 14, color: C.text2 });
  card(s, { x: 8.3, y: 4.3, w: 4.4, h: 2.4, head: '도전. 범퍼 센서', iconName: 'FaBolt', accent: C.accent1, body: '섀시가 벽에 닿으면 /bumper (Bool)를 True로 50 Hz 발행. 힌트: d.contact, m.geom_bodyid', bodySize: 14, fill: C.text1, headColor: C.background1, bodyColor: C.accent5 });
};
