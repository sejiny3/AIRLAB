"""Natural-language task planning for UNBOLT: Claude turns a command into skill calls.

The robot's skills (navigate, pick, place, arm postures) are exposed to Claude as
tools. Claude plans, calls them one at a time, sees each result, and finally
answers the user. Execution feedback goes through an `on_event` callback so the
ROS node can publish it (dashboard, CLI).

Nothing here talks to ROS directly except through RobotSkills, so the loop can be
tested with ScriptedLLM (a stand-in that replays a fixed tool sequence) when no
API key is available.
"""

import json
import math
import time
import types

from unbolt_manipulation.skills import GRASP_XY, RobotSkills

MODEL = 'claude-opus-5-5'
MAX_TURNS = 20

# Known places: where to stand (map frame, Nav2 goal) and which marker marks the place spot.
LOCATIONS = {
    'supply_table': {'staging': (-0.15, -1.55, -math.pi / 2), 'place_marker': 5,
                     'description': 'supply table (south side of the room), light-blue top'},
    'work_table': {'staging': (1.20, 0.0, 0.0), 'place_marker': 3,
                   'description': 'work table (centre-east of the room), wooden top'},
    'home': {'staging': (0.0, 0.0, 0.0), 'place_marker': None,
             'description': 'start position in the middle of the room (no table)'},
}
OBJECTS = {
    'red_box': {'marker': 7, 'description': 'red box, 5 cm cube, 100 g', 'location': 'supply_table'},
}

SYSTEM_PROMPT = f"""You are the task planner of UNBOLT, a mobile robot with two arms (OpenArm v2) on a
wheeled base, working in a simulated room. A person gives you a command in natural language
(usually Korean). Turn it into robot actions by calling the tools, one at a time, and look at
each result before deciding the next step.

How the robot works:
- It can only pick an object or place it while standing at the table where that happens:
  navigate_to the object's location before pick_object, and to the destination before place_object.
- It carries at most one object at a time. pick_object and place_object find the object or the
  place spot with the head camera (ArUco markers) and line the base up by themselves.
- Call get_world_state first when you need to know where things are; it is cheap.
- If a tool fails, read its message. Retry a failed step once when the message suggests it could
  work again; otherwise stop and explain.
- If the command asks for something the robot cannot do (an unknown object or place, or an action
  with no tool), do not improvise: say what is possible instead.

Known locations: {', '.join(f'{k} ({v["description"]})' for k, v in LOCATIONS.items())}.
Known objects: {', '.join(f'{k} ({v["description"]})' for k, v in OBJECTS.items())}.
"작업대" means work_table; "공급 테이블"/"보관대" means supply_table; "원래 자리"/"처음 자리" of the
red box means supply_table.

When you are done, reply to the person in the language they used, in one or two short sentences
that say what the robot did (or why it could not)."""


def _schema(properties, required):
    return {'type': 'object', 'properties': properties, 'required': required, 'additionalProperties': False}


TOOLS = [
    {
        'name': 'get_world_state',
        'description': 'Where the robot is, what it is holding, and where each known object is. No arguments.',
        'strict': True,
        'input_schema': _schema({}, []),
    },
    {
        'name': 'navigate_to',
        'description': 'Drive the base to a known location (arms are tucked first). '
                       'Stands about 0.8 m in front of a table, facing it.',
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
        'description': 'Put the held object down on the place spot of the table the robot is standing at, '
                       'then back away. Only tables have place spots.',
        'strict': True,
        'input_schema': _schema({'location': {'type': 'string', 'enum': [k for k, v in LOCATIONS.items()
                                                                         if v['place_marker'] is not None]}},
                                ['location']),
    },
    {
        'name': 'set_arm_posture',
        'description': "Move both arms to a posture: 'tuck' (folded, safe for driving near tables) or "
                       "'home' (hanging down). Not allowed while holding an object.",
        'strict': True,
        'input_schema': _schema({'posture': {'type': 'string', 'enum': ['tuck', 'home']}}, ['posture']),
    },
]


class TaskExecutor:
    """Runs the tools on the robot and keeps a symbolic world state for the planner."""

    def __init__(self, skills: RobotSkills):
        self.s = skills
        self.reset()

    def reset(self):
        """Symbolic state of a freshly started (or reset) world."""
        self.robot_location = 'home'
        self.object_location = {name: o['location'] for name, o in OBJECTS.items()}
        self.held = None

    def world_state(self):
        return {
            'robot_location': self.robot_location,
            'holding': self.held,
            'objects': {n: {'location': loc, 'description': OBJECTS[n]['description']}
                        for n, loc in self.object_location.items()},
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
        if self.object_location.get(object) != self.robot_location:
            return False, {'error': f'{object} is at {self.object_location.get(object)}, '
                                    f'but the robot is at {self.robot_location}; navigate there first'}
        marker = OBJECTS[object]['marker']
        # small markers flicker in and out ~0.8 m away: a recent sighting carried by odometry is enough to aim
        seen = self.s.marker_in_base(marker, samples=3, use_memory=True)
        if seen is None:
            return False, {'error': f'{object} (marker {marker}) is not visible from here'}
        arm = 'left' if seen[0][1] > 0 else 'right'
        if not self.s.servo_to_marker(marker, GRASP_XY[arm]):
            return False, {'error': f'could not line up with {object}'}
        if not self.s.pick(marker):
            return False, {'error': f'grasping {object} failed; it is probably still on the table'}
        self.held, self.object_location[object] = object, 'gripper'
        self.s.drive_straight(-0.35)
        return True, {'message': f'picked {object} with the {arm} arm', 'holding': object}

    def _tool_place_object(self, location):
        if self.held is None:
            return False, {'error': 'not holding anything'}
        if location != self.robot_location:
            return False, {'error': f'the robot is at {self.robot_location}, not {location}; navigate there first'}
        marker = LOCATIONS[location]['place_marker']
        if not self.s.servo_to_marker(marker, GRASP_XY[self.s.holding]):
            return False, {'error': f'could not line up with the place spot on {location}'}
        if not self.s.place(marker):
            return False, {'error': f'placing on {location} failed'}
        obj, self.held = self.held, None
        self.object_location[obj] = location
        self.s.drive_straight(-0.35)
        return True, {'message': f'placed {obj} on {location}', 'holding': None}

    def _tool_set_arm_posture(self, posture):
        if self.held is not None:
            return False, {'error': 'cannot change arm posture while holding an object'}
        ok = self.s.move_arms(posture)
        return ok, {'message': f'arms {posture}'} if ok else {'error': f'moving arms to {posture} failed'}


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
    command and replays it regardless of the tool results.
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


# Plans a planner should produce, for ScriptedLLM: keyword in the command -> (tool calls, reply).
SCRIPTS = {
    'default': ([  # "빨간 상자를 작업대로 옮겨줘"
        ('get_world_state', {}),
        ('navigate_to', {'location': 'supply_table'}),
        ('pick_object', {'object': 'red_box'}),
        ('navigate_to', {'location': 'work_table'}),
        ('place_object', {'location': 'work_table'}),
    ], '빨간 상자를 작업대로 옮겼습니다. (scripted)'),
    '원래': ([  # "빨간 상자를 원래 자리로 갖다 놔"
        ('get_world_state', {}),
        ('navigate_to', {'location': 'work_table'}),
        ('pick_object', {'object': 'red_box'}),
        ('navigate_to', {'location': 'supply_table'}),
        ('place_object', {'location': 'supply_table'}),
        ('navigate_to', {'location': 'home'}),
    ], '빨간 상자를 공급 테이블에 다시 놓고 원위치로 돌아왔습니다. (scripted)'),
}
