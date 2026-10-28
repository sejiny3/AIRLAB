"""Natural-language task planning for AIRLAB: Claude turns a command into skill calls.

The robot's skills (navigate, pick, place, look, arm postures) are exposed to Claude as
tools. Claude plans, calls them one at a time, sees each result, and finally answers the
user. Execution feedback goes through an `on_event` callback so the ROS node can publish it
(dashboard, CLI).

Nothing here talks to ROS directly except through RobotSkills, so the loop can be
tested with ScriptedLLM (a stand-in that replays a fixed tool sequence) when no
API key is available.
"""

import json
import math
import time
import types

from airlab_manipulation.skills import GRASP_XY, RobotSkills

MODEL = 'claude-opus-5-5'
MAX_TURNS = 40      # moving all three boxes takes 4 tool calls each, plus looking around

# Known places (models/scene.xml): where to stand (map frame, Nav2 goal, facing the table) and
# the place spots there. A spot is named from the robot's point of view when it faces the table
# and is marked by an ArUco pad (marker id); xy is the pad centre in the map frame, used to tell
# which spot a box the camera sees is standing on. Every spot holds one box.
LOCATIONS = {
    'supply_1': {'staging': (0.0, -2.8, -math.pi / 2),
                 'spots': {'right': {'marker': 11, 'xy': (-0.15, -3.61)}, 'left': {'marker': 12, 'xy': (0.15, -3.61)}},
                 'description': 'supply table 1, by the south wall (light-blue top)'},
    'supply_2': {'staging': (2.0, 2.8, math.pi / 2),
                 'spots': {'right': {'marker': 21, 'xy': (2.15, 3.61)}, 'left': {'marker': 22, 'xy': (1.85, 3.61)}},
                 'description': 'supply table 2, by the north wall (light-blue top)'},
    'supply_3': {'staging': (-2.05, 2.6, math.pi),
                 'spots': {'right': {'marker': 31, 'xy': (-2.86, 2.75)}, 'left': {'marker': 32, 'xy': (-2.86, 2.45)}},
                 'description': 'supply table 3, in the west room behind the partition wall (light-blue top)'},
    'work_table': {'staging': (3.8, 0.0, 0.0),
                   'spots': {'left': {'marker': 1, 'xy': (4.6, 0.25)}, 'middle': {'marker': 2, 'xy': (4.6, 0.0)},
                             'right': {'marker': 3, 'xy': (4.6, -0.25)}},
                   'description': 'work table, east side of the room (wooden top)'},
    'home': {'staging': (0.0, 0.0, 0.0), 'spots': {},
             'description': 'start position in the middle of the room (no table)'},
}
TABLES = [k for k, v in LOCATIONS.items() if v['spots']]
SPOTS = ['left', 'middle', 'right']
OBJECTS = {
    'red_box': {'marker': 7, 'color': 'red', 'home': ('supply_1', 'right'), 'description': 'red box, 5 cm cube, 100 g'},
    'green_box': {'marker': 8, 'color': 'green', 'home': ('supply_2', 'right'), 'description': 'green box, 5 cm cube, 100 g'},
    'blue_box': {'marker': 9, 'color': 'blue', 'home': ('supply_3', 'right'), 'description': 'blue box, 5 cm cube, 100 g'},
}
SPOT_MATCH = 0.12   # a box seen within this of a spot's centre stands on that spot [m]

SYSTEM_PROMPT = f"""You are the task planner of AIRLAB, a mobile robot with two arms (OpenArm v2) on a
wheeled base, working in a simulated room. A person gives you a command in natural language
(usually Korean). Turn it into robot actions by calling the tools, one at a time, and look at
each result before deciding the next step.

How the robot works:
- It can only pick an object or place it while standing at the table where that happens:
  navigate_to the object's location before pick_object, and to the destination before place_object.
- It carries at most one object at a time, so to move several boxes, move them one after another.
- pick_object and place_object find the object or the place spot with the head camera (ArUco
  markers) and line the base up by themselves.
- Every table has place spots that hold one box each: the work table has left, middle and right,
  each supply table has right and left (seen from the robot facing the table). place_object takes
  a spot, or 'auto' for the box's own start spot when it goes back to its supply table and
  otherwise the first free spot.
- Call get_world_state first when you need to know where things are; it is cheap but it is only
  the robot's memory. check_table looks with the camera at the table the robot stands at and
  corrects that memory.
- If a tool fails, read its message. Retry a failed step once when the message suggests it could
  work again; otherwise stop and explain.
- If the command asks for something the robot cannot do (an unknown object or place, or an action
  with no tool), do not improvise: say what is possible instead.

Commands with conditions and an order:
- Do the steps in the order the person gave ("먼저 ... 그다음 ...", "...하고 나서", "마지막에").
- A condition ("...이면", "...가 없으면", "...일 때만") is decided from the world state before acting on
  it. Use check_table instead of memory when the person asks to look or confirm ("가서 봐", "확인해"),
  or when memory may be wrong (after a failed pick or place, or if the person says things were moved).
- When a condition is false, skip that part and say so in the reply. "Wait N seconds" is the wait tool.

Known locations: {', '.join(f'{k} ({v["description"]})' for k, v in LOCATIONS.items())}.
Known objects: {', '.join(f'{k} ({v["description"]}, starts on {v["home"][0]} {v["home"][1]} spot)' for k, v in OBJECTS.items())}.
"작업대" means work_table; "1번/2번/3번 공급 테이블" (also "공급대", "보관대") mean supply_1/supply_2/supply_3;
"남쪽"/"북쪽"/"서쪽 방" tables are supply_1/supply_2/supply_3. "빨간/초록/파란 상자" are red_box/green_box/blue_box.
"원래 자리"/"제자리"/"처음 자리" of a box is its start spot; "왼쪽/가운데/오른쪽 자리" are the spots.

When you are done, reply to the person in one or two short sentences that say what the robot did
(or why it could not), entirely in the language they used (a Korean command gets a Korean reply)."""


def _schema(properties, required):
    return {'type': 'object', 'properties': properties, 'required': required, 'additionalProperties': False}


TOOLS = [
    {
        'name': 'get_world_state',
        'description': 'Where the robot is, what it is holding, where each box is (table and spot) and which '
                       'spots of each table are free, as the robot remembers it. No arguments.',
        'strict': True,
        'input_schema': _schema({}, []),
    },
    {
        'name': 'navigate_to',
        'description': 'Drive the base to a known location (arms are tucked first). '
                       'Stands about 0.65 m in front of a table, facing it.',
        'strict': True,
        'input_schema': _schema({'location': {'type': 'string', 'enum': list(LOCATIONS)}}, ['location']),
    },
    {
        'name': 'pick_object',
        'description': 'Pick up a known object at the table the robot is standing at: finds it with the camera, '
                       'lines the base up, grasps it, lifts it and backs away from the table.',
        'strict': True,
        'input_schema': _schema({'object': {'type': 'string', 'enum': list(OBJECTS)}}, ['object']),
    },
    {
        'name': 'place_object',
        'description': "Put the held object down on a free spot of the table the robot is standing at, then back "
                       "away. spot: 'left' / 'middle' / 'right' (middle only on the work table), or 'auto' for the "
                       "box's own start spot on its supply table, otherwise the first free spot.",
        'strict': True,
        'input_schema': _schema({'location': {'type': 'string', 'enum': TABLES},
                                 'spot': {'type': 'string', 'enum': ['auto'] + SPOTS}}, ['location', 'spot']),
    },
    {
        'name': 'check_table',
        'description': 'Look with the head camera at the table the robot is standing at (moving a little closer '
                       'if needed) and report which box stands on which spot. Corrects the remembered world state: '
                       'a box seen here is here, a box remembered here but not seen is marked unknown.',
        'strict': True,
        'input_schema': _schema({'location': {'type': 'string', 'enum': TABLES}}, ['location']),
    },
    {
        'name': 'set_arm_posture',
        'description': "Move both arms to a posture: 'tuck' (folded, safe for driving near tables) or "
                       "'home' (hanging down). Not allowed while holding an object.",
        'strict': True,
        'input_schema': _schema({'posture': {'type': 'string', 'enum': ['tuck', 'home']}}, ['posture']),
    },
    {
        'name': 'wait',
        'description': 'Stay still for a number of seconds (1 to 120), e.g. when the person asks to wait '
                       'between two steps.',
        'strict': True,
        'input_schema': _schema({'seconds': {'type': 'integer'}}, ['seconds']),
    },
]


class TaskExecutor:
    """Runs the tools on the robot and keeps a symbolic world state for the planner."""

    def __init__(self, skills: RobotSkills, pick_mode='classical'):
        self.s = skills
        self.pick_mode = pick_mode  # 'classical' (MoveIt grasp from the marker pose) or 'vla' (learned policy)
        self.reset()

    def reset(self):
        """Symbolic state of a freshly started (or reset) world."""
        self.robot_location = 'home'
        # box -> (location, spot): a table and spot, ('gripper', None) or ('unknown', None)
        self.where = {name: o['home'] for name, o in OBJECTS.items()}
        self.held = None

    def occupant(self, location, spot):
        return next((n for n, w in self.where.items() if w == (location, spot)), None)

    def world_state(self):
        return {
            'robot_location': self.robot_location,
            'holding': self.held,
            'objects': {n: {'location': loc, 'spot': spot, 'description': OBJECTS[n]['description']}
                        for n, (loc, spot) in self.where.items()},
            'tables': {t: {'description': LOCATIONS[t]['description'],
                           'spots': {s: self.occupant(t, s) for s in LOCATIONS[t]['spots']}} for t in TABLES},
            'locations': {n: v['description'] for n, v in LOCATIONS.items()},
        }

    def run(self, name, args):
        """Execute one tool call; returns (ok, result dict)."""
        handler = getattr(self, f'_tool_{name}', None)
        if handler is None:
            return False, {'error': f'unknown tool {name}'}
        try:
            ok, result = handler(**args)
        except Exception as e:  # a skill crashing must not kill the planner loop
            self.s.stop()
            ok, result = False, {'error': f'{type(e).__name__}: {e}'}
        if not ok and self.s.cancel_event.is_set():
            result = {'error': 'cancelled by the operator', 'cancelled': True}
        return ok, result

    def _tool_get_world_state(self):
        return True, self.world_state()

    def _tool_navigate_to(self, location):
        if location not in LOCATIONS:
            return False, {'error': f'unknown location {location}'}
        if not self.s.move_arms('tuck'):
            return False, {'error': 'could not tuck the arms before driving'}
        if not self.s.navigate(*LOCATIONS[location]['staging']):
            self.robot_location = None
            return False, {'error': f'navigation to {location} failed', 'robot_location': None}
        self.robot_location = location
        return True, {'message': f'arrived at {location}', 'robot_location': location}

    def _tool_pick_object(self, object):
        if self.held is not None:
            return False, {'error': f'already holding {self.held}; place it first'}
        location, spot = self.where[object]
        if location == 'unknown':
            return False, {'error': f'where {object} is is unknown; check_table at the tables to find it'}
        if location != self.robot_location:
            return False, {'error': f'{object} is at {location}, but the robot is at {self.robot_location}; '
                                    f'navigate there first'}
        marker = OBJECTS[object]['marker']
        # small markers flicker in and out ~0.8 m away: a recent sighting carried by odometry is enough to aim
        seen = self.s.marker_in_base(marker, samples=3, use_memory=True)
        if seen is None:
            return False, {'error': f'{object} (marker {marker}) is not visible from here'}
        # the policy was trained on the right arm only
        arm = 'right' if self.pick_mode == 'vla' else 'left' if seen[0][1] > 0 else 'right'
        if not self.s.servo_to_marker(marker, GRASP_XY[arm]):
            return False, {'error': f'could not line up with {object}'}
        if self.pick_mode == 'vla':
            picked = self.s.vla_pick(marker, f'pick up the {object.replace("_", " ")}')
        else:
            picked = self.s.pick(marker)
        # lined up, the chassis is under the table edge: back away before anything else, picked or not
        self.s.drive_straight(-0.35)
        if not picked:
            return False, {'error': f'grasping {object} failed; it is probably still on the table'}
        self.held, self.where[object] = object, ('gripper', None)
        return True, {'message': f'picked {object} from the {spot} spot of {location} with the {arm} arm',
                      'holding': object}

    def _choose_spot(self, location, spot):
        """The spot to place on: (spot, None) or (None, error message)."""
        spots = LOCATIONS[location]['spots']
        if spot == 'auto':
            home = OBJECTS[self.held]['home']
            order = ([home[1]] if home[0] == location else []) + list(spots)
            spot = next((s for s in order if self.occupant(location, s) is None), None)
            return (spot, None) if spot else (None, f'every spot on {location} is taken')
        if spot not in spots:
            return None, f'{location} has no {spot} spot (it has {", ".join(spots)})'
        taken = self.occupant(location, spot)
        return (None, f'the {spot} spot of {location} is taken by {taken}') if taken else (spot, None)

    def _tool_place_object(self, location, spot):
        if self.held is None:
            return False, {'error': 'not holding anything'}
        if location != self.robot_location:
            return False, {'error': f'the robot is at {self.robot_location}, not {location}; navigate there first'}
        spot, problem = self._choose_spot(location, spot)
        if problem:
            return False, {'error': problem}
        marker = LOCATIONS[location]['spots'][spot]['marker']
        if not self.s.servo_to_marker(marker, GRASP_XY[self.s.holding]):
            return False, {'error': f'could not line up with the {spot} spot on {location}'}
        placed = self.s.place(marker)
        self.s.drive_straight(-0.35)  # back away from the table edge, placed or not
        if not placed:
            return False, {'error': f'placing on {location} failed'}
        obj, self.held = self.held, None
        self.where[obj] = (location, spot)
        return True, {'message': f'placed {obj} on the {spot} spot of {location}', 'holding': None}

    def _look(self, location):
        """Boxes the camera sees on `location`'s spots: {box: spot}."""
        markers = {o['marker']: n for n, o in OBJECTS.items() if n != self.held}
        x, y, yaw = self.s.base_pose_in('map')
        found = {}
        for marker, p in self.s.look_for(list(markers), duration=3.0).items():
            wx = x + math.cos(yaw) * p[0] - math.sin(yaw) * p[1]
            wy = y + math.sin(yaw) * p[0] + math.cos(yaw) * p[1]
            dist, spot = min((math.hypot(wx - s['xy'][0], wy - s['xy'][1]), name)
                             for name, s in LOCATIONS[location]['spots'].items())
            if dist < SPOT_MATCH:
                found[markers[marker]] = spot
        return found

    def _tool_check_table(self, location):
        if location != self.robot_location:
            return False, {'error': f'the robot is at {self.robot_location}, not {location}; navigate there first'}
        found = self._look(location)
        expected = {n for n, w in self.where.items() if w[0] == location}
        if expected - set(found):  # the 3.75 cm box markers flicker at the staging distance: look closer
            self.s.drive_straight(0.25)
            found.update(self._look(location))
            self.s.drive_straight(-0.25)
        for name, spot in found.items():
            self.where[name] = (location, spot)
        missing = sorted(n for n, w in self.where.items() if w[0] == location and n not in found)
        for name in missing:
            self.where[name] = ('unknown', None)
        spots = {s: next((n for n, sp in found.items() if sp == s), None) for s in LOCATIONS[location]['spots']}
        result = {'location': location, 'spots': spots}
        if missing:
            result['not_found'] = missing
        return True, result

    def _tool_set_arm_posture(self, posture):
        if self.held is not None:
            return False, {'error': 'cannot change arm posture while holding an object'}
        ok = self.s.move_arms(posture)
        return ok, {'message': f'arms {posture}'} if ok else {'error': f'moving arms to {posture} failed'}

    def _tool_wait(self, seconds):
        seconds = max(1, min(120, int(seconds)))
        end = time.time() + seconds
        while time.time() < end:
            if self.s.cancel_event.is_set():
                return False, {'error': 'cancelled'}
            time.sleep(0.1)
        return True, {'message': f'waited {seconds} s'}


class TaskPlanner:
    """Claude tool-use loop over TaskExecutor."""

    def __init__(self, executor: TaskExecutor, llm=None, model=MODEL, effort='medium'):
        self.executor = executor
        if llm is None:
            import anthropic
            llm = anthropic.Anthropic()  # credentials from ANTHROPIC_API_KEY / ant profile
        self.llm = llm
        self.model = model
        self.effort = effort

    def run(self, command, on_event=lambda e: None):
        """Plan and execute one command. Returns the final reply text."""
        messages = [{'role': 'user', 'content': command}]
        on_event({'type': 'command', 'text': command})
        t0 = time.time()
        cancel = self.executor.s.cancel_event
        cancel.clear()
        usage = {'input_tokens': 0, 'output_tokens': 0}  # summed over the turns (cost of this command)

        def finish(ok, reply, **extra):
            on_event({'type': 'final', 'ok': ok, 'text': reply, 'seconds': time.time() - t0,
                      'usage': dict(usage), **extra})
            return reply

        def cancelled():
            return finish(False, '작업을 취소했습니다. 진행 중이던 동작만 마치고 멈췄어요.', cancelled=True)

        for turn in range(MAX_TURNS):
            if cancel.is_set():
                return cancelled()
            on_event({'type': 'thinking', 'turn': turn + 1})
            response = self.llm.beta.messages.create(
                model=self.model,
                max_tokens=16000,
                system=SYSTEM_PROMPT,
                tools=TOOLS,
                # robot actions are sequential: at most one tool call per turn
                tool_choice={'type': 'auto', 'disable_parallel_tool_use': True},
                output_config={'effort': self.effort},
                betas=['server-side-fallback-2026-07-01'],
                fallbacks='default',  # re-run on another model if this one declines
                messages=messages,
            )
            u = getattr(response, 'usage', None)  # ScriptedLLM has none
            if u is not None:
                usage['input_tokens'] += u.input_tokens
                usage['output_tokens'] += u.output_tokens
            if response.stop_reason == 'refusal':
                return finish(False, '모델의 안전 시스템이 이 요청을 거절했습니다.')
            messages.append({'role': 'assistant', 'content': response.content})
            for block in response.content:
                if block.type == 'text' and block.text.strip():
                    on_event({'type': 'thought' if response.stop_reason == 'tool_use' else 'reply',
                              'text': block.text.strip()})

            calls = [b for b in response.content if b.type == 'tool_use']
            if response.stop_reason != 'tool_use' or not calls:
                return finish(True, ' '.join(b.text.strip() for b in response.content if b.type == 'text').strip())

            results = []
            for call in calls:
                if cancel.is_set():
                    return cancelled()
                on_event({'type': 'tool_call', 'name': call.name, 'input': call.input})
                started = time.time()
                ok, result = self.executor.run(call.name, call.input)
                on_event({'type': 'tool_result', 'name': call.name, 'ok': ok, 'result': result,
                          'seconds': time.time() - started})
                results.append({'type': 'tool_result', 'tool_use_id': call.id,
                                'content': json.dumps(result, ensure_ascii=False), 'is_error': not ok})
            messages.append({'role': 'user', 'content': results})
            if cancel.is_set():
                return cancelled()

        return finish(False, f'계획 단계가 {MAX_TURNS}번을 넘어 작업을 끝내지 못하고 멈췄습니다.')


class ScriptedLLM:
    """Test double for the Claude client: replays a fixed tool sequence, then a final reply.

    It checks the loop and the robot side (tool execution, results, world state) when no
    API key is available. It is not a planner: it picks one of SCRIPTS by a keyword in the
    command and replays it regardless of the tool results (so it cannot follow a condition).
    """

    def __init__(self, steps=None, reply=None):
        self.steps, self.reply, self.i = (list(steps) if steps else None), reply, 0
        self.beta = types.SimpleNamespace(messages=types.SimpleNamespace(create=self._create))

    def _create(self, **kwargs):
        if self.steps is None:  # choose a script from the command on the first call
            command = kwargs['messages'][0]['content']
            key = next((k for k in SCRIPTS if k != 'default' and k in command), 'default')
            self.steps, self.reply = list(SCRIPTS[key][0]), SCRIPTS[key][1]
        if self.i < len(self.steps):
            name, args = self.steps[self.i]
            self.i += 1
            block = types.SimpleNamespace(type='tool_use', id=f'toolu_scripted_{self.i}', name=name, input=args)
            return types.SimpleNamespace(stop_reason='tool_use', content=[block])
        text = types.SimpleNamespace(type='text', text=self.reply)
        return types.SimpleNamespace(stop_reason='end_turn', content=[text])


def _move(obj, src, dst, spot='auto'):
    return [('navigate_to', {'location': src}), ('pick_object', {'object': obj}),
            ('navigate_to', {'location': dst}), ('place_object', {'location': dst, 'spot': spot})]


# Plans a planner should produce, for ScriptedLLM: keyword in the command -> (tool calls, reply).
SCRIPTS = {
    'default': ([  # "빨간 상자를 작업대로 옮겨줘"
        ('get_world_state', {}), *_move('red_box', 'supply_1', 'work_table'),
    ], '빨간 상자를 작업대로 옮겼습니다. (scripted)'),
    '원래': ([  # "빨간 상자를 원래 자리로 갖다 놔"
        ('get_world_state', {}), *_move('red_box', 'work_table', 'supply_1'),
        ('navigate_to', {'location': 'home'}),
    ], '빨간 상자를 공급 테이블에 다시 놓고 원위치로 돌아왔습니다. (scripted)'),
    '제자리': ([  # "작업대의 상자를 모두 제자리로" (after '모아'); checked before '모아'
        ('get_world_state', {}),
        *_move('red_box', 'work_table', 'supply_1'),
        *_move('green_box', 'work_table', 'supply_2'),
        *_move('blue_box', 'work_table', 'supply_3'),
        ('navigate_to', {'location': 'home'}),
    ], '세 상자를 모두 처음 자리로 돌려놓았습니다. (scripted)'),
    '모아': ([  # "상자를 모두 작업대에 모아 줘": one box at a time, left to right
        ('get_world_state', {}),
        *_move('red_box', 'supply_1', 'work_table', 'left'),
        *_move('green_box', 'supply_2', 'work_table', 'middle'),
        *_move('blue_box', 'supply_3', 'work_table', 'right'),
        ('navigate_to', {'location': 'home'}),
    ], '빨간·초록·파란 상자를 작업대의 왼쪽·가운데·오른쪽 자리에 모았습니다. (scripted)'),
    '확인': ([  # "작업대에 뭐가 있는지 가서 확인해 줘"
        ('navigate_to', {'location': 'work_table'}), ('check_table', {'location': 'work_table'}),
    ], '작업대를 카메라로 확인했습니다. (scripted)'),
}
