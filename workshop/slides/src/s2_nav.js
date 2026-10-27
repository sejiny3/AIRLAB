// 모듈 2: SLAM + Nav2
const L = require('./lib');
const { C, HEX, MONO, text, box, circleIcon, pill, card, callout, code, bullets, arrow, img, table, step, flow, lab, quiz, summary, content } = L;
const TAG = '모듈 2 · 주행';

module.exports = function build() {
  let s;
  L.section('모듈 2: SLAM + Nav2', '모듈 2 · 1일차 12:30–16:30', 'SLAM Toolbox + Nav2\n실내 자율주행', [
    '"나는 어디에 있나?"를 지도와 LiDAR로 푸는 방법을 안다',
    'slam_toolbox로 방 지도를 만들고 저장한다',
    'Nav2의 AMCL, costmap, planner, controller가 하는 일을 말할 수 있다',
    'RViz와 Python으로 목표점 주행을 시키고 오차를 잰다',
  ], '점심 직후 모듈입니다. 오전 실습 6에서 잰 오도메트리 오차를 상기시키고 시작합니다: "그 오차를 어떻게 바로잡을까?"');

  s = content('오늘 오후에 할 일', TAG, '4시간 흐름입니다. 지도 만들기(실습 1~2) → 지도로 주행(실습 3~4) → 실험(실습 5~6) → 프로그래밍(실습 7) → 자동 탐색(실습 8, 시간이 모자라면 시연) → 통합 데모.');
  [['12:30', '개념', '위치 추정, SLAM, Nav2 구조'], ['13:00', '실습 1~2', '지도 만들기, 저장'], ['13:50', '실습 3~4', '목표점 주행, 오차 재기'], ['14:50', '실습 5~6', '파라미터 실험, 지도에 없는 장애물'], ['15:40', '실습 7~8', 'Python으로 순찰 프로그램, 자동 탐색으로 지도 만들기'], ['16:10', '통합 데모', '내 지도 + 내 순찰 프로그램 시연']].forEach(([t, h, b], i) => {
    const y = 1.5 + i * 0.88;
    pill(s, t, 0.6, y + 0.17, 1.2, i % 2 ? C.accent2 : C.text1);
    box(s, 2.1, y, 10.6, 0.72, C.background2);
    text(s, h, { x: 2.35, y, w: 2.2, h: 0.72, fontSize: 17, bold: true, valign: 'middle' });
    text(s, b, { x: 4.6, y, w: 8.0, h: 0.72, fontSize: 16, color: C.text2, valign: 'middle' });
  });

  s = content('로봇의 질문: "나는 지금 어디에 있지?"', TAG, '세 경우를 구분해 줍니다. 지도가 있으면 위치만 찾으면 되고(AMCL, 실습 3), 위치를 정확히 알면 지도만 그리면 됩니다. 둘 다 모르는 것이 SLAM입니다(실습 1). 처음 간 건물에서 약도를 그리며 걷는 비유가 잘 통합니다.');
  [['FaMap', '지도는 있다', '→ 위치만 찾으면 된다.\n저장된 지도와 지금 LiDAR에 보이는 벽을 맞춰 본다.\n= 위치 추정 (AMCL)', C.accent3],
    ['FaCrosshairs', '위치는 안다', '→ 지도만 그리면 된다.\n정확한 위치에서 본 LiDAR 점을 모으면 지도가 된다.\n= 지도 작성 (mapping)', C.accent2],
    ['FaCompass', '둘 다 모른다', '→ 둘을 동시에.\n조금 움직이고, 지도를 그리고, 그 지도로 위치를 고친다.\n= SLAM', C.accent1]].forEach(([ic, h, b, a], i) => {
    card(s, { x: 0.6 + i * 4.1, y: 1.5, w: 3.85, h: 3.5, head: h, body: b, iconName: ic, accent: a, headSize: 16, bodySize: 15 });
  });
  callout(s, 'analogy', 0.6, 5.25, 12.1, 1.45, '처음 가 보는 건물에서 약도를 그리며 걷기. 복도를 걸으며 그리고, 그린 약도를 보며 "아, 아까 그 계단이구나" 하고 내 위치를 고친다.');

  s = content('세 개의 좌표계: map, odom, base', TAG, 'REP-105 좌표계 규칙입니다. odom은 부드럽지만 어긋나고, map은 정확하지만 툭 뛸 수 있습니다. SLAM/AMCL은 로봇 위치를 직접 바꾸지 않고 map→odom을 조정해서 둘의 장점을 합칩니다. 실습 2에서 tf2_echo map odom으로 이 값이 조금씩 바뀌는 것을 봅니다.');
  [['map', C.accent1], ['odom', C.accent3], ['base_footprint', C.text1]].forEach(([t, f], i) => {
    const x = 0.6 + i * 4.3;
    box(s, x, 1.6, 3.4, 1.0, f);
    text(s, t, { x, y: 1.6, w: 3.4, h: 1.0, fontSize: 22, bold: true, fontFace: MONO, color: C.background1, align: 'center', valign: 'middle' });
    if (i < 2) arrow(s, x + 3.45, 2.1, x + 4.25, 2.1);
  });
  card(s, { x: 0.6, y: 2.95, w: 6.0, h: 2.0, head: 'map → odom: SLAM / AMCL이 낸다', body: 'LiDAR로 지도에 맞춰 보정. 정확하지만 보정 순간에 툭 뛸 수 있다.', accent: C.accent1, headSize: 16 });
  card(s, { x: 6.75, y: 2.95, w: 5.95, h: 2.0, head: 'odom → base: 브리지가 낸다', body: '휠 오도메트리. 부드럽고 끊김 없지만 시간이 갈수록 어긋난다.', headSize: 16 });
  callout(s, 'why', 0.6, 5.2, 12.1, 1.5, '로봇 위치를 직접 "점프"시키면 제어가 흔들린다. 그래서 부드러운 odom은 그대로 두고, map과 odom 사이의 차이만 조금씩 고친다. 고친 양 = 오도메트리 오차.');

  s = content('SLAM Toolbox: 스캔을 이어 붙여 지도로', TAG, '오른쪽 그림은 SLAM 지도(검은 점)와 실제 월드의 벽(초록 선)을 겹친 것입니다. 해상도 0.05 m. 거의 정확히 겹칩니다.');
  step(s, 1, '스캔 매칭', '새 스캔을 지금까지의 지도에 맞춰 오도메트리보다 정확한 위치를 구한다', 0.6, 1.6, 6.6);
  step(s, 2, '포즈 그래프', '0.2 m 또는 0.2 rad 움직일 때마다 "여기서 이렇게 보였다"를 노드로 저장', 0.6, 3.05, 6.6);
  step(s, 3, '루프 클로저', '왔던 곳에 돌아오면 알아보고, 그동안 쌓인 오차를 그래프 전체에 나눠 줄인다', 0.6, 4.5, 6.6);
  text(s, '그래서 지도를 만들 때는 천천히, 그리고 처음 자리로 돌아오기', { x: 0.6, y: 6.0, w: 6.6, h: 0.6, fontSize: 15, bold: true, color: C.accent1 });
  img(s, 'step3_map_overlay.png', 7.6, 1.5, 5.1, 5.2, 'SLAM으로 만든 지도와 실제 월드 벽 비교');

  s = content('스캔 매칭을 그림으로 보면', TAG, '왼쪽: 오도메트리만 믿으면 새 스캔(주황)이 지도(회색)와 어긋나 있습니다. 오른쪽: 스캔 매칭은 새 스캔을 살짝 옮기고 돌려서 가장 잘 겹치는 위치를 찾습니다. 그만큼이 오도메트리 오차이고, 고친 위치가 더 정확한 로봇 위치입니다.');
  const wall = (s2, x0, y0, color, w = 2.5) => {
    s2.addShape(L.S.LINE, { x: x0, y: y0, w: 0, h: 2.8, line: { color, width: w } });
    s2.addShape(L.S.LINE, { x: x0, y: y0 + 2.8, w: 3.6, h: 0, line: { color, width: w } });
  };
  box(s, 0.6, 1.5, 5.9, 3.9, C.background2);
  wall(s, 1.3, 1.9, HEX.accent5, 5); wall(s, 1.75, 1.75, HEX.accent1, 2.5);
  text(s, '오도메트리만 믿으면: 어긋남', { x: 0.8, y: 4.85, w: 5.5, h: 0.45, fontSize: 15, bold: true, align: 'center' });
  arrow(s, 6.6, 3.45, 7.0, 3.45);
  box(s, 7.1, 1.5, 5.6, 3.9, C.background2);
  wall(s, 7.8, 1.9, HEX.accent5, 5); wall(s, 7.8, 1.9, HEX.accent1, 2.5);
  text(s, '스캔 매칭 후: 딱 겹침', { x: 7.3, y: 4.85, w: 5.2, h: 0.45, fontSize: 15, bold: true, align: 'center' });
  pill(s, '회색 = 지금까지의 지도', 0.6, 5.65, 3.0, C.accent5, C.text1, 12);
  pill(s, '주황 = 방금 들어온 스캔', 3.8, 5.65, 3.0, C.accent1, C.background1, 12);
  callout(s, 'analogy', 7.1, 5.6, 5.6, 1.1, '퍼즐 조각을 돌려 가며 딱 맞는 자리 찾기', '비유');

  s = content('실습 1. SLAM으로 지도 만들기', TAG, '칸막이벽의 문(y −0.4~0.8 m)을 지나 서쪽 방까지 다녀오게 합니다. 시간이 부족한 학생은 explore_waypoints.py를 쓰게 하세요. 이것은 실제 위치(/ground_truth)로 정해진 경로를 도는 지도 작성 도우미이지 Nav2가 아닙니다. 체크포인트 2-1.');
  lab(s, {
    cmd: '# 터미널 1\n$ ros2 launch unbolt_navigation slam.launch.py\n\n# 터미널 2: 키보드로 천천히 (x 키로 감속)\n$ ros2 run teleop_twist_keyboard teleop_twist_keyboard\n\n# 시간이 부족하면 자동 탐색 (약 2분)\n$ ros2 run unbolt_navigation explore_waypoints.py \\\n    --ros-args -p use_sim_time:=true',
    cmdH: 3.5,
    explain: ['RViz에 회색 지도가 조금씩 생긴다', '문을 지나 서쪽 방까지 갔다가 처음 자리로 돌아오기'],
    ok: '벽이 이중으로 겹치지 않은 방 전체 지도가 보인다.\n\n✅ 체크포인트 2-1',
    fail: '벽이 겹치면 너무 빨리 돌았다. 처음부터 다시 (Ctrl+C 후 launch), 특히 회전을 천천히',
  });

  s = content('좋은 지도, 나쁜 지도', TAG, '학생들이 자기 지도를 평가하는 기준입니다. 나쁜 지도로 주행하면 AMCL이 위치를 잘못 잡아서 모듈 2 후반이 다 어려워집니다. 다시 만드는 데 2분이면 되니 과감히 다시 하라고 권하세요.');
  img(s, 'step3_map_overlay.png', 0.6, 1.5, 4.6, 5.2, '좋은 지도 예시');
  card(s, { x: 5.5, y: 1.5, w: 3.5, h: 2.5, head: '좋은 지도', iconName: 'FaCheckCircle', accent: C.accent2, body: '벽이 한 줄, 모서리가 직각, 방이 닫혀 있다', bodySize: 15 });
  card(s, { x: 9.2, y: 1.5, w: 3.5, h: 2.5, head: '나쁜 지도', iconName: 'FaExclamationTriangle', accent: C.accent6, body: '벽이 두 줄로 겹침, 방이 휘어 있음, 구멍이 뚫림', bodySize: 15 });
  callout(s, 'tip', 5.5, 4.2, 7.2, 2.5, '1. 천천히 (특히 제자리 회전)\n2. 벽에서 0.5 m 이상 떨어져서\n3. 마지막에 처음 자리로 돌아오기 (루프 클로저)\n4. 망쳤으면 다시: Ctrl+C → launch, 2분이면 된다', '좋은 지도를 만드는 요령');

  s = content('실습 2. map → odom 관찰하고 지도 저장', TAG, 'tf2_echo의 값이 로봇을 몰 때마다 조금씩 변합니다. 오도메트리 오차를 SLAM이 보정하는 양입니다. 지도는 src 폴더가 아니라 홈의 maps에 저장합니다. 체크포인트 2-2.');
  lab(s, {
    cmd: '# SLAM이 켜진 상태에서\n$ ros2 run tf2_ros tf2_echo map odom \\\n    --ros-args -p use_sim_time:=true\n\n# 지도 저장 (SLAM이 켜져 있어야 한다)\n$ mkdir -p ~/maps\n$ ros2 run nav2_map_server map_saver_cli \\\n    -f ~/maps/my_room --ros-args -p use_sim_time:=true\n$ ls ~/maps',
    cmdH: 3.6,
    explain: ['tf2_echo: 두 좌표계 사이의 변환을 계속 출력', 'map_saver_cli: 지금 지도를 .pgm(그림) + .yaml(정보)로 저장'],
    ok: 'tf2_echo 값이 몰 때마다 조금씩 바뀐다.\n~/maps에 my_room.pgm, my_room.yaml\n\n✅ 체크포인트 2-2',
    fail: 'Failed to spin map subscription → SLAM이 꺼져 있다. 켠 상태에서 저장',
  });

  s = content('지도 파일 읽는 법', TAG, '지도는 그림(pgm)과 설명(yaml) 두 파일입니다. 흰색은 빈 곳, 검은색은 벽, 회색은 모르는 곳입니다. origin은 그림 왼쪽 아래 칸의 월드 좌표이고, resolution은 한 칸의 크기입니다. 142×122칸 × 0.05 m = 7.1 × 6.1 m.');
  box(s, 0.6, 1.5, 4.0, 4.0, C.background2);
  [['흰색', '빈 곳 (갈 수 있음)', 'FFFFFF'], ['검은색', '벽·장애물', '1B2430'], ['회색', '모르는 곳 (안 봄)', 'C9D1DC']].forEach(([a, b, col], i) => {
    const y = 1.8 + i * 1.15;
    s.addShape(L.S.RECTANGLE, { x: 0.9, y, w: 0.8, h: 0.8, fill: { color: col }, line: { color: HEX.dk2, width: 1 } });
    text(s, a, { x: 1.9, y, w: 2.5, h: 0.4, fontSize: 16, bold: true });
    text(s, b, { x: 1.9, y: y + 0.4, w: 2.6, h: 0.4, fontSize: 14, color: C.text2 });
  });
  text(s, 'my_room.pgm (그림)', { x: 0.6, y: 5.6, w: 4.0, h: 0.4, fontSize: 14, bold: true, align: 'center' });
  code(s, 'image: my_room.pgm\nmode: trinary\nresolution: 0.05          # 한 칸 = 5 cm\norigin: [-2.54, -3.03, 0] # 왼쪽 아래 칸의 (x, y, θ)\nnegate: 0\noccupied_thresh: 0.65     # 이보다 어두우면 벽\nfree_thresh: 0.25         # 이보다 밝으면 빈 곳', 4.9, 1.5, 7.8, 3.0, 14);
  callout(s, 'why', 4.9, 4.75, 7.8, 1.95, 'origin과 resolution이 있어야 "그림의 몇 번째 칸 = 방의 몇 m"를 계산할 수 있다. 대시보드도 이 두 값으로 지도 위에 로봇을 그린다.');

  s = content('AMCL: 여러 추측 중에 맞는 것만 남긴다', TAG, '파티클 필터를 네 단계로 설명합니다. RViz의 초록 화살표 구름이 파티클입니다. 처음에 퍼져 있다가 로봇이 움직이며 한 점으로 모입니다. 보물찾기 비유: 여러 사람이 흩어져 추측하고, 단서에 맞는 사람만 남깁니다.');
  [['흩뿌리기', '로봇이 있을 법한 곳에 추측(파티클) 500~2000개'], ['움직임 반영', '오도메트리만큼 모든 추측을 같이 옮김'], ['점수 매기기', '각 추측 위치에서 지도상 벽과 LiDAR가 맞는지'], ['맞는 것만 남기기', '점수 높은 추측 주변으로 다시 뽑기 → 반복']].forEach(([h, b], i) => step(s, i + 1, h, b, 0.6 + i * 3.08, 1.6, 2.9, 1.2));
  img(s, 'step3_nav_rviz.jpg', 0.6, 3.5, 5.3, 3.2, 'RViz의 AMCL 파티클과 지도');
  callout(s, 'analogy', 6.2, 3.5, 6.5, 1.5, '보물찾기: 여러 명이 흩어져 "여기일까?" 추측하고, 단서와 맞는 사람 주변으로 다시 모인다.');
  callout(s, 'tip', 6.2, 5.2, 6.5, 1.5, '파티클이 엉뚱한 곳에 모이면 RViz의 2D Pose Estimate로 실제 위치를 알려 준다.');

  s = content('costmap: "여기는 얼마나 위험한가" 지도', TAG, '세 층을 겹쳐 하나의 비용 지도를 만듭니다. static은 저장된 지도의 벽, obstacle은 지금 LiDAR에 보이는 것(지도에 없는 상자도), inflation은 벽 주변을 0.6 m까지 점점 비싸게 칠한 띠입니다. 로봇 몸(footprint, 0.60 × 0.54 m)이 비싼 칸에 닿지 않게 경로를 짭니다.');
  [['static layer', '저장된 지도의 벽', C.text1], ['obstacle layer', 'LiDAR에 지금 보이는 장애물', C.accent3], ['inflation layer', '벽 주변 0.6 m 위험 띠', C.accent2]].forEach(([h, b, f], i) => {
    const y = 1.6 + i * 1.05;
    box(s, 0.6 + i * 0.35, y, 5.6, 0.9, f);
    text(s, h, { x: 0.8 + i * 0.35, y, w: 2.3, h: 0.9, fontSize: 15, bold: true, fontFace: MONO, color: C.background1, valign: 'middle' });
    text(s, b, { x: 3.1 + i * 0.35, y, w: 3.0, h: 0.9, fontSize: 14, color: C.background1, valign: 'middle' });
  });
  arrow(s, 3.7, 4.75, 3.7, 5.15);
  box(s, 0.6, 5.2, 6.3, 0.9, C.accent1);
  text(s, '= 하나의 costmap (칸마다 0~254 비용)', { x: 0.6, y: 5.2, w: 6.3, h: 0.9, fontSize: 16, bold: true, color: C.background1, align: 'center', valign: 'middle' });
  card(s, { x: 7.3, y: 1.5, w: 5.4, h: 2.4, head: 'global costmap', iconName: 'FaMap', accent: C.text1, body: '방 전체. 전체 경로를 짤 때 (1 Hz 갱신)', bodySize: 15 });
  card(s, { x: 7.3, y: 4.1, w: 5.4, h: 2.4, head: 'local costmap', iconName: 'FaCrosshairs', accent: C.accent1, body: '로봇 주변 4 × 4 m만. 바로 앞을 피할 때 (5 Hz 갱신)', bodySize: 15 });

  s = content('Nav2 구조: 누가 무엇을 하나', TAG, 'Nav2는 서버 여러 개를 행동 트리(bt_navigator)가 지휘합니다. planner는 전체 경로, controller는 그 경로를 따라가는 속도 명령을 냅니다. AMCL은 따로 위치를 계속 추정합니다.');
  box(s, 0.6, 1.6, 2.6, 1.0, C.accent5);
  text(s, '목표\n(RViz / Python)', { x: 0.6, y: 1.6, w: 2.6, h: 1.0, fontSize: 15, bold: true, align: 'center', valign: 'middle' });
  arrow(s, 3.25, 2.1, 3.85, 2.1);
  box(s, 3.9, 1.6, 3.4, 1.0, C.text1);
  text(s, 'bt_navigator\n행동 트리: 계획→추종→복구', { x: 3.9, y: 1.6, w: 3.4, h: 1.0, fontSize: 14, bold: true, color: C.background1, align: 'center', valign: 'middle' });
  box(s, 8.0, 1.6, 4.7, 1.0, C.accent3);
  text(s, 'planner_server (NavFn)\nglobal costmap 위에서 전체 경로', { x: 8.0, y: 1.6, w: 4.7, h: 1.0, fontSize: 14, bold: true, color: C.background1, align: 'center', valign: 'middle' });
  arrow(s, 7.35, 2.1, 7.95, 2.1);
  box(s, 8.0, 3.1, 4.7, 1.0, C.accent2);
  text(s, 'controller_server (RPP)\nlocal costmap 위에서 속도 명령', { x: 8.0, y: 3.1, w: 4.7, h: 1.0, fontSize: 14, bold: true, color: C.background1, align: 'center', valign: 'middle' });
  arrow(s, 7.3, 2.62, 7.98, 3.45);
  box(s, 8.0, 4.6, 4.7, 0.8, C.background2);
  text(s, 'velocity_smoother → /cmd_vel → 브리지', { x: 8.0, y: 4.6, w: 4.7, h: 0.8, fontSize: 14, bold: true, align: 'center', valign: 'middle' });
  arrow(s, 10.35, 4.1, 10.35, 4.55);
  card(s, { x: 0.6, y: 3.1, w: 6.4, h: 1.6, head: 'AMCL (위치 추정)', iconName: 'FaMap', accent: C.accent1, body: '지도 + LiDAR + 오도메트리 → map→odom', headSize: 16, bodySize: 14 });
  card(s, { x: 0.6, y: 4.9, w: 6.4, h: 1.8, head: 'map_server', iconName: 'FaTable', accent: C.text1, body: '저장한 지도 파일(yaml + pgm)을 읽어 /map으로 내보낸다', headSize: 16, bodySize: 14 });

  s = content('planner와 controller는 무엇이 다른가', TAG, '내비게이션 앱과 운전자의 비유입니다. 앱(planner)은 출발 전에 전체 길을 보여 주고, 운전자(controller)는 그 길을 따라 매 순간 핸들과 페달을 조절합니다. 길이 막히면 앱이 다시 길을 찾습니다(재계획).');
  card(s, { x: 0.6, y: 1.5, w: 5.95, h: 3.2, head: 'planner = 내비게이션 앱', iconName: 'FaRoute', accent: C.accent3, body: '방 전체 지도를 보고 출발점에서 목표까지 선 하나를 긋는다.\n\n우리 설정: NavFn (가장 비용이 싼 길)\n1초마다 다시 계산', bodySize: 15 });
  card(s, { x: 6.75, y: 1.5, w: 5.95, h: 3.2, head: 'controller = 운전자', iconName: 'FaCompass', accent: C.accent2, body: '그 선을 따라가며 지금 낼 속도(직진, 회전)를 정한다.\n\n우리 설정: Regulated Pure Pursuit, 0.35 m/s\n앞으로 0.6 m 지점을 계속 바라보며 간다', bodySize: 15 });
  callout(s, 'why', 0.6, 4.95, 12.1, 1.75, '둘을 나누면 각자 잘하는 일에 집중한다. 전체 길 찾기는 느려도 되고(1 Hz), 핸들 조작은 빨라야 한다(20 Hz). 차동구동 로봇이라 제자리 회전이 되는 Pure Pursuit 계열을 골랐다.');

  s = content('막히면 어떻게 하나: 행동 트리와 복구', TAG, 'bt_navigator의 행동 트리는 "계획 → 따라가기"를 반복하다 실패하면 복구 동작을 차례로 시도합니다. 실습 6에서 지도에 없는 장애물을 만나면 터미널 로그에서 Running spin, Running backup 같은 줄을 찾아보게 하세요.');
  flow(s, [['경로 계획', C.accent3, C.background1], ['경로 따라가기', C.accent2, C.background1], ['도착!', C.accent1, C.background1]], 0.6, 1.6, 8.0, 0.9, 0.45, 16);
  text(s, '실패하면 ↓', { x: 3.0, y: 2.6, w: 3.0, h: 0.4, fontSize: 14, bold: true, color: C.accent6, align: 'center' });
  flow(s, ['costmap 비우기', '제자리 회전 (spin)', '후진 (backup)', '잠시 대기 (wait)'], 0.6, 3.1, 12.1, 0.9, 0.4, 15);
  text(s, '↺ 복구 후 다시 경로 계획부터. 계속 실패하면 목표를 포기하고 "실패"를 돌려준다', { x: 0.6, y: 4.15, w: 12.1, h: 0.45, fontSize: 15, color: C.text2 });
  callout(s, 'analogy', 0.6, 4.9, 6.0, 1.8, '길이 막힌 운전자: 일단 주위를 둘러보고(회전), 조금 물러났다가(후진), 잠깐 기다렸다가 다시 길을 찾는다.');
  callout(s, 'tip', 6.75, 4.9, 5.95, 1.8, '로봇이 같은 자리에서 계속 돌면 목표가 벽 안이거나 AMCL 위치가 틀렸다 → 2D Pose Estimate');

  s = content('이 로봇의 Nav2 설정', TAG, 'Humble 공식 nav2_params.yaml에서 출발해 바꾼 점만 정리했습니다. 실습 5에서 이 중 inflation과 속도를 바꿔 봅니다.');
  table(s, [['항목', '값', '이유'], ['footprint', '0.60 × 0.54 m 직사각형', '섀시 + 바퀴. 원보다 문 통과가 정확'], ['controller', 'Regulated Pure Pursuit, 0.35 m/s', '차동구동, 제자리 회전 가능'], ['inflation_radius', '0.6 m', '벽에서 여유'], ['local costmap', '4 × 4 m, 0.05 m', 'LiDAR 장애물만'], ['goal tolerance', 'xy 0.15 m, yaw 0.2 rad', '이만큼 가까우면 도착으로 판정'], ['AMCL 시작 위치', '지도 원점 (0, 0, 0)', '로봇이 원점에서 시작']], 0.6, 1.5, 12.1, [2.6, 4.3, 5.2], 16);
  text(s, '파일: unbolt_navigation/config/nav2_params.yaml (맨 위 주석에 공식 파일과 다른 점)', { x: 0.6, y: 6.1, w: 12.1, h: 0.5, fontSize: 14, color: C.text2 });

  s = content('실습 3. 저장된 지도로 목표점 주행', TAG, '체크포인트 2-3은 동쪽 방, 서쪽 방 목표 연속 도착입니다. 칸막이 문을 통과하는 모습을 보게 하세요.');
  img(s, 'step3_nav_rviz.jpg', 0.6, 1.5, 6.6, 4.5, 'RViz의 Nav2: 지도, costmap, 전역 경로');
  code(s, '$ ros2 launch unbolt_navigation navigation.launch.py', 0.6, 6.15, 6.6, 0.6, 13);
  step(s, 1, '위치 확인', '초록 파티클이 로봇 주변에 모였나? 아니면 2D Pose Estimate', 7.5, 1.6, 5.2);
  step(s, 2, '목표 찍기', '2D Goal Pose로 드래그 (화살표 = 도착 방향)', 7.5, 2.85, 5.2);
  step(s, 3, '보이는 것', '초록·분홍 선 = 경로, 색 사각형 = local costmap, 하늘색 띠 = inflation', 7.5, 4.1, 5.2);
  step(s, 4, '서쪽 방도', '칸막이 문을 지나가는지 확인 ✅ 2-3', 7.5, 5.35, 5.2);

  s = content('실습 4. 내 지도로 주행하고 오차 재기', TAG, 'nav_goal_test.py는 목표 3개를 차례로 가고, 시뮬레이터의 진짜 위치와 비교해 오차를 출력합니다. 표를 채우게 하세요. 체크포인트 2-4: 3/3 도착, 위치 오차 15 cm 이내.');
  code(s, '$ ros2 launch unbolt_navigation navigation.launch.py \\\n    map:=$HOME/maps/my_room.yaml\n\n# 다른 터미널: 목표 3개 자동 주행 + 오차 출력\n$ ros2 run unbolt_navigation nav_goal_test.py \\\n    --ros-args -p use_sim_time:=true', 0.6, 1.5, 6.6, 2.6, 13);
  table(s, [['목표', '걸린 시간', '위치 오차 (cm)', '방향 오차 (°)'], ['(3.0, −1.4)', '', '', ''], ['(−1.9, 1.6)', '', '', ''], ['(0.0, 0.0)', '', '', '']], 0.6, 4.35, 6.6, [1.8, 1.4, 1.8, 1.6], 15);
  callout(s, 'ok', 7.5, 1.5, 5.2, 2.5, '3/3 도착, 위치 오차 15 cm 이내\n\n✅ 체크포인트 2-4');
  callout(s, 'why', 7.5, 4.2, 5.2, 2.5, '오차가 tolerance(15 cm)보다 작은 이유: Nav2는 15 cm 안에 들어오면 "도착"이라 멈추지만, 보통은 더 가까이 와서 멈춘다.');

  s = content('실습 5. 파라미터 바꿔 보기', TAG, 'A와 B는 global, local 두 costmap 모두 바꿔야 합니다. 일부 파라미터는 ros2 param set으로 실행 중에도 바뀝니다. 기본 과제는 이 중 두 개의 결과 제출입니다.');
  table(s, [['실험', '바꿀 곳', '예상'], ['A', 'inflation_radius 0.6 → 0.25 (둘 다)', '벽에 바짝 붙는 경로'], ['B', 'inflation_radius 0.6 → 1.2', '문을 통과하지 못할 수도'], ['C', 'desired_linear_vel 0.35 → 0.6', '빨라지지만 코너에서?'], ['D', 'xy_goal_tolerance 0.15 → 0.05', '도착 판정이 엄격해져 오래 걸림']], 0.6, 1.5, 12.1, [1.2, 5.6, 5.3], 16);
  code(s, '$ cp $(ros2 pkg prefix unbolt_navigation)/share/unbolt_navigation/config/nav2_params.yaml ~/my_nav2.yaml\n$ code ~/my_nav2.yaml        # VS Code로 열어 고치기\n$ ros2 launch unbolt_navigation navigation.launch.py params_file:=$HOME/my_nav2.yaml', 0.6, 4.15, 12.1, 1.3, 13);
  callout(s, 'tip', 0.6, 5.65, 12.1, 1.05, '원본은 그대로 두고 복사본을 고친다. 하나씩 바꾸고 같은 목표로 비교한다.', '팁');

  s = content('실습 6. 지도에 없는 장애물', TAG, '상자 위치는 (2.0, −1.0). 원래 경로가 정확히 그 자리를 지나기 때문에 우회가 분명하게 보입니다. 옛 지도(상자 없음)를 쓰는 것이 핵심입니다.');
  box(s, 0.6, 1.5, 5.9, 2.4, C.background2);
  text(s, '12초', { x: 0.9, y: 1.6, w: 5.3, h: 1.1, fontSize: 54, bold: true, color: C.accent3 });
  text(s, '상자 없음: 작업대와 기둥 사이 남쪽 길', { x: 0.9, y: 2.8, w: 5.3, h: 0.9, fontSize: 16 });
  box(s, 6.8, 1.5, 5.9, 2.4, C.text1);
  text(s, '18초', { x: 7.1, y: 1.6, w: 5.3, h: 1.1, fontSize: 54, bold: true, color: C.accent1 });
  text(s, '상자 있음: LiDAR가 보고 작업대 북쪽으로 우회', { x: 7.1, y: 2.8, w: 5.3, h: 0.9, fontSize: 16, color: C.background1 });
  code(s, '<geom name="surprise" type="box" size="0.2 0.2 0.3" pos="2.0 -1.0 0.3"/>   # my_scene.xml에 추가\n$ ros2 launch unbolt_navigation navigation.launch.py \\\n    model_path:=$UNBOLT_ROOT/models/my_scene.xml       # 지도는 옛 지도 그대로', 0.6, 4.15, 12.1, 1.15, 13);
  bullets(s, ['obstacle layer가 LiDAR로 본 상자를 costmap에 표시 → planner가 경로를 다시 계산', '너무 늦게 보이면 controller가 멈추고 복구 동작 (로그에서 Running spin / backup 찾기)'], 0.6, 5.5, 9.6, 1.2, 15);
  text(s, '원점 → (3.0, −1.4)\n강사 노트북 실측 ✅ 2-5', { x: 10.3, y: 5.5, w: 2.4, h: 1.0, fontSize: 12, color: C.text2, align: 'right' });

  s = content('실습 7. Python으로 순찰 프로그램', TAG, '전체 코드는 02_slam_nav2.md 실습 7에 있습니다. BasicNavigator가 Nav2 액션을 감싸서 몇 줄로 주행을 시킵니다. 강사 노트북에서 네 곳 모두 도착(약 11, 11, 30, 14초)을 확인했습니다. 체크포인트 2-6.');
  code(s, 'from nav2_simple_commander.robot_navigator import (\n    BasicNavigator, TaskResult)\n\nPOINTS = [(3.2, 1.2, 0.0), (3.0, -1.4, -math.pi/2),\n          (-1.9, 1.6, math.pi/2), (0.0, 0.0, 0.0)]\n\nnav = BasicNavigator()\nnav.waitUntilNav2Active()          # Nav2가 준비될 때까지\nfor x, y, yaw in POINTS:\n    nav.goToPose(pose(nav, x, y, yaw))   # 목표 보내기\n    while not nav.isTaskComplete():      # 끝날 때까지\n        fb = nav.getFeedback()           # 남은 거리 등\n    print(nav.getResult() == TaskResult.SUCCEEDED)', 0.6, 1.5, 7.6, 5.2, 13);
  text(s, '실행', { x: 8.5, y: 1.5, w: 4.2, h: 0.45, fontSize: 17, bold: true });
  code(s, '$ python3 ~/patrol.py \\\n    --ros-args -p \\\n    use_sim_time:=true', 8.5, 2.0, 4.2, 1.5, 14);
  callout(s, 'ok', 8.5, 3.75, 4.2, 1.35, '네 곳 모두 "도착" ✅ 2-6');
  callout(s, 'why', 8.5, 5.3, 4.2, 1.4, 'pose()는 (x, y, yaw)를 map 기준 PoseStamped로 바꾸는 작은 함수');

  s = content('BasicNavigator 자주 쓰는 함수', TAG, '모듈 3의 skills.py도 이 함수들로 주행합니다. 특히 cancelTask는 모듈 4의 작업 취소, setInitialPose는 초기화 버튼에서 씁니다.');
  table(s, [['함수', '하는 일', '이 강습회에서'], ['waitUntilNav2Active()', 'Nav2가 다 켜질 때까지 기다림', '모든 스크립트의 시작'], ['goToPose(pose)', '목표 하나로 주행 시작 (바로 돌아옴)', '순찰, 스킬의 navigate'], ['isTaskComplete()', '끝났는지 확인 (True/False)', '반복문 조건'], ['getFeedback()', '남은 거리, 걸린 시간 등', '진행 표시'], ['getResult()', 'SUCCEEDED / FAILED / CANCELED', '성공 판정'], ['cancelTask()', '주행 중단', '모듈 4 작업 취소'], ['followWaypoints([...])', '여러 지점을 한 번에', '과제'], ['setInitialPose(pose)', 'AMCL에 현재 위치 알려 주기', '초기화 버튼']], 0.6, 1.5, 12.1, [3.4, 5.0, 3.7], 15);

  s = content('자동 탐색: 프론티어를 따라가면 지도가 완성된다', TAG, '실습 1에서는 사람이 몰면서 지도를 만들었습니다. 이번에는 로봇이 스스로 다닙니다(능동 탐색, active exploration). 프론티어는 아는 빈 곳과 모르는 곳의 경계입니다. 그림은 대시보드의 지도 만들기 모드로, 하늘색 선이 프론티어, 파란 원이 지금 가는 곳(설 자리), 점선 끝의 하늘색 점이 보러 가는 프론티어입니다. 프론티어가 하나도 안 남으면 지도가 완성된 것입니다.');
  img(s, 'dashboard_mapping_map.png', 0.6, 1.5, 6.9, 5.2, '지도 만들기 모드의 지도: 자라는 SLAM 지도, 하늘색 프론티어, 탐색 목표와 경로');
  [['FaMap', '아는 빈 곳', 'LiDAR가 비춰 본 바닥. 지도에서 밝은 칸'], ['FaQuestionCircle', '모르는 곳 (미지)', '아직 한 번도 못 본 곳. 지도에서 회색 칸'], ['FaCompass', '프론티어 = 둘의 경계', '빈 칸인데 바로 옆이 미지인 칸. 여기 가서 보면 그 너머가 지도에 채워진다']].forEach(([ic, h, b], i) => {
    card(s, { x: 7.8, y: 1.5 + i * 1.3, w: 4.9, h: 1.15, head: h, body: b, iconName: ic, accent: [C.text2, C.accent5, C.accent2][i], headSize: 15, bodySize: 13 });
  });
  callout(s, 'analogy', 7.8, 5.5, 4.9, 1.2, '불 꺼진 집을 손전등으로: 빛이 닿는 끝까지 걸어가기를 반복하면 집 전체가 보인다');

  s = content('frontier_explorer가 1초마다 하는 일', TAG, 'unbolt_navigation/scripts/frontier_explorer.py입니다. ①②는 OpenCV 몇 줄(오른쪽 코드), ③이 핵심입니다. 설 자리는 costmap 비용이 낮고(벽에서 약 0.55 m 이상), 로봇이 갈 수 있고, 프론티어에서 빈 공간을 따라 1 m 안이어야 합니다. "빈 공간을 따라"가 중요합니다: 직선 거리로 재면 칸막이 벽 반대편이 뽑혀서 그 너머를 못 봅니다. 그래도 못 보면 다른 자리에서 한 번 더, 두 번 실패하면 그 프론티어는 포기합니다(벽에 붙은 좁은 틈 등). 탐색 모드의 Nav2는 로봇을 반지름 0.44 m 원으로 봅니다(회전 때 모서리가 쓰는 0.40 m + 여유). 실제로 겪은 문제: 처음에는 실행 절반 정도에서 지도가 비스듬히 두 번 그려졌는데, 추적해 보니 로봇이 공급 테이블 다리에 걸려 바퀴만 헛돌았고(오도메트리 틀어짐), 근본 원인은 브리지의 LiDAR가 쓰던 mj_multiRay가 테이블 다리 두 개를 건너뛴 것이었습니다(지금은 광선마다 mj_ray). 고친 뒤 6번 연속 성공. 강사 노트북에서 약 2~4분, 목표 15개 안팎, 실패 0~1번이었습니다.');
  [['프론티어 칸 찾기', '빈 칸 중 옆이 미지인 칸 (/map)'], ['묶기', '붙어 있는 칸끼리 한 묶음, 0.3 m 미만은 무시'], ['설 자리 고르기', 'costmap이 낮고 · 갈 수 있고 · 빈 공간을 따라 1 m 안'], ['점수로 하나 고르기', '가는 거리 − 프론티어 길이 보너스'], ['Nav2로 가기', 'NavigateToPose. 가는 도중 프론티어가 지워지면 바로 다음으로'], ['끝', '갈 수 있는 프론티어가 없으면 지도 저장 (~/maps)']].forEach(([h, b], i) => step(s, i + 1, h, b, 0.6, 1.5 + i * 0.86, 6.4, 0.4));
  code(s, '# ① 프론티어 칸\nfree = (grid >= 0) & (grid < 25)\nunknown = grid < 0\nfrontier = free & (cv2.dilate(\n    unknown.astype(np.uint8), cross) > 0)\n\n# ② 붙어 있는 칸끼리 묶기\nn, labels, stats, _ = \\\n  cv2.connectedComponentsWithStats(\n    frontier.astype(np.uint8),\n    connectivity=8)', 7.3, 1.5, 5.4, 3.5, 12);
  callout(s, 'why', 7.3, 5.2, 5.4, 1.5, '거리는 빈 공간을 따라 잰다: 직선으로 재면 벽 반대편에 서서 아무것도 못 본다');

  s = content('실습 8. 대시보드로 자동 지도 만들기', TAG, '런처의 "지도 만들기" 모드는 시뮬레이터 + slam_toolbox + Nav2(저장된 지도·AMCL 없이) + frontier_explorer + 대시보드를 켭니다(unbolt_dashboard mapping.launch.py). 준비되면 탐색이 저절로 시작됩니다. 지도 카드에서 지도가 자라는 모습과 목표가 바뀌는 순간을 같이 보세요. 터미널로만 하려면 ros2 launch unbolt_navigation explore.launch.py (RViz로 보기). 체크포인트 2-7.');
  img(s, 'dashboard_explored.png', 0.6, 1.5, 6.9, 5.2, '탐색이 끝난 지도 만들기 화면: 완성된 지도, 저장 경로, 키보드 조종');
  code(s, '$ ros2 run unbolt_dashboard \\\n      dashboard_launcher\n# 브라우저: http://localhost:8080', 7.8, 1.5, 4.9, 1.2, 13);
  [['모드: 지도 만들기 → 연결', '20~40초 뒤 탐색이 저절로 시작'], ['지켜보기', '지도가 자라고, 하늘색 프론티어가 줄어든다'], ['탐색 완료 (3~4분)', '~/maps에 지도 자동 저장']].forEach(([h, b], i) => step(s, i + 1, h, b, 7.8, 2.9 + i * 0.9, 4.9, 0.4));
  callout(s, 'ok', 7.8, 5.6, 4.9, 1.1, '"탐색 완료" + 저장 경로 ✅ 2-7');

  s = content('탐색이 끝나면: 키보드로 몰기 · 저장 · 작업에 쓰기', TAG, '탐색이 끝나거나 멈춤을 누르면 키보드 조종 카드가 켜집니다. 페이지를 한 번 클릭하고 W A S D 또는 방향키. 누르고 있는 동안만 /cmd_vel을 10 Hz로 보내고, 떼면 멈춥니다(브리지도 0.5초 동안 명령이 없으면 멈춤). LiDAR로 앞(약 0.35 m)이나 뒤(약 0.7 m)가 막혔으면 그쪽으로는 안 갑니다. 몰고 다니는 동안에도 SLAM이 지도를 고치므로, 남은 회색 곳을 채운 뒤 지도 저장을 다시 누르면 됩니다. 저장한 지도는 작업 모드의 지도 목록에 나옵니다. 로봇이 같은 자리(원점)에서 출발하므로 공급 테이블·작업대 좌표가 그대로 맞습니다.');
  const keys = [['W', 1, 0, '앞 0.25 m/s'], ['A', 0, 1, '왼쪽 회전'], ['S', 1, 1, '뒤 0.15 m/s'], ['D', 2, 1, '오른쪽 회전']];
  keys.forEach(([k, cx, cy, lbl]) => {
    const x = 0.9 + cx * 1.25, y = 1.7 + cy * 1.25;
    box(s, x, y, 1.1, 1.1, k === 'W' ? C.accent1 : C.text1);
    text(s, k, { x, y, w: 1.1, h: 1.1, fontSize: 28, bold: true, color: C.background1, align: 'center', valign: 'middle', margin: 0 });
    text(s, lbl, { x: x - 0.1, y: y + (cy ? 1.15 : -0.45), w: 1.3, h: 0.4, fontSize: 12, color: C.text2, align: 'center', margin: 0 });
  });
  text(s, '방향키도 같음 · 스페이스 = 정지\n누르는 동안만 움직인다', { x: 0.6, y: 4.6, w: 4.1, h: 0.8, fontSize: 14, color: C.text2, align: 'center' });
  callout(s, 'warn', 0.6, 5.5, 4.1, 1.2, '앞이나 뒤가 너무 가까우면 그 방향으로는 안 움직인다 (LiDAR 확인)');
  [['FaKeyboard', '키보드로 빈 곳 채우기', '몰고 다니는 동안에도 SLAM이 지도를 계속 고친다. 남은 회색 곳에 가 보기'], ['FaHdd', '지도 저장', '"지도 저장"을 누를 때마다 ~/maps에 새 파일 (.yaml + .pgm)'], ['FaPlay', '작업 모드에서 쓰기', '시스템 종료 → 모드 "작업" → 지도 목록에서 내 지도 → 연결. 장소 좌표는 그대로 맞다']].forEach(([ic, h, b], i) => {
    card(s, { x: 5.0, y: 1.5 + i * 1.75, w: 7.7, h: 1.6, head: h, body: b, iconName: ic, accent: [C.accent2, C.accent3, C.accent1][i], headSize: 16, bodySize: 14 });
  });

  s = content('전반부 통합 데모', TAG, '1일차 마무리입니다. 아침에 만든 브리지 위에 SLAM과 Nav2가 올라가 한 줄로 이어졌다는 것을 정리합니다.');
  flow(s, [['ros2 launch', C.text1, C.background1], ['MuJoCo 물리', C.accent3, C.background1], ['브리지', C.text1, C.background1], ['SLAM 지도', C.accent3, C.background1], ['AMCL', C.text1, C.background1], ['Nav2', C.accent1, C.background1], ['/cmd_vel', C.text1, C.background1]], 0.6, 1.7, 12.1, 1.0, 0.25, 14);
  text(s, '↻ /cmd_vel 은 다시 MuJoCo로', { x: 0.6, y: 2.85, w: 12.1, h: 0.4, fontSize: 14, color: C.text2, align: 'right' });
  card(s, { x: 0.6, y: 3.5, w: 6.0, h: 3.1, head: '조별 시연', iconName: 'FaUsers', accent: C.accent2, body: '조마다 한 명씩: 내가 만든 지도로, 내 순찰 프로그램을 돌리고 MuJoCo와 RViz를 나란히 보여 준다' });
  card(s, { x: 6.75, y: 3.5, w: 5.95, h: 3.1, head: '1일차 끝!', iconName: 'FaFlagCheckered', accent: C.accent1, body: '오늘 만든 것: 시뮬레이터 ↔ ROS 브리지, 방 지도, 자율주행.\n내일: 팔로 집고, 말로 시키기.' });

  summary('모듈 2 한 장 요약', TAG, [
    ['FaCompass', 'SLAM = 지도 그리기 + 내 위치 찾기를 동시에', '스캔 매칭 → 포즈 그래프 → 루프 클로저. 천천히, 처음 자리로 돌아오기'],
    ['FaSitemap', 'map → odom → base', 'odom은 부드럽지만 어긋나고, SLAM/AMCL이 map→odom으로 고친다'],
    ['FaMap', 'AMCL = 파티클 필터', '저장된 지도 + LiDAR로 위치 추정. 틀리면 2D Pose Estimate'],
    ['FaLayerGroup', 'costmap = static + obstacle + inflation', '지도에 없는 장애물도 LiDAR로 보고 피한다'],
    ['FaRoute', 'planner(전체 길) + controller(핸들) + 행동 트리(복구)', 'Python에서는 BasicNavigator로 몇 줄이면 된다'],
  ], '다섯 줄로 정리합니다.');

  quiz('모듈 2 셀프 체크', TAG, [
    ['SLAM으로 지도를 만들 때와 AMCL로 주행할 때, 각각 map → odom을 누가 발행할까?', '지도 만들 때는 slam_toolbox, 주행할 때는 AMCL.'],
    ['inflation_radius를 로봇 크기(footprint)보다 작게 하면 어떤 일이 생길까?', '경로가 벽에 너무 붙어 로봇 몸이 벽에 스치거나, controller가 충돌 위험으로 자주 멈춘다.'],
    ['지도에 없는 장애물이 global costmap에도 나타나는 이유는?', 'global costmap에도 obstacle_layer(LiDAR)가 있어서, 지금 보이는 장애물을 지도 위에 더한다.'],
    ['로봇이 제자리에서 계속 회전만 한다. 의심할 것 두 가지는?', '목표가 벽 안/너무 가까움, 또는 AMCL 위치가 틀림(2D Pose Estimate로 고치기).'],
    ['지도를 망쳤을 때 가장 빠른 해결은?', 'SLAM을 끄고 다시 켜서 처음부터 천천히 다시 만든다(2분).'],
    ['자동 탐색에서 프론티어란? 탐색은 언제 끝날까?', '아는 빈 칸과 모르는 칸의 경계. 갈 수 있는(설 자리가 있는) 프론티어가 하나도 남지 않으면 끝.'],
  ], '답은 발표자 노트에 있습니다.');

  s = content('모듈 2 과제', TAG, '기본 과제는 모두 하고, 도전 과제는 관심 있는 학생에게 권합니다.');
  card(s, { x: 0.6, y: 1.5, w: 12.1, h: 1.6, head: '기본. 파라미터 실험 보고서', iconName: 'FaPencilAlt', accent: C.accent2, body: '실습 5의 실험 A~D 중 두 개: 스크린샷 + 시간·오차 표 + 한 줄 해석', bodySize: 15 });
  card(s, { x: 0.6, y: 3.3, w: 5.95, h: 3.3, head: '도전 1. 더 똑똑한 탐색', iconName: 'FaCompass', accent: C.accent1, body: 'frontier_explorer.py는 "가까운 곳 + 긴 프론티어"로 고른다. 설 자리에서 광선을 쏘아 새로 보일 미지 칸 수(정보 이득)를 점수에 넣어 보자.\n탐색 시간과 목표 수를 3번씩 재서 비교', bodySize: 14 });
  card(s, { x: 6.75, y: 3.3, w: 5.95, h: 3.3, head: '도전 2. 출입 금지 구역', iconName: 'FaShieldAlt', accent: C.accent6, body: 'Nav2 keepout filter로 방 한쪽을 출입 금지로 만들고, 그쪽 목표를 주면 계획이 실패하는 것을 보이자.\n힌트: nav2_costmap_2d::KeepoutFilter, 금지 구역을 칠한 mask 지도', bodySize: 14 });
};
