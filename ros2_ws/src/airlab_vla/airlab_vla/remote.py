"""π0.5 on another machine, behind PolicyRunner's interface (used by the ROS node).

pi05/serve_pi05.py runs the model on a GPU and answers over a websocket. An answer takes longer
than a control step, and the ROS callbacks must keep running meanwhile, so a worker thread does
the talking and act() returns None until the answer is there. The arm holds its last target in
that time, which keeps the state the model was shown valid when the answer arrives: the pick
goes in short bursts, each REPLAN steps long.

The messages are openpi's: msgpack with numpy arrays as maps (openpi_client/msgpack_numpy.py).
"""

import queue
import threading
import time

import msgpack
import numpy as np
from websockets.sync.client import connect

from airlab_vla.sim import pad_square

REPLAN = 5            # steps of each 10-step chunk to play before asking again (pi05/evaluate_pi05.py)
REPLY_TIMEOUT = 15.0  # [s] the longest wait for the server


def pack_array(obj):
    if isinstance(obj, np.ndarray):
        return {b'__ndarray__': True, b'data': obj.tobytes(), b'dtype': obj.dtype.str, b'shape': obj.shape}
    return obj


def unpack_array(obj):
    if b'__ndarray__' in obj:
        return np.ndarray(buffer=obj[b'data'], dtype=np.dtype(obj[b'dtype']), shape=obj[b'shape'])
    if b'__npgeneric__' in obj:
        return np.dtype(obj[b'dtype']).type(obj[b'data'])
    return obj


def websocket_url(server):
    """https://x.trycloudflare.com -> wss://x.trycloudflare.com, localhost:8000 -> ws://localhost:8000"""
    url = server.strip().rstrip('/')
    if url.startswith('http'):
        return 'ws' + url[len('http'):]
    return url if url.startswith('ws') else f'ws://{url}'


class RemoteRunner:
    latency = None  # [s] the last round trip to the server

    def __init__(self, server, replan=REPLAN):
        self.url, self.replan = websocket_url(server), replan
        self.jobs = None

    def reset(self, instruction):
        """Start a pick with a connection of its own: a tunnel may drop an idle one between picks."""
        if self.jobs is not None:
            self.jobs.put(None)  # the last pick's worker closes its connection
        self.jobs, self.replies = queue.SimpleQueue(), queue.SimpleQueue()
        self.prompt, self.chunk, self.t, self.asked = instruction, None, 0, None
        threading.Thread(target=self._talk, args=(self.jobs, self.replies), daemon=True).start()

    def _talk(self, jobs, replies):
        try:
            with connect(self.url, compression=None, max_size=None, open_timeout=REPLY_TIMEOUT,
                         close_timeout=1) as ws:
                ws.recv(timeout=REPLY_TIMEOUT)  # the server opens with its metadata
                while (obs := jobs.get()) is not None:
                    ws.send(msgpack.packb(obs, default=pack_array))
                    replies.put(ws.recv(timeout=REPLY_TIMEOUT))
        except Exception as e:  # noqa: BLE001 - whatever went wrong, act() reports it from the node's thread
            replies.put(e)

    def act(self, head, wrist, state):
        """head (126, 224, 3) and wrist (224, 224, 3) uint8 images, state (8,) joint angles.
        Returns the joint targets for now (8,) and the done value, or None while the server
        has not answered. Raises RuntimeError if it cannot."""
        if self.chunk is None or self.t >= self.replan:
            if self.asked is None:
                self.asked = time.monotonic()
                self.jobs.put({'observation/image': pad_square(head), 'observation/wrist_image': wrist,
                               'observation/state': state, 'prompt': self.prompt})
            try:
                reply = self.replies.get_nowait()
            except queue.Empty:
                return None
            if isinstance(reply, Exception):
                raise RuntimeError(f'{type(reply).__name__}: {reply}')
            if isinstance(reply, str):  # the server sends a traceback instead of an answer
                raise RuntimeError(reply.strip().splitlines()[-1])
            self.chunk, self.t = msgpack.unpackb(reply, object_hook=unpack_array)['actions'], 0
            self.latency, self.asked = time.monotonic() - self.asked, None
        step = self.chunk[self.t]
        self.t += 1
        return step[:8], float(np.clip(step[8], 0.0, 1.0))
