from __future__ import division, print_function

import sys
import threading
import time
import unittest

from test_common import GUI_TEST, INPUT_FUNC, P, require_gui_or_skip

import pyautogui

require_gui_or_skip()


@GUI_TEST
class TestGeneral(unittest.TestCase):
    def setUp(self):
        self.oldFailsafeSetting = pyautogui.FAILSAFE
        pyautogui.FAILSAFE = False
        pyautogui.moveTo(42, 42)
        pyautogui.FAILSAFE = True

    def tearDown(self):
        pyautogui.FAILSAFE = self.oldFailsafeSetting

    def test_accessibleNames(self):
        pyautogui.moveTo
        pyautogui.moveRel
        pyautogui.dragTo
        pyautogui.dragRel
        pyautogui.mouseDown
        pyautogui.mouseUp
        pyautogui.click
        pyautogui.rightClick
        pyautogui.doubleClick
        pyautogui.tripleClick
        pyautogui.typewrite
        pyautogui.hotkey
        pyautogui.keyDown
        pyautogui.keyUp
        pyautogui.press
        pyautogui.hold
        pyautogui.position
        pyautogui.size
        pyautogui.scroll
        pyautogui.hscroll
        pyautogui.vscroll
        pyautogui.KEYBOARD_KEYS
        pyautogui.isShiftCharacter
        pyautogui.locateAll
        pyautogui.locate
        pyautogui.locateOnScreen
        pyautogui.locateAllOnScreen
        pyautogui.locateCenterOnScreen
        pyautogui.center
        pyautogui.pixelMatchesColor
        pyautogui.pixel
        pyautogui.screenshot
        pyautogui.getPointOnLine
        pyautogui.linear
        pyautogui.easeInQuad
        pyautogui.easeOutQuad
        pyautogui.easeInOutQuad
        pyautogui.easeInCubic
        pyautogui.easeOutCubic
        pyautogui.easeInOutCubic
        pyautogui.easeInQuart
        pyautogui.easeOutQuart
        pyautogui.easeInOutQuart
        pyautogui.easeInQuint
        pyautogui.easeOutQuint
        pyautogui.easeInOutQuint
        pyautogui.easeInSine
        pyautogui.easeOutSine
        pyautogui.easeInOutSine
        pyautogui.easeInExpo
        pyautogui.easeOutExpo
        pyautogui.easeInOutExpo
        pyautogui.easeInCirc
        pyautogui.easeOutCirc
        pyautogui.easeInOutCirc
        pyautogui.easeInElastic
        pyautogui.easeOutElastic
        pyautogui.easeInOutElastic
        pyautogui.easeInBack
        pyautogui.easeOutBack
        pyautogui.easeInOutBack
        pyautogui.easeInBounce
        pyautogui.easeOutBounce
        pyautogui.easeInOutBounce

    def test_size(self):
        width, height = pyautogui.size()
        self.assertTrue(isinstance(width, int), 'Type of width is %s' % (type(width)))
        self.assertTrue(isinstance(height, int), 'Type of height is %s' % (type(height)))
        self.assertTrue(width > 0, 'Width is set to %s' % (width))
        self.assertTrue(height > 0, 'Height is set to %s' % (height))

    def test_position(self):
        mousex, mousey = pyautogui.position()
        self.assertTrue(isinstance(mousex, int), 'Type of mousex is %s' % (type(mousex)))
        self.assertTrue(isinstance(mousey, int), 'Type of mousey is %s' % (type(mousey)))
        pyautogui.moveTo(mousex + 1, mousey + 1)
        x, y = pyautogui.position(mousex, None)
        self.assertEqual(x, mousex)
        self.assertNotEqual(y, mousey)
        x, y = pyautogui.position(None, mousey)
        self.assertNotEqual(x, mousex)
        self.assertEqual(y, mousey)

    def test_onScreen(self):
        zero = P(0, 0)
        xone = P(1, 0)
        yone = P(0, 1)
        size = P(*pyautogui.size())
        half = size / 2
        on_screen = [zero, zero + xone, zero + yone, zero + xone + yone, half, size - xone - yone]
        off_screen = [zero - xone, zero - yone, zero - xone - yone, size - xone, size - yone, size]
        for value, coords in [(True, on_screen), (False, off_screen)]:
            for coord in coords:
                self.assertEqual(value, pyautogui.onScreen(*coord))
                self.assertEqual(value, pyautogui.onScreen(list(coord)))
                self.assertEqual(value, pyautogui.onScreen(tuple(coord)))
                self.assertEqual(value, pyautogui.onScreen(coord))
        with self.assertRaises(pyautogui.PyAutoGUIException):
            pyautogui.onScreen([0, 0], 0)
        with self.assertRaises(pyautogui.PyAutoGUIException):
            pyautogui.onScreen((0, 0), 0)

    def test_pause(self):
        old_value = pyautogui.PAUSE
        start_time = time.time()
        pyautogui.PAUSE = 0.35
        pyautogui.moveTo(1, 1)
        pyautogui.moveRel(0, 1)
        pyautogui.moveTo(1, 1)
        elapsed = time.time() - start_time
        self.assertTrue(1.0 < elapsed < 1.1, 'Took %s seconds, expected 1.0 < 1.1 seconds.' % (elapsed))
        pyautogui.PAUSE = old_value


@GUI_TEST
class TestMouse(unittest.TestCase):
    TWEENS = [
        'linear',
        'easeInElastic',
        'easeOutElastic',
        'easeInOutElastic',
        'easeInBack',
        'easeOutBack',
        'easeInOutBack',
    ]

    def setUp(self):
        self.oldFailsafeSetting = pyautogui.FAILSAFE
        self.center = P(*pyautogui.size()) // 2
        pyautogui.FAILSAFE = False
        pyautogui.moveTo(*self.center)
        pyautogui.FAILSAFE = True

    def tearDown(self):
        pyautogui.FAILSAFE = self.oldFailsafeSetting

    def test_moveTo(self):
        desired = self.center
        pyautogui.moveTo(*desired)
        self.assertEqual(P(*pyautogui.position()), desired)
        pyautogui.moveTo(None, None)
        self.assertEqual(P(*pyautogui.position()), desired)
        desired += P(42, 42)
        pyautogui.moveTo(*desired)
        self.assertEqual(P(*pyautogui.position()), desired)
        desired -= P(42, 42)
        pyautogui.moveTo(desired.x, desired.y, duration=0.2)
        self.assertEqual(P(*pyautogui.position()), desired)
        desired += P(42, 42)
        pyautogui.moveTo(list(desired))
        self.assertEqual(P(*pyautogui.position()), desired)
        desired += P(42, 42)
        pyautogui.moveTo(tuple(desired))
        self.assertEqual(P(*pyautogui.position()), desired)
        desired -= P(42, 42)
        pyautogui.moveTo(desired)
        self.assertEqual(P(*pyautogui.position()), desired)

    def test_moveToWithTween(self):
        origin = self.center - P(100, 100)
        destination = self.center + P(100, 100)

        def reset_mouse():
            pyautogui.moveTo(*origin)
            self.assertEqual(P(*pyautogui.position()), origin)

        for tween_name in self.TWEENS:
            tween_func = getattr(pyautogui, tween_name)
            reset_mouse()
            pyautogui.moveTo(destination.x, destination.y, duration=pyautogui.MINIMUM_DURATION * 2, tween=tween_func)
            self.assertEqual(P(*pyautogui.position()), destination)

    def test_moveRel(self):
        desired = self.center
        pyautogui.moveTo(*desired)
        self.assertEqual(P(*pyautogui.position()), desired)
        desired += P(42, 42)
        pyautogui.moveRel(42, 42)
        self.assertEqual(P(*pyautogui.position()), desired)
        desired -= P(42, 42)
        pyautogui.moveRel(-42, -42)
        self.assertEqual(P(*pyautogui.position()), desired)
        desired += P(42, 0)
        pyautogui.moveRel(42, 0)
        self.assertEqual(P(*pyautogui.position()), desired)
        desired += P(0, 42)
        pyautogui.moveRel(0, 42)
        self.assertEqual(P(*pyautogui.position()), desired)
        desired += P(-42, 0)
        pyautogui.moveRel(-42, 0)
        self.assertEqual(P(*pyautogui.position()), desired)
        desired += P(0, -42)
        pyautogui.moveRel(0, -42)
        self.assertEqual(P(*pyautogui.position()), desired)
        desired += P(42, 42)
        pyautogui.moveRel([42, 42])
        self.assertEqual(P(*pyautogui.position()), desired)
        desired -= P(42, 42)
        pyautogui.moveRel((-42, -42))
        self.assertEqual(P(*pyautogui.position()), desired)
        desired += P(42, 42)
        pyautogui.moveRel(P(42, 42))
        self.assertEqual(P(*pyautogui.position()), desired)

    def test_moveRelWithTween(self):
        origin = self.center - P(100, 100)
        delta = P(200, 200)
        destination = origin + delta

        def reset_mouse():
            pyautogui.moveTo(*origin)
            self.assertEqual(P(*pyautogui.position()), origin)

        for tween_name in self.TWEENS:
            tween_func = getattr(pyautogui, tween_name)
            reset_mouse()
            pyautogui.moveRel(delta.x, delta.y, duration=pyautogui.MINIMUM_DURATION * 2, tween=tween_func)
            self.assertEqual(P(*pyautogui.position()), destination)

    def test_scroll(self):
        pyautogui.scroll(1)
        pyautogui.scroll(-1)
        pyautogui.hscroll(1)
        pyautogui.hscroll(-1)
        pyautogui.vscroll(1)
        pyautogui.vscroll(-1)

    def test_mouse_button_swap(self):
        pass


class TypewriteThread(threading.Thread):
    def __init__(self, msg, interval=0.0):
        super().__init__(daemon=True)
        self.msg = msg
        self.interval = interval

    def run(self):
        time.sleep(0.25)
        pyautogui.typewrite(self.msg, self.interval)


class PressThread(threading.Thread):
    def __init__(self, keys_arg):
        super().__init__(daemon=True)
        self.keysArg = keys_arg

    def run(self):
        time.sleep(0.25)
        pyautogui.press(self.keysArg)


class HoldThread(threading.Thread):
    def __init__(self, hold_keys_arg, press_keys_arg=None):
        super().__init__(daemon=True)
        self.holdKeysArg = hold_keys_arg
        self.pressKeysArg = press_keys_arg

    def run(self):
        time.sleep(0.25)
        with pyautogui.hold(self.holdKeysArg):
            if self.pressKeysArg is not None:
                pyautogui.press(self.pressKeysArg)


@GUI_TEST
class TestKeyboard(unittest.TestCase):
    def setUp(self):
        self.oldFailsafeSetting = pyautogui.FAILSAFE
        pyautogui.FAILSAFE = False
        pyautogui.moveTo(42, 42)
        pyautogui.FAILSAFE = True

    def tearDown(self):
        pyautogui.FAILSAFE = self.oldFailsafeSetting

    def test_typewrite(self):
        t = TypewriteThread('Hello world!\n')
        t.start()
        response = INPUT_FUNC()
        self.assertEqual(response, 'Hello world!')

        t = TypewriteThread(list('Hello world!\n'))
        t.start()
        response = INPUT_FUNC()
        self.assertEqual(response, 'Hello world!')

        all_keys = ''.join(chr(c) for c in range(32, 127))
        t = TypewriteThread(all_keys + '\n')
        t.start()
        response = INPUT_FUNC()
        self.assertEqual(response, all_keys)

    def checkForValidCharacters(self, msg):
        for c in msg:
            self.assertTrue(pyautogui.isValidKey(c), '"%c" is not a valid key on platform %s' % (c, sys.platform))

    def test_typewrite_slow(self):
        t = TypewriteThread('Hello world!\n', 0.1)
        start_time = time.time()
        t.start()
        response = INPUT_FUNC()
        self.assertEqual(response, 'Hello world!')
        elapsed = time.time() - start_time
        self.assertTrue(1.0 < elapsed < 2.0, 'Took %s seconds, expected 1.0 < x 2.0 seconds.' % (elapsed))

    def test_typewrite_editable(self):
        t = TypewriteThread(['a', 'b', 'c', '\b', 'backspace', 'x', 'y', 'z', '\n'])
        t.start()
        response = INPUT_FUNC()
        self.assertEqual(response, 'axyz')

        if sys.platform != 'darwin':
            t = TypewriteThread(['a', 'b', 'c', 'left', 'left', 'right', 'x', '\n'])
            t.start()
            response = INPUT_FUNC()
            self.assertEqual(response, 'abxc')

        t = TypewriteThread(['a', 'b', 'c', 'left', 'left', 'left', 'del', 'delete', '\n'])
        t.start()
        response = INPUT_FUNC()
        self.assertEqual(response, 'c')

        t = TypewriteThread(['a', 'b', 'c', 'home', 'x', 'end', 'z', '\n'])
        t.start()
        response = INPUT_FUNC()
        self.assertEqual(response, 'xabcz')

    def test_press(self):
        t = PressThread('enter')
        t.start()
        response = INPUT_FUNC()
        self.assertEqual(response, '')

        t = PressThread(['a', 'enter'])
        t.start()
        response = INPUT_FUNC()
        self.assertEqual(response, 'a')

        t = PressThread(['a', 'left', 'b', 'enter'])
        t.start()
        response = INPUT_FUNC()
        self.assertEqual(response, 'ba')

    def test_hold(self):
        t = HoldThread('enter')
        t.start()
        response = INPUT_FUNC()
        self.assertEqual(response, '')

        t = HoldThread(['a', 'enter'])
        t.start()
        response = INPUT_FUNC()
        self.assertEqual(response, 'a')

        t = HoldThread(['a', 'left', 'b', 'enter'])
        t.start()
        response = INPUT_FUNC()
        self.assertEqual(response, 'ba')

    def test_press_during_hold(self):
        t = HoldThread('shift', 'enter')
        t.start()
        response = INPUT_FUNC()
        self.assertEqual(response, '')

        t = HoldThread('shift', ['a', 'enter'])
        t.start()
        response = INPUT_FUNC()
        self.assertEqual(response, 'A')

        t = HoldThread('shift', ['a', 'b', 'enter'])
        t.start()
        response = INPUT_FUNC()
        self.assertEqual(response, 'AB')

    def test_typewrite_space(self):
        t = TypewriteThread(['space', ' ', '\n'])
        t.start()
        response = INPUT_FUNC()
        self.assertEqual(response, '  ')

    def test_isShiftCharacter(self):
        for char in 'ABCDEFGHIJKLMNOPQRSTUVWXYZ' + '~!@#$%^&*()_+{}|:"<>?':
            self.assertTrue(pyautogui.isShiftCharacter(char))
        for char in 'abcdefghijklmnopqrstuvwxyz' + " `1234567890-=,./;'[]\\":
            self.assertFalse(pyautogui.isShiftCharacter(char))


@GUI_TEST
class TestFailSafe(unittest.TestCase):
    def test_failsafe(self):
        self.oldFailsafeSetting = pyautogui.FAILSAFE
        pyautogui.moveTo(1, 1)
        for x, y in pyautogui.FAILSAFE_POINTS:
            pyautogui.FAILSAFE = True
            pyautogui.moveTo(x, y)
            pyautogui.FAILSAFE = False
            pyautogui.moveTo(1, 1)

        pyautogui.moveTo(1, 1)
        for x, y in pyautogui.FAILSAFE_POINTS:
            pyautogui.FAILSAFE = True
            pyautogui.moveTo(x, y)
            self.assertRaises(pyautogui.FailSafeException, pyautogui.press, 'esc')
            pyautogui.FAILSAFE = False
            pyautogui.moveTo(1, 1)

        for x, y in pyautogui.FAILSAFE_POINTS:
            pyautogui.FAILSAFE = False
            pyautogui.moveTo(x, y)
            pyautogui.press('esc')

        pyautogui.FAILSAFE = self.oldFailsafeSetting


@GUI_TEST
class TestPyScreezeFunctions(unittest.TestCase):
    def test_locateFunctions(self):
        pyautogui.useImageNotFoundException()
        with self.assertRaises(pyautogui.ImageNotFoundException):
            pyautogui.locate('100x100blueimage.png', '100x100redimage.png')
        with self.assertRaises(pyautogui.ImageNotFoundException):
            pyautogui.locateOnScreen('100x100blueimage.png')
        with self.assertRaises(pyautogui.ImageNotFoundException):
            pyautogui.locateCenterOnScreen('100x100blueimage.png')

        pyautogui.useImageNotFoundException(False)
        self.assertEqual(pyautogui.locate('100x100blueimage.png', '100x100redimage.png'), None)
        self.assertEqual(pyautogui.locateOnScreen('100x100blueimage.png'), None)
        self.assertEqual(pyautogui.locateCenterOnScreen('100x100blueimage.png'), None)
