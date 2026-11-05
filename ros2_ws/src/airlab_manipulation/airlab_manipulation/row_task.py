"""The 'row' task in the full stack: three boxes side by side, the learned policy picks by the sentence.

The bridge lays red, green and blue box side by side on the work table in a random order
(box_layout:=row). Every command is then run the same way, without the LLM planner:

  1. drive to the work table (Nav2), if the robot is not there yet
  2. line up with the MIDDLE box of the row (its ArUco marker), whatever colour it is, so that it
     sits at (GRASP_XY right x, ROW_Y) in the base frame, as in the training scenes
     (airlab_vla.sim.reset_row). The markers only place the robot; they never say which box to take.
  3. the command sentence goes to the policy as it is (vla_pick), and the policy alone decides
     which box to reach for from the camera images
  4. back away, and report which box was lifted (simulator ground truth)
  5. put the boxes back in a row, in a new random order (bridge relay_row), for the next command

Which box the sentence meant is not known here (no LLM reads it), so the report only says what
was lifted; the person who typed the sentence judges it.
"""

import math
import threading
import time

from geometry_msgs.msg import PoseStamped
from std_srvs.srv import Trigger

from airlab_manipulation.skills import GRASP_XY
from airlab_manipulation.task_planner_core import LOCATIONS, OBJECTS, TaskExecutor

ROW_TABLE = 'work_table'
ROW_Y = -0.08         # middle box at this base y when lined up (airlab_vla.sim.ROW_Y)
ROW_GAP = 0.10        # box spacing (mujoco_bridge ROW_GAP)
LIFTED_Z = 0.705      # a box centre above this is off the table (airlab_vla.sim lifted(): 3 cm up)
SLOTS = ('left', 'middle', 'right')
MARKER_BOX = {o['marker']: name for name, o in OBJECTS.items()}
COLOUR_KO = {'red_box': '빨간', 'green_box': '초록', 'blue_box': '파란'}
SLOT_KO = {'left': '왼쪽', 'middle': '가운데', 'right': '오른쪽'}


def _row_slots():
    """Slot centres (world x, y): the middle on the work table's middle pad, the others ROW_GAP to
    the robot's left and right as it faces the table (+y and -y there)."""
    mid = LOCATIONS[ROW_TABLE]['spots']['middle']['xy']
    return {'left': (mid[0], mid[1] + ROW_GAP), 'middle': mid, 'right': (mid[0], mid[1] - ROW_GAP)}


class RowExecutor(TaskExecutor):
    """The world state comes from the simulator's ground truth: the boxes move only by the policy
    and by the bridge re-laying them."""

    def __init__(self, skills, pick_mode):
        self.truth = {}  # box -> (x, y, z) in the world frame
        self.truth_lock = threading.Lock()
        for name in OBJECTS:
            skills.node.create_subscription(PoseStamped, f'/ground_truth/{name}',
                                            lambda m, n=name: self._on_truth(n, m), 10)
        self.relay = skills.node.create_client(Trigger, '/mujoco_bridge/relay_row')
        self.slot_xy = _row_slots()
        super().__init__(skills, pick_mode)

    def _on_truth(self, name, msg):
        p = msg.pose.position
        with self.truth_lock:
            self.truth[name] = (p.x, p.y, p.z)

    def _truth(self):
        with self.truth_lock:
            return dict(self.truth)

    def slots_now(self):
        """{box: slot} of the boxes resting near a slot (within half a gap)."""
        found = {}
        for name, (x, y, z) in self._truth().items():
            if z > LIFTED_Z:
                continue
            d, slot = min((math.hypot(x - sx, y - sy), s) for s, (sx, sy) in self.slot_xy.items())
            if d < ROW_GAP / 2:
                found[name] = slot
        return found

    def reset(self):
        super().reset()
        self.refresh()

    def refresh(self):
        slots = self.slots_now()
        for name in OBJECTS:
            if name == self.held:
                self.where[name] = ('gripper', None)
            elif name in slots:
                self.where[name] = (ROW_TABLE, slots[name])
            else:
                self.where[name] = ('unknown', None)

    def world_state(self):
        self.refresh()
        return super().world_state()

    # ------------------------------------------------------------------ steps
    def line_up_row(self):
        """Stand so that the middle box of the row is where the policy expects it."""
        found = self.s.look_for(list(MARKER_BOX), duration=3.0)
        if len(found) < 3:  # the 3.75 cm box markers flicker at the staging distance: look closer
            self.s.drive_straight(0.25)
            found = self.s.look_for(list(MARKER_BOX), duration=3.0)
        if len(found) < 3:
            seen = ', '.join(MARKER_BOX[m] for m in found) or 'none'
            return False, {'error': f'need all three box markers to find the middle of the row; saw {seen}'}
        order = sorted(found, key=lambda m: -found[m][1])  # robot's left (+y) first
        middle = order[1]
        if not self.s.servo_to_marker(middle, (GRASP_XY['right'][0], ROW_Y)):
            return False, {'error': 'could not line up with the middle of the row'}
        boxes = [MARKER_BOX[m] for m in order]
        return True, {'message': '줄 가운데에 정렬 (왼쪽부터 ' + ' · '.join(COLOUR_KO[b] for b in boxes) + ')',
                      'order': boxes}

    def policy_pick(self, instruction):
        before = self.slots_now()
        picked = self.s.vla_pick(None, instruction)
        self.s.drive_straight(-0.35)  # lined up, the chassis is under the table edge
        time.sleep(0.5)
        up = [n for n, (x, y, z) in self._truth().items() if z > LIFTED_Z]
        result = {'instruction': instruction, 'policy_ok': picked,
                  'lifted': up[0] if len(up) == 1 else None,
                  'slot': before.get(up[0]) if len(up) == 1 else None}
        if len(up) == 1:
            self.held = up[0]
            where = SLOT_KO.get(result['slot'])
            result['message'] = f'{where + "의 " if where else ""}{COLOUR_KO[up[0]]} 상자를 들었습니다'
            return True, result
        if up:
            result['error'] = '상자 여러 개가 함께 들렸습니다: ' + ', '.join(COLOUR_KO[n] for n in up)
        else:
            reason = (self.s.vla_result or {}).get('reason', '')
            result['error'] = '아무 상자도 들지 못했습니다' + (f' ({reason})' if reason else '')
        return False, result

    def relay_row(self):
        if not self.relay.wait_for_service(timeout_sec=5.0):
            return False, {'error': '/mujoco_bridge/relay_row is not available (box_layout:=row?)'}
        res = self.s._wait(self.relay.call_async(Trigger.Request()), 10.0)
        if res is None or not res.success:
            return False, {'error': 'the simulator did not re-lay the boxes'}
        # whatever was in the hand is back on the table now
        self.s.holding = None
        self.s.held_marker = None
        for m in MARKER_BOX:
            self.s.forget_marker(m)
        self.held = None
        time.sleep(1.0)  # the bridge applies it on its next cycle, ground truth follows
        order = res.message.split(',')
        self.refresh()
        return True, {'message': '상자를 다시 한 줄로 놓았습니다 (왼쪽부터 ' + ' · '.join(COLOUR_KO[b] for b in order) + ')',
                      'order': order}


class RowPlanner:
    """Stands in for TaskPlanner in the row modes: a fixed sequence, the sentence goes to the policy
    unchanged. Emits the same events, so the dashboard timeline works as in the task mode."""

    model = 'none'

    def __init__(self, executor: RowExecutor):
        self.executor = executor

    def run(self, command, on_event=lambda e: None):
        ex, cancel = self.executor, self.executor.s.cancel_event
        cancel.clear()
        t0 = time.time()
        on_event({'type': 'command', 'text': command})

        def step(name, args, fn):
            on_event({'type': 'tool_call', 'name': name, 'input': args})
            started = time.time()
            try:
                ok, result = fn()
            except Exception as e:  # a skill crashing must not kill the node
                ex.s.stop()
                ok, result = False, {'error': f'{type(e).__name__}: {e}'}
            if not ok and cancel.is_set():
                result = {'error': 'cancelled by the operator', 'cancelled': True}
            on_event({'type': 'tool_result', 'name': name, 'ok': ok, 'result': result,
                      'seconds': time.time() - started})
            return ok, result

        def finish(ok, text, **extra):
            on_event({'type': 'final', 'ok': ok, 'text': text, 'seconds': time.time() - t0, **extra})
            return text

        if ex.robot_location != ROW_TABLE:
            ok, r = step('navigate_to', {'location': ROW_TABLE}, lambda: ex._tool_navigate_to(ROW_TABLE))
            if not ok:
                return finish(False, '작업대로 가지 못했습니다.', cancelled=bool(r.get('cancelled')))
        ok, r = step('line_up_row', {}, ex.line_up_row)
        if not ok:
            if ex.s.cancel_event.is_set():
                return finish(False, '작업을 취소했습니다.', cancelled=True)
            return finish(False, '상자 줄 앞에 정렬하지 못했습니다: ' + r.get('error', ''))
        ok, picked = step('policy_pick', {'instruction': command}, lambda: ex.policy_pick(command))
        if ex.s.cancel_event.is_set():
            return finish(False, '작업을 취소했습니다.', cancelled=True)
        ok2, relaid = step('relay_row', {}, ex.relay_row)
        text = picked.get('message') or picked.get('error', '')
        if ok2:
            text += '. ' + relaid['message'] + '.'
        return finish(ok, text, lifted=picked.get('lifted'), slot=picked.get('slot'))
