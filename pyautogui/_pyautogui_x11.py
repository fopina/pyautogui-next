# NOTE - It is a known issue that the keyboard-related functions don't work on Ubuntu VMs in Virtualbox.

import os
import subprocess
import sys

import Xlib.XK
from Xlib import X
from Xlib.display import Display
from Xlib.ext.xtest import fake_input

import pyautogui
from pyautogui import LEFT, MIDDLE, RIGHT

BUTTON_NAME_MAPPING = {LEFT: 1, MIDDLE: 2, RIGHT: 3, 1: 1, 2: 2, 3: 3, 4: 4, 5: 5, 6: 6, 7: 7}


if sys.platform == 'java':
    raise Exception('The pyautogui_x11 module should not be loaded on Jython.')

# from pyautogui import *

"""
Much of this code is based on information gleaned from Paul Barton's PyKeyboard in PyUserInput from 2013, itself derived from Akkana Peck's pykey in 2008 ( http://www.shallowsky.com/software/crikey/pykey-0.1 ), itself derived from her "Crikey" lib.
"""


def _position():
    """Returns the current xy coordinates of the mouse cursor as a two-integer
    tuple.

    Returns:
      (x, y) tuple of the current xy coordinates of the mouse cursor.
    """
    display = _getDisplay()
    coord = display.screen().root.query_pointer()._data
    return coord['root_x'], coord['root_y']


def _size():
    display = _getDisplay()
    return display.screen().width_in_pixels, display.screen().height_in_pixels


def _vscroll(clicks, x=None, y=None):
    clicks = int(clicks)
    if clicks == 0:
        return
    elif clicks > 0:
        button = 4  # scroll up
    else:
        button = 5  # scroll down

    for i in range(abs(clicks)):
        _click(x, y, button=button)


def _hscroll(clicks, x=None, y=None):
    clicks = int(clicks)
    if clicks == 0:
        return
    elif clicks > 0:
        button = 7  # scroll right
    else:
        button = 6  # scroll left

    for i in range(abs(clicks)):
        _click(x, y, button=button)


def _scroll(clicks, x=None, y=None):
    return _vscroll(clicks, x, y)


def _click(x, y, button):
    assert button in BUTTON_NAME_MAPPING.keys(), "button argument not in ('left', 'middle', 'right', 4, 5, 6, 7)"
    button = BUTTON_NAME_MAPPING[button]

    _mouseDown(x, y, button)
    _mouseUp(x, y, button)


_mouse_is_swapped_setting = None


def _mouse_is_swapped():
    # TODO - for performance reasons, we only check the swapped mouse button
    # setting from the OS once at start up, rather than every mouse click.
    # Testing shows this takes about 0.02 seconds on my machine in a vm.
    # This may change in the future.
    global _mouse_is_swapped_setting
    if _mouse_is_swapped_setting is None:
        try:
            proc = subprocess.Popen(
                ['dconf', 'read', '/org/gnome/desktop/peripherals/mouse/left-handed'], stdout=subprocess.PIPE
            )
            stdout_bytes, stderr_bytes = proc.communicate()
            _mouse_is_swapped_setting = stdout_bytes.decode('utf-8') == 'true\n'
        except FileNotFoundError:
            # The user is not running Gnome (the default window manager on Ubuntu) so just assume it's not swapped.
            _mouse_is_swapped_setting = False
    return _mouse_is_swapped_setting


def _moveTo(x, y):
    display = _getDisplay()
    fake_input(display, X.MotionNotify, x=x, y=y)
    display.sync()


def _mouseDown(x, y, button):
    _moveTo(x, y)
    display = _getDisplay()
    assert button in BUTTON_NAME_MAPPING.keys(), "button argument not in ('left', 'middle', 'right', 4, 5, 6, 7)"
    button = BUTTON_NAME_MAPPING[button]
    fake_input(display, X.ButtonPress, button)
    display.sync()


def _mouseUp(x, y, button):
    _moveTo(x, y)
    display = _getDisplay()
    assert button in BUTTON_NAME_MAPPING.keys(), "button argument not in ('left', 'middle', 'right', 4, 5, 6, 7)"
    button = BUTTON_NAME_MAPPING[button]
    fake_input(display, X.ButtonRelease, button)
    display.sync()


def _keyDown(key):
    """Performs a keyboard key press without the release. This will put that
    key in a held down state.

    NOTE: For some reason, this does not seem to cause key repeats like would
    happen if a keyboard key was held down on a text field.

    Args:
      key (str): The key to be pressed down. The valid names are listed in
      pyautogui.KEY_NAMES.

    Returns:
      None
    """
    display = _getDisplay()
    keyboardMapping = _getKeyboardMapping()
    if key not in keyboardMapping or keyboardMapping[key] is None:
        return

    if type(key) == int:
        fake_input(display, X.KeyPress, key)
        display.sync()
        return

    needsShift = pyautogui.isShiftCharacter(key)
    if needsShift:
        fake_input(display, X.KeyPress, keyboardMapping['shift'])

    fake_input(display, X.KeyPress, keyboardMapping[key])

    if needsShift:
        fake_input(display, X.KeyRelease, keyboardMapping['shift'])
    display.sync()


def _keyUp(key):
    """Performs a keyboard key release (without the press down beforehand).

    Args:
      key (str): The key to be released up. The valid names are listed in
      pyautogui.KEY_NAMES.

    Returns:
      None
    """

    """
    Release a given character key. Also works with character keycodes as
    integers, but not keysyms.
    """
    display = _getDisplay()
    keyboardMapping = _getKeyboardMapping()
    if key not in keyboardMapping or keyboardMapping[key] is None:
        return

    if type(key) == int:
        keycode = key
    else:
        keycode = keyboardMapping[key]

    fake_input(display, X.KeyRelease, keycode)
    display.sync()


_display_name = None
_display = None
_display_override = None
_keyboardMapping = None
_keyboardMappingDisplayName = None


def _closeDisplay():
    global _display_name, _display, _keyboardMapping, _keyboardMappingDisplayName
    old_display = _display
    _display_name = None
    _display = None
    _keyboardMapping = None
    _keyboardMappingDisplayName = None

    if old_display is not None:
        try:
            old_display.close()
        except Exception:
            pass


def _setDisplayOverride(display_name):
    global _display_override
    previous_display = _display_override
    _display_override = display_name
    _closeDisplay()
    return previous_display


def _getDisplay():
    global _display_name, _display
    display_name = _display_override or os.environ['DISPLAY']
    if _display is not None and _display_name == display_name:
        return _display

    _closeDisplay()
    _display = Display(display_name)
    _display_name = display_name

    return _display


def _keycode(display, key_name):
    return display.keysym_to_keycode(Xlib.XK.string_to_keysym(key_name))


def _getKeyboardMapping():
    global _keyboardMapping, _keyboardMappingDisplayName
    display = _getDisplay()
    if _keyboardMapping is not None and _keyboardMappingDisplayName == _display_name:
        return _keyboardMapping

    # Information for keyboardMapping derived from PyKeyboard's special_key_assignment() function.
    # The *KB dictionaries in pyautogui map a string that can be passed to keyDown(),
    # keyUp(), or press() into the code used for the OS-specific keyboard function.
    # They should always be lowercase, and the same keys should be used across all OSes.
    keyboardMapping = dict([(key, None) for key in pyautogui.KEY_NAMES])
    keyboardMapping.update(
        {
            'backspace': _keycode(display, 'BackSpace'),
            '\b': _keycode(display, 'BackSpace'),
            'tab': _keycode(display, 'Tab'),
            'enter': _keycode(display, 'Return'),
            'return': _keycode(display, 'Return'),
            'shift': _keycode(display, 'Shift_L'),
            'ctrl': _keycode(display, 'Control_L'),
            'alt': _keycode(display, 'Alt_L'),
            'pause': _keycode(display, 'Pause'),
            'capslock': _keycode(display, 'Caps_Lock'),
            'esc': _keycode(display, 'Escape'),
            'escape': _keycode(display, 'Escape'),
            'pgup': _keycode(display, 'Page_Up'),
            'pgdn': _keycode(display, 'Page_Down'),
            'pageup': _keycode(display, 'Page_Up'),
            'pagedown': _keycode(display, 'Page_Down'),
            'end': _keycode(display, 'End'),
            'home': _keycode(display, 'Home'),
            'left': _keycode(display, 'Left'),
            'up': _keycode(display, 'Up'),
            'right': _keycode(display, 'Right'),
            'down': _keycode(display, 'Down'),
            'select': _keycode(display, 'Select'),
            'print': _keycode(display, 'Print'),
            'execute': _keycode(display, 'Execute'),
            'prtsc': _keycode(display, 'Print'),
            'prtscr': _keycode(display, 'Print'),
            'prntscrn': _keycode(display, 'Print'),
            'printscreen': _keycode(display, 'Print'),
            'insert': _keycode(display, 'Insert'),
            'del': _keycode(display, 'Delete'),
            'delete': _keycode(display, 'Delete'),
            'help': _keycode(display, 'Help'),
            'win': _keycode(display, 'Super_L'),
            'winleft': _keycode(display, 'Super_L'),
            'winright': _keycode(display, 'Super_R'),
            'apps': _keycode(display, 'Menu'),
            'num0': _keycode(display, 'KP_0'),
            'num1': _keycode(display, 'KP_1'),
            'num2': _keycode(display, 'KP_2'),
            'num3': _keycode(display, 'KP_3'),
            'num4': _keycode(display, 'KP_4'),
            'num5': _keycode(display, 'KP_5'),
            'num6': _keycode(display, 'KP_6'),
            'num7': _keycode(display, 'KP_7'),
            'num8': _keycode(display, 'KP_8'),
            'num9': _keycode(display, 'KP_9'),
            'multiply': _keycode(display, 'KP_Multiply'),
            'add': _keycode(display, 'KP_Add'),
            'separator': _keycode(display, 'KP_Separator'),
            'subtract': _keycode(display, 'KP_Subtract'),
            'decimal': _keycode(display, 'KP_Decimal'),
            'divide': _keycode(display, 'KP_Divide'),
            'f1': _keycode(display, 'F1'),
            'f2': _keycode(display, 'F2'),
            'f3': _keycode(display, 'F3'),
            'f4': _keycode(display, 'F4'),
            'f5': _keycode(display, 'F5'),
            'f6': _keycode(display, 'F6'),
            'f7': _keycode(display, 'F7'),
            'f8': _keycode(display, 'F8'),
            'f9': _keycode(display, 'F9'),
            'f10': _keycode(display, 'F10'),
            'f11': _keycode(display, 'F11'),
            'f12': _keycode(display, 'F12'),
            'f13': _keycode(display, 'F13'),
            'f14': _keycode(display, 'F14'),
            'f15': _keycode(display, 'F15'),
            'f16': _keycode(display, 'F16'),
            'f17': _keycode(display, 'F17'),
            'f18': _keycode(display, 'F18'),
            'f19': _keycode(display, 'F19'),
            'f20': _keycode(display, 'F20'),
            'f21': _keycode(display, 'F21'),
            'f22': _keycode(display, 'F22'),
            'f23': _keycode(display, 'F23'),
            'f24': _keycode(display, 'F24'),
            'numlock': _keycode(display, 'Num_Lock'),
            'scrolllock': _keycode(display, 'Scroll_Lock'),
            'shiftleft': _keycode(display, 'Shift_L'),
            'shiftright': _keycode(display, 'Shift_R'),
            'ctrlleft': _keycode(display, 'Control_L'),
            'ctrlright': _keycode(display, 'Control_R'),
            'altleft': _keycode(display, 'Alt_L'),
            'altright': _keycode(display, 'Alt_R'),
            # These are added because unlike a-zA-Z0-9, the single characters do not have a
            ' ': _keycode(display, 'space'),
            'space': _keycode(display, 'space'),
            '\t': _keycode(display, 'Tab'),
            '\n': _keycode(display, 'Return'),  # for some reason this needs to be cr, not lf
            '\r': _keycode(display, 'Return'),
            '\e': _keycode(display, 'Escape'),
            '!': _keycode(display, 'exclam'),
            '#': _keycode(display, 'numbersign'),
            '%': _keycode(display, 'percent'),
            '$': _keycode(display, 'dollar'),
            '&': _keycode(display, 'ampersand'),
            '"': _keycode(display, 'quotedbl'),
            "'": _keycode(display, 'apostrophe'),
            '(': _keycode(display, 'parenleft'),
            ')': _keycode(display, 'parenright'),
            '*': _keycode(display, 'asterisk'),
            '=': _keycode(display, 'equal'),
            '+': _keycode(display, 'plus'),
            ',': _keycode(display, 'comma'),
            '-': _keycode(display, 'minus'),
            '.': _keycode(display, 'period'),
            '/': _keycode(display, 'slash'),
            ':': _keycode(display, 'colon'),
            ';': _keycode(display, 'semicolon'),
            '<': _keycode(display, 'less'),
            '>': _keycode(display, 'greater'),
            '?': _keycode(display, 'question'),
            '@': _keycode(display, 'at'),
            '[': _keycode(display, 'bracketleft'),
            ']': _keycode(display, 'bracketright'),
            '\\': _keycode(display, 'backslash'),
            '^': _keycode(display, 'asciicircum'),
            '_': _keycode(display, 'underscore'),
            '`': _keycode(display, 'grave'),
            '{': _keycode(display, 'braceleft'),
            '|': _keycode(display, 'bar'),
            '}': _keycode(display, 'braceright'),
            '~': _keycode(display, 'asciitilde'),
        }
    )

    # Trading memory for time" populate winKB so we don't have to call VkKeyScanA each time.
    for c in """abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890""":
        keyboardMapping[c] = _keycode(display, c)

    _keyboardMapping = keyboardMapping
    _keyboardMappingDisplayName = _display_name
    return keyboardMapping
