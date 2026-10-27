// 심화 모듈 5: VLA (learned pick policy)
const L = require('./lib');
const { C, HEX, MONO, text, box, circleIcon, pill, card, callout, code, bullets, arrow, img, table, step, flow, lab, quiz, summary, content } = L;
const TAG = '심화 · VLA';

// closed-loop evaluation on 100 unseen setups, all four tables (ros2 run unbolt_vla evaluate --episodes 100)
const EVAL = { policy: '100%', expert: '100%', note: '이 저장소의 정책(시연 1,155개, 20000단계)은 네 테이블 모두 100%, 옆에 다른 색 상자가 있던 43번도 모두 맞는 상자를 집었습니다.' };

module.exports = function build() {
  let s;
  L.section('심화 모듈 5: VLA', '심화 모듈 5 · 선택 · 약 3시간', 'VLA\n보고 배우는 집기 정책', [
    '"계산해서 집기"와 "배워서 집기"의 차이를 설명한다',
    '스크립트 전문가의 시연으로 작은 정책을 노트북 CPU에서 학습한다',
    '처음 보는 배치에서 정책과 전문가의 성공률을 비교한다',
    '정책을 ROS 노드로 감싸 작업의 "집기" 한 단계만 바꿔 끼운다',
  ], '모듈 4까지 끝낸 뒤 시간이 남거나 관심 있는 학생을 위한 심화 모듈입니다. GPU는 필요 없고 PyTorch CPU판만 있으면 됩니다. 녹화 약 40분과 학습 약 65분이 걸리므로 녹화와 학습을 먼저 걸어 두고 개념을 설명하면 시간이 맞습니다. 시간이 부족하면 강사가 미리 학습한 정책으로 평가와 대시보드만 합니다.');

  s = content('계산해서 집기 vs 배워서 집기', TAG, '모듈 3의 pick()은 마커에서 상자의 위치와 방향을 숫자로 얻고, 손 자세를 계산해 MoveIt에 맡깁니다. 정확하지만 마커가 붙은 물체만 집을 수 있고, 잡는 법을 사람이 코드로 정해야 합니다. 학습된 정책은 숫자 좌표 없이 영상에서 바로 관절 명령을 냅니다.');
  card(s, { x: 0.6, y: 1.5, w: 5.95, h: 3.4, head: '계산해서 (모듈 3)', iconName: 'FaCogs', accent: C.accent3, bodySize: 15,
    body: '카메라 → ArUco 마커 → 상자 위치·방향 (숫자)\n→ 손 목표 자세 계산 (접근 15°)\n→ MoveIt IK · 경로 계획 → 궤적\n\n• 정확하고 왜 그렇게 움직였는지 설명 가능\n• 마커 없는 물체, 새 모양은 사람이 다시 코딩' });
  card(s, { x: 6.75, y: 1.5, w: 5.95, h: 3.4, head: '배워서 (이 모듈)', iconName: 'FaBrain', accent: C.accent1, bodySize: 15,
    body: '카메라 영상 + 명령 문장 + 관절각\n→ 신경망 → 다음 1초의 관절 목표\n(0.1초마다 다시 보고 다시 낸다)\n\n• 시연만 있으면 새 물체·새 동작도 같은 방법\n• 데이터 밖 상황에서는 무엇을 할지 모른다' });
  callout(s, 'analogy', 0.6, 5.1, 12.1, 1.6, '요리책을 보고 계량해서 만드는 사람(계산)과, 잘하는 사람 옆에서 수백 번 보고 손이 기억하는 사람(학습). 앞사람은 레시피가 없으면 못 하고, 뒷사람은 처음 보는 부엌에서 헤맨다.');

  s = content('VLA = Vision + Language → Action', TAG, 'RT-2, OpenVLA, π0 같은 큰 VLA는 인터넷 규모 데이터로 미리 학습한 수십억 매개변수 모델이고 GPU가 필요합니다. 여기서는 같은 입출력 구조를 아주 작게(60만 매개변수) 만들어 노트북 CPU에서 학습합니다. 작게 만들어도 "영상을 보고 관절을 낸다"는 핵심은 같습니다.');
  [['머리 카메라 128×72', C.accent3], ['손목 카메라 96×96', C.accent3], ['명령 "pick up the green box"', C.accent4], ['관절각 8개', C.accent5]].forEach(([t, f], i) => {
    box(s, 0.6, 1.5 + i * 0.82, 3.6, 0.66, f);
    text(s, t, { x: 0.7, y: 1.5 + i * 0.82, w: 3.4, h: 0.66, fontSize: 15, bold: true, color: C.background1, align: 'center', valign: 'middle' });
    arrow(s, 4.25, 1.83 + i * 0.82, 5.0, 3.0);
  });
  box(s, 5.05, 2.2, 2.6, 1.6, C.text1);
  text(s, '정책 신경망\n60만 매개변수\nCPU 한 번 4 ms', { x: 5.05, y: 2.2, w: 2.6, h: 1.6, fontSize: 15, bold: true, color: C.background1, align: 'center', valign: 'middle' });
  arrow(s, 7.7, 3.0, 8.4, 3.0);
  box(s, 8.45, 2.2, 4.25, 1.6, C.accent1);
  text(s, '앞으로 1초(10단계)의\n오른팔 관절 7 + 손가락 목표\n+ "다 집었다" 확률', { x: 8.5, y: 2.2, w: 4.15, h: 1.6, fontSize: 15, bold: true, color: C.background1, align: 'center', valign: 'middle' });
  text(s, '0.1초마다 새 영상으로 다시 → /joint_commands', { x: 5.05, y: 3.95, w: 7.65, h: 0.4, fontSize: 13, color: C.text2, align: 'center' });
  table(s, [['', '큰 VLA (OpenVLA, π0)', '이 모듈'], ['매개변수', '30억~70억', '60만'], ['학습', 'GPU 수십 대, 시연 수십만 개', '노트북 CPU 약 1시간, 시연 1,155개'], ['할 수 있는 일', '여러 물체, 여러 동작, 처음 보는 말', '세 색 상자 집기 (테이블 네 곳)']], 0.6, 5.0, 12.1, [2.2, 5.2, 4.7], 14);

  s = content('무엇을 바꾸고 무엇을 그대로 두나', TAG, '전체를 학습으로 바꾸지 않고 집기 한 단계만 바꿉니다. 그래야 성공률을 기존 방식과 바로 비교할 수 있고, 실패하면 원인이 정책에 있다는 것을 압니다. 정책은 상자가 오른손 앞 대략 그 자리에 있을 때만 학습했으므로, 정렬(마커 정밀 접근)은 그대로 씁니다.');
  table(s, [['단계', '작업 모드', 'VLA 집기 모드'], ['계획', 'LLM (Claude)', '같음'], ['테이블까지 주행', 'Nav2', '같음'], ['상자 앞 정렬', 'ArUco 정밀 접근', '같음 (항상 오른팔 기준)'], ['집기', '마커 좌표 → MoveIt', '정책이 카메라를 보고 (/joint_commands 10 Hz)'], ['팔 접기 · 놓기', 'MoveIt', '같음']], 0.6, 1.5, 12.1, [3.0, 4.0, 5.1], 16);
  callout(s, 'why', 0.6, 5.0, 12.1, 1.7, '로봇 학습에서도 "한 번에 하나만 바꾸기"가 중요하다. 주행·정렬·놓기는 검증된 방식을 쓰고, 집기만 학습으로 바꿔 차이를 정확히 잰다.');

  s = content('무엇으로 만들었나: 프레임워크', TAG, '시뮬레이션과 데이터는 MuJoCo와 NumPy, 신경망과 학습은 PyTorch(CPU판), 로봇 시스템에 붙이는 일은 ROS 2(rclpy)가 맡습니다. LeRobot 같은 로봇 학습 프레임워크나 미리 학습된 가중치는 일부러 쓰지 않았습니다. 전체가 939줄이라 처음부터 끝까지 읽을 수 있고, 모든 숫자가 어디서 나오는지 보입니다. 구조를 이해한 뒤 LeRobot으로 옮기면 같은 시연으로 ACT를 학습해 비교할 수 있습니다.');
  table(s, [['도구', '버전', '맡은 일'], ['MuJoCo (Python)', '3.12', '물리(mj_step), 카메라 렌더링(Renderer), IK용 자코비안(mj_jac)'], ['PyTorch (CPU)', '2.x', '신경망(nn.Module), 자동 미분, AdamW, 저장(torch.save)'], ['NumPy', '1.x', '시연 배열, .npz 파일'], ['multiprocessing', '표준', '녹화를 프로세스 6개로 병렬'], ['ROS 2 rclpy + OpenCV', 'Humble', 'vla_pick 노드, 영상 축소'], ['쓰지 않음', '', 'LeRobot, Hugging Face, 사전학습 가중치, GPU']], 0.6, 1.5, 7.3, [2.4, 0.9, 4.0], 13);
  table(s, [['파일', '줄', '하는 일'], ['sim.py', '173', '집기 전용 장면'], ['expert.py', '164', '스크립트 전문가 (IK)'], ['record.py', '98', '시연 녹화 → .npz'], ['model.py', '86', '정책 신경망'], ['train.py', '132', '학습 루프'], ['runner.py', '45', '실행 (시간 평균)'], ['evaluate.py', '94', '닫힌 루프 평가'], ['vla_pick_node.py', '147', 'ROS 2 노드']], 8.2, 1.5, 4.5, [1.9, 0.6, 2.0], 13);
  callout(s, 'tip', 0.6, 5.3, 7.3, 1.4, '학습·평가는 ROS 없이 MuJoCo만으로. 브리지와 같은 scene.xml, 같은 액추에이터·중력 보상(load_model)이라 여기서 배운 정책이 ROS 안의 로봇에 그대로 맞는다.', 'ROS 없이 학습');

  s = content('전체 흐름: 데이터에서 로봇까지', TAG, '왼쪽 네 단계는 ROS 없이 돌고, 마지막만 ROS 2 노드입니다. 시연 1편은 0.1초마다 한 장면씩 77장면이고, 학습은 장면 하나하나를 표본으로 씁니다. evaluate는 같은 장면 코드로 정책과 전문가를 나란히 시켜 성공률을 잽니다.');
  flow(s, [['sim.py + expert.py\n장면 + 전문가', C.accent3, C.background1], ['record.py\n40분 · 1155편', C.accent2, C.background1], ['demos/*.npz\n460 MB', C.background2, C.text1], ['train.py\n65분 · CPU', C.accent1, C.background1], ['policy.pt\n2.4 MB', C.background2, C.text1], ['vla_pick 노드\nROS 2 · 10 Hz', C.text1, C.background1]], 0.6, 1.6, 12.1, 1.3, 0.3, 13);
  text(s, '└─ evaluate.py: 처음 보는 배치 100개에서 정책 vs 전문가', { x: 6.2, y: 3.0, w: 6.5, h: 0.4, fontSize: 13, color: C.text2, align: 'right' });
  table(s, [['단계', '입력', '출력'], ['녹화', '무작위 배치 (테이블, 자리, 상자 색, 옆 상자, 정렬 오차)', '편마다 영상 2종·관절각·정답 목표·끝 표시'], ['학습', '모든 장면 (80,080개) + 증강', '검증 오차가 가장 낮은 가중치'], ['평가', '처음 보는 배치 (seed 100000~)', '정책·전문가 성공률, GIF'], ['실행', '/camera, /wrist_camera, /joint_states', '/joint_commands, /vla/result']], 0.6, 3.6, 12.1, [1.6, 5.0, 5.5], 14);

  s = content('모방 학습: 잘하는 사람을 따라 하기', TAG, '전문가는 사람 대신 expert.py입니다. 시뮬레이터가 아는 상자의 실제 위치로 IK를 풀어 pick()과 같은 순서로 움직입니다. 정책은 실제 위치를 모르고 영상만 봅니다. 그래서 "영상에서 위치를 알아내는 법"까지 스스로 배워야 합니다.');
  step(s, 1, '전문가가 시연한다', 'expert.py: 상자 실제 위치 → IK → 손 벌리며 다가가기 → 비스듬히 밀어 넣기 → 쥐기 → 들기 (7.7초)', 0.6, 1.5, 6.0);
  step(s, 2, '0.1초마다 기록한다', '(머리·손목 영상, 관절각, 명령 문장) → 그 순간 전문가가 보낸 관절 목표', 0.6, 2.85, 6.0);
  step(s, 3, '같은 입력에서 같은 출력을 내게 학습', '지도 학습. 정답과 예측의 차이(L1)를 줄인다. 시연 1,155개 = 약 8.9만 장면', 0.6, 4.2, 6.0);
  callout(s, 'warn', 0.6, 5.55, 6.0, 1.15, '정책은 실제 위치를 모른다. 영상만 보고 흉내 낸다.', '핵심');
  code(s, '# expert.py (줄임)\ngrasp = box_center + [0, 0, 0.015]\npre   = grasp - 0.10 * approach + [0, 0, 0.04]\nq_pre = ik.best(pre, R)          # 여러 시작점\nfor 단계 in 경유점들:\n    q = ik.solve(q, 직선 위의 점, R)\n    actions.append([*q, 손가락])\n# 정답 = actions (10 Hz)', 6.9, 1.5, 5.8, 5.2, 13);

  s = content('장면 (sim.py): 관찰과 행동', TAG, '정책이 보는 것(관찰)과 내는 것(행동)을 정하는 곳입니다. 행동은 토크가 아니라 관절 위치 목표라서, 정책이 조금 틀려도 MuJoCo의 위치 액추에이터가 부드럽게 따라갑니다. 머리 카메라는 ROS 노드가 1280×720을 줄이는 것과 같아지도록 3배 크게 그린 뒤 3×3 평균으로 줄입니다.');
  table(s, [['', '내용', '크기'], ['관찰: 머리 카메라', 'head_camera, 384×216 렌더 → 3×3 평균', '72×128×3'], ['관찰: 손목 카메라', 'camera_wrist_right (fovy 66°)', '96×96×3'], ['관찰: 관절각', '오른팔 관절 1~7 + 손가락', '8'], ['행동', '같은 8개 관절의 위치 목표 → 위치 액추에이터 (kp 230~30)', '8'], ['제어 주기', '0.1초 = mj_step(1 ms) 100번', '10 Hz'], ['성공', '집으라고 한 상자가 3 cm 이상 올라감', '']], 0.6, 1.5, 7.6, [2.2, 4.3, 1.1], 13);
  card(s, { x: 8.5, y: 1.5, w: 4.2, h: 5.2, head: 'reset(): 매번 다르게', iconName: 'FaArrowsAlt', accent: C.accent3, bodySize: 12,
    body: '1. 테이블 넷 중 하나, 그 테이블의 자리 하나, 상자 색 하나\n2. 상자: 자리 중심 ±3 cm, 방향 ±45°\n3. 절반은 다른 색 상자를 옆자리에\n4. 로봇: 집을 상자가 몸 기준 (0.38, −0.15) m ± (4, 5) cm에 오게, 방향 ±8°\n5. 두 팔 tuck, 0.3초 놓아 두기\n\n자리와 방향은 scene.xml에서 읽는다 (이름에 _pad_가 든 geom)' });

  s = content('전문가의 IK: 감쇠 최소제곱', TAG, '전문가는 MoveIt 대신 IK를 직접 풉니다. 목표와 지금 손의 위치·자세 차이(6차원)를 자코비안으로 관절 7개의 변화로 바꿉니다. λ를 더해 팔이 쭉 펴진 특이점 근처에서도 값이 튀지 않게 합니다. 팔이 접힌 tuck은 시작점으로 나빠서 home 자세부터 시도하고, 같은 시작점을 먼저 써서 시연마다 팔 모양이 같게 합니다.');
  code(s, 'e  = [ p* − p ;  0.5 · rotvec(R* Rᵀ) ]       # 6차원 오차\nJ  = [ Jp ; 0.5 · Jr ]     (6 × 7)             # mj_jac\nΔq = Jᵀ (J Jᵀ + λI)⁻¹ e,   λ = 1e-4\nq  ← clip(q + clip(Δq, ±0.2), 관절 범위)\n# 오차가 작아질 때까지 최대 100번 (시작점 찾기 300번)\n\nTCP = 손 끝 사이트에서 손가락 쪽 0.14 m (두 패드 가운데)\n잡는 자세 = 앞으로, 15° 아래로, 상자 면에 맞춰 ±45°', 0.6, 1.5, 7.2, 3.3, 13);
  table(s, [['구간', '시간', '움직임'], ['reach', '2.5 s', '관절 공간, 손 벌리기'], ['pre', '1.0 s', '사전 접근 자세로 직선'], ['approach', '1.5 s', '잡기 자세로 직선'], ['close', '1.0 s', '손 닫기'], ['lift', '1.2 s', '8 cm 들기'], ['hold', '0.5 s', '그대로 ("끝" 정답)']], 8.1, 1.5, 4.6, [1.4, 0.9, 2.3], 13);
  callout(s, 'tip', 0.6, 5.0, 7.2, 1.7, '직선 구간은 0.1초마다 점을 찍고 각 점에서 IK를 푼다. 보간은 smooth(t) = t²(3 − 2t). 모두 77개 목표 = 7.7초.', '경로 만들기');
  callout(s, 'warn', 8.1, 4.9, 4.6, 1.8, 'IK가 경유점에 5 mm 넘게 못 닿은 시연은 버린다 (1200개 중 45개를 실패로 버림).', '나쁜 예는 버린다');

  s = content('시연 한 편 (7.7초)', TAG, '2번 공급 테이블에서 "pick up the green cube from the table"을 녹화한 시연입니다. 옆자리에 파란 상자가 있습니다. 위는 머리 카메라, 아래는 손목 카메라입니다. 손목 카메라에서 상자가 점점 커지다가 손가락 사이로 들어옵니다. 집는 순간에는 머리 카메라에서 손이 상자를 가리기 때문에, 마지막 몇 cm는 손목 카메라가 결정적입니다.');
  img(s, 'vla_episode.png', 0.6, 1.5, 12.1, 2.6, '시연 한 편: 머리 카메라와 손목 카메라 영상 7장');
  table(s, [['기록', '모양', '뜻'], ['head', '77 × 72 × 128 × 3', '머리 카메라 (ROS 1280×720을 10배 줄인 것과 같게)'], ['wrist', '77 × 96 × 96 × 3', '오른손 손목 카메라'], ['state / action', '77 × 8', '관절각 / 그때 전문가가 보낸 목표'], ['done', '77', '마지막 0.5초만 1 ("다 집었다")']], 0.6, 4.35, 12.1, [2.4, 3.2, 6.5], 14);

  s = content('작은 차이가 쌓이는 문제와 세 가지 대책', TAG, '정책이 조금만 틀려도 다음 장면은 시연에 없던 장면이 되고, 거기서 더 틀리게 됩니다(compounding error). 모방 학습의 가장 큰 문제입니다. 세 가지로 막습니다.');
  card(s, { x: 0.6, y: 1.5, w: 3.9, h: 3.9, head: '넓게 모으기', iconName: 'FaArrowsAlt', accent: C.accent3, bodySize: 14,
    body: '테이블 네 곳 × 자리 × 색 셋\n절반은 옆자리에 다른 상자\n상자 ±3 cm, 방향 ±45°\n로봇 정렬 오차 ±4×5 cm, ±8°\n\n매 시연마다 무작위\n(sim.py TABLES, BOXES, SPREAD)' });
  card(s, { x: 4.7, y: 1.5, w: 3.9, h: 3.9, head: '흔들어 모으기 (DART)', iconName: 'FaRedo', accent: C.accent2, bodySize: 14,
    body: '시연 절반은 실제로 보내는 목표에 천천히 변하는 잡음 d를 더한다.\nd ← 0.85·d + N(0, 0.012²) rad\n\n기록하는 정답은 전문가 목표 그대로\n→ "어긋났을 때 돌아오는 법"이 데이터에 들어간다' });
  card(s, { x: 8.8, y: 1.5, w: 3.9, h: 3.9, head: '묶음으로 내기 (ACT)', iconName: 'FaLayerGroup', accent: C.accent1, bodySize: 14,
    body: '1단계가 아니라 10단계를 한 번에 예측.\n\n매 순간 겹치는 예측 여러 개를 평균 (temporal ensembling)\n→ 떨림이 줄고 한 번의 실수가 덜 퍼진다' });
  callout(s, 'analogy', 0.6, 5.6, 12.1, 1.1, '운전 연수에서 강사가 일부러 핸들을 살짝 틀어 놓고 "다시 차선으로 돌아오는 법"을 가르치는 것이 DART다.');

  s = content('정책의 구조 (model.py)', TAG, '영상마다 작은 합성곱 신경망을 지나 공간 소프트맥스로 "특징이 가장 강한 위치 (x, y)" 64개를 뽑습니다. 상자와 손가락이 어디 있는지가 숫자로 나오는 셈이라 적은 데이터로도 잘 배웁니다. 명령은 단어를 해시해서 어떤 문장이든 벡터로 만듭니다.');
  code(s, '이미지 ─ 합성곱 4층 ─ 공간 소프트맥스 ─▶ 키포인트 64개 (x, y) = 128\n  (머리 72×128, 손목 96×96 각각)\n\n명령 ── 단어 해시 (512칸) ── 단어 벡터 평균 ─▶ 32\n\n관절각 8 ── 정규화 ─────────────────────────▶ 8\n\n이어 붙이기 (296) ─ MLP 512 ─ MLP 512 ─▶ 10단계 × 8 관절 목표\n                                        + "끝" 확률 1', 0.6, 1.5, 12.1, 3.0, 14);
  table(s, [['선택', '이유'], ['공간 소프트맥스', '집기에 필요한 것은 "어디에"다. 위치를 직접 숫자로 뽑는다'], ['카메라 두 대', '멀리서는 머리 카메라, 마지막 몇 cm는 손목 카메라'], ['영상 흔들기 · 밝기 바꾸기', '렌더링이 조금 달라도(ROS 영상 축소 방식 등) 버티게'], ['단어 해시', 'LLM이 보낸 어떤 문장도 들어갈 수 있다 (실험해 보니 지금 정책은 색 낱말보다 정렬 위치를 본다 → "언어 확인 실험")']], 0.6, 4.7, 12.1, [3.4, 8.7], 13);

  s = content('층별 모양과 매개변수 (PyTorch)', TAG, 'nn.Sequential로 쌓은 인코더 두 개(머리, 손목은 가중치를 따로 가짐), 단어 임베딩 표, MLP입니다. 매개변수 대부분(76%)은 MLP에 있습니다. 직접 확인: python3 -c "from unbolt_vla.model import PickPolicy; print(PickPolicy())"');
  table(s, [['층', '머리 카메라', '손목 카메라'], ['입력 (0~1 → −0.5~0.5)', '3 × 72 × 128', '3 × 96 × 96'], ['Conv 5×5 보폭 2, 32 + GroupNorm + ReLU', '32 × 36 × 64', '32 × 48 × 48'], ['Conv 3×3 보폭 2, 64 + GN + ReLU', '64 × 18 × 32', '64 × 24 × 24'], ['Conv 3×3 보폭 1, 64 + GN + ReLU', '64 × 18 × 32', '64 × 24 × 24'], ['Conv 1×1, 64 (키포인트 지도)', '64 × 18 × 32', '64 × 24 × 24'], ['공간 소프트맥스', '128', '128']], 0.6, 1.5, 7.6, [3.6, 2.0, 2.0], 13);
  table(s, [['부분', '매개변수'], ['머리 인코더', '62,336'], ['손목 인코더', '62,336'], ['단어 표 512 × 32', '16,384'], ['MLP 296 → 512 → 512 → 81', '456,273'], ['합계', '597,329']], 8.5, 1.5, 4.2, [2.6, 1.6], 13);
  code(s, 'def forward(self, head, wrist, words, offsets, state):\n    z = torch.cat([self.head_enc(head - 0.5), self.wrist_enc(wrist - 0.5),\n                   self.words(words, offsets),\n                   (state - self.mean) / self.std], dim=1)   # (n, 296)\n    out = self.trunk(z)                                      # (n, 81)\n    return out[:, :-1].view(-1, 10, 8), out[:, -1]           # 묶음, "끝" 로짓', 0.6, 4.7, 12.1, 2.0, 13);

  s = content('공간 소프트맥스: "어디에"를 숫자로', TAG, '특징 지도 한 장을 화면 전체에 대한 확률로 바꾸고, 그 확률로 화면 좌표의 평균을 냅니다. 결과는 "이 특징이 화면 어디에 있나"라는 숫자 두 개입니다. 학습하면서 어떤 키포인트는 상자를, 어떤 것은 손가락 끝을 따라가게 됩니다. Levine 등(2016)이 로봇 손-눈 협응 학습에 쓴 방법입니다.');
  code(s, 'p_k(i, j) = exp(f_k(i, j)) / Σ exp(f_k)      # k번째 지도의 확률\nx̂_k = Σ p_k(i, j) · x_j                     # x_j, y_i ∈ [−1, 1]\nŷ_k = Σ p_k(i, j) · y_i\n\n# model.py SpatialSoftmax.forward\np  = F.softmax(x.flatten(2), dim=-1).view(n, c, h, w)\nxs = torch.linspace(-1, 1, w); ys = torch.linspace(-1, 1, h)\nreturn torch.cat([(p.sum(2) * xs).sum(-1),\n                  (p.sum(3) * ys).sum(-1)], dim=1)   # (n, 2c)', 0.6, 1.5, 7.4, 3.9, 13);
  card(s, { x: 8.3, y: 1.5, w: 4.4, h: 3.9, head: '왜 평균 풀링이 아닌가', iconName: 'FaCrosshairs', accent: C.accent1, bodySize: 14,
    body: '평균 풀링은 "무엇이 있나"는 남기지만 "어디에"를 지운다.\n\n공간 소프트맥스는 위치를 그대로 숫자로 넘겨 주므로, 상자가 2 cm 옮겨지면 키포인트도 그만큼 움직인다.\n\n→ 시연 수백 개, CPU로도 배운다' });
  callout(s, 'analogy', 0.6, 5.6, 12.1, 1.1, '사진 64장에 각각 "가장 밝은 곳에 핀을 꽂아라"를 시키고, 핀 64개의 좌표만 다음 사람에게 넘기는 것.');

  s = content('학습 설정 (train.py)', TAG, '시연의 모든 장면이 표본 하나입니다. 그 순간의 영상 두 장·관절각·문장을 넣고, 그 장면부터 10단계의 전문가 목표를 맞히게 합니다. 손실은 묶음 전체의 L1과 "끝" 판단의 이진 교차 엔트로피입니다. 검증은 편 단위로 떼어 둔 10%로 합니다(같은 편의 장면이 양쪽에 섞이면 검증이 너무 쉬워짐).');
  table(s, [['항목', '값'], ['표본', '학습 1040편 = 80,080장면, 검증 115편'], ['정답', '그 장면부터 10단계 목표 (끝은 마지막 목표로 채움), 평균·표준편차로 정규화'], ['손실', 'L1(묶음) + 0.1 × BCE("끝")'], ['최적화', 'AdamW, lr 1e-3, weight decay 1e-4, OneCycleLR'], ['배치 · 단계', '64 · 20,000 (약 16 에포크), CPU 8스레드 약 0.19 s/단계'], ['증강', '영상 ±4 px 이동, 밝기·대비 ±10%, 관절각 잡음 0.01 rad'], ['저장', '500단계마다 검증, 가장 좋을 때 policy.pt']], 0.6, 1.5, 6.9, [1.6, 5.3], 13);
  code(s, '# 학습 한 단계 (train.py)\nidx = rng.integers(0, len(train), 64)\nhead, wrist, words, offsets, state, \\\n    chunk, done = train.batch(idx, True)\npred, logit = policy(head, wrist, words,\n                     offsets, state)\ntarget = (chunk - mean) / std\nloss = F.l1_loss(pred, target) + 0.1 * \\\n    F.binary_cross_entropy_with_logits(\n        logit, done)\nopt.zero_grad()\nloss.backward()\nopt.step()\nsched.step()', 7.8, 1.5, 4.9, 5.2, 12);

  s = content('학습 곡선: 검증 오차', TAG, '이 저장소의 실제 학습 기록입니다(테이블 넷, 시연 1,155편, 20000단계). 검증 L1은 정규화 단위라 0.0385는 관절마다 평균 0.4~1.4° 차이입니다. 오른쪽 표의 아래 두 줄은 방을 넓히기 전(테이블 둘)의 실험입니다. 공급 테이블만 쓴 학습도 곡선은 비슷하게 내려갔지만 작업대에서는 0/20이었습니다. 검증 데이터가 학습 데이터와 같은 범위에서만 왔기 때문입니다. 낮은 검증 오차가 "처음 보는 곳에서도 잘한다"를 뜻하지 않습니다.');
  const steps = [];
  for (let k = 500; k <= 20000; k += 500) steps.push(String(k));
  const four = [0.1263, 0.0982, 0.0820, 0.0714, 0.0678, 0.0669, 0.0667, 0.0638, 0.0636, 0.0613, 0.0580, 0.0589, 0.0559, 0.0517, 0.0523, 0.0517, 0.0502, 0.0487, 0.0499, 0.0486, 0.0477, 0.0467, 0.0473, 0.0460, 0.0460, 0.0438, 0.0440, 0.0428, 0.0423, 0.0420, 0.0408, 0.0403, 0.0395, 0.0397, 0.0390, 0.0388, 0.0390, 0.0385, 0.0385, 0.0385];
  s.addChart(L.pres.ChartType.line, [{ name: '테이블 넷 · 상자 셋, 1,155편', labels: steps, values: four }], {
    x: 0.6, y: 1.5, w: 8.2, h: 5.2, chartColors: [HEX.accent1], lineSize: 2.5, lineDataSymbol: 'none',
    showLegend: true, legendPos: 'b', legendFontSize: 13, legendFontFace: '+mn-lt',
    showTitle: true, title: '검증 L1 (500단계마다)', titleFontSize: 15, titleFontFace: '+mn-lt', titleColor: HEX.dk1,
    catAxisLabelColor: HEX.dk2, valAxisLabelColor: HEX.dk2, catAxisLabelFontSize: 11, valAxisLabelFontSize: 11,
    catAxisLabelFontFace: '+mn-lt', valAxisLabelFontFace: '+mn-lt', catAxisLabelFrequency: 8,
    valAxisMinVal: 0, valAxisMaxVal: 0.14, valAxisLabelFormatCode: '0.00',
    valGridLine: { color: HEX.lt2, size: 0.75 }, catGridLine: { style: 'none' }, objectName: 'chart_val_l1' });
  table(s, [['학습 데이터', '검증 L1', '닫힌 루프'], ['테이블 넷 1,155편', '0.0385', '100/100'], ['(전) 테이블 둘 583편', '0.038', '100/100'], ['(전) 공급만 297편', '0.043', '작업대 0/20']], 9.1, 1.5, 3.6, [1.6, 0.8, 1.2], 12);
  callout(s, 'warn', 9.1, 3.6, 3.6, 3.1, '검증 오차는 "본 적 있는 종류의 장면"에서의 실력이다. 쓸 곳에서 닫힌 루프로 직접 평가해야 안다.', '숫자만 믿지 말 것');

  s = content('실행: 묶음 예측의 시간 평균 (runner.py)', TAG, '정책은 0.1초마다 앞으로 10단계를 예측합니다. 그러면 "지금"에 대한 예측이 최근 10번의 호출에서 하나씩 쌓입니다. 이것을 가중 평균해 보냅니다(ACT의 temporal ensembling). 오래된 예측에 조금 더 무게를 둬서 움직임이 매끄럽고, 한 번 튄 예측이 바로 팔을 흔들지 못합니다.');
  for (let r = 0; r < 4; r++) {
    for (let c = 0; c < 10; c++) {
      const x = 0.6 + (r + c) * 0.52, y = 1.6 + r * 0.55;
      if (x + 0.48 > 6.9) continue;
      box(s, x, y, 0.48, 0.45, r + c === 3 ? C.accent1 : C.background2);
    }
    text(s, r === 3 ? '지금(t) 예측' : `t−${3 - r}에 예측`, { x: 7.0, y: 1.6 + r * 0.55, w: 1.4, h: 0.45, fontSize: 12, color: C.text2, valign: 'middle' });
  }
  text(s, '주황 칸 = 모두 "지금(t)"에 대한 예측 → 가중 평균해서 보냄', { x: 0.6, y: 3.9, w: 7.6, h: 0.4, fontSize: 13, color: C.text2 });
  code(s, 'a_now = Σ w_i · a_i / Σ w_i,   w_i = exp(−0.1 · i)\n        (i = 0이 가장 오래된 예측)\n\n# runner.py\nself.chunks.append(unnormalise(pred))          # 최근 10개\nnow = [c[n - 1 - i] for i, c in enumerate(self.chunks)]\nreturn (w[:, None] * now).sum(0) / w.sum()', 0.6, 4.4, 7.6, 2.3, 13);
  card(s, { x: 8.5, y: 1.5, w: 4.2, h: 5.2, head: '언제 멈추나', iconName: 'FaStopCircle', accent: C.accent6, bodySize: 14,
    body: '"끝" 확률(시그모이드)이 3단계 연속 0.5를 넘으면 멈춘다.\n\nROS 노드는 그다음 한 번 더 확인한다: 손을 닫으라고 명령했고(목표 > −0.15) 손가락이 물체에 걸려 덜 닫혔는가(|각도| > 0.06).\n\n한 번 계산 = CPU 약 4 ms (torch.no_grad, 4스레드)' });

  s = content('따라 하기: 시연 녹화와 학습', TAG, '녹화는 MuJoCo만 쓰고 ROS는 필요 없습니다. 8코어 노트북에서 녹화 약 40분, 학습 약 65분입니다(학습 중에 ROS를 같이 돌리면 더 걸림). 학습을 걸어 두고 앞의 개념 슬라이드와 model.py를 읽으면 시간이 맞습니다. 검증 오차가 가장 낮을 때마다 policy.pt를 덮어씁니다.');
  lab(s, {
    cmd: '# 시연 1200개, 테이블 넷 × 상자 셋 (약 40분, ~/unbolt_vla/demos)\n$ ros2 run unbolt_vla record --episodes 1200\n1155/1200 episodes kept in ~/unbolt_vla/demos\n\n# 학습 (약 65분, ~/unbolt_vla/policy.pt)\n$ ros2 run unbolt_vla train\n1040 training episodes (80080 steps), 115 validation\nstep    500  train 0.1300  val 0.1263  done 0.094\n...\nstep  20000  train 0.0365  val 0.0385  done 0.045',
    cmdH: 3.9, cmdSize: 13,
    explain: ['val = 학습에 안 쓴 시연 115개에서의 오차 (작을수록 좋음)', 'done = "다 집었다" 판단의 오차'],
    ok: 'val이 처음보다 크게 줄고 policy.pt가 생긴다.\n\n✅ 체크포인트 5-2',
    fail: 'No module named torch → pip install --user torch --index-url https://download.pytorch.org/whl/cpu',
  });

  s = content('처음 보는 배치에서 평가', TAG, `evaluate는 학습에 쓰지 않은 무작위 배치 100개(테이블·자리·색·옆 상자 모두 무작위)에서 정책과 전문가를 똑같이 시킵니다. 정책은 "다 집었다"를 세 번 연속 말하거나 12초가 지나면 멈춥니다. 성공 = 상자가 3 cm 이상 들렸다. ${EVAL.note}`);
  [[EVAL.policy, '정책 100/100 (영상만 보고)', C.accent1], [EVAL.expert, '전문가 100/100 (위치를 알고)', C.accent3]].forEach(([v, k, f], i) => {
    const x = 0.6 + i * 3.2;
    box(s, x, 1.5, 3.0, 2.4, C.background2);
    text(s, v, { x, y: 1.6, w: 3.0, h: 1.3, fontSize: 48, bold: true, color: f, align: 'center', valign: 'middle' });
    text(s, k, { x, y: 2.95, w: 3.0, h: 0.8, fontSize: 15, color: C.text2, align: 'center', valign: 'middle' });
  });
  code(s, '$ ros2 run unbolt_vla evaluate --episodes 100\nsupply_1  15/15   supply_2  33/33   supply_3  23/23\nwork_table 29/29  옆 상자 있음 43/43  없음 57/57', 0.6, 4.1, 6.2, 1.2, 13);
  callout(s, 'tip', 0.6, 5.5, 6.2, 1.2, '--video ~/vla.gif: 처음 3편을 GIF로. --table supply_1 등: 한 테이블만.', '영상으로 확인');
  callout(s, 'why', 7.1, 1.5, 5.6, 5.2, '100%가 나와도 끝이 아니다.\n\n• 정책이 무엇을 보고 맞혔나? 색 낱말인가, 다른 단서인가 (다음 장)\n• 평가 배치는 학습과 같은 범위에서 뽑았다. 정렬이 더 틀어지면? (도전 과제)\n• 시뮬레이터 렌더링만 봤다. 실제 카메라, 조명, 다른 상자는?\n• 데이터가 한쪽에만 있으면? (그다음 장)');

  s = content('언어 확인 실험: 정책은 지름길을 배웠다', TAG, '100/100은 틀린 숫자가 아니지만 "색 낱말을 읽고 골랐다"는 증거는 아닙니다. evaluate --ask-other는 두 상자가 있는 배치에서 로봇을 한 상자에 정렬하고, 명령으로는 옆 상자의 색을 말합니다. 정책은 20번 모두 정렬한 상자를 집었습니다. 시연에서는 늘 "오른손 앞에 정렬된 상자 = 집으라는 상자"였기 때문에, 더 쉬운 단서(정렬 위치)를 배운 것입니다. 이것을 shortcut learning이라고 합니다. 실제 작업에서는 작업 관리자가 집을 상자의 마커로 정렬하므로 이 지름길로도 맞게 동작합니다.');
  code(s, '$ ros2 run unbolt_vla evaluate --ask-other --episodes 20\nepisode   0  supply_3   lined up with red  , asked for blue  -> lifted the lined-up box\nepisode   1  supply_2   lined up with green, asked for blue  -> lifted the lined-up box\n...\nnamed box: 0/20, lined-up box: 20/20, nothing: 0/20', 0.6, 1.5, 12.1, 1.8, 13);
  card(s, { x: 0.6, y: 3.55, w: 5.95, h: 3.15, head: '왜 이렇게 배웠나', iconName: 'FaRoute', accent: C.accent6, bodySize: 14,
    body: '모든 시연에서 집을 상자는 오른손 앞 (0.38, −0.15) m 근처에 있었다.\n"오른손 앞의 상자"만 보면 정답 행동을 낼 수 있으니, 신경망은 색 낱말을 쓸 이유가 없었다.\n데이터가 허락하는 가장 쉬운 규칙을 배운다.' });
  card(s, { x: 6.75, y: 3.55, w: 5.95, h: 3.15, head: '언어가 꼭 필요하게 하려면 (과제 3)', iconName: 'FaComments', accent: C.accent3, bodySize: 14,
    body: '두 상자 사이에 정렬하고 명령한 색의 상자로 손을 뻗는 시연을 모은다.\n그러면 영상만으로는 어느 쪽인지 알 수 없어 색 낱말을 써야 한다.\n다시 --ask-other로 "named box"가 늘었는지 확인.' });

  s = content('정책은 본 것만 할 수 있다 (방을 넓히기 전 실험)', TAG, '방을 넓히기 전(테이블 둘, 빨간 상자 하나)의 실험입니다. 그래서 지금은 네 테이블 모두에서 시연을 모읍니다. 처음에는 공급 테이블 시연만으로 학습했습니다. 공급 테이블에서는 거의 다 집었지만, 나무색 작업대에서는 한 번도 못 집었고, 팔을 조금 움직이다 2초 만에 "다 집었다"고 말했습니다. "원래 자리에 갖다 놔"는 작업대에서 집어야 하므로 작업대 시연을 더해 다시 학습했습니다. 멈춤(stall)도 시연을 늘리자 사라졌습니다.');
  table(s, [['학습 데이터', '공급 테이블', '작업대', '실패 모양'], ['공급 테이블 시연 297개', '48/50 (96%)', '0/20 (0%)', '공급: 접근 시작 자세에서 멈춤 2번\n작업대: 2초 만에 "다 집었다"'], ['두 테이블 시연 583개', '48/48 (100%)', '52/52 (100%)', '없음']], 0.6, 1.5, 12.1, [3.3, 2.0, 2.0, 4.8], 16);
  card(s, { x: 0.6, y: 3.9, w: 5.95, h: 2.8, head: '멈춤 (stall)', iconName: 'FaStopCircle', accent: C.accent6, bodySize: 14,
    body: '손이 상자 위 접근 시작 자세까지 가서 서 버린다.\n전문가가 경유점마다 잠깐 서기 때문에 "멈춘 장면에서 계속 서 있기"도 그럴듯한 답이 된다. 모방 학습에서 흔한 실패.' });
  card(s, { x: 6.75, y: 3.9, w: 5.95, h: 2.8, head: '처음 보는 장면', iconName: 'FaEye', accent: C.accent3, bodySize: 14,
    body: '상판 색, 방 배경, 로봇 방향이 바뀌면 정책에게는 다른 세상이다. 공간 소프트맥스도 "어디에"를 찾을 특징이 없다.\n→ 쓸 곳의 장면을 데이터에 넣는 것이 가장 확실한 해결.' });

  s = content('ROS에 끼우기: vla_pick 노드', TAG, 'pick:=vla로 켜면 브리지가 손목 카메라를 켜고 머리 카메라를 10 Hz로 올립니다(정책은 매 단계 새 영상으로 학습). 작업 관리자는 정렬까지 한 뒤 /vla/pick에 명령 문장을 보내고 /vla/result를 기다립니다. 성공하면 MoveIt으로 팔을 접는 것부터는 기존과 같습니다.');
  flow(s, [['pick_object\n(작업 관리자)', C.accent3, C.background1], ['정렬\nservo_to_marker', C.background2, C.text1], ['/vla/pick\n"pick up the red box"', C.accent4, C.background1], ['vla_pick 노드\n10 Hz', C.accent1, C.background1], ['/vla/result\n{ok, steps}', C.accent2, C.background1]], 0.6, 1.5, 12.1, 1.2, 0.35, 14);
  table(s, [['방향', '토픽', '내용'], ['sub', '/camera/image_raw → 128×72', '머리 카메라 (INTER_AREA로 줄임)'], ['sub', '/wrist_camera/image_raw', '손목 카메라 96×96 (브리지 wrist_camera_rate)'], ['sub', '/joint_states', '오른팔 7 + 손가락'], ['pub', '/joint_commands', '0.1초마다 관절 목표 (브리지가 actuator 목표로)'], ['pub', '/vla/status', '단계, "끝" 확률 (대시보드 카드)']], 0.6, 3.0, 7.6, [0.9, 3.3, 3.4], 13);
  code(s, '# 터미널에서\n$ ros2 launch unbolt_manipulation \\\n    bringup.launch.py planner:=true \\\n    dashboard:=true pick:=vla\n\n# 대시보드 런처: 모드\n# "VLA 집기" → 연결', 8.5, 3.0, 4.2, 3.7, 13);

  s = content('대시보드: VLA 집기 모드', TAG, '1번 공급 테이블에서 정책이 빨간 상자를 집은 직후입니다. 아래 카드에 손목 카메라(정책이 보는 96×96), 단계 수, "다 집었다" 확률, 마지막 결과가 나옵니다. vla_pick은 정책의 "다 집었다"를 그대로 믿지 않고, 손을 닫으라고 명령했고 손가락이 물체에 걸려 덜 닫혔을 때만 성공으로 보고합니다. 처음에는 손가락 각도만 봐서, 벌린 손도 성공으로 잘못 보고된 적이 있습니다.');
  img(s, 'dashboard_vla.jpg', 0.6, 1.4, 6.2, 5.45, '대시보드 VLA 집기 모드: 헤드 카메라에 상자를 쥔 손, 아래 VLA 카드에 손목 카메라와 성공 91단계');
  callout(s, 'warn', 7.5, 1.5, 5.2, 2.6, '학습된 부품의 출력은 다른 신호로 한 번 더 확인한다.\n성공 = 손을 닫으라고 명령했고(목표 > −0.15) 손가락이 덜 닫혔다(|각도| > 0.06).', '"다 집었다"를 믿지 말 것');
  callout(s, 'ok', 7.5, 4.3, 5.2, 2.4, '"상자를 모두 작업대에 모아" → "모두 제자리로": 세 테이블과 작업대 세 자리에서 정책이 집음\n(이 저장소에서 ROS로 6번 모두 성공, 74~88단계)\n\n✅ 체크포인트 5-4');

  s = content('ACT · LeRobot · 큰 VLA와 비교', TAG, '구조는 같고 크기와 부품이 다릅니다. ACT는 같은 "묶음 예측 + 시간 평균"을 트랜스포머와 CVAE로 합니다. OpenVLA는 큰 언어 모델이 행동을 토큰으로 하나씩 말하고, π0는 비전-언어 모델 옆의 "행동 전문가"가 flow matching으로 50단계 묶음을 만듭니다. LeRobot은 이런 정책과 데이터 형식, 학습 스크립트를 모아 둔 Hugging Face의 프레임워크입니다.');
  table(s, [['', '이 모듈', 'ACT (2023)', 'OpenVLA (2024)', 'π0 (2024)'], ['영상', 'CNN 4층 + 공간 소프트맥스 (처음부터)', 'ResNet-18 (ImageNet)', 'DINOv2 + SigLIP', 'SigLIP (PaliGemma)'], ['언어', '단어 해시 + 임베딩 평균', '없음', 'Llama 2 7B', 'Gemma 2B (PaliGemma)'], ['행동', 'MLP, 10단계 묶음', '트랜스포머 디코더 + CVAE, 묶음', '256칸 토큰을 하나씩', 'flow matching, 50단계 묶음'], ['매개변수', '60만', '약 8천만', '70억', '약 33억'], ['학습', '노트북 CPU 약 1시간, 시연 1,155편', 'GPU, 과제당 시연 약 50편', 'GPU 수십 장, 약 97만 편', 'GPU 대규모 사전학습 + 미세조정']], 0.6, 1.5, 12.1, [1.4, 2.9, 2.6, 2.5, 2.7], 13);
  callout(s, 'tip', 0.6, 5.2, 12.1, 1.5, 'record.py → train.py → evaluate.py는 LeRobot의 "모으기 → 학습 → 평가"를 작게 손으로 짠 것이다. 구조를 이해했다면 같은 시연을 LeRobot 형식으로 옮겨 ACT를 학습해 비교해 볼 수 있다 (GPU 권장).', '다음 단계');

  s = content('한계와 다음 단계', TAG, '이 모듈의 정책은 장난감 크기입니다. 그래도 큰 VLA가 부딪히는 문제를 그대로 겪어 볼 수 있습니다. 과제에서 하나씩 건드려 봅니다.');
  [['FaCube', '언어 대신 정렬 위치를 본다', '상자가 셋이어도 색 낱말을 쓰지 않는다 → 과제 3: 두 상자 사이에 정렬하고 말로 고르게'], ['FaCamera', '시뮬레이터 영상만', '실제 카메라와 렌더링의 차이(sim-to-real) → 도메인 무작위화, 실제 시연 섞기'], ['FaArrowsAlt', '학습한 범위 밖', '정렬이 더 틀어지면 실패 → 도전 과제: SPREAD 두 배로 평가'], ['FaHandPaper', '집기 한 동작', '놓기·다른 동작은 데이터를 따로 모아야 → 시연 수와 성공률의 관계(과제 1)']].forEach(([ic, h, b], i) => {
    const y = 1.5 + i * 1.3;
    circleIcon(s, ic, 0.6, y, 0.8, [C.accent1, C.accent3, C.accent6, C.accent2][i]);
    text(s, h, { x: 1.65, y: y - 0.05, w: 11, h: 0.45, fontSize: 18, bold: true });
    text(s, b, { x: 1.65, y: y + 0.4, w: 11, h: 0.6, fontSize: 15, color: C.text2 });
  });

  summary('심화 모듈 5 한 장 요약', TAG, [
    ['FaBrain', 'VLA = 영상 + 문장 → 관절 명령', '좌표 계산 없이 0.1초마다 보고 다음 1초의 관절 목표를 낸다'],
    ['FaUsers', '모방 학습: 전문가 시연 → 지도 학습', '전문가는 실제 위치를 알고, 정책은 영상만 본다'],
    ['FaShieldAlt', '쌓이는 오차를 막는 세 가지', '넓게 모으기, DART 잡음, 묶음 예측 + 시간 평균'],
    ['FaCrosshairs', '공간 소프트맥스 + 손목 카메라', '"어디에"를 숫자로. 마지막 몇 cm는 손목 카메라'],
    ['FaLink', '한 단계만 바꿔 끼운다', 'pick:=vla — 계획·주행·정렬·놓기는 그대로, 집기만 정책'],
  ], '다섯 줄로 정리합니다.');

  quiz('심화 모듈 5 셀프 체크', TAG, [
    ['전문가는 상자의 실제 위치를 알고 정책은 모른다. 그런데도 정책이 집을 수 있는 이유는?', '영상에 상자가 보이고, 같은 영상에서 전문가가 낸 관절 목표를 수만 번 보며 "영상 속 위치 → 관절" 관계를 배웠기 때문이다. 공간 소프트맥스가 위치를 숫자로 뽑는 것을 돕는다.'],
    ['DART에서 정답을 잡음 섞인 목표가 아니라 전문가 목표로 기록하는 이유는?', '잡음 섞인 목표를 정답으로 두면 잡음까지 따라 한다. 어긋난 장면에서 "원래 가야 할 곳"을 정답으로 줘야 돌아오는 법을 배운다.'],
    ['한 단계씩이 아니라 10단계 묶음으로 예측하는 장점은?', '움직임이 매끄럽고, 한 번 틀린 예측의 영향이 겹치는 다른 예측과 평균되어 줄어든다. 결정 횟수가 줄어 오차가 덜 쌓인다.'],
    ['VLA 모드에서도 마커 정렬을 그대로 쓰는 이유는?', '정책은 상자가 오른손 앞 대략 그 자리(±수 cm)에 있을 때만 학습했다. 그 범위로 데려다 놓는 일은 검증된 방식이 맡는다.'],
    ['이 정책을 실제 로봇에 바로 쓰기 어려운 이유 두 가지는?', '렌더링과 실제 카메라 영상의 차이(색·조명·노이즈), 상자·테이블의 다양성, 실제 관절 응답과 지연의 차이 등.'],
    ['공간 소프트맥스가 평균 풀링보다 집기에 유리한 이유는?', '평균 풀링은 위치 정보를 지우지만 공간 소프트맥스는 특징의 화면 좌표를 숫자로 넘긴다. 집기는 "어디에"가 핵심이라 적은 데이터로도 배운다.'],
    ['평가는 100/100인데 --ask-other에서는 0/20이었다. 정책은 무엇을 보고 상자를 고르나?', '색 낱말이 아니라 "오른손 앞에 정렬된 상자"를 본다. 시연에서는 그 둘이 늘 같았으므로 더 쉬운 단서를 배웠다(shortcut learning). 단서를 어긋나게 만든 시험을 해야 드러난다.'],
    ['공급 테이블만 학습한 정책은 검증 오차가 낮았는데 작업대에서 0/20이었다. 왜?', '검증 데이터도 공급 테이블에서만 왔다. 검증 오차는 본 적 있는 종류의 장면에서의 실력일 뿐이고, 처음 보는 장면(색·배경·방향)에서는 닫힌 루프로 평가해야 안다.'],
  ], '답은 발표자 노트에 있습니다.');
};
