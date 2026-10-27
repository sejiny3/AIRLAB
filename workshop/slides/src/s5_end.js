// 마무리 + 부록
const L = require('./lib');
const { C, MONO, text, box, circleIcon, pill, card, callout, code, bullets, arrow, img, table, content } = L;
const TAG = '마무리';

module.exports = function build() {
  let s;
  L.section('마무리', '2일 정리', '2일 동안 만든 것', [
    '시뮬레이터 ↔ ROS 브리지',
    'SLAM 지도와 자율주행',
    '카메라로 찾아서 집고 놓는 양팔',
    '자연어 한 문장으로 전체를 시키는 LLM 계획기',
    '(심화) 카메라를 보고 집는 법을 배운 VLA 정책',
  ], '처음의 전체 구조 그림으로 돌아갑니다.');

  s = content('아래에서 위로, 다시 한 번', TAG, '처음 보여 준 구조를 다시 봅니다. 브리지가 실제 로봇 드라이버와 같은 토픽을 내도록 만들었기 때문에, 실제 로봇에서는 맨 아래 층만 바뀌고 위 층은 거의 그대로 쓸 수 있다는 점을 강조하세요.');
  [['모듈 4', 'Claude 도구 호출 계획기 + 두 단계 검증 + 웹 대시보드', C.text1], ['모듈 3', 'MoveIt 2 양팔 + ArUco 정밀 접근 + Pick & Place', C.accent1], ['모듈 2', 'SLAM 지도 + AMCL + Nav2 자율주행, 지도에 없는 장애물 회피', C.accent2], ['모듈 1', '직접 만든 MuJoCo ↔ ROS 2 브리지: 시간, 센서, 명령', C.accent3]].forEach(([m, t, f], i) => {
    const y = 1.5 + i * 1.15;
    pill(s, m, 0.6, y + 0.27, 1.5, f);
    box(s, 2.4, y, 10.3, 0.9, C.background2);
    text(s, t, { x: 2.65, y, w: 9.9, h: 0.9, fontSize: 18, bold: true, valign: 'middle' });
  });
  callout(s, 'why', 0.6, 6.15 - 0.2, 12.1, 0.95, '위층은 아래층을 믿고 만들었다 → 실제 로봇에서는 맨 아래(브리지)만 실제 드라이버로 바뀐다', '핵심');

  s = content('실제 로봇으로 가려면 무엇이 다를까', TAG, '토론 주제로 써도 좋습니다. 시뮬레이터가 대신해 주던 것(정답 위치, 완벽한 카메라, 지연 없음, 안전)을 실제로는 우리가 챙겨야 합니다.');
  [['FaLink', '브리지 → 실제 드라이버', '같은 토픽(/cmd_vel, /scan, /joint_states)을 내는 실제 모터·센서 드라이버로 바꾼다. 위층 코드는 거의 그대로.'], ['FaWifi', '노이즈와 지연', '센서는 더 흔들리고, 명령은 늦게 도착한다. 바닥 마찰도 장소마다 다르다. 파라미터를 다시 맞춰야 한다.'], ['FaShieldAlt', '안전', '비상 정지 버튼, 속도 제한, 사람 감지. 시뮬레이터에서는 부딪혀도 괜찮았지만 실제는 아니다.'], ['FaCamera', '보정(캘리브레이션)', '카메라 내부 값, 카메라 장착 위치, 실제 마커 크기를 재서 맞춘다. 틀리면 집는 위치가 cm 단위로 틀린다.']].forEach(([ic, h, b], i) => {
    const x = 0.6 + (i % 2) * 6.15, y = 1.5 + Math.floor(i / 2) * 2.65;
    card(s, { x, y, w: 5.95, h: 2.45, head: h, body: b, iconName: ic, accent: [C.accent3, C.accent1, C.accent6, C.accent2][i], bodySize: 15 });
  });

  s = content('더 공부하고 싶다면', TAG, '공식 문서 위주로 골랐습니다. 이 강습회의 모든 코드는 저장소에 있으니, 과제를 하며 직접 고쳐 보는 것이 가장 좋은 공부입니다.');
  table(s, [['주제', '자료', '먼저 볼 곳'], ['ROS 2', 'docs.ros.org/en/humble', 'Tutorials → Beginner: CLI tools, Client libraries'], ['MuJoCo', 'mujoco.readthedocs.io', 'Overview, XML Reference, Python bindings'], ['Nav2', 'docs.nav2.org', 'Getting Started, Tuning Guide, Simple Commander'], ['MoveIt 2', 'moveit.picknik.ai/humble', 'Tutorials → Your First C++/Python MoveIt Project'], ['Claude 도구 호출', 'docs.claude.com', 'Tool use overview, Prompt caching'], ['이 강습회', '저장소의 workshop/ 폴더', '00_install ~ 04 교재, troubleshooting, 과제']], 0.6, 1.5, 12.1, [2.4, 4.0, 5.7], 15);

  s = content('수료와 과제 제출', TAG, '수료 기준과 제출 방법을 안내합니다. 설문(모듈별 난이도, 설치 가이드의 막힌 지점, 시간 배분)도 이때 받습니다.');
  card(s, { x: 0.6, y: 1.5, w: 3.85, h: 2.2, head: '체크포인트', iconName: 'FaCheckCircle', accent: C.accent2, body: '모듈 1~4의 ✅ 모두 통과' });
  card(s, { x: 4.73, y: 1.5, w: 3.85, h: 2.2, head: '최종 미션', iconName: 'FaFlagCheckered', accent: C.accent1, body: '자연어 한 문장으로 상자 옮기기 성공' });
  card(s, { x: 8.85, y: 1.5, w: 3.85, h: 2.2, head: '과제 1개 이상', iconName: 'FaBook', accent: C.accent3, body: '기본 또는 도전 과제. 스크린샷 + 짧은 설명' });
  box(s, 0.6, 4.0, 12.1, 2.7, C.background2);
  text(s, '끝나고 꼭 할 것', { x: 0.9, y: 4.15, w: 11.5, h: 0.5, fontSize: 18, bold: true });
  bullets(s, ['과제와 설문 제출', 'API 키를 받았다면: Console에서 키 삭제 (강사가 일괄 삭제)', '노트북을 정리하려면: 설치 가이드 부록 B (wsl --unregister Ubuntu-22.04, 파일이 모두 지워지니 먼저 백업)'], 0.9, 4.7, 11.5, 1.9, 16);

  s = content('부록: 자주 나는 오류 TOP 8', '부록', '강습회에서 실제로 자주 나오는 순서로 골랐습니다. 자세한 내용은 troubleshooting.md에 있습니다.');
  table(s, [['증상', '원인', '해결'], ['ros2: command not found', '설치 전에 연 터미널', '새 터미널 또는 source ~/.bashrc'], ['Lookup would require extrapolation', 'use_sim_time 빠짐', '--ros-args -p use_sim_time:=true'], ['No module named \'rclpy._rclpy_pybind11\'', 'conda/venv가 켜져 있음', 'conda deactivate'], ['대시보드 "ROS 연결 끊김"', 'dashboard:=true 빠짐 / rosbridge 죽음', 'launch 인자 확인, 로그에서 rosbridge'], ['로봇이 엉뚱한 곳으로 주행', 'AMCL 위치가 틀림', 'RViz 2D Pose Estimate 또는 초기화'], ['simulation is slower 경고', '노트북이 느림', '다른 프로그램 끄기, 전원 연결, use_viewer:=false'], ['busy; ignored command', '이전 명령이 실행 중', '기다리거나 /task_cancel'], ['APIConnectionError (Brotli)', 'Ubuntu 기본 Brotli 1.0.9', 'pip3 install --user --upgrade Brotli']], 0.6, 1.5, 12.1, [4.2, 3.6, 4.3], 14);

  s = content('부록: 실행 명령 모음', '부록', '한 장에 모은 실행 명령입니다. 인쇄해서 옆에 두면 좋습니다.');
  code(s, '# 모듈 1: 시뮬레이터 + RViz\n$ ros2 launch unbolt_mujoco_bridge sim.launch.py\n$ ros2 run teleop_twist_keyboard teleop_twist_keyboard\n\n# 모듈 2: 지도 만들기 / 주행\n$ ros2 launch unbolt_navigation slam.launch.py\n$ ros2 run nav2_map_server map_saver_cli -f ~/maps/my_room --ros-args -p use_sim_time:=true\n$ ros2 launch unbolt_navigation navigation.launch.py map:=$HOME/maps/my_room.yaml\n\n# 모듈 3: MoveIt / 전체 + Pick & Place\n$ ros2 launch unbolt_moveit_config moveit.launch.py\n$ ros2 launch unbolt_manipulation bringup.launch.py\n$ ros2 run unbolt_manipulation pick_place_demo --ros-args -p use_sim_time:=true\n\n# 모듈 4: LLM + 대시보드 (키가 없으면 llm:=scripted 추가)\n$ ros2 launch unbolt_manipulation bringup.launch.py planner:=true dashboard:=true\n$ ros2 run unbolt_manipulation ask "빨간 상자를 작업대로 옮겨줘"\n$ ros2 run unbolt_dashboard dashboard_launcher   # 브라우저의 "연결"로 켜고 끄기\n\n# 심화 모듈 5: VLA (녹화 13분 → 학습 35분 → 평가 → 집기만 정책으로)\n$ ros2 run unbolt_vla record --episodes 600 && ros2 run unbolt_vla train && ros2 run unbolt_vla evaluate\n$ ros2 launch unbolt_manipulation bringup.launch.py planner:=true dashboard:=true pick:=vla', 0.6, 1.5, 12.1, 5.2, 12);

  s = content('부록: 확인·정리 명령 모음', '부록', '문제가 생겼을 때 상태를 확인하고 정리하는 명령입니다.');
  code(s, '# 무엇이 돌고 있나\n$ ros2 node list\n$ ros2 topic list\n$ ros2 topic hz /scan\n$ ros2 topic echo /task_status --field data\n\n# 멈추기 / 되돌리기 / 모두 끄기\n$ ros2 topic pub --once /task_cancel std_msgs/msg/Empty        # 작업 취소\n$ ros2 topic pub --once /task_reset std_msgs/msg/Empty         # 초기화\n$ ros2 topic pub --once /dashboard/shutdown std_msgs/msg/Empty # 시스템 종료 (대시보드 버튼과 같음)\n\n# 그래도 남은 프로세스가 있으면\n$ pkill -INT -f ros2; sleep 3; ros2 daemon stop\n# 그래도 이상하면 PowerShell에서: wsl --shutdown\n\n# 환경 점검\n$ bash ~/unbolt/workshop/setup/check_env.sh', 0.6, 1.5, 12.1, 5.2, 13);

  L.titleSlide('마무리', '질문과 토론', '이틀 동안 수고 많으셨습니다', 'FaComments', '질의응답. 실제 로봇으로 옮길 때 무엇이 달라지는지(센서 노이즈, 지연, 안전) 토론으로 마무리하면 좋습니다.');
};
