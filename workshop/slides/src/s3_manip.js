// 모듈 3: MoveIt 2 + Pick & Place
const L = require('./lib');
const { C, HEX, MONO, text, box, circleIcon, pill, card, callout, code, bullets, arrow, img, marker, table, step, flow, lab, quiz, summary, content } = L;
const TAG = '모듈 3 · 조작';

module.exports = function build() {
  let s;
  L.section('모듈 3: MoveIt 2 + Pick & Place', '모듈 3 · 2일차 09:30–11:30', 'MoveIt 2 양팔 제어\n모바일 매니퓰레이션', [
    '관절 공간과 작업 공간, FK와 IK의 차이를 안다',
    'MoveIt 2가 계획한 궤적이 MuJoCo까지 가는 길을 따라간다',
    'Pose goal, 직선 경로, 그리퍼를 Python에서 보낸다',
    '카메라로 마커를 찾아 주행 → 정밀 접근 → 집기 → 놓기를 잇는다',
  ], '2일차 시작. 어제 만든 주행 위에 팔을 얹습니다.');

  s = content('오늘 오전에 할 일', TAG, '2시간 흐름입니다. RViz로 팔을 움직여 보고(실습 1~2), Python으로 움직이고(실습 3), 카메라로 상자를 찾아(실습 4) 집어서 옮깁니다(실습 5).');
  [['09:30', '개념', '팔 제어의 기본, MoveIt 2, 카메라'], ['09:50', '실습 1~2', 'RViz로 팔 계획·실행, 자동 테스트'], ['10:20', '실습 3', 'Python으로 팔 움직이기'], ['10:45', '실습 4~5', '마커 검출, Pick & Place 전체'], ['11:15', '정리', '요약, 퀴즈, 과제']].forEach(([t, h, b], i) => {
    const y = 1.5 + i * 1.03;
    pill(s, t, 0.6, y + 0.22, 1.2, i % 2 ? C.accent1 : C.text1);
    box(s, 2.1, y, 10.6, 0.82, C.background2);
    text(s, h, { x: 2.35, y, w: 2.2, h: 0.82, fontSize: 18, bold: true, valign: 'middle' });
    text(s, b, { x: 4.6, y, w: 8.0, h: 0.82, fontSize: 16, color: C.text2, valign: 'middle' });
  });

  s = content('팔을 움직이는 두 가지 방법: FK와 IK', TAG, '관절 각도를 주면 손 위치가 정해집니다(FK, 쉬움). 반대로 손을 어디에 두고 싶은지 주고 관절 각도를 찾는 것이 IK(어려움, 답이 없거나 여러 개)입니다. 컵을 잡을 때 우리는 "손을 컵에"라고 생각하지 팔꿈치 각도를 생각하지 않습니다. 로봇에게도 IK가 필요한 이유입니다.');
  box(s, 0.6, 1.6, 4.4, 2.4, C.accent3);
  text(s, '관절 공간\n(joint space)\n\njoint1 = 0.3 rad\njoint2 = -0.5 rad … × 7', { x: 0.7, y: 1.6, w: 4.2, h: 2.4, fontSize: 16, bold: true, color: C.background1, align: 'center', valign: 'middle' });
  box(s, 8.3, 1.6, 4.4, 2.4, C.accent1);
  text(s, '작업 공간\n(task space)\n\n손 위치 (0.38, -0.15, 0.80)\n손 방향 (15° 아래)', { x: 8.4, y: 1.6, w: 4.2, h: 2.4, fontSize: 16, bold: true, color: C.background1, align: 'center', valign: 'middle' });
  arrow(s, 5.1, 2.35, 8.2, 2.35); arrow(s, 8.2, 3.25, 5.1, 3.25);
  text(s, 'FK (정기구학): 계산 쉬움, 답 하나', { x: 5.1, y: 1.85, w: 3.1, h: 0.45, fontSize: 13, bold: true, align: 'center' });
  text(s, 'IK (역기구학): 어려움, 답이 없거나 여러 개', { x: 5.1, y: 3.35, w: 3.1, h: 0.6, fontSize: 13, bold: true, align: 'center', color: C.accent1 });
  callout(s, 'analogy', 0.6, 4.3, 6.0, 2.4, '컵을 잡을 때 "팔꿈치 40°, 어깨 20°"라고 생각하지 않는다. "손을 컵에"라고 생각하면 뇌가 각도를 정한다. 그 뇌의 역할이 IK.');
  callout(s, 'why', 6.75, 4.3, 5.95, 2.4, '손이 닿지 않는 곳(너무 멀거나 몸 안쪽)은 IK 답이 없다. 실습 1에서 "계획 실패"가 나오는 가장 흔한 이유.');

  s = content('7자유도 팔이란?', TAG, '사람 팔도 어깨 3 + 팔꿈치 1 + 손목 3 = 7자유도입니다. 손 위치·방향(6개 값)을 정하는 데 6개면 충분하지만, 하나가 더 있으면 같은 손 위치에서 팔꿈치를 다른 곳에 둘 수 있습니다(장애물 피하기). 대신 IK 답이 무수히 많아 계획기가 하나를 골라야 합니다.');
  img(s, 'robot_front.png', 0.6, 1.5, 6.4, 3.6, 'OpenArm 양팔');
  table(s, [['부위', '관절', '사람으로 치면'], ['joint1~3', '회전 3개', '어깨 (앞뒤, 옆, 비틀기)'], ['joint4', '회전 1개', '팔꿈치'], ['joint5~7', '회전 3개', '손목'], ['finger_joint1', '그리퍼', '엄지와 검지로 집기']], 7.3, 1.5, 5.4, [1.6, 1.4, 2.4], 14);
  callout(s, 'why', 0.6, 5.35, 12.1, 1.35, '6개 값(손 위치 x, y, z + 방향 3개)을 맞추는데 관절이 7개라 여유가 하나 생긴다. 그 여유로 팔꿈치를 테이블이나 몸에서 멀리 둘 수 있다.');

  s = content('MoveIt 2가 해 주는 일', TAG, '"손을 저기로"라는 요청 하나에 MoveIt이 네 가지를 차례로 합니다. 우리는 목표만 주고, 충돌 없는 경로와 시간표는 MoveIt이 만듭니다.');
  [['IK', '목표 손 위치에 맞는 관절 각도 찾기 (KDL)'], ['경로 계획', '지금 자세에서 목표까지 부딪히지 않는 길 (OMPL)'], ['시간 매개화', '속도·가속도 제한 안에서 언제 어디 있을지 시간표'], ['실행', '컨트롤러에 궤적을 보내고 끝날 때까지 지켜보기']].forEach(([h, b], i) => step(s, i + 1, h, b, 0.6 + i * 3.08, 1.6, 2.9, 1.3));
  flow(s, [['RViz / Python\n목표', C.accent5, C.text1], ['move_group\nIK · OMPL · 충돌', C.text1, C.background1], ['FollowJointTrajectory\n액션 × 4', C.accent3, C.background1], ['브리지\ntrajectory_server', C.accent2, C.background1], ['MuJoCo\n위치 모터', C.accent1, C.background1]], 0.6, 3.9, 12.1, 1.3, 0.3, 13);
  callout(s, 'why', 0.6, 5.5, 12.1, 1.2, 'ros2_control 없이 브리지가 FollowJointTrajectory 액션 서버를 직접 제공한다. MoveIt 입장에서는 실제 로봇 컨트롤러와 똑같이 보인다.');

  s = content('SRDF: 계획 그룹과 이름 붙은 자세', TAG, 'URDF가 "몸의 구조"라면 SRDF는 "MoveIt에게 알려 주는 사용법"입니다. 어느 관절을 한 묶음으로 계획할지(그룹), 자주 쓰는 자세(home, tuck 등), 서로 부딪힐 수 없는 링크 쌍(자기충돌 행렬)을 적습니다. 자기충돌 행렬은 Setup Assistant가 이 로봇에서 멈춰서 MuJoCo로 계산했습니다.');
  table(s, [['그룹', '관절', '용도'], ['left_arm / right_arm', 'openarm_*_joint1..7', '한 팔 계획, 끝점 grasp_frame (손가락 끝)'], ['both_arms', '14개', '두 팔 동시 (home, ready, tuck)'], ['left_gripper / right_gripper', 'finger_joint1', 'open / closed']], 0.6, 1.5, 12.1, [3.7, 3.4, 5.0], 16);
  text(s, '이름 붙은 자세 (named state)', { x: 0.6, y: 3.55, w: 6, h: 0.45, fontSize: 18, bold: true });
  [['home', '팔을 아래로'], ['ready', '앞으로 준비'], ['tuck', '주행용 접은 자세'], ['open / closed', '그리퍼']].forEach(([a, b], i) => {
    const x = 0.6 + i * 3.08;
    box(s, x, 4.1, 2.85, 1.3, C.background2);
    text(s, a, { x: x + 0.2, y: 4.2, w: 2.45, h: 0.55, fontSize: 18, bold: true, fontFace: MONO });
    text(s, b, { x: x + 0.2, y: 4.8, w: 2.45, h: 0.5, fontSize: 15, color: C.text2 });
  });
  callout(s, 'analogy', 0.6, 5.6, 12.1, 1.1, 'URDF = 몸의 설계도, SRDF = 그 몸을 쓰는 사용 설명서 (어느 팔을 같이 쓰고, 자주 하는 자세는 무엇인지)');

  s = content('planning scene: MoveIt이 아는 세상', TAG, 'MoveIt은 MuJoCo의 세계를 모릅니다. planning scene에 넣어 준 것만 피합니다. 그래서 집을 때 테이블 상판을 상자(충돌 물체)로 넣어 줍니다. 계획이 끝나면 다시 빼는 이유: 로봇이 주행하면 base 기준 테이블 위치가 바뀌는데 planning scene의 상판은 그대로 남기 때문입니다.');
  box(s, 0.6, 1.5, 5.9, 3.4, C.background2);
  text(s, 'MuJoCo가 아는 것', { x: 0.85, y: 1.6, w: 5.4, h: 0.45, fontSize: 17, bold: true });
  bullets(s, ['방, 벽, 테이블 네 개, 상자 세 개', '로봇의 모든 부품', '중력, 마찰, 접촉'], 0.85, 2.15, 5.4, 2.6, 16);
  box(s, 6.8, 1.5, 5.9, 3.4, C.accent3);
  text(s, 'MoveIt이 아는 것 (planning scene)', { x: 7.05, y: 1.6, w: 5.4, h: 0.45, fontSize: 17, bold: true, color: C.background1 });
  bullets(s, ['로봇 자신 (URDF + 관절 상태)', '우리가 넣어 준 충돌 물체만', '→ 집을 때 테이블 상판 (0.5 × 0.8 × 0.04 m)'], 7.05, 2.15, 5.4, 2.6, 16, C.background1);
  callout(s, 'analogy', 0.6, 5.15, 6.0, 1.55, '가구 배치도: MoveIt은 우리가 그려 준 배치도만 보고 길을 찾는다. 배치도에 없는 가구에는 부딪힌다.');
  callout(s, 'why', 6.75, 5.15, 5.95, 1.55, '상판을 넣으면 계획이 상판 아래로 손을 넣지 않는다. 계획 후 빼는 건 주행하면 위치가 틀려지기 때문.');

  s = content('실습 1. RViz MotionPlanning', TAG, 'MuJoCo 뷰어의 팔이 RViz 계획과 똑같이 움직이는지 보게 합니다. 손이 닿지 않는 곳으로 끌면 계획이 실패하는 것도 일부러 경험하게 하세요(IK 해 없음). 체크포인트 3-1.');
  img(s, 'step4_moveit_rviz.jpg', 0.6, 1.5, 6.6, 4.4, 'RViz MotionPlanning 패널과 양팔 로봇');
  code(s, '$ ros2 launch airlab_moveit_config moveit.launch.py', 0.6, 6.05, 6.6, 0.65, 13);
  step(s, 1, 'right_arm → tuck → home', 'Planning Group 고르고 Goal State → Plan → Execute', 7.5, 1.6, 5.2);
  step(s, 2, '손 끝 마커 끌기', '화살표·고리를 드래그 → Plan & Execute', 7.5, 2.85, 5.2);
  step(s, 3, '닿지 않는 곳으로', '계획 실패를 일부러 경험 (IK 해 없음)', 7.5, 4.1, 5.2);
  step(s, 4, 'both_arms → ready / tuck', '두 팔 동시 계획 ✅ 3-1', 7.5, 5.35, 5.2);

  s = content('실습 2. 자동 테스트와 궤적 흐름 보기', TAG, '같은 launch를 켜 둔 채 다른 터미널에서 실행합니다. 6개 동작(관절 목표, 자세 목표, 그리퍼)을 계획·실행하고 목표와 실제 관절 각도 오차를 출력합니다. 체크포인트 3-2.');
  lab(s, {
    cmd: '$ ros2 run airlab_moveit_config moveit_test.py \\\n    --ros-args -p use_sim_time:=true\n\n# 실행되는 동안 다른 터미널에서\n$ ros2 action list\n$ ros2 topic echo /joint_states --field position --once',
    cmdH: 2.6,
    explain: ['ros2 action list: /right_arm_controller/follow_joint_trajectory 등 4개가 보인다', '이 액션 서버들은 브리지 안에 있다 (trajectory_server.py)'],
    ok: '6/6 성공, 관절 오차가 아주 작다 (0.01 rad 안팎).\n\n✅ 체크포인트 3-2',
    fail: 'goal rejected / 시간 초과 → moveit.launch.py가 다 켜질 때까지 10~20초 기다렸다가 다시',
  });

  s = content('Pose goal vs 직선 경로 (Cartesian path)', TAG, 'move_to_pose는 목표 자세 하나만 주고 경로는 OMPL이 찾습니다. 중간에 손이 크게 휘어 돌아갈 수 있습니다. move_linear는 손끝이 직선으로 움직이는 경로를 만듭니다. 집기 직전 접근, 들어 올리기처럼 경로 자체가 중요할 때 씁니다.');
  box(s, 0.6, 1.5, 5.95, 3.0, C.background2);
  text(s, 'move_to_pose (자세 목표)', { x: 0.85, y: 1.6, w: 5.5, h: 0.45, fontSize: 17, bold: true });
  s.addShape(L.S.ARC, { x: 1.3, y: 2.3, w: 4.4, h: 2.6, angleRange: [180, 360], line: { color: HEX.accent3, width: 3, dashType: 'dash' } });
  circleIcon(s, 'FaHandPaper', 1.05, 3.35, 0.5, C.accent3); circleIcon(s, 'FaBox', 5.45, 3.35, 0.5, C.accent1);
  text(s, '길은 MoveIt 마음대로 (휘어질 수 있음)', { x: 0.85, y: 4.0, w: 5.5, h: 0.4, fontSize: 14, color: C.text2, align: 'center' });
  box(s, 6.75, 1.5, 5.95, 3.0, C.text1);
  text(s, 'move_linear (직선 경로)', { x: 7.0, y: 1.6, w: 5.5, h: 0.45, fontSize: 17, bold: true, color: C.background1 });
  s.addShape(L.S.LINE, { x: 7.7, y: 3.6, w: 4.0, h: 0, line: { color: HEX.accent1, width: 3 } });
  circleIcon(s, 'FaHandPaper', 7.2, 3.35, 0.5, C.accent3); circleIcon(s, 'FaBox', 11.6, 3.35, 0.5, C.accent1);
  text(s, '손끝이 자를 대고 그은 듯 직선 (98% 못 만들면 실패)', { x: 7.0, y: 4.0, w: 5.5, h: 0.4, fontSize: 14, color: C.accent5, align: 'center' });
  table(s, [['', 'move_to_pose', 'move_linear'], ['주는 것', '목표 자세 하나', '지금 위치에서 얼마나 (dx, dy, dz)'], ['경로', 'OMPL이 찾음', '직선 (GetCartesianPath)'], ['쓰는 곳', '멀리 이동 (pre-grasp까지)', '접근, 들기, 내리기, 빠지기']], 0.6, 4.75, 12.1, [2.0, 4.6, 5.5], 15);

  s = content('실습 3. Python으로 팔 움직이기', TAG, 'arm_play.py(교재 03 실습 3)의 핵심입니다. bringup.launch.py는 주행·카메라·MoveIt을 한 번에 켭니다. z를 0.70, 0.60으로 낮춰 보고 어디서부터 실패하는지, 이유가 도달 범위인지 섀시 충돌인지 토론합니다. 체크포인트 3-3.');
  code(s, '$ ros2 launch airlab_manipulation bringup.launch.py   # 터미널 1\n\n# ~/arm_play.py\ns = RobotSkills(); s.wait_ready()\ns.move_arms(\'home\')                              # 이름 붙은 자세\ns.set_gripper(\'right\', -0.6)                     # 열기 (오른쪽은 음수)\ns.move_to_pose(\'right\', (0.38, -0.15, 0.80),\n               grasp_rotation(0.0), \'pose\')       # 자세 목표\nfor dz in (-0.05, +0.05):\n    s.move_linear(\'right\', (0, 0, dz), \'linear\')  # 직선 5 cm\ns.set_gripper(\'right\', 0.0); s.move_arms(\'tuck\')\n\n$ python3 ~/arm_play.py --ros-args -p use_sim_time:=true', 0.6, 1.5, 7.6, 5.2, 13);
  callout(s, 'ok', 8.5, 1.5, 4.2, 1.9, '팔이 home → 앞으로 뻗기 → 5 cm 내렸다 올리기 → tuck. 오류 없이 끝 ✅ 3-3');
  callout(s, 'tip', 8.5, 3.6, 4.2, 1.5, '좌표는 base_footprint 기준 (앞 +x, 왼쪽 +y, 위 +z) [m]', '좌표 읽는 법');
  callout(s, 'why', 8.5, 5.3, 4.2, 1.4, 'z를 0.60으로 내리면? 손이 섀시에 가까워져 실패. 왜인지 토론');

  s = content('이 로봇에서 집기가 어려운 이유', TAG, 'skills.py의 상수(GRASP_PITCH, GRASP_HEIGHT, GRASP_XY)와 lower_until_contact가 이 네 문제에 대한 답입니다. 기본 과제 B에서 이 값을 바꿔 무엇이 실패하는지 봅니다.');
  [['도달 범위가 좁다', '팔이 아래로 늘어진 구조라 앞쪽 x 0.30~0.45 m만. 테이블 0.65 m, 섀시가 상판 아래로 들어가게', 'FaRobot'], ['손과 상판 충돌', '계획할 때만 상판을 planning scene에 추가, 15° 아래로 접근, 상자 중심 1.5 cm 위를 집기', 'FaLayerGroup'], ['가까이 가면 마커가 가려짐', '마지막으로 본 마커 위치를 odom 좌표로 기억하고 오도메트리로 이어 씀', 'FaEye'], ['놓을 높이가 몇 cm 틀림', '직선으로 내리다 3 cm 이상 내려간 뒤 막히면 "닿았다": guarded move', 'FaHandPaper']].forEach(([h, b, ic], i) => {
    const x = 0.6 + (i % 2) * 6.15, y = 1.5 + Math.floor(i / 2) * 2.65;
    card(s, { x, y, w: 5.95, h: 2.45, head: h, body: b, iconName: ic, accent: [C.accent1, C.accent3, C.accent2, C.text1][i], bodySize: 15 });
  });

  s = content('헤드 카메라로 본 세상', TAG, '로봇이 각 테이블 앞에 섰을 때 헤드 카메라 영상입니다(초록 테두리 = ArUco 검출, OpenCV가 그린 것). 아래쪽에 보이는 검은 것은 접은(tuck) 팔입니다. 팔을 펼친 채로 두면 시야를 가려서, 운반·접근 중에는 항상 tuck 자세를 씁니다.');
  img(s, 'headcam_supply.png', 0.6, 1.5, 5.95, 3.35, '1번 공급 테이블 앞 헤드 카메라: 빨간 상자 마커 7과 빈자리 마커 12 검출');
  img(s, 'headcam_work.png', 6.75, 1.5, 5.95, 3.35, '작업대 앞 헤드 카메라: 놓을 자리 마커 1·2·3 검출');
  text(s, '1번 공급 테이블 앞: 상자 마커 7 (3.75 cm), 빈자리 12', { x: 0.6, y: 4.95, w: 5.95, h: 0.4, fontSize: 15, bold: true, align: 'center' });
  text(s, '작업대 앞: 놓을 자리 마커 1·2·3 (7.5 cm)', { x: 6.75, y: 4.95, w: 5.95, h: 0.4, fontSize: 15, bold: true, align: 'center' });
  callout(s, 'why', 0.6, 5.5, 12.1, 1.2, '카메라는 받침대 위(바닥에서 약 1 m)에서 47° 아래를 본다. 아래쪽 검은 것은 접은 팔. 팔을 펴면 시야를 가려서 이동할 때는 항상 tuck.');

  s = content('ArUco 마커로 위치 알아내기', TAG, 'aruco_detector.py가 하는 일 세 단계입니다. 마커는 흑백 격자 무늬에 번호가 들어 있어 빠르고 확실하게 찾을 수 있습니다. 마커 크기를 알기 때문에 사진 한 장으로 거리와 방향까지 계산합니다(다음 장).');
  [['detectMarkers', 'DICT_4X4_50으로\n네 꼭짓점과 번호 찾기'], ['solvePnP', '마커 크기 + 카메라 정보로\n카메라 기준 위치·자세'], ['TF aruco_<id>', '스킬은 base_footprint\n기준으로 읽는다']].forEach(([h, b], i) => {
    const x = 0.6 + i * 4.15;
    box(s, x, 1.6, 3.7, 2.1, i === 1 ? C.accent1 : C.background2);
    const col = i === 1 ? C.background1 : C.text1;
    text(s, h, { x: x + 0.25, y: 1.75, w: 3.2, h: 0.6, fontSize: 19, bold: true, fontFace: MONO, color: col });
    text(s, b, { x: x + 0.25, y: 2.45, w: 3.2, h: 1.1, fontSize: 15, color: col });
    if (i < 2) arrow(s, x + 3.75, 2.65, x + 4.1, 2.65);
  });
  [['마커 7 · 8 · 9', '빨강·초록·파랑 상자 윗면, 3.75 cm'], ['마커 N1 · N2', 'N번 공급 테이블 오른쪽·왼쪽 자리, 7.5 cm'], ['마커 1 · 2 · 3', '작업대 왼쪽·가운데·오른쪽 자리, 7.5 cm']].forEach(([a, b], i) => {
    const x = 0.6 + i * 4.15;
    circleIcon(s, 'FaQrcode', x, 4.05, 0.6, C.text1);
    text(s, a, { x: x + 0.75, y: 4.0, w: 3.0, h: 0.35, fontSize: 16, bold: true });
    text(s, b, { x: x + 0.75, y: 4.35, w: 3.0, h: 0.35, fontSize: 14, color: C.text2 });
  });
  callout(s, 'analogy', 0.6, 5.1, 12.1, 1.6, 'QR 코드와 비슷한 "로봇용 이정표". 번호가 들어 있어서 어느 물건인지 바로 알고, 크기를 알아서 얼마나 떨어져 있는지도 안다.');

  s = content('크기를 알면 거리를 안다: solvePnP', TAG, '멀리 있는 사람의 키가 대략 170 cm라는 걸 알면 작게 보일수록 멀다는 걸 압니다. 카메라도 같습니다. 마커 한 변이 7.5 cm인 걸 알고, 사진에서 몇 픽셀로 보이는지 재면 거리가 나옵니다. 네 꼭짓점이 찌그러진 모양으로 기울어진 방향까지 구합니다.');
  box(s, 0.6, 1.5, 6.4, 3.6, C.background2);
  circleIcon(s, 'FaCamera', 0.9, 2.95, 0.8, C.text1);
  [[3.0, 1.0, '가까우면 크게'], [5.6, 0.5, '2배 멀면 절반 크기']].forEach(([x, sz, t]) => {
    s.addShape(L.S.RECTANGLE, { x, y: 3.35 - sz / 2, w: sz, h: sz, fill: { color: HEX.dk1 }, line: { color: HEX.dk1, width: 0 } });
    s.addShape(L.S.RECTANGLE, { x: x + sz * 0.25, y: 3.35 - sz * 0.25, w: sz * 0.5, h: sz * 0.5, fill: { color: HEX.lt1 }, line: { color: HEX.lt1, width: 0 } });
    text(s, t, { x: x - 0.7, y: 4.2, w: sz + 1.4, h: 0.5, fontSize: 13, align: 'center' });
  });
  arrow(s, 1.75, 3.35, 2.95, 3.35); arrow(s, 4.05, 3.35, 5.55, 3.35);
  code(s, '거리 ≈ 초점거리(픽셀) × 실제 크기 / 보이는 크기(픽셀)\n\n예) 헤드 카메라 초점거리 624 px\n    (720 px, 화각 60°), 마커 7.5 cm가\n    사진에서 56 px로 보이면 → 약 0.84 m', 7.3, 1.5, 5.4, 2.4, 14);
  callout(s, 'analogy', 7.3, 4.1, 5.4, 1.0, '키를 아는 사람이 작게 보이면 멀리 있다', '비유');
  callout(s, 'why', 0.6, 5.35, 12.1, 1.35, '그래서 마커 크기를 정확히 알려 줘야 한다 (aruco_detector의 marker_sizes 파라미터: 상자 0.0375, 놓을 자리 0.075). 크기를 틀리게 주면 거리도 같은 비율로 틀린다.');

  s = content('실습 4. 마커 검출 확인', TAG, 'bringup이 켜진 상태에서 합니다. 로봇을 1번 공급 테이블(남쪽 벽, 하늘색 상판) 쪽으로 돌려야 마커가 보입니다. 체크포인트 3-4는 tf2_echo로 상자까지 거리 읽기입니다.');
  lab(s, {
    cmd: '# 카메라 영상 (검출 결과가 그려짐)\n$ ros2 run rqt_image_view rqt_image_view /aruco/debug_image\n\n# 키보드로 로봇을 1번 공급 테이블 쪽으로 돌리기\n$ ros2 run teleop_twist_keyboard teleop_twist_keyboard\n\n# 로봇 기준 상자 마커 위치\n$ ros2 run tf2_ros tf2_echo base_footprint aruco_7 \\\n    --ros-args -p use_sim_time:=true',
    cmdH: 3.5,
    explain: ['Translation: [x, y, z] = 로봇 기준 상자 위치 [m]', '마커가 안 보이면 TF도 안 나온다 (정상)'],
    ok: '영상에 초록 테두리 + id=7, tf2_echo에 x ≈ 0.8 m 같은 값.\n\n✅ 체크포인트 3-4',
    fail: '아무것도 안 보이면 로봇이 테이블을 향하고 있는지 확인. 팔이 펴져 있으면 시야를 가린다',
  });

  s = content('정밀 접근: 상자를 손 앞 1 cm에 세우기', TAG, 'servo_to_marker()입니다. 차동구동 로봇은 옆으로 갈 수 없어서 "마커까지의 거리"와 "마커가 보이는 방향(방위각)" 두 가지를 맞춥니다. 방향이 맞으면 그 거리만큼 앞뒤로 갑니다. 목표 위치(오른팔 기준 (0.38, -0.15))에 1 cm 안으로 세 번 연속 들어오면 끝입니다.');
  box(s, 0.6, 1.5, 6.0, 4.0, C.background2);
  box(s, 1.2, 3.65, 1.0, 0.8, C.accent1);
  text(s, '로봇', { x: 1.2, y: 3.65, w: 1.0, h: 0.8, fontSize: 13, bold: true, color: C.background1, align: 'center', valign: 'middle' });
  circleIcon(s, 'FaBox', 5.0, 1.9, 0.6, C.accent6);
  s.addShape(L.S.LINE, { x: 2.2, y: 2.2, w: 2.8, h: 1.85, flipV: true, line: { color: HEX.accent3, width: 2, dashType: 'dash' } });
  s.addShape(L.S.LINE, { x: 2.2, y: 4.05, w: 3.6, h: 0, line: { color: HEX.dk2, width: 1.5 } });
  text(s, 'r = 거리', { x: 3.0, y: 2.55, w: 1.6, h: 0.4, fontSize: 14, bold: true, color: C.accent3 });
  text(s, 'φ = 방위각', { x: 3.5, y: 3.55, w: 1.8, h: 0.4, fontSize: 14, bold: true });
  text(s, '앞 (+x)', { x: 5.0, y: 4.15, w: 1.2, h: 0.4, fontSize: 12, color: C.text2 });
  code(s, '회전 속도 w = 1.2 × (φ - 목표φ)   # 최대 0.3 rad/s\n직진 속도 v = 0.8 × (r - 목표r)    # 최대 0.08 m/s\n   (방향이 거의 맞을 때만 직진)\n\nx, y 오차가 1 cm 안 × 3번 연속 → 끝', 6.9, 1.5, 5.8, 2.5, 14);
  callout(s, 'analogy', 6.9, 4.2, 5.8, 1.3, '주차할 때: 먼저 핸들로 방향을 맞추고, 그다음 천천히 앞뒤로', '비유');
  callout(s, 'why', 0.6, 5.75, 12.1, 0.95, '팔이 닿는 범위가 x 0.30~0.45 m뿐이라 Nav2(오차 15 cm)만으로는 부족하다. 카메라로 마지막 수십 cm를 1 cm까지 맞춘다.');

  s = content('마커가 가려지면: 기억 + 오도메트리', TAG, '상자에 가까이 가면 손과 상자가 마커를 가리거나 화면 밖으로 나갑니다. 마지막으로 본 마커 위치를 odom 좌표로 기억해 두고, 로봇이 움직인 만큼 오도메트리로 옮겨서 계속 씁니다. 단, 손에 든 물체의 마커는 기억하지 않습니다(손과 같이 움직이니까).');
  flow(s, [['멀리서 마커 보임', C.accent2, C.background1], ['odom 좌표로 기억', C.accent3, C.background1], ['가까이서 안 보임', C.accent6, C.background1], ['기억 + 오도메트리로 계산', C.accent1, C.background1]], 0.6, 1.7, 12.1, 1.2, 0.35, 15);
  callout(s, 'analogy', 0.6, 3.25, 6.0, 1.9, '어두운 방에서 불을 끄기 직전 문 위치를 기억하고, 걸음 수로 문까지 가는 것', '비유');
  callout(s, 'warn', 6.75, 3.25, 5.95, 1.9, '손에 든 상자의 마커는 기억하지 않는다. 집거나 놓은 뒤에는 그 마커의 기억을 지운다 (위치가 바뀌었으니까).');
  callout(s, 'why', 0.6, 5.4, 12.1, 1.3, '짧은 거리에서는 오도메트리 오차가 작아서(수 mm) 기억한 위치를 믿어도 된다. 오래 움직이면 틀어지니 새로 보이면 바로 갱신한다.');

  s = content('Pick & Place = 스킬을 잇는 상태 기계', TAG, 'pick_place_demo.py는 스킬을 and로 잇습니다. 하나라도 실패하면 거기서 멈춥니다. 줄 끝(집기)은 다음 줄로 이어집니다.');
  ['tuck', '주행: 1번 공급 테이블', '정밀 접근: 마커 7', '집기', '후진', '주행: 작업대', '정밀 접근: 마커 2', '놓기'].forEach((t, i) => {
    const r = Math.floor(i / 4), c = i % 4;
    const x = 0.6 + c * 3.1, y = 1.5 + r * 1.2;
    box(s, x, y, 2.75, 0.8, i === 3 || i === 7 ? C.accent1 : C.background2);
    text(s, `${i + 1}. ${t}`, { x, y, w: 2.75, h: 0.8, fontSize: 15, bold: true, color: i === 3 || i === 7 ? C.background1 : C.text1, align: 'center', valign: 'middle' });
    if (c < 3) arrow(s, x + 2.77, y + 0.4, x + 3.08, y + 0.4);
  });
  arrow(s, 11.95, 2.32, 11.95, 2.68);
  img(s, 'step5_pick_place.jpg', 0.6, 3.75, 12.1, 2.95, 'Pick & Place 장면: 상자를 집고 작업대에 놓는 로봇');

  s = content('pick() 안에서 일어나는 일', TAG, 'skills.py의 pick()을 위에서 아래로 읽은 것입니다. 실패하면 그리퍼를 열고 tuck 한 뒤 다시 닫아 카메라 시야를 비웁니다.');
  [['상자 중심 계산', '마커 위치 - 2.5 cm × 마커 z축 (마커는 윗면에 붙어 있다)'], ['팔·손 방향 고르기', '상자가 왼쪽(y > 0)이면 왼팔. 상자 yaw에 맞춰 ±45° 안에서 손 돌리기'], ['planning scene에 상판', '계획하는 동안만 충돌 물체로 추가'], ['pre-grasp → 직선 접근', '10 cm 뒤, 4 cm 위에서 move_linear로 다가감'], ['닫고 확인', '닫은 뒤에도 손가락이 0.06 rad 이상 벌어져 있으면 "잡았다"'], ['들기 → tuck', '직선 8 cm 들고 접은 자세, 상판 제거']].forEach(([h, b], i) => step(s, i + 1, h, b, 0.6 + (i % 2) * 6.15, 1.6 + Math.floor(i / 2) * 1.7, 5.9, 0.9));

  s = content('place() 안에서 일어나는 일: 조심스럽게 내리기', TAG, '놓을 자리 높이는 멀리서 본 마커로 계산해서 몇 cm 틀릴 수 있습니다(가까이서는 든 상자가 마커를 가림). 그래서 목표 높이까지 무조건 내리지 않고, 내려가다 막히면 "바닥에 닿았다"고 판단합니다. 실제 로봇 팔의 guarded move와 같은 방식입니다.');
  [['마커 2 위 8 cm로', 'move_to_pose로 놓을 자리 위까지'], ['직선으로 내리기', '8 cm 아래로 move_linear (충돌 검사 끄고)'], ['막히면 = 닿았다', '3 cm 이상 내려간 뒤 막히면 상자가 테이블에 닿은 것'], ['그리퍼 열기', '상자를 놓는다'], ['위로 4 cm → 뒤로', '손가락이 상자를 끌지 않게 먼저 위로'], ['tuck → 그리퍼 닫기', '닫아야 카메라 시야가 열린다']].forEach(([h, b], i) => step(s, i + 1, h, b, 0.6 + (i % 2) * 6.15, 1.6 + Math.floor(i / 2) * 1.4, 5.9, 0.7));
  callout(s, 'analogy', 0.6, 5.65, 12.1, 1.05, '눈 감고 컵을 책상에 놓을 때: 천천히 내리다가 "턱" 하고 닿는 느낌이 나면 손을 놓는다', '비유');

  s = content('실습 5. Pick & Place 전체 실행', TAG, '실습 4에서 로봇을 몰았다면 시뮬레이터 리셋 후 AMCL에 원점을 다시 알려 줘야 합니다(/initialpose). 마지막 로그의 "N cm from the pad centre"를 적게 하세요. 새로 설치한 환경에서 0.8 cm로 성공했습니다. 체크포인트 3-5.');
  lab(s, {
    cmd: '# 월드 리셋 + AMCL에 원점 알려 주기\n$ ros2 service call /mujoco_bridge/reset std_srvs/srv/Trigger\n$ ros2 topic pub --once /initialpose \\\n    geometry_msgs/msg/PoseWithCovarianceStamped \\\n    "{header: {frame_id: map}, pose: {pose: {orientation: {w: 1.0}}}}"\n\n# 데모 (약 1분)\n$ ros2 run airlab_manipulation pick_place_demo \\\n    --ros-args -p use_sim_time:=true',
    cmdH: 3.6, cmdSize: 12,
    explain: ['리셋은 로봇을 원점에 옮기지만 AMCL은 모른다 → /initialpose', '로그에 단계마다 OK / FAILED가 찍힌다'],
    ok: 'demo SUCCEEDED, "red box ends … N cm from the pad centre" (3 cm 이내)\n\n✅ 체크포인트 3-5',
    fail: 'marker not visible → 리셋 후 다시. gripper closed on nothing → 정밀 접근 오차, 다시 시도',
  });

  summary('모듈 3 한 장 요약', TAG, [
    ['FaArrowsAlt', 'FK는 쉽고 IK는 어렵다', '손 위치를 주면 MoveIt(KDL)이 관절 각도를 찾는다. 닿지 않으면 답이 없다'],
    ['FaCogs', 'MoveIt = IK + 충돌 없는 경로 + 시간표 + 실행', 'SRDF(그룹·자세), planning scene(우리가 알려 준 장애물만 피함)'],
    ['FaRoute', 'pose goal은 멀리, 직선 경로는 가까이', '접근·들기·내리기는 move_linear'],
    ['FaQrcode', 'ArUco: 크기를 알면 거리를 안다', 'solvePnP → TF aruco_<id>. 가려지면 기억 + 오도메트리'],
    ['FaHandPaper', 'Pick & Place = 스킬 상태 기계', '주행 → 정밀 접근(1 cm) → 집기 → 운반 → 놓기(닿으면 멈춤)'],
  ], '다섯 줄로 정리합니다.');

  quiz('모듈 3 셀프 체크', TAG, [
    ['집기 직전 접근에 move_to_pose 대신 move_linear를 쓰는 이유는?', 'move_to_pose는 경로가 휘어 손이 상자나 상판을 칠 수 있다. 직선으로 다가가야 안전하다.'],
    ['계획할 때만 상판을 planning scene에 넣고 끝나면 빼는 이유는?', '로봇이 주행하면 base 기준 테이블 위치가 바뀌는데, 넣어 둔 상판은 그대로라 틀린 장애물이 된다.'],
    ['마커 크기를 실제보다 2배 크게 알려 주면 거리는 어떻게 계산될까?', '2배 멀리 있다고 계산된다(거리 ∝ 실제 크기).'],
    ['"기억한 마커 + 오도메트리"가 틀어지는 경우는?', '오래 움직이거나 미끄러질 때(오도메트리 오차 누적), 또는 그 물체가 움직였을 때.'],
    ['실제 로봇에서는 "잡았다"를 무엇으로 판단할 수 있을까?', '그리퍼 모터 전류/힘 센서, 손가락 위치, 촉각 센서, 카메라로 확인 등.'],
  ], '답은 발표자 노트에 있습니다.');

  s = content('모듈 3 과제', TAG, '도전 과제는 포스터의 "planning scene attach/detach" 항목에 해당합니다. 지금 코드는 상판만 planning scene에 넣습니다.');
  card(s, { x: 0.6, y: 1.5, w: 5.95, h: 2.5, head: '기본 A. 되돌려 놓기', iconName: 'FaUndo', accent: C.accent2, body: 'pick_place_demo.py를 복사해 상자를 작업대 → 1번 공급 테이블(처음 자리, 마커 11)로 되돌리는 put_back.py', bodySize: 15 });
  card(s, { x: 6.75, y: 1.5, w: 5.95, h: 2.5, head: '기본 B. 파지 파라미터', iconName: 'FaWrench', accent: C.accent3, body: 'skills.py의 PRE_GRASP_UP(0.04)을 0으로, GRASP_HEIGHT(0.015)를 0으로 바꿔 각각 무엇이 실패하는지 로그로 설명 (끝나면 원래대로)', bodySize: 15 });
  card(s, { x: 0.6, y: 4.2, w: 12.1, h: 2.5, head: '도전. Attach / Detach', iconName: 'FaLink', accent: C.accent1, body: '잡은 상자를 AttachedCollisionObject(5 cm 상자, 손 링크 openarm_*_ee_base_link에 붙이고 손가락 충돌은 touch_links로 허용)로 추가하고, 놓은 뒤 떼어 내도록 pick()/place()를 고치기. RViz MotionPlanning의 Scene Objects에서 확인', bodySize: 15, fill: C.text1, headColor: C.background1, bodyColor: C.accent5 });
};
