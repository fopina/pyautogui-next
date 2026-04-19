from __future__ import division, print_function

import os
import signal
import sys
import threading
import types
from collections import namedtuple
from queue import Queue

import pytest

# Make the cwd the tests folder so image fixtures resolve like the original suite expected.
SCRIPT_FOLDER = os.path.dirname(os.path.realpath(__file__))
os.chdir(SCRIPT_FOLDER)

GUI_TEST = pytest.mark.skipif(
    os.environ.get('PYAUTOGUI_RUN_GUI_TESTS') != '1',
    reason='GUI and interactive tests are disabled unless PYAUTOGUI_RUN_GUI_TESTS=1',
)

INPUT_TIMEOUT = float(os.environ.get('PYAUTOGUI_INPUT_TIMEOUT', '1'))


def _timed_input(prompt=''):
    if hasattr(signal, 'SIGALRM') and threading.current_thread() is threading.main_thread():

        def handle_timeout(signum, frame):
            raise TimeoutError('Timed out waiting for interactive test input after {} seconds'.format(INPUT_TIMEOUT))

        previous_handler = signal.signal(signal.SIGALRM, handle_timeout)
        signal.setitimer(signal.ITIMER_REAL, INPUT_TIMEOUT)
        try:
            return input(prompt)
        finally:
            signal.setitimer(signal.ITIMER_REAL, 0)
            signal.signal(signal.SIGALRM, previous_handler)

    result = Queue(maxsize=1)

    def reader():
        try:
            result.put((True, input(prompt)))
        except BaseException as exc:  # pragma: no cover - only exercised on input failure paths.
            result.put((False, exc))

    thread = threading.Thread(target=reader, daemon=True)
    thread.start()
    thread.join(INPUT_TIMEOUT)
    if thread.is_alive():
        raise TimeoutError('Timed out waiting for interactive test input after {} seconds'.format(INPUT_TIMEOUT))

    ok, value = result.get()
    if ok:
        return value
    raise value


INPUT_FUNC = _timed_input


class P(namedtuple('P', ['x', 'y'])):
    def __str__(self):
        return '{0},{1}'.format(self.x, self.y)

    def __repr__(self):
        return 'P({0}, {1})'.format(self.x, self.y)

    def __eq__(self, other):
        return self.x == other.x and self.y == other.y

    def __ne__(self, other):
        return self.x != other.x and self.y != other.y

    def __add__(self, other):
        return P(self.x + other.x, self.y + other.y)

    def __sub__(self, other):
        return P(self.x - other.x, self.y - other.y)

    def __mul__(self, other):
        return P(self.x * other, self.y * other)

    def __rmul__(self, other):
        return self.__mul__(other)

    def __floordiv__(self, other):
        return P(self.x // other, self.y // other)

    def __truediv__(self, other):
        return P(self.x / other, self.y / other)

    def __neg__(self):
        return P(-self.x, -self.y)

    def __pos__(self):
        return self

    def __abs__(self):
        return P(abs(self.x), abs(self.y))


def install_headless_stubs():
    if 'mouseinfo' not in sys.modules:
        stub = types.ModuleType('mouseinfo')
        stub.MouseInfoWindow = lambda *args, **kwargs: None
        sys.modules['mouseinfo'] = stub

    if HEADLESS_LINUX and 'pyautogui._pyautogui_x11' not in sys.modules:
        stub = types.ModuleType('pyautogui._pyautogui_x11')
        stub._size = lambda: (1920, 1080)
        stub._position = lambda: (0, 0)
        stub._moveTo = lambda x, y: None
        stub._dragTo = lambda x, y, button=None: None
        stub._click = lambda x, y, button='left': None
        stub._mouseDown = lambda x, y, button='left': None
        stub._mouseUp = lambda x, y, button='left': None
        stub._scroll = lambda clicks, x=None, y=None: None
        stub._hscroll = lambda clicks, x=None, y=None: None
        stub._vscroll = lambda clicks, x=None, y=None: None
        stub._keyDown = lambda key: None
        stub._keyUp = lambda key: None
        stub._mouse_is_swapped = lambda: False
        stub.keyboardMapping = {chr(i): i for i in range(32, 127)}
        sys.modules['pyautogui._pyautogui_x11'] = stub


HEADLESS_LINUX = sys.platform.startswith('linux') and not os.environ.get('DISPLAY')


def require_gui_or_skip():
    if HEADLESS_LINUX and os.environ.get('PYAUTOGUI_RUN_GUI_TESTS') != '1':
        pytest.skip('GUI tests require a real DISPLAY on Linux', allow_module_level=True)
