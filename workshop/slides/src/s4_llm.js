// 모듈 4: LLM 작업 계획
const L = require('./lib');
const { C, HEX, MONO, text, box, circleIcon, pill, card, callout, code, bullets, arrow, img, marker, table, step, flow, lab, quiz, summary, content } = L;
const TAG = '모듈 4 · LLM';

module.exports = function build() {
  let s;
  L.section('모듈 4: LLM 작업 계획', '모듈 4 · 2일차 12:30–16:30', 'LLM 작업 계획\n자연어에서 로봇 제어까지', [
    'LLM이 로봇을 직접 움직이지 않고 "도구를 고르는" 구조를 안다',
    '도구 정의(스키마)와 작업 관리자(월드 검증)로 실수를 막는다',
    '명령 → 계획 → 실행 → 결과 → 다음 계획의 루프를 따라간다',
    '웹 대시보드로 명령하고, 최종 미션을 완수한다',
  ], '마지막 모듈입니다. API 키가 없는 학생은 llm:=scripted로 따라옵니다. 실습 2(실제 Claude)만 키가 필요합니다.');

  s = content('오늘 오후에 할 일', TAG, '4시간 흐름입니다. 대역(scripted)으로 로봇 쪽을 먼저 확인한 뒤 실제 Claude로 넘어갑니다. 15:40부터 최종 미션입니다.');
  [['12:30', '개념', 'LLM, 도구 호출, 두 단계 검증'], ['13:00', '실습 1~2', '대역으로 확인 → 실제 Claude로 계획'], ['13:40', '실습 3~4', '코드 읽기, 실패 복구·취소·초기화'], ['14:30', '실습 5~6', '웹 대시보드, 프롬프트 고치기'], ['15:40', '최종 미션', '한 문장으로 상자 옮기기 + 추가 미션'], ['16:20', '마무리', '정리, 설문']].forEach(([t, h, b], i) => {
    const y = 1.5 + i * 0.88;
    pill(s, t, 0.6, y + 0.17, 1.2, i % 2 ? C.accent1 : C.text1);
    box(s, 2.1, y, 10.6, 0.72, C.background2);
    text(s, h, { x: 2.35, y, w: 2.2, h: 0.72, fontSize: 17, bold: true, valign: 'middle' });
    text(s, b, { x: 4.6, y, w: 8.0, h: 0.72, fontSize: 16, color: C.text2, valign: 'middle' });
  });

  s = content('LLM은 무엇을 잘하고 무엇을 못하나', TAG, 'LLM은 아주 많은 글로 "다음에 올 말"을 예측하도록 학습한 모델입니다. 그래서 말을 이해하고, 계획을 세우고, 설명하는 데 뛰어납니다. 하지만 로봇의 몸이나 방의 좌표를 모르고, 실시간 제어(ms 단위)에는 느립니다. 그래서 우리가 할 수 있는 일(도구)을 알려 주고 고르게 합니다.');
  card(s, { x: 0.6, y: 1.5, w: 5.95, h: 3.0, head: '잘하는 것', iconName: 'FaCheckCircle', accent: C.accent2, body: '• 애매한 말 이해하기 ("원래 자리" = 공급 테이블)\n• 순서 계획하기 (가서 → 집고 → 옮겨서 → 놓기)\n• 실패 메시지를 읽고 다음 행동 정하기\n• 사람에게 결과를 설명하기', bodySize: 15 });
  card(s, { x: 6.75, y: 1.5, w: 5.95, h: 3.0, head: '못하는 것 (그래서 도구가 필요)', iconName: 'FaExclamationTriangle', accent: C.accent6, body: '• 로봇 몸·방 좌표를 모른다\n• 느리다 (응답에 몇 초)\n• 가끔 틀린다 (그럴듯한 실수)\n• 직접 모터를 돌릴 수 없다', bodySize: 15 });
  callout(s, 'analogy', 0.6, 4.75, 12.1, 1.95, '똑똑한 신입 사장님: 말귀는 정말 잘 알아듣고 계획도 잘 세우지만, 공장 기계를 직접 만지게 하면 위험하다. 그래서 "버튼 메뉴(도구)"만 주고, 버튼을 누르면 숙련된 기술자(스킬)가 일한다.');

  s = content('도구 호출(tool use)이란', TAG, 'Claude는 글만 씁니다. 다만 "이 도구를 이 값으로 써 줘"라는 주문서(tool_use 블록)를 쓸 수 있습니다. 우리 코드가 그 주문서대로 로봇을 움직이고, 결과(tool_result)를 다시 Claude에게 보여 줍니다. Claude는 결과를 보고 다음 주문서를 쓰거나 사람에게 답합니다.');
  // lane headers centred on the lifelines at x = 2.6, 5.8, 10.2
  const lane = [['사람', 2.6, 2.4, C.accent5, C.text1], ['Claude', 5.8, 2.4, C.accent1, C.background1], ['우리 코드 + 로봇', 10.2, 3.2, C.accent3, C.background1]];
  lane.forEach(([t, cx, w, f, col]) => { box(s, cx - w / 2, 1.45, w, 0.6, f); text(s, t, { x: cx - w / 2, y: 1.45, w, h: 0.6, fontSize: 15, bold: true, color: col, align: 'center', valign: 'middle' }); });
  const msgs = [[2.6, 5.8, '"빨간 상자를 작업대로 옮겨줘"', 2.35], [5.8, 10.2, 'tool_use: navigate_to(supply_1)', 3.05], [10.2, 5.8, 'tool_result: arrived at supply_1', 3.75], [5.8, 10.2, 'tool_use: pick_object(red_box)', 4.45], [10.2, 5.8, 'tool_result: picked red_box', 5.15], [5.8, 2.6, '"작업대로 옮겼습니다"', 5.85]];
  msgs.forEach(([x1, x2, t, y]) => { arrow(s, x1, y + 0.35, x2, y + 0.35, x1 < x2 ? HEX.accent3 : HEX.accent1); text(s, t, { x: Math.min(x1, x2), y: y - 0.05, w: Math.abs(x2 - x1), h: 0.38, fontSize: 13, bold: true, fontFace: MONO, align: 'center' }); });
  [2.6, 5.8, 10.2].forEach((x) => s.addShape(L.S.LINE, { x, y: 2.05, w: 0, h: 4.4, line: { color: HEX.accent5, width: 1, dashType: 'dash' } }));
  text(s, '… navigate_to(work_table), place_object(work_table) 도 같은 방식', { x: 6.0, y: 6.45, w: 6.7, h: 0.35, fontSize: 12, color: C.text2, align: 'right' });

  s = content('역할 분담: LLM은 "무엇을", 스킬은 "어떻게"', TAG, 'LLM은 좌표, 관절각, 팔 선택을 모릅니다. 장소와 물체 이름만 고르고 구체적인 값은 작업 관리자와 스킬이 정합니다. 그래서 LLM이 엉뚱한 숫자로 로봇을 위험하게 움직일 수 없습니다.');
  [['LLM (Claude)', '무엇을, 어떤 순서로', '느리다 (초 단위) · 가끔 틀린다 · 말을 잘 안다', C.accent1], ['작업 관리자 (TaskExecutor)', '지금 할 수 있는 일인가', '사전 조건 검사 → 안 되면 이유를 LLM에 돌려줌', C.accent3], ['로봇 스킬 (RobotSkills)', '어떻게', '빠르다 (ms) · 모듈 1~3에서 검증한 코드', C.accent2]].forEach(([h, m, b, f], i) => {
    const y = 1.5 + i * 1.75;
    box(s, 0.6, y, 7.2, 1.4, f);
    text(s, h, { x: 0.85, y: y + 0.1, w: 6.8, h: 0.6, fontSize: 19, bold: true, color: C.background1 });
    text(s, m, { x: 0.85, y: y + 0.7, w: 6.8, h: 0.55, fontSize: 16, color: C.background1 });
    text(s, b, { x: 8.1, y, w: 4.6, h: 1.4, fontSize: 15, color: C.text2, valign: 'middle' });
    if (i < 2) arrow(s, 4.2, y + 1.4, 4.2, y + 1.75);
  });

  s = content('도구 하나는 이렇게 정의한다', TAG, 'task_planner_core.py의 TOOLS 중 navigate_to입니다. description은 Claude가 읽는 설명서라서 정확하게 써야 합니다. enum은 고를 수 있는 값을 딱 정해 줍니다. strict: True면 Claude가 이 형식을 벗어난 주문서를 아예 만들 수 없습니다.');
  code(s, '{\n  "name": "navigate_to",\n  "description": "Drive the base to a known location\n                  (arms are tucked first). Stands about\n                  0.65 m in front of a table, facing it.",\n  "strict": true,\n  "input_schema": {\n    "type": "object",\n    "properties": {\n      "location": {"type": "string",\n        "enum": ["supply_1", "supply_2", "supply_3",\n                 "work_table", "home"]}\n    },\n    "required": ["location"],\n    "additionalProperties": false\n  }\n}', 0.6, 1.5, 7.0, 5.2, 13);
  table(s, [['부분', '뜻'], ['name', '도구 이름 (Claude가 부를 때 쓰는 이름)'], ['description', 'Claude가 읽는 설명서. 언제 쓰는지, 무엇을 하는지'], ['enum', '고를 수 있는 값 목록. "kitchen"은 못 고른다'], ['required', '꼭 넣어야 하는 값'], ['additionalProperties: false', '정해지지 않은 값은 넣을 수 없음'], ['strict: true', '이 형식을 반드시 지켜서 생성']], 7.9, 1.5, 4.8, [2.0, 2.8], 13);

  s = content('우리 로봇의 도구 일곱 개', TAG, '도구는 일부러 적고 단순하게 만들었습니다. 각 도구 안에서 스킬 여러 개가 이어집니다(예: pick_object = 마커 찾기 → 정밀 접근 → 집기 → 후진). check_table과 wait는 조건·순서가 있는 명령을 위해 넣은 도구입니다(실습 4-B).');
  table(s, [['도구', '입력', '안에서 하는 일'], ['get_world_state', '없음', '로봇 위치, 들고 있는 것, 상자마다 테이블·자리, 빈자리 (기억, 빠름)'], ['navigate_to', 'location: supply_1~3 / work_table / home', '팔 tuck → Nav2로 테이블 앞 0.65 m'], ['pick_object', 'object: red_box / green_box / blue_box', '마커 찾기 → 정밀 접근 → 집기 → 들기 → 후진'], ['place_object', 'location: 테이블, spot: left / middle / right / auto', '그 자리 마커로 정밀 접근 → 내려놓기 → 후진 (자리가 차 있으면 거부)'], ['check_table', 'location: 지금 선 테이블', '카메라로 보고 자리마다 무엇이 있는지 → 기억을 고친다'], ['set_arm_posture', 'posture: tuck / home', '두 팔 자세 바꾸기 (물체를 들고 있으면 거부)'], ['wait', 'seconds (1~120)', '그 자리에서 기다리기']], 0.6, 1.5, 12.1, [2.2, 4.0, 5.9], 13);
  callout(s, 'why', 0.6, 5.55, 12.1, 1.15, '좌표 같은 숫자 대신 이름만 받는다. Claude가 "x=3.7" 같은 엉뚱한 숫자를 만들 수 없고, 이름 → 좌표 변환은 우리가 검증한 표(LOCATIONS)에서 한다.');

  s = content('시스템 프롬프트: Claude에게 주는 업무 지침', TAG, 'SYSTEM_PROMPT 발췌입니다(실제는 영어). 로봇의 규칙, 실패했을 때 행동, 모르는 요청 처리, 한국어 별칭, 답하는 방식을 적습니다. 실습 6에서 여기에 규칙을 하나 추가합니다.');
  code(s, 'You are the task planner of UNBOLT, a mobile robot\nwith two arms ... call the tools, one at a time ...\n\n- It can only pick an object or place it while standing\n  at the table where that happens.\n- If a tool fails, read its message. Retry once when it\n  could work again; otherwise stop and explain.\n- If the command asks for something the robot cannot do,\n  do not improvise: say what is possible instead.\n\n"작업대" means work_table; "1번/2번/3번 공급 테이블"\nmean supply_1/2/3; "원래 자리" of a box is its start spot.', 0.6, 1.5, 7.0, 5.2, 13);
  [['로봇의 규칙', '테이블 앞에 서 있어야 집고 놓을 수 있다'], ['실패하면', '메시지를 읽고 한 번 재시도, 아니면 멈추고 설명'], ['모르는 요청', '지어내지 말고 가능한 일을 안내'], ['한국어 별칭', '"작업대", "원래 자리"가 무엇인지'], ['답하는 방식', '사용자 언어로 한두 문장']].forEach(([h, b], i) => {
    const y = 1.5 + i * 1.05;
    box(s, 7.9, y, 4.8, 0.9, C.background2);
    text(s, h, { x: 8.1, y: y + 0.05, w: 4.5, h: 0.4, fontSize: 15, bold: true });
    text(s, b, { x: 8.1, y: y + 0.45, w: 4.5, h: 0.4, fontSize: 13, color: C.text2 });
  });

  s = content('도구 호출 루프 (코드)', TAG, 'TaskPlanner.run을 줄인 것입니다. 실제 코드에는 취소 확인, 거절(refusal) 처리, 토큰 집계가 더 있습니다. 로봇은 두 곳에 동시에 갈 수 없으니 한 번에 하나씩(disable_parallel_tool_use) 부르게 합니다.');
  code(s, 'messages = [{"role": "user", "content": command}]\nfor turn in range(MAX_TURNS):                  # 최대 20번\n    response = client.beta.messages.create(\n        model="claude-opus-5-5", system=SYSTEM_PROMPT, tools=TOOLS,\n        tool_choice={"type": "auto", "disable_parallel_tool_use": True},\n        messages=messages, ...)\n    messages.append({"role": "assistant", "content": response.content})\n    if response.stop_reason != "tool_use":\n        return 최종_답변                            # 계획 끝\n    ok, result = executor.run(call.name, call.input)   # 로봇이 실행 (수십 초)\n    messages.append({"role": "user", "content": [\n        tool_result(result, is_error=not ok)]})    # 결과를 보여 주기', 0.6, 1.5, 8.2, 5.2, 13);
  callout(s, 'why', 9.1, 1.5, 3.6, 2.5, '한 번에 하나씩: 앞 결과(성공/실패, 지금 위치)를 보고 다음을 정해야 한다.');
  callout(s, 'tip', 9.1, 4.2, 3.6, 2.5, 'is_error: 실패를 결과로 돌려주면 Claude가 읽고 계획을 고친다.', '실패도 정보');

  s = content('한 명령이 실제로 흘러가는 모습', TAG, '"빨간 상자를 작업대로 옮겨줘"를 대역(scripted)으로 실행했을 때의 실제 기록입니다(10 × 8.5 m 방, 총 약 80초). 실제 Claude도 거의 같은 순서를 고릅니다. 자리를 말하지 않았으니 auto로 놓고, 작업대의 첫 빈자리(왼쪽)에 놓입니다. 각 단계 시간 중 대부분은 로봇이 움직이는 시간이고, Claude가 생각하는 시간은 몇 초입니다.');
  [['명령', '"빨간 상자를 작업대로 옮겨줘"', '', C.accent5, C.text1], ['get_world_state()', '로봇 원위치, 빨간 상자는 supply_1 오른쪽 자리', '0 s', C.background2, C.text1], ['navigate_to(supply_1)', 'arrived at supply_1', '13 s', C.background2, C.text1], ['pick_object(red_box)', 'picked red_box from the right spot of supply_1', '24 s', C.background2, C.text1], ['navigate_to(work_table)', 'arrived at work_table', '20 s', C.background2, C.text1], ['place_object(work_table, auto)', 'placed red_box on the left spot of work_table', '23 s', C.background2, C.text1], ['최종 답', '"빨간 상자를 작업대로 옮겼습니다."', '80 s', C.accent1, C.background1]].forEach(([h, b, t, f, col], i) => {
    const y = 1.45 + i * 0.72;
    box(s, 0.6, y, 12.1, 0.62, f);
    text(s, h, { x: 0.85, y, w: 4.6, h: 0.62, fontSize: 14, bold: true, fontFace: MONO, color: col, valign: 'middle' });
    text(s, b, { x: 5.5, y, w: 6.0, h: 0.62, fontSize: 14, color: col, valign: 'middle' });
    text(s, t, { x: 11.5, y, w: 1.0, h: 0.62, fontSize: 14, bold: true, color: col, align: 'right', valign: 'middle' });
  });
  text(s, '시간 = 그 단계에서 로봇이 움직인 시간 (마지막 줄은 전체)', { x: 0.6, y: 6.5, w: 12.1, h: 0.3, fontSize: 11, color: C.text2 });

  s = content('두 단계 검증: 형식과 상황', TAG, '포스터의 "schema vs world validation"입니다. 스키마는 생성 자체를 제약하고, 월드 검증은 실행 직전에 상태를 봅니다. 다음 장에서 월드 검증 코드를 봅니다.');
  [['스키마 검증 (형식)', 'TOOLS (strict: True, enum)', '장소 이름이 supply_1~3 / work_table / home 중 하나인가', 'navigate_to("kitchen") → 애초에 만들 수 없음', C.background2, C.text1], ['월드 검증 (상황)', 'TaskExecutor._tool_*', '지금 그 일을 할 수 있는 상태인가', '들고 있는 게 없는데 place_object → "not holding anything"', C.text1, C.background1]].forEach(([h, where, what, ex, f, col], i) => {
    const x = 0.6 + i * 6.15;
    box(s, x, 1.5, 5.95, 5.2, f);
    text(s, h, { x: x + 0.35, y: 1.7, w: 5.3, h: 0.6, fontSize: 22, bold: true, color: col });
    text(s, where, { x: x + 0.35, y: 2.4, w: 5.3, h: 0.5, fontSize: 15, fontFace: MONO, color: i ? C.accent4 : C.accent3 });
    text(s, what, { x: x + 0.35, y: 3.1, w: 5.3, h: 1.2, fontSize: 17, color: col });
    text(s, '예', { x: x + 0.35, y: 4.45, w: 5.3, h: 0.4, fontSize: 15, bold: true, color: col });
    text(s, ex, { x: x + 0.35, y: 4.85, w: 5.3, h: 1.6, fontSize: 15, color: col });
  });

  s = content('월드 검증은 이렇게 생겼다', TAG, '_tool_pick_object의 앞부분입니다. 조건이 맞지 않으면 로봇을 움직이지 않고 이유를 문장으로 돌려줍니다. Claude는 그 문장을 읽고 "먼저 1번 공급 테이블로 가야겠다"처럼 계획을 고칩니다. 어느 팔로 집을지도 여기서(마커가 보이는 쪽) 정합니다. LLM이 정하지 않습니다.');
  code(s, 'def _tool_pick_object(self, object):\n    if self.held is not None:                       # 이미 들고 있으면\n        return False, {"error": f"already holding {self.held}; place it first"}\n    location, spot = self.where[object]             # 기억: (테이블, 자리)\n    if location != self.robot_location:             # 다른 테이블이면\n        return False, {"error": f"{object} is at {location}, ... navigate there first"}\n    seen = self.s.marker_in_base(marker, samples=3, use_memory=True)\n    if seen is None:                                # 마커가 안 보이면\n        return False, {"error": f"{object} (marker {marker}) is not visible"}\n    arm = "left" if seen[0][1] > 0 else "right"     # 팔은 여기서 정한다\n    ...  # 정밀 접근 → 집기 → 후진', 0.6, 1.5, 12.1, 3.6, 13);
  callout(s, 'ok', 0.6, 5.35, 6.0, 1.35, '조건이 맞을 때만 로봇이 움직인다', '안전장치');
  callout(s, 'why', 6.75, 5.35, 5.95, 1.35, '오류를 문장으로 돌려주면 Claude가 읽고 스스로 고친다');

  s = content('대화형 동작 세 가지', TAG, '포스터의 clarification, interrupt, failure recovery 세 가지입니다. 팔 동작을 끝까지 하는 이유: 중간에 멈추면 팔이 테이블 위 애매한 자세로 남습니다.');
  [['FaQuestionCircle', '되묻기 (clarification)', '모르는 물건·장소면 즉흥으로 하지 않고 가능한 일을 안내. 실습 6에서 "목적지가 없으면 질문" 규칙 추가', C.accent3], ['FaStopCircle', '중단 (interrupt)', '/task_cancel → 주행·정밀 접근은 즉시 정지, 진행 중인 팔 동작은 끝내고 다음 단계를 시작하지 않음', C.accent6], ['FaUndo', '실패 복구 (recovery)', '실패 메시지를 읽고 될 것 같으면 한 번 재시도, 아니면 멈추고 현재 상태(상자를 든 채 등)를 보고', C.accent2]].forEach(([ic, h, b, a], i) => {
    const y = 1.5 + i * 1.75;
    circleIcon(s, ic, 0.6, y + 0.1, 0.9, a);
    text(s, h, { x: 1.8, y, w: 10.9, h: 0.55, fontSize: 20, bold: true });
    text(s, b, { x: 1.8, y: y + 0.6, w: 10.9, h: 0.9, fontSize: 16, color: C.text2 });
  });

  s = content('실습 1. 대역(scripted)으로 파이프라인 확인', TAG, 'ScriptedLLM은 명령의 키워드로 정해진 도구 순서를 재생하는 시험용 대역입니다(계획은 하지 않음). API 비용 없이 로봇 쪽 전체가 동작하는지 먼저 확인합니다. 체크포인트 4-1.');
  lab(s, {
    cmd: '# 터미널 1\n$ ros2 launch unbolt_manipulation bringup.launch.py \\\n    planner:=true llm:=scripted\n\n# 터미널 2\n$ ros2 run unbolt_manipulation ask "빨간 상자를 작업대로 옮겨줘"\n>> 빨간 상자를 작업대로 옮겨줘\n  -> get_world_state({})\n  -> navigate_to({"location": "supply_1"})\n     OK (13 s) arrived at supply_1\n  -> pick_object({"object": "red_box"})\n     OK (24 s) picked red_box from the right spot of supply_1 ...\n  ...\n== done in 80 s: 빨간 상자를 작업대로 옮겼습니다. (scripted)',
    cmdH: 5.2, cmdSize: 12,
    ok: '"done in … s" 로 끝나고 MuJoCo에서 상자가 작업대 위에 있다.\n\n✅ 체크포인트 4-1',
    fail: 'ask가 기다리기만 하면 planner:=true를 빠뜨렸다. ros2 node list에 /task_planner가 있는지',
  });

  s = content('작업 이벤트: /task_status', TAG, '플래너는 모든 일을 JSON 이벤트로 /task_status에 냅니다. ask와 대시보드는 이것을 받아 화면을 그립니다. 세 번째 터미널에서 ros2 topic echo /task_status --field data로 원본을 직접 보게 하세요.');
  table(s, [['type', '언제', '주요 내용'], ['command', '명령을 받았을 때', 'text'], ['thinking', 'Claude에게 묻는 중', 'turn (몇 번째)'], ['tool_call', '도구를 부를 때', 'name, input'], ['tool_result', '도구가 끝났을 때', 'ok, result, seconds'], ['thought / reply', 'Claude가 글을 썼을 때', 'text'], ['final', '명령이 끝났을 때', 'ok, text, seconds, usage (토큰)'], ['world', '상태가 바뀌었을 때', 'robot_location, holding, objects, busy'], ['reset_requested / reset', '초기화', 'ok, text']], 0.6, 1.5, 8.0, [2.6, 2.4, 3.0], 14);
  code(s, '$ ros2 topic echo /task_status \\\n    --field data\n\n{"type": "tool_call",\n "name": "navigate_to",\n "input": {"location":\n           "supply_1"}}', 8.9, 1.5, 3.8, 3.3, 12);
  callout(s, 'why', 8.9, 5.0, 3.8, 1.7, 'JSON으로 내면 터미널, 대시보드, 로그 저장 등 누구든 같은 정보를 쓸 수 있다.');

  s = content('실습 2. 실제 Claude로 계획', TAG, '같은 명령도 실행할 때마다 계획이 조금 다를 수 있습니다(예: get_world_state를 먼저 부르는지). 결과가 같으면 정상입니다. 체크포인트 4-2: 모르는 물건(노란 공)은 도구를 부르지 않고 안내만.');
  code(s, '$ ros2 launch unbolt_manipulation bringup.launch.py planner:=true\n\n$ ros2 run unbolt_manipulation ask "빨간 상자를 작업대로 옮겨줘"\n$ ros2 run unbolt_manipulation ask "노란 공 좀 가져다 줄래?"\n$ ros2 run unbolt_manipulation ask "이제 빨간 상자를 원래 자리에 다시 갖다 놔"\n$ ros2 run unbolt_manipulation ask "작업대 앞에 갔다가 처음 위치로 돌아와"', 0.6, 1.5, 12.1, 2.3, 13);
  table(s, [['명령', 'Claude가 고른 도구 순서', '결과', '토큰 / 비용'], ['빨간 상자를 작업대로', '', '', ''], ['노란 공', '', '', ''], ['원래 자리에', '', '', ''], ['작업대 갔다가 돌아와', '', '', '']], 0.6, 4.05, 8.6, [2.6, 3.0, 1.4, 1.6], 14);
  callout(s, 'ok', 9.5, 4.05, 3.2, 2.65, '노란 공은 도구 없이 "할 수 없어요 + 가능한 일" 안내 ✅ 4-2');

  s = content('비용은 얼마나 드나', TAG, '토큰은 모델이 글을 읽고 쓰는 조각 단위입니다. Claude에 보내는 글(입력)과 받는 글(출력)에 따라 요금이 붙습니다. 명령 하나에 Claude를 도구 수 + 1번 정도 부르고, 매번 지금까지의 대화를 다시 보냅니다. ask가 명령마다 실제 토큰과 대략의 비용을 출력하니 표에 적게 하세요.');
  [['입력', '$4', '100만 토큰당 (보내는 글)'], ['출력', '$20', '100만 토큰당 (받는 글)'], ['명령 1회', '5~7번', 'Claude 호출 (도구 수 + 1)']].forEach(([a, b, c], i) => {
    const x = 0.6 + i * 4.1;
    box(s, x, 1.5, 3.85, 2.3, C.background2);
    text(s, a, { x: x + 0.3, y: 1.65, w: 3.3, h: 0.45, fontSize: 16, bold: true, color: C.text2 });
    text(s, b, { x: x + 0.3, y: 2.1, w: 3.3, h: 0.9, fontSize: 38, bold: true, color: C.accent1 });
    text(s, c, { x: x + 0.3, y: 3.05, w: 3.3, h: 0.6, fontSize: 14 });
  });
  code(s, '== done in 70 s: 빨간 상자를 작업대로 옮겼습니다.\n   tokens: … in / … out (about $…)      ← ask가 마지막에 출력', 0.6, 4.05, 12.1, 1.0, 13);
  callout(s, 'tip', 0.6, 5.3, 6.0, 1.4, '키가 없거나 아끼고 싶으면 llm:=scripted. 로봇 동작은 똑같다.', '아끼는 법');
  callout(s, 'warn', 6.75, 5.3, 5.95, 1.4, 'API 키는 비밀번호. 채팅방·스크린샷·GitHub에 올리지 않기.', '주의');

  s = content('실습 4. 실패 복구와 취소', TAG, '월드 검증 → 계획 수정 흐름과 취소를 직접 경험합니다. 취소 뒤에 같은 명령을 다시 보내면 Claude가 get_world_state로 현재 상태(위치를 모름 / 이미 공급 테이블 앞 등)를 확인하고 이어서 계획하는지 보세요. 체크포인트 4-3.');
  lab(s, {
    cmd: '# 1) 들고 있지 않은데 놓으라고 하기\n$ ros2 run unbolt_manipulation ask "작업대에 들고 있는 걸 내려놔"\n\n# 2) 긴 명령을 보내고, 주행이 시작되면 다른 터미널에서 취소\n$ ros2 run unbolt_manipulation ask "빨간 상자를 작업대로 옮겨줘"\n$ ros2 topic pub --once /task_cancel std_msgs/msg/Empty\n\n# 3) 같은 명령을 다시\n$ ros2 run unbolt_manipulation ask "빨간 상자를 작업대로 옮겨줘"',
    cmdH: 3.8, cmdSize: 12,
    explain: ['1) Claude가 "not holding anything" 오류를 읽고 어떻게 답하나?', '2) 로봇이 바로 멈추고 "작업을 취소했습니다"'],
    ok: '취소 후 다시 보낸 명령이 성공한다.\n\n✅ 체크포인트 4-3',
    fail: 'busy; ignored command → 이전 명령이 아직 실행 중. 끝나길 기다리거나 취소',
  });

  s = content('테이블 넷, 상자 셋, 자리 아홉: 명령이 다양해진다', TAG, '방이 10 × 8.5 m로 넓어지고 공급 테이블이 세 개가 되었습니다. 상자마다 처음 자리가 있고, 작업대에는 놓을 자리가 세 칸 있습니다. 그래서 "무엇을 어디로"뿐 아니라 어느 자리에, 어떤 순서로, 어떤 조건일 때만이 명령에 들어갈 수 있습니다. 순서를 정하고 조건을 판단하는 것은 LLM입니다. 새 도구는 자리(spot), 눈으로 확인(check_table), 기다리기(wait) 세 가지뿐입니다.');
  img(s, 'room_layout.png', 0.6, 1.45, 6.9, 3.9, '방 배치: 공급 테이블 1·2·3, 작업대, 로봇이 서는 곳(주황 화살표)');
  table(s, [['종류', '예'], ['자리 지정', '"파란 상자를 작업대 오른쪽 자리에"'], ['여러 개 · 순서', '"초록 먼저, 그다음 파랑"'], ['조건', '"작업대에 빨간 상자가 없으면 가져다 놔"'], ['확인', '"작업대에 뭐가 있는지 가서 봐"'], ['되돌리기', '"모두 원래 자리에 돌려놓고 원위치로"']], 7.8, 1.45, 4.9, [1.6, 3.3], 13);
  callout(s, 'why', 0.6, 5.55, 12.1, 1.15, '로봇 쪽 코드는 그대로 두고 표(LOCATIONS: 테이블·자리·마커, OBJECTS: 상자·처음 자리)와 도구 세 개만 늘렸다. 순서와 조건은 LLM이 계획한다.');

  s = content('실습 4-B. 조건과 순서가 있는 명령', TAG, '조건은 LLM이 판단합니다. 시스템 프롬프트의 규칙: 순서는 사람이 말한 대로, 조건은 행동 전에 상태를 보고 판단(평소에는 기억 get_world_state, "가서 봐/확인해"라고 하거나 실패 직후처럼 기억이 틀렸을 수 있으면 check_table), 조건이 거짓이면 그 부분을 건너뛰고 답에서 알린다. 체크포인트 4-3B. 명령 하나에 2~4분 걸리는 것도 있으니 차례로 보내세요.');
  lab(s, {
    cmd: '$ ros2 run unbolt_manipulation ask \\\n  "초록 상자를 먼저 작업대 왼쪽에 놓고, 그다음 파란 상자를 오른쪽에 놓아줘"\n$ ros2 run unbolt_manipulation ask "작업대에 빨간 상자가 없으면 가져다 놔"\n$ ros2 run unbolt_manipulation ask "작업대에 뭐가 있는지 가서 확인해 줘"\n$ ros2 run unbolt_manipulation ask \\\n  "작업대에 빨간 상자가 있으면 원래 자리로 돌려놓고, 없으면 그냥 원위치로 와"\n$ ros2 run unbolt_manipulation ask \\\n  "상자를 모두 원래 자리에 돌려놓고 원위치로 와"',
    cmdH: 3.8, cmdSize: 12,
    explain: ['조건을 무엇으로 판단했나? 기억(get_world_state)인가, 카메라(check_table)인가', '조건이 거짓인 쪽은 건너뛰고 답에서 알리는가'],
    ok: '조건에 맞는 쪽만 실행하고, 판단 근거를 답에 밝힌다.\n\n✅ 체크포인트 4-3B',
    fail: 'the left spot of work_table is taken → 자리가 이미 찼다. Claude가 다른 자리를 고르거나 물어보는지 보기',
  });

  s = content('강사 노트북의 실제 결과', TAG, '위 다섯 명령과 모르는 물건(노란 공)을 한 번의 실행에서 차례로 보낸 결과입니다(claude-opus-5-5, 합계 약 $0.50). 두 번째 명령의 답 "로봇 기억으로는 없었어요"처럼 판단 근거를 말하게 해 두면, 기억이 틀렸을 가능성을 사람이 알아챌 수 있습니다. 마지막 명령에서도 "빨간 상자는 기억상 이미 제자리라 옮기지 않았다(카메라로 확인하지는 않았다)"고 덧붙였습니다.');
  table(s, [['명령', 'Claude가 고른 도구 순서', '결과'], ['초록 먼저 왼쪽, 그다음 파랑 오른쪽', '상태 → 2번 → 집기 → 작업대 → 놓기(left) → 3번 → 집기 → 작업대 → 놓기(right)', '성공 195 s, $0.14'], ['빨간 상자가 없으면 가져와', '상태(기억: 없음) → 1번 → 집기 → 작업대 → 놓기(auto → 가운데)', '성공 99 s, 근거를 말함'], ['가서 확인해', '(이미 작업대 앞) → check_table', '왼쪽 초록 · 가운데 빨강 · 오른쪽 파랑, 10 s'], ['있으면 돌려놓고 없으면 원위치', '상태(있음) → 집기 → 1번 → 놓기(auto → 처음 자리)', '성공 72 s, 원위치는 건너뜀'], ['노란 공', '(도구 없음)', '할 수 있는 일 안내, 3 s'], ['모두 원래 자리로 + 원위치', '상태 → 초록·파랑만 처음 자리로 (빨강은 이미 제자리) → 원위치', '성공 208 s, 오차 1.2 cm 이내']], 0.6, 1.5, 12.1, [3.0, 6.0, 3.1], 12);
  callout(s, 'warn', 0.6, 5.75, 12.1, 0.95, '기억과 실제가 다를 수 있다: MuJoCo 창에서 상자를 끌어 떨어뜨린 뒤 "있으면 …"과 "가서 보고 있으면 …"을 비교해 보자.');

  s = content('처음부터 다시: 초기화', TAG, '대시보드의 초기화 버튼과 같은 일을 합니다. 시뮬레이터만 리셋(/mujoco_bridge/reset)하면 플래너와 AMCL이 옛 상태를 기억해서 다음 명령이 꼬입니다. 플래너가 켜져 있으면 /task_reset을 쓰세요. 대기 중 약 2초, 작업 중이면 취소까지 약 3초 걸립니다.');
  flow(s, [['진행 중인\n작업 취소', C.accent6, C.background1], ['시뮬레이터 리셋\n로봇·팔·상자 처음 위치', C.text1, C.background1], ['AMCL 원점으로\ncostmap 비우기', C.accent3, C.background1], ['플래너 상태도\n처음으로', C.accent2, C.background1]], 0.6, 1.6, 12.1, 1.4, 0.35, 15);
  code(s, '# 터미널에서\n$ ros2 topic pub --once /task_reset std_msgs/msg/Empty\n\n# 대시보드에서: 초기화 버튼 → "정말 초기화?" → 4초 안에 한 번 더', 0.6, 3.35, 7.4, 1.65, 13);
  callout(s, 'ok', 8.3, 3.35, 4.4, 1.65, '타임라인에 "✓ 초기화", 상태가 "초기화됨"');
  callout(s, 'warn', 0.6, 5.25, 12.1, 1.45, '시뮬레이터만 리셋하면 AMCL이 옛 위치를 기억해 지도 위 위치가 수십 cm 틀린다. 플래너를 켰을 때는 /task_reset(초기화 버튼).');

  s = content('웹 대시보드 둘러보기', TAG, '번호를 짚으며 설명합니다. 1 ROS 연결 상태(초록 = 연결됨), 2 플래너 상태, 3 지도(로봇·LiDAR·경로·테이블·상자), 4 명령 입력, 5 자주 쓰는 명령, 6 초기화·작업 취소, 7 작업 진행 타임라인, 8 로봇 상태, 9 헤드 카메라(아래로 스크롤), 10 시스템 종료(두 번 눌러 확인하면 launch의 모든 프로그램을 끔).');
  const r = img(s, 'dashboard_idle.png', 0.6, 1.45, 7.8, 5.3, '웹 대시보드 화면');
  const P = (u, v) => [r.x + u / 1440 * r.w, r.y + v / 1000 * r.h];
  [[1, 225, 24], [2, 332, 24], [3, 420, 450], [4, 1080, 146], [5, 1200, 245], [6, 1300, 344], [7, 1125, 470], [8, 1125, 870], [9, 420, 930], [10, 1375, 52]].forEach(([n, u, v]) => marker(s, n, ...P(u, v)));
  table(s, [['번호', '이름', '설명'], ['1', 'ROS 연결', '초록 = rosbridge 연결됨'], ['2', '플래너 상태', '대기 / 계획 중 / 완료'], ['3', '지도', '로봇, LiDAR, 경로, 상자'], ['4', '명령 입력', '자연어 한 문장'], ['5', '자주 쓰는 명령', '눌러서 바로 보내기'], ['6', '초기화 · 취소', '두 번 눌러 초기화'], ['7', '작업 진행', '단계별 결과와 시간'], ['8', '로봇 상태', '위치, 들고 있는 것, 그리퍼'], ['9', '헤드 카메라', '마커 검출 영상'], ['10', '시스템 종료', '두 번 눌러 모두 끄기']], 8.7, 1.45, 4.0, [0.7, 1.4, 1.9], 12);

  s = content('브라우저에서 켜고 끄기: 연결 버튼', TAG, '런처(dashboard_launcher)를 한 번 켜 두면 ROS가 꺼져 있어도 페이지가 뜨고, "연결"로 bringup 전체를 켭니다. 런처는 페이지를 보여 주고 bringup을 대신 실행해 주는 작은 프로그램입니다. 끌 때는 시스템 종료, 다시 켤 때는 다시 연결. 강사 시연 때 터미널을 띄울 필요가 없어 편합니다. 강사 노트북 기준으로 연결 후 13초에 rosbridge 연결, 25초에 플래너 준비가 끝났습니다.');
  img(s, 'dashboard_off.png', 0.6, 1.5, 6.9, 4.3, 'ROS가 꺼져 있을 때의 대시보드: 연결 버튼과 시작 옵션');
  code(s, '# 한 번만 켜 두기 (터미널 하나)\n$ ros2 run unbolt_dashboard dashboard_launcher', 0.6, 6.0, 6.9, 0.75, 13);
  step(s, 1, 'http://localhost:8080 열기', '"ROS가 꺼져 있습니다" 화면이 뜬다', 7.8, 1.6, 4.9, 0.6);
  step(s, 2, '모드·옵션 고르고 연결', '작업(지도·LLM), VLA 집기(모듈 5) 또는 지도 만들기, MuJoCo 창, RViz', 7.8, 2.7, 4.9, 0.6);
  step(s, 3, '25~60초 기다리기', '켜지는 동안 진행 상황과 로그가 보인다. 중간에 시작 취소 가능', 7.8, 3.8, 4.9, 0.8);
  step(s, 4, '끝: 시스템 종료 → 다시 연결', '런처 터미널의 Ctrl+C는 런처가 켠 시스템도 함께 끈다', 7.8, 5.1, 4.9, 0.8);

  s = content('실습 5. 웹 대시보드로 명령하기', TAG, 'WSL이 localhost를 Windows로 연결해 주므로 Windows의 Chrome/Edge에서 바로 열립니다. F12 → Network → WS에서 오가는 JSON을 직접 보게 하세요. 체크포인트 4-4.');
  lab(s, {
    cmd: '$ ros2 launch unbolt_manipulation bringup.launch.py \\\n    planner:=true dashboard:=true\n\n# Windows 브라우저 (Chrome / Edge)\nhttp://localhost:8080\n\n# 대시보드에서\n#  1) "빨간 상자를 작업대로 옮겨줘" 버튼\n#  2) 작업 진행이 단계별로 쌓이는 것 보기\n#  3) 초기화 → 다시',
    cmdH: 3.6,
    explain: ['F12 → Network → WS: 브라우저와 rosbridge가 주고받는 JSON', '휴대폰은 같은 와이파이에서 http://<노트북 IP>:8080 (안 될 수도 있음)'],
    ok: '상단 "ROS 연결됨", 명령을 보내면 작업 진행이 단계별로 표시된다.\n\n✅ 체크포인트 4-4',
    fail: '"ROS 연결 끊김" → dashboard:=true 확인. 로그에 rosbridge died면 conda deactivate 후 다시',
  });

  s = content('대시보드 데이터 흐름', TAG, '외부 라이브러리 없이 rosbridge 프로토콜을 직접 구현한 페이지입니다. 브라우저는 ROS를 모르고, rosbridge가 WebSocket(JSON)과 ROS 토픽을 서로 옮겨 줍니다. 모듈 1의 브리지와 같은 "통역사" 역할입니다.');
  img(s, 'step7_dashboard.jpg', 0.6, 1.5, 5.6, 5.2, '작업 중인 웹 대시보드');
  box(s, 6.6, 1.5, 6.1, 0.9, C.accent5);
  text(s, '브라우저 (index.html)  http://localhost:8080', { x: 6.6, y: 1.5, w: 6.1, h: 0.9, fontSize: 15, bold: true, align: 'center', valign: 'middle' });
  arrow(s, 9.65, 2.45, 9.65, 2.9);
  text(s, 'WebSocket :9090 · JSON', { x: 9.8, y: 2.45, w: 2.9, h: 0.45, fontSize: 12, color: C.text2 });
  box(s, 6.6, 2.95, 6.1, 0.9, C.accent3);
  text(s, 'rosbridge_websocket (통역사)', { x: 6.6, y: 2.95, w: 6.1, h: 0.9, fontSize: 16, bold: true, color: C.background1, align: 'center', valign: 'middle' });
  arrow(s, 9.65, 3.9, 9.65, 4.3);
  table(s, [['ROS 토픽', '방향'], ['/task_command, /task_cancel, /task_reset, /task_manual_drive', '→ task_planner'], ['/cmd_vel (키보드 조종)', '→ 브리지'], ['/task_status (JSON 이벤트)', '← task_planner'], ['/scan · /plan · 로봇 위치', '← 브리지·Nav2'], ['/aruco/debug_image/compressed', '← 마커 검출']], 6.6, 4.35, 6.1, [4.0, 2.1], 13);

  s = content('실습 6. 시스템 프롬프트 고치기', TAG, '--symlink-install이라 빌드 없이 bringup만 다시 시작하면 됩니다. 되묻기 규칙을 넣은 뒤 "작업대로"만 보내면 앞 질문을 기억하지 못합니다. 명령마다 대화가 새로 시작되기 때문입니다(도전 과제 1). 체크포인트 4-5.');
  text(s, 'SYSTEM_PROMPT에 규칙 한 줄 추가 (task_planner_core.py)', { x: 0.6, y: 1.5, w: 7.5, h: 0.5, fontSize: 17, bold: true });
  code(s, '- If the command does not say where to take the object,\n  do not guess: ask the person which table, in one short\n  question, and do not call any tool.', 0.6, 2.05, 7.5, 1.55, 14);
  step(s, 1, 'bringup 다시 시작', 'Ctrl + C → 다시 launch (빌드 불필요)', 0.6, 3.9, 7.5);
  step(s, 2, '"빨간 상자 좀 옮겨 줘"', '목적지가 없다 → 질문으로 답하는가?', 0.6, 5.0, 7.5);
  step(s, 3, '"작업대로"', '앞 질문을 기억할까? (안 한다 → 도전 과제 1)', 0.6, 6.1, 7.5, 0.5);
  callout(s, 'ok', 8.4, 1.5, 4.3, 2.4, 'Claude가 "어느 테이블로 옮길까요?"처럼 묻는다 ✅ 4-5');
  callout(s, 'why', 8.4, 4.1, 4.3, 2.6, '시스템 프롬프트는 Claude의 업무 지침. 코드를 안 바꾸고 행동을 바꿀 수 있다.');

  s = content('최종 미션', TAG, '대시보드 명령창에 한 문장. 강사 시연 기준 약 80초가 걸립니다. 그동안 타임라인을 짚으며 지금 Claude가 무엇을 골랐는지 설명하세요.');
  box(s, 0.6, 1.5, 12.1, 1.9, C.text1);
  circleIcon(s, 'FaFlagCheckered', 1.0, 1.9, 1.1, C.accent1);
  text(s, '"공급 테이블로 가서 빨간 상자를 집고 작업대로 옮겨"', { x: 2.4, y: 1.5, w: 10.0, h: 1.9, fontSize: 26, bold: true, color: C.background1, valign: 'middle' });
  [['위치', '작업대 자리 (마커 1·2·3)', '대시보드 지도 · MuJoCo 화면'], ['개입', '0번', '취소·재명령 없이 한 문장으로'], ['시간', '3분 이내', '타임라인 총 시간']].forEach(([a, b, c], i) => {
    const x = 0.6 + i * 4.1;
    box(s, x, 3.75, 3.85, 2.85, C.background2);
    text(s, a, { x: x + 0.3, y: 3.95, w: 3.3, h: 0.45, fontSize: 16, bold: true, color: C.text2 });
    text(s, b, { x: x + 0.3, y: 4.45, w: 3.3, h: 0.95, fontSize: 36, bold: true, color: C.accent1 });
    text(s, c, { x: x + 0.3, y: 5.5, w: 3.3, h: 0.8, fontSize: 15 });
  });

  s = content('추가 미션 (조별 경쟁)', TAG, '시간이 남는 조를 위한 확장입니다. 복구 미션은 "하던 일"이 무엇인지 모델이 모른다는 점(대화가 새로 시작됨)을 깨닫게 하는 것이 목적입니다.');
  card(s, { x: 0.6, y: 1.5, w: 3.85, h: 3.4, head: '왕복', iconName: 'FaUndo', accent: C.accent2, body: '"상자를 원래 자리에 갖다 놓고 처음 위치로 돌아와"\n\n한 문장으로 세 단계' });
  card(s, { x: 4.73, y: 1.5, w: 3.85, h: 3.4, head: '복구', iconName: 'FaStopCircle', accent: C.accent6, body: '주행 중 작업 취소 → "하던 일 계속해" 한 문장으로 마무리시키기\n\n프롬프트를 어떻게 고칠까?' });
  card(s, { x: 8.85, y: 1.5, w: 3.85, h: 3.4, head: '새 도구', iconName: 'FaWrench', accent: C.accent1, body: '도전 2의 drive_forward를 추가하고 그것을 쓰는 명령 만들기' });
  callout(s, 'tip', 0.6, 5.15, 12.1, 1.55, '조마다 성공한 미션 수와 걸린 시간을 칠판에 적는다. 실패한 시도도 타임라인을 캡처해 두면 좋은 발표 자료가 된다.', '진행 방법');

  summary('모듈 4 한 장 요약', TAG, [
    ['FaBrain', 'LLM은 "무엇을", 스킬은 "어떻게"', 'Claude는 이름만 고르고, 좌표·팔 선택·안전은 우리 코드가 정한다'],
    ['FaListOl', '도구 호출 = 주문서와 결과의 왕복', '한 번에 하나씩 부르고, 결과(실패 포함)를 보고 다음을 정한다'],
    ['FaShieldAlt', '두 단계 검증: 형식(스키마) + 상황(월드)', 'strict·enum으로 엉뚱한 값을 막고, 사전 조건으로 지금 못 하는 일을 막는다'],
    ['FaComments', '되묻기 · 중단 · 실패 복구 · 초기화', '시스템 프롬프트로 행동을 바꾸고, /task_cancel·/task_reset으로 사람이 개입한다'],
    ['FaGlobe', '대시보드 = rosbridge로 ROS와 웹을 잇기', '/task_status JSON 이벤트 하나로 터미널과 웹이 같은 정보를 본다'],
  ], '다섯 줄로 정리합니다.');

  quiz('모듈 4 셀프 체크', TAG, [
    ['LLM에게 좌표를 직접 내게 하지 않고 장소 이름만 고르게 한 이유는?', '엉뚱한 숫자로 위험하게 움직이는 것을 막고, 좌표는 검증된 표(LOCATIONS)에서 가져오기 위해. 단점: 새 장소마다 표에 추가해야 한다.'],
    ['스키마로는 못 막고 월드 검증으로만 막을 수 있는 잘못의 예는?', '들고 있지 않은데 place_object, 다른 테이블에 있는 물체 pick_object, 들고 있는데 팔 자세 바꾸기 등.'],
    ['도구를 한 번에 하나씩만 부르게 한 이유는?', '로봇은 동시에 두 곳에 갈 수 없고, 앞 단계 결과(성공/실패, 지금 위치)를 봐야 다음을 정할 수 있다.'],
    ['취소할 때 "진행 중인 팔 동작은 끝까지"로 정한 이유는?', '팔을 중간에 멈추면 테이블 위 애매한 자세로 남아 다음 동작(계획)이 어려워진다.'],
    ['네트워크가 끊겨 Claude가 응답하지 않으면 로봇은 어떤 상태로 남나?', '진행 중이던 스킬은 끝나고 다음 단계는 시작되지 않는다. 플래너는 오류로 끝나고 로봇은 그 자리에서 멈춘다.'],
  ], '답은 발표자 노트에 있습니다.');

  s = content('모듈 4 과제', TAG, '도전 2는 strict 스키마가 숫자 범위를 강제하지 않는다는 점이 함정입니다. 범위는 월드 검증에서 막아야 합니다. 도전 3은 cache_read_input_tokens로 캐시 여부를 확인합니다.');
  card(s, { x: 0.6, y: 1.5, w: 12.1, h: 1.5, head: '기본. 실습 2의 표 + 일부러 실패시키는 명령 하나', iconName: 'FaPencilAlt', accent: C.accent2, body: '없는 장소, 순서가 이상한 명령 등. Claude의 반응을 /task_status 로그와 함께 제출', bodySize: 14 });
  [['도전 1. 대화 이어 가기', '최근 명령과 최종 답을 기억해 다음 명령에 붙인다. "작업대로" 같은 짧은 답을 이해하게. 무엇을 남길지(토큰) 정하기', 'FaComments'], ['도전 2. 새 도구 drive_forward', 'distance_m(−0.5~0.5)만큼 직진. 범위 밖이면 오류, 테이블 바로 앞에서 전진 거부. "조금 뒤로 물러나 봐"로 시험', 'FaRoute'], ['도전 3. 비용 줄이기', '매 턴 같은 SYSTEM_PROMPT와 TOOLS를 보낸다 → prompt caching(cache_control)으로 전후 토큰·비용 비교', 'FaDollarSign']].forEach(([h, b, ic], i) => {
    card(s, { x: 0.6 + i * 4.1, y: 3.2, w: 3.85, h: 3.5, head: h, body: b, iconName: ic, accent: [C.accent3, C.accent1, C.text1][i], headSize: 15, bodySize: 14 });
  });
};
