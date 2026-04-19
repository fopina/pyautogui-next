from __future__ import division, print_function

import os
import sys
import types
from collections import namedtuple

import pytest

# Make the cwd the tests folder so image fixtures resolve like the original suite expected.
SCRIPT_FOLDER = os.path.dirname(os.path.realpath(__file__))
os.chdir(SCRIPT_FOLDER)

GUI_TEST = pytest.mark.skipif(
    os.environ.get('PYAUTOGUI_RUN_GUI_TESTS') != '1',
    reason='GUI and interactive tests are disabled unless PYAUTOGUI_RUN_GUI_TESTS=1',
)

INPUT_FUNC = input


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
