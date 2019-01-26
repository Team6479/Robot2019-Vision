import os
import queue
import sys
import threading

from enum import Enum


# Taken from pipenv
# see https://github.com/pypa/pipenv/blob/master/pipenv/__init__.py
ROOT = os.path.abspath(os.path.dirname(os.path.realpath(__file__)))
VENDOR = os.sep.join([ROOT, "vendor"])
PATCHED = os.sep.join([ROOT, "patched"])

# Inject vendored libraries into system path.
sys.path.insert(0, VENDOR)
# Inject patched libraries into system path.
sys.path.insert(0, PATCHED)


class Target(Enum):
    NONE = None
    BALL = "ball"
    HATCH = "hatch"
    TAPE = "tape"


class OverwritingLifoQueue(queue.LifoQueue):
    """Variant of Queue that retrieves most recently added entries first."""

    def _get(self):
        return self.queue[-1]

    def put(self, item):
        if self.full():
            try:
                self.queue.popleft()
            except Exception:
                pass
        self._put(item)


class StoppableThread(threading.Thread):
    """Thread class with a stop() method. The thread itself has to check
    regularly for the stopped() condition."""

    def __init__(self):
        super(StoppableThread, self).__init__()
        self._stop_event = threading.Event()

    def stop(self):
        self._stop_event.set()

    def stopped(self):
        return self._stop_event.is_set()
