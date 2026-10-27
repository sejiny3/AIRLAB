# 모듈 4. LLM 작업 계획: 자연어 명령에서 로봇 제어까지

**2일차 12:30–16:30 (4시간)**

| 시간 | 내용 |
|---|---|
| 12:30–13:00 | 개념: LLM을 로봇 작업 계획기로 쓰기, 도구 호출, 스키마 검증 vs 월드 검증 |
| 13:00–13:40 | 실습 1~2: 대역(scripted)으로 파이프라인 확인 → 실제 Claude로 계획 |
| 13:40–14:20 | 실습 3~4: 코드 읽기, 실패 복구와 취소 |
| 14:20–14:30 | 휴식 |
| 14:30–15:00 | 실습 5: 웹 대시보드, 데이터 흐름 |
| 15:00–15:40 | 실습 6: 시스템 프롬프트·도구 고치기 |
| 15:40–16:20 | **최종 미션** |
| 16:20–16:30 | 마무리, 설문 |

## 학습 목표

1. LLM이 로봇을 "직접 제어"하지 않고 **검증된 스킬을 골라 부르는 계획기** 역할을 하는 구조를 설명한다.
2. 도구 정의(strict JSON schema)로 **명령 형식**을, 작업 관리자의 사전 조건으로 **세계 상태**를 검증한다.
3. 자연어 명령 → 계획 → 스킬 실행 → 결과 피드백 → 다음 계획의 루프를 코드로 따라간다.
4. 브라우저 대시보드에서 로봇 상태를 보고 명령을 보내며, ROS 2 ↔ rosbridge ↔ 웹의 데이터 흐름을 안다.

## 준비

- API 키를 넣었는지: `bash ~/unbolt/workshop/setup/check_env.sh` 마지막 부분 (없으면 [설치 가이드 7](00_install.md#7-claude-api-키-모듈-4-전까지-선택))
- 키가 없으면 실습 1, 3, 4(일부), 5는 `llm:=scripted`로 그대로 할 수 있습니다.

---

## 개념

### 왜 LLM이 관절을 직접 움직이지 않나

```
  "공급 테이블로 가서 빨간 상자를 집고 작업대로 옮겨"
                 │
                 ▼
   ┌──── LLM (Claude) : 무엇을, 어떤 순서로 ────┐      느리다 (초 단위), 가끔 틀린다
   │  get_world_state → navigate_to(supply_1)     │
   │  → pick_object(red_box) → navigate_to(...)   │
   └──────────────┬───────────────────────────────┘
                  │ 도구 호출 (JSON)
   ┌──────────────▼──── 작업 관리자 (TaskExecutor) ┐      사전 조건 검사
   └──────────────┬────────────────────────────────┘
                  ▼
   ┌──── 스킬 (RobotSkills): 어떻게 ──────────────┐      빠르다 (ms), 검증된 코드
   │  Nav2 주행, 마커 정밀 접근, MoveIt 집기/놓기   │
   └───────────────────────────────────────────────┘
```

LLM은 **언어 이해와 순서 계획**을 맡고, 실시간 제어와 안전은 모듈 1~3에서 만든 스킬이 맡습니다.
LLM이 틀린 계획을 내도 스킬과 작업 관리자가 실행 전에 거르고, 실패하면 그 이유를 LLM에 돌려줍니다.

### 도구 호출 루프

```python
messages = [{'role': 'user', 'content': command}]
for turn in range(MAX_TURNS):
    response = client.beta.messages.create(model=..., system=SYSTEM_PROMPT, tools=TOOLS, messages=messages,
                                           tool_choice={'type': 'auto', 'disable_parallel_tool_use': True}, ...)
    messages.append({'role': 'assistant', 'content': response.content})
    if response.stop_reason != 'tool_use':
        return 최종 답변                                    # 계획 끝
    ok, result = executor.run(call.name, call.input)         # 로봇이 실제로 실행 (수십 초)
    messages.append({'role': 'user', 'content': [tool_result(result, is_error=not ok)]})   # 결과를 보고 다음 계획
```

**한 번에 하나씩** 부르게 합니다(`disable_parallel_tool_use`). 로봇은 두 곳으로 동시에 갈 수 없고,
앞 단계의 결과(성공/실패, 지금 위치)를 보고 다음 단계를 정해야 하기 때문입니다.

### 두 단계 검증

| | 스키마 검증 | 월드(세계 상태) 검증 |
|---|---|---|
| 어디서 | 도구 정의 `TOOLS` (`strict: True`, `enum`) | `TaskExecutor._tool_*` |
| 무엇을 | 형식: 장소 이름이 `supply_1`~`supply_3` / `work_table` / `home` 중 하나인가, 자리가 `auto`/`left`/`middle`/`right` 중 하나인가 | 의미: 지금 그 일을 할 수 있는 상태인가 (그 자리가 비었나, 그 상자가 거기 있나) |
| 예 | `navigate_to(location="kitchen")` → API가 애초에 만들지 못함 | 들고 있는 게 없는데 `place_object` → `"not holding anything"` |
| 실패 시 | 생성 자체가 스키마를 따름 | 오류를 도구 결과로 돌려줌 → LLM이 읽고 계획 수정 |

### 대화형 동작 세 가지

| 상황 | 이 시스템에서 |
|---|---|
| **되묻기 (clarification)** | 모르는 물건·장소면 즉흥으로 하지 말고 가능한 일을 안내 (시스템 프롬프트). 실습 6에서 확장 |
| **중단 (interrupt)** | `/task_cancel` → 주행·정밀 접근은 즉시 정지, 진행 중인 팔 동작은 끝낸 뒤 다음 단계를 시작하지 않음 |
| **실패 복구** | 실패 메시지를 읽고 다시 될 것 같으면 한 번 재시도, 아니면 멈추고 현재 상태(예: 상자를 든 채)를 보고 |

---

## 실습 1. 대역(scripted)으로 파이프라인 확인

LLM 없이 **로봇 쪽 전체**가 동작하는지 먼저 봅니다. `ScriptedLLM`은 명령의 키워드로 정해진 도구 호출 순서를
재생하는 시험용 대역입니다 (계획을 하지는 않습니다).

```bash
$ ros2 launch unbolt_manipulation bringup.launch.py planner:=true llm:=scripted
```

다른 터미널:

```bash
$ ros2 run unbolt_manipulation ask "빨간 상자를 작업대로 옮겨줘"
```

```
>> 빨간 상자를 작업대로 옮겨줘
  -> get_world_state({})
     OK (0 s)
  -> navigate_to({"location": "supply_1"})
     OK (13 s) arrived at supply_1
  -> pick_object({"object": "red_box"})
     OK (24 s) picked red_box from the right spot of supply_1 with the right arm
  ...
== done in 80 s: 빨간 상자를 작업대로 옮겼습니다. (scripted)
```

세 번째 터미널에서 이벤트 원본을 보세요:

```bash
$ ros2 topic echo /task_status --field data
```

`command`, `thinking`, `tool_call`, `tool_result`, `final`, `world` 이벤트가 JSON으로 나옵니다.
대시보드도 이것을 그대로 받아 화면을 그립니다.

✅ **체크포인트 4-1**: scripted 모드로 상자가 작업대에 놓였다.

## 실습 2. 실제 Claude로 계획

bringup을 끄고 (`Ctrl + C`) LLM을 켜서 다시 실행합니다 (다시 켜면 월드도 처음 상태로 시작합니다):

```bash
$ ros2 launch unbolt_manipulation bringup.launch.py planner:=true
```

아래 명령을 차례로 보내고, Claude가 고른 도구 순서와 답을 표에 적으세요.

```bash
$ ros2 run unbolt_manipulation ask "빨간 상자를 작업대로 옮겨줘"
$ ros2 run unbolt_manipulation ask "노란 공 좀 가져다 줄래?"
$ ros2 run unbolt_manipulation ask "이제 빨간 상자를 원래 자리에 다시 갖다 놔"
$ ros2 run unbolt_manipulation ask "작업대 앞에 갔다가 처음 위치로 돌아와"
```

| 명령 | Claude의 도구 순서 | 결과 | 토큰 / 비용 |
|---|---|---|---|
| 빨간 상자를 작업대로 | | | |
| 노란 공 | | | |
| 원래 자리에 | | | |
| 작업대 갔다가 돌아와 | | | |

`ask`는 끝에 그 명령에 쓴 토큰과 대략의 비용을 출력합니다 (`tokens: … in / … out (about $…)`).

> 같은 명령도 실행할 때마다 계획이 조금 다를 수 있습니다 (예: `get_world_state`를 먼저 부르는지).
> 결과가 같으면 정상입니다.

✅ **체크포인트 4-2**: 모르는 물건(노란 공)은 도구를 부르지 않고 안내만 했다.

## 실습 3. 코드 읽기

`ros2_ws/src/unbolt_manipulation/unbolt_manipulation/task_planner_core.py`를 열고 찾아보세요.

| 찾을 것 | 질문 |
|---|---|
| `LOCATIONS`, `OBJECTS` | 장소마다 `staging`(Nav2 목표)과 놓는 자리 `spots`(마커 번호, 지도 좌표)가 있다. 상자마다 처음 자리 `home`이 있다. LLM은 좌표를 아나? |
| `SYSTEM_PROMPT` | 로봇의 규칙(먼저 그 장소로 가야 집을 수 있다 등)을 어떻게 알려 주나? 한국어 별칭은? |
| `TOOLS` | `strict`, `enum`, `additionalProperties: False`가 각각 무엇을 막나? |
| `TaskExecutor._tool_pick_object` | 월드 검증 두 가지는? 어느 팔로 집을지는 누가 정하나? 집기에 실패해도 뒤로 물러나는 이유는? |
| `TaskExecutor._choose_spot` | `auto`는 어떤 순서로 자리를 고르나? 이미 상자가 있는 자리를 고르면? |
| `TaskExecutor._tool_check_table` | 카메라로 본 상자가 어느 자리인지 어떻게 정하나(`SPOT_MATCH`)? 기억에는 있는데 안 보이는 상자는? |
| `TaskPlanner.run` | `stop_reason`이 무엇일 때 루프가 끝나나? 도구 결과에 `is_error`를 넣는 이유는? |
| `task_planner.py` | 명령이 실행 중일 때 새 명령이 오면? |

**핵심**: LLM은 좌표·관절각·팔 선택을 모릅니다. 이름(`supply_1`, `red_box`, `left`)만 고르고,
구체적인 값은 작업 관리자와 스킬이 정합니다. 그래서 LLM이 엉뚱한 숫자를 만들어 로봇을 위험하게 움직일 수 없습니다.

## 실습 4. 실패 복구와 취소

**월드 검증 → 계획 수정**: 상자가 공급 테이블에 있을 때

```bash
$ ros2 run unbolt_manipulation ask "작업대에 들고 있는 걸 내려놔"
```

들고 있는 게 없으므로 `place_object`는 `not holding anything` 오류를 돌려줍니다 (Claude가 부른다면).
Claude가 그 오류를 읽고 어떻게 답하는지 보세요.

**중단**: 긴 명령을 보내고 주행 중에 취소합니다.

```bash
$ ros2 run unbolt_manipulation ask "빨간 상자를 작업대로 옮겨줘"
# 로봇이 주행을 시작하면 다른 터미널에서:
$ ros2 topic pub --once /task_cancel std_msgs/msg/Empty
```

로봇이 즉시 멈추고 `작업을 취소했습니다`가 나옵니다. 이어서 같은 명령을 다시 보내면 Claude가
`get_world_state`로 현재 상태(위치를 모름 / 이미 공급 테이블 앞 등)를 확인하고 이어서 계획하는지 보세요.

✅ **체크포인트 4-3**: 취소 후 다시 보낸 명령이 성공했다.

**처음부터 다시 (초기화)**: 상자가 엉뚱한 곳에 있거나 로봇이 꼬였을 때, bringup을 다시 켜지 않고 처음 상태로 되돌립니다.

```bash
$ ros2 topic pub --once /task_reset std_msgs/msg/Empty
```

진행 중인 작업을 취소한 뒤 → 시뮬레이터 리셋(로봇·팔·상자 세 개를 처음 위치로) → AMCL 위치 추정을 원점으로 다시 맞추고
costmap을 비움 → 플래너가 기억하는 상태(위치, 들고 있는 것, 마커 위치)도 처음으로. 몇 초면 끝납니다.

> 시뮬레이터만 리셋하는 `ros2 service call /mujoco_bridge/reset std_srvs/srv/Trigger`는 플래너와 AMCL이 옛 상태를
> 기억하고 있어서 다음 명령이 꼬입니다. 플래너를 켠 상태에서는 `/task_reset`을 쓰세요.

## 실습 4-B. 조건과 순서가 있는 명령

방에는 공급 테이블이 세 개(1번 남쪽 · 빨간 상자, 2번 북쪽 · 초록 상자, 3번 서쪽 방 · 파란 상자) 있고,
작업대에는 상자를 하나씩 놓는 자리가 왼쪽 · 가운데 · 오른쪽 세 칸 있습니다. 그래서 명령이 훨씬 다양해집니다:
"무엇을 어디로"뿐 아니라 **어느 자리에**, **어떤 순서로**, **어떤 조건일 때만**.

이를 위해 도구가 두 개 늘고, 하나가 바뀌었습니다:

| 도구 | 하는 일 | 왜 필요한가 |
|---|---|---|
| `place_object(location, spot)` | `spot`: `left` / `middle` / `right` 또는 `auto` (그 상자의 처음 자리, 아니면 첫 빈자리) | "작업대 왼쪽에 놓아" 같은 명령. 이미 상자가 있는 자리면 월드 검증이 거절 |
| `check_table(location)` | 지금 선 테이블을 카메라로 3초 보고, 어느 자리에 어떤 상자가 있는지 보고 (안 보이면 25 cm 다가가 한 번 더) | 기억(`get_world_state`)이 틀렸을 수 있을 때 **눈으로 확인**. 보이는 상자는 그 자리로, 있어야 하는데 안 보이는 상자는 "모름"으로 고친다 |
| `wait(seconds)` | 1~120초 그 자리에서 기다리기 | "10초 기다렸다가 …" 같은 순서 명령 |

조건 판단은 LLM이 합니다. 시스템 프롬프트에 규칙을 두었습니다:
**순서는 사람이 말한 대로**, **조건은 행동 전에 상태를 보고 판단**(평소에는 기억, "가서 봐/확인해"라고 하거나
실패 직후처럼 기억이 틀렸을 수 있으면 `check_table`), **조건이 거짓이면 그 부분을 건너뛰고 답에서 알린다**.

```bash
$ ros2 run unbolt_manipulation ask "초록 상자를 먼저 작업대 왼쪽에 놓고, 그다음 파란 상자를 오른쪽에 놓아줘"
$ ros2 run unbolt_manipulation ask "작업대에 빨간 상자가 없으면 가져다 놔"
$ ros2 run unbolt_manipulation ask "작업대에 뭐가 있는지 가서 확인해 줘"
$ ros2 run unbolt_manipulation ask "작업대에 빨간 상자가 있으면 원래 자리로 돌려놓고, 없으면 그냥 원위치로 와"
$ ros2 run unbolt_manipulation ask "상자를 모두 원래 자리에 돌려놓고 원위치로 와"
```

| 명령 | Claude가 조건을 무엇으로 판단했나 (기억 / 카메라) | 도구 순서 | 결과 |
|---|---|---|---|
| 초록 먼저 왼쪽, 그다음 파랑 오른쪽 | | | |
| 빨간 상자가 없으면 가져와 | | | |
| 가서 확인해 | | | |
| 있으면 돌려놓고 없으면 원위치 | | | |
| 모두 원래 자리로 + 원위치 | | | |

✅ **체크포인트 4-3B**: 조건이 들어간 명령에서 Claude가 상태를 먼저 확인하고, 조건에 맞는 쪽만 실행했다.

강사 노트북에서 위 명령을 차례로 보낸 실제 결과입니다 (`claude-opus-5-5`, 한 번의 실행, 상자 세 개가 모두 처음 자리에서 시작):

| 명령 | Claude가 고른 도구 순서 | 결과 · 시간 · 비용 |
|---|---|---|
| 초록 먼저 왼쪽, 그다음 파랑 오른쪽 | 상태 → 2번 → 집기(초록) → 작업대 → 놓기(`left`) → 3번 → 집기(파랑) → 작업대 → 놓기(`right`) | 성공, 195 s, $0.14 |
| 빨간 상자가 없으면 가져와 | 상태(기억: 없음) → 1번 → 집기 → 작업대 → 놓기(`auto` → 가운데) | "로봇 기억으로는 없었어요"라고 근거를 밝히고 실행, 99 s, $0.08 |
| 가서 확인해 | 작업대(이미 앞) → `check_table` | 왼쪽 초록 · 가운데 빨강 · 오른쪽 파랑, 10 s, $0.03 |
| 있으면 돌려놓고 없으면 원위치 | 상태(있음) → 집기 → 1번 → 놓기(`auto` → 처음 자리) | "있었기 때문에 원위치로는 가지 않았다"고 보고, 72 s, $0.07 |
| 노란 공 | (도구 없음) | 알고 있는 물건과 장소를 안내, 3 s, $0.01 |
| 모두 원래 자리로 + 원위치 | 상태 → 초록·파랑을 각자 처음 자리로 → 원위치 (빨강은 이미 제자리라 건너뜀) | 성공, 208 s, $0.16, 세 상자 모두 처음 자리에서 1.2 cm 이내 |

마지막 답에서 Claude는 "빨간 상자는 기억상 이미 제자리라 옮기지 않았다(카메라로 확인하지는 않았다)"고 덧붙였습니다.
**무엇을 근거로 판단했는지 말하게** 하면, 사람이 기억이 틀렸을 가능성을 알아챌 수 있습니다.

> **기억과 실제가 다를 때.** MuJoCo 창에서 작업대 위의 상자를 더블클릭하고 `Ctrl + 마우스 오른쪽 드래그`로 바닥에 떨어뜨려
> 보세요. 플래너는 여전히 작업대에 있다고 기억합니다. 이때 "작업대에 빨간 상자가 있으면 …"을 보내면 Claude가 기억만 믿고 틀리게
> 판단할 수 있습니다. 같은 명령을 "작업대에 빨간 상자가 있는지 **가서 보고** …"로 바꾸면 `check_table`이 기억을 고칩니다. 직접 비교해 보세요. 로봇 시스템에서
> "세계 상태를 믿을 것인가, 다시 볼 것인가"는 늘 비용(시간)과 정확도의 맞바꿈입니다.

## 실습 5. 웹 대시보드

```bash
$ ros2 launch unbolt_manipulation bringup.launch.py planner:=true dashboard:=true
```

Windows의 Chrome/Edge에서 **<http://localhost:8080>** 을 엽니다 (WSL이 localhost를 Windows로 연결해 줍니다).

![Dashboard](../docs/step7_dashboard.jpg)

- **지도**: SLAM 지도 + 로봇 외곽선·방향 + LiDAR 점 + Nav2 경로 + 테이블 네 개와 놓는 자리 + 빨강·초록·파랑 상자(시뮬레이터 실제 위치)
- **헤드 카메라**: 마커 검출 결과가 그려진 영상
- **명령**: 자연어 입력, 자주 쓰는 명령 버튼, 작업 취소, **초기화**(한 번 누르면 "정말 초기화?"로 바뀌고 4초 안에 한 번 더 누르면 실행, `/task_reset`과 같음)
- **시스템 종료** (오른쪽 위): 두 번 눌러 확인하면 시뮬레이터, Nav2, MoveIt, 플래너, RViz까지 **이 launch의 모든 프로그램**을 끕니다.
  터미널에서 `Ctrl + C`를 누른 것과 같습니다. 화면에 다시 시작하는 명령이 나오고, 다시 켜면 페이지가 저절로 다시 연결됩니다.
- **연결** (런처를 켰을 때): 아래 "브라우저에서 켜고 끄기"
- **작업 진행**: Claude가 부른 단계마다 상태·시간·결과, Claude의 답
- **키보드 조종**: 작업이 없을 때 `W A S D`/방향키(스페이스 = 정지)로 로봇을 직접 몹니다. 누르는 동안만 움직이고, 앞뒤 장애물이
  가까우면 그쪽으로는 가지 않습니다. 작업 중에는 잠기고, 몰고 나면 플래너가 로봇 위치를 "알 수 없음"으로 바꿔 다음 명령은 주행부터 합니다
  (`/task_manual_drive`). 지도 만들기 모드와 같은 카드입니다.
- **로봇 상태**: 위치, 들고 있는 물체, 속도, 그리퍼

**브라우저에서 켜고 끄기 (런처)**: 터미널 명령 대신 대시보드의 버튼으로 시스템을 켜고 끌 수 있습니다.
런처를 한 번만 켜 두세요:

```bash
$ ros2 run unbolt_dashboard dashboard_launcher
```

http://localhost:8080 을 열면 ROS가 꺼져 있어도 페이지가 뜨고 **"ROS가 꺼져 있습니다"** 화면이 나옵니다.
모드와 옵션을 고르고 **연결 (시스템 시작)** 을 누르면 시스템이 켜지고 (보통 25~60초), 준비가 끝나면 화면이 닫힙니다.
끌 때는 오른쪽 위 **시스템 종료**, 다시 켤 때는 다시 **연결**.

| 모드 | 켜지는 것 | 고를 것 |
|---|---|---|
| **작업** (LLM 명령, 저장된 지도) | bringup 전체: 시뮬레이터, Nav2(AMCL), MoveIt, 마커 검출, 플래너 | 지도 (기본 지도 또는 `~/maps`에 저장한 지도), LLM (Claude / 대역) |
| **지도 만들기** (SLAM + 자동 탐색) | 시뮬레이터, slam_toolbox, Nav2(지도 없이), 프론티어 탐색 | 없음. 로봇이 스스로 탐색한 뒤 키보드로 조종 ([모듈 2 실습 8](02_slam_nav2.md#실습-8-자동-탐색으로-지도-만들기-대시보드)) |
| **VLA 집기** (작업 + 학습된 집기 정책) | 작업 모드 전체 + 손목 카메라 + `vla_pick` 노드 (`pick:=vla`) | 작업 모드와 같음. 학습한 정책(`~/unbolt_vla/policy.pt`)이 있어야 켜짐 ([심화 모듈 5](05_vla.md)) |

세 모드 모두 MuJoCo 창과 RViz를 켤지 고를 수 있습니다. 지도 만들기로 만든 지도를 **작업** 모드의 지도 목록에서 고르면,
그 지도로 상자 옮기기를 할 수 있습니다 (로봇이 같은 자리에서 출발하므로 장소 좌표가 그대로 맞습니다).

- 런처는 페이지만 보여 주고 bringup을 대신 실행해 주는 작은 프로그램입니다 (로그: `~/.ros/unbolt_launcher.log`).
- 켜는 도중에 **시작 취소**를 누를 수 있습니다. 런처 터미널에서 `Ctrl + C`를 누르면 런처가 켠 시스템도 함께 꺼집니다.
- 다른 터미널에서 켠 시스템이 있으면 그것에 연결만 하고, 새로 켜지는 않습니다.

데이터 흐름:

```
 브라우저 (index.html, 자바스크립트)
    │  WebSocket :9090  (rosbridge v2 JSON 프로토콜: subscribe / publish / advertise)
    ▼
 rosbridge_websocket ──── ROS 2 토픽 ────┬─ /task_command ▶ task_planner
                                          ├─ /task_status  ◀ task_planner (JSON 이벤트)
                                          ├─ /scan, /plan, /dashboard/robot_pose, /ground_truth/{red,green,blue}_box
                                          └─ /aruco/debug_image/compressed (JPEG)
 dashboard_server (:8080) ── index.html, /map.png, /config.json (지도 해상도·원점, 테이블 위치)
```

브라우저 개발자 도구(F12) → **Network → WS** 에서 오가는 JSON 메시지를 직접 보세요.
휴대폰으로 보고 싶으면 같은 와이파이에서 `http://<노트북 IP>:8080` (Windows 방화벽·WSL 네트워크 설정에 따라 안 될 수 있음).

✅ **체크포인트 4-4**: 대시보드에서 명령을 보내고 작업 진행이 단계별로 표시된다.

## 실습 6. 시스템 프롬프트와 도구 고치기

`--symlink-install`이므로 파이썬 파일을 고치고 **bringup만 다시 시작**하면 됩니다 (빌드 불필요).

**6-A. 되묻기.** `SYSTEM_PROMPT`에 규칙을 하나 추가합니다:

```
- If the command does not say where to take the object, do not guess: ask the person which table,
  in one short question, and do not call any tool.
```

`"빨간 상자 좀 옮겨 줘"`(목적지 없음)를 보내 Claude가 되묻는지 확인하세요. 그다음 `"작업대로"`만 보내면?
→ 지금 구조는 **명령마다 대화가 새로 시작**되어 앞 질문을 기억하지 못합니다 (도전 과제 1).

**6-B. 장소 별칭.** "선반 옆 테이블"이라고 부르면 작업대로 알아듣게 프롬프트의 별칭 줄을 고쳐 보세요.

✅ **체크포인트 4-5**: 목적지 없는 명령에 Claude가 질문으로 답했다.

---

## 최종 미션 (15:40–16:20)

대시보드 명령창에 **한 문장**으로:

> **"공급 테이블로 가서 빨간 상자를 집고 작업대로 옮겨"**

| 성공 조건 | 확인 방법 |
|---|---|
| 빨간 상자가 작업대의 놓을 자리(마커 1·2·3 중 하나) 위에 있다 | 대시보드 지도의 빨간 상자 위치, MuJoCo 화면 |
| 사람이 중간에 손대지 않았다 (취소·재명령 없이) | 작업 진행 타임라인 |
| 3분 이내 | 타임라인의 총 시간 |

**추가 미션** (시간이 남으면, 조별 경쟁):

1. **왕복**: "상자를 원래 자리에 갖다 놓고 처음 위치로 돌아와" — 한 문장으로 세 단계
2. **복구**: 주행 중 대시보드의 **작업 취소** → "하던 일 계속해" 한 문장으로 마무리시키기 (프롬프트를 어떻게 고쳐야 할까?)
3. **새 도구**: 아래 도전 과제 2의 도구를 추가하고 그것을 쓰는 명령 만들기

---

## 과제

**기본 과제.** 실습 2의 표와, 일부러 실패시키는 명령 하나(예: 없는 장소, 순서가 이상한 명령)를 골라
Claude가 어떻게 반응했는지 `/task_status` 로그와 함께 제출.

**도전 과제 1. 대화 이어 가기.** `TaskPlanner.run`이 명령마다 `messages`를 새로 만듭니다. 최근 대화(명령과 최종 답)를
기억해 두었다가 다음 명령에 앞에 붙여, 6-A의 "작업대로" 같은 답을 이해하게 하세요.
(주의: 도구 호출 기록까지 넘기면 토큰이 빠르게 늘어납니다. 무엇을 남길지 정하세요.)

**도전 과제 2. 새 도구 `drive_forward`.** 앞뒤로 `distance_m`(−0.5~0.5)만큼 직진하는 도구를 추가하세요.
- 스키마: `{"distance_m": {"type": "number"}}`, `strict: True` (strict 스키마는 숫자 범위를 강제하지 않으니 범위는…)
- 월드 검증: 범위 밖이면 오류, 테이블 바로 앞(`robot_location`이 테이블)에서 전진은 거부
- 실행: `self.s.drive_straight(distance_m)`
- 시험: "조금 뒤로 물러나 봐"

**도전 과제 3. 비용 줄이기.** 명령 하나에 토큰을 얼마나 쓰는지 재고(`ask` 출력), 매 턴마다 같은 `SYSTEM_PROMPT`와
`TOOLS`를 다시 보낸다는 점을 이용해 **prompt caching**(`cache_control`)으로 줄여 보세요. 전후 토큰·비용을 비교합니다.
(Anthropic 문서의 Prompt caching 참고. 캐시되는 최소 길이가 있으니 실제로 캐시됐는지 `usage`의
`cache_read_input_tokens`로 확인)

## 정리 질문

1. LLM에게 좌표를 직접 내게 하지 않고 장소 이름만 고르게 한 이유는? 장단점은?
2. 스키마 검증으로 막을 수 없고 월드 검증으로만 막을 수 있는 잘못의 예를 두 개 들어 보자.
3. 취소했을 때 "진행 중인 팔 동작은 끝까지 한다"로 정한 이유는?
4. 이 구조에서 LLM이 아예 응답하지 않으면(네트워크 끊김) 로봇은 어떤 상태로 남나?

## 참고

| 파일 | 내용 |
|---|---|
| `unbolt_manipulation/task_planner_core.py` | `SYSTEM_PROMPT`, `TOOLS`, `TaskExecutor`, `TaskPlanner`, `ScriptedLLM` |
| `unbolt_manipulation/task_planner.py` | ROS 노드: `/task_command` → `/task_status`, `/task_cancel`, `/task_world`, `/task_reset` |
| `unbolt_manipulation/ask.py` | 명령 CLI |
| `unbolt_dashboard/web/index.html` | 대시보드 (외부 라이브러리 없이 rosbridge 프로토콜 직접 구현) |
| `unbolt_dashboard/dashboard_server.py` | 웹 서버, 지도 PNG, 로봇 위치 TF 재발행 |
| Claude API 문서 – Tool use | <https://docs.claude.com/en/docs/agents-and-tools/tool-use/overview> |
