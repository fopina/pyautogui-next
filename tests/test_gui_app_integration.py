from __future__ import division, print_function

import json
import os
import queue
import subprocess
import sys
import tempfile
import threading
import time
import unittest

import pytest
from test_common import GUI_TEST, SCRIPT_FOLDER, require_gui_or_skip

import pyautogui

require_gui_or_skip()


APP_PROJECT_PATH = os.path.join(SCRIPT_FOLDER, 'gui_test_app')
DEFAULT_APP_PYTHON = '3.12'
APP_PYTHON = os.environ.get('PYAUTOGUI_GUI_TEST_APP_PYTHON', DEFAULT_APP_PYTHON)
REPO_ROOT = os.path.dirname(SCRIPT_FOLDER)
READY_TIMEOUT = int(os.environ.get('PYAUTOGUI_GUI_TEST_READY_TIMEOUT', '60'))
SNAPSHOT_TIMEOUT = 5
TYPE_TIMEOUT = 5
LOCATE_TIMEOUT = 5
LOCATE_CENTER_TOLERANCE = 10
LOCATE_BUTTON_IMAGES = {
    'darwin': os.path.join(SCRIPT_FOLDER, 'click-target-button-darwin.png'),
    'linux': os.path.join(SCRIPT_FOLDER, 'click-target-button-linux.png'),
    'linux-docker': os.path.join(SCRIPT_FOLDER, 'click-target-button-linux-docker.png'),
    'win32': os.path.join(SCRIPT_FOLDER, 'click-target-button-windows.png'),
}
LOCATE_BUTTON_FALLBACK_IMAGE = LOCATE_BUTTON_IMAGES['darwin']
LOCATE_SCREENSHOT_DIR = os.environ.get(
    'PYAUTOGUI_LOCATE_SCREENSHOT_DIR',
    os.path.join(REPO_ROOT, 'artifacts', 'gui-test-screenshots'),
)


class GuiTestAppProcess:
    def __enter__(self):
        self.tmpdir = tempfile.TemporaryDirectory()
        ready_file = os.path.join(self.tmpdir.name, 'ready.json')
        self.process = subprocess.Popen(
            [
                'uvx',
                '--refresh',
                '--python',
                APP_PYTHON,
                '--from',
                APP_PROJECT_PATH,
                'gui-test-app',
                '--ready-file',
                ready_file,
            ],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
        )
        self.stdout = _start_reader(self.process.stdout)
        self.ready = _read_ready_file(ready_file, self.process)
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        try:
            if self.process.poll() is None:
                _write_command(self.process, 'quit')
                try:
                    self.process.wait(timeout=2)
                except subprocess.TimeoutExpired:
                    self.process.terminate()
                    self.process.wait(timeout=2)
        finally:
            self.tmpdir.cleanup()


def _read_lines(stream, output):
    for line in stream:
        output.put(line)


def _start_reader(stream):
    output = queue.Queue()
    thread = threading.Thread(target=_read_lines, args=(stream, output), daemon=True)
    thread.start()
    return output


def _read_json_event(output, event_name, timeout):
    deadline = time.time() + timeout
    last_payload = None
    while time.time() < deadline:
        try:
            line = output.get(timeout=0.05)
        except queue.Empty:
            continue
        try:
            payload = json.loads(line)
        except ValueError:
            continue
        last_payload = payload
        if payload.get('event') == event_name:
            return payload
    raise AssertionError('Timed out waiting for {0!r} event. Last payload: {1!r}'.format(event_name, last_payload))


def _read_ready_file(path, process):
    deadline = time.time() + READY_TIMEOUT
    while time.time() < deadline:
        if os.path.exists(path):
            with open(path) as ready_file:
                return json.load(ready_file)
        returncode = process.poll()
        if returncode is not None:
            stderr = process.stderr.read()
            if returncode == 2:
                pytest.skip('GUI test app could not start: {0}'.format(stderr.strip()))
            raise AssertionError('GUI test app exited with {0}: {1}'.format(returncode, stderr.strip()))
        time.sleep(0.05)
    raise AssertionError('Timed out waiting for GUI test app ready file: {0}'.format(path))


def _write_command(process, command):
    process.stdin.write('{0}\n'.format(command))
    process.stdin.flush()


def _wait_for_text(process, stdout, expected):
    deadline = time.time() + TYPE_TIMEOUT
    last_text = None
    while time.time() < deadline:
        _write_command(process, 'snapshot')
        snapshot = _read_json_event(stdout, 'snapshot', SNAPSHOT_TIMEOUT)
        last_text = snapshot['state']['text']
        if last_text == expected:
            return snapshot
        time.sleep(0.1)
    raise AssertionError('Timed out waiting for input text {0!r}. Last text: {1!r}'.format(expected, last_text))


def _wait_for_located_center(image_path):
    deadline = time.time() + LOCATE_TIMEOUT
    last_error = None
    while time.time() < deadline:
        try:
            center = pyautogui.locateCenterOnScreen(image_path)
        except pyautogui.ImageNotFoundException as exc:
            last_error = exc
            center = None
        if center is not None:
            return center
        time.sleep(0.1)
    _raise_with_locate_debug_screenshot(
        AssertionError('Timed out locating image on screen: {0}. Last error: {1!r}'.format(image_path, last_error))
    )


def _save_locate_debug_screenshot():
    os.makedirs(LOCATE_SCREENSHOT_DIR, exist_ok=True)
    timestamp = time.strftime('%Y%m%d-%H%M%S')
    path = os.path.join(LOCATE_SCREENSHOT_DIR, 'locate-button-image-{0}.png'.format(timestamp))
    pyautogui.screenshot().save(path)
    return path


def _raise_with_locate_debug_screenshot(error):
    try:
        screenshot_path = _save_locate_debug_screenshot()
    except Exception as screenshot_error:
        raise AssertionError(
            '{0}\nUnable to save locate debug screenshot: {1!r}'.format(error, screenshot_error)
        ) from error
    raise AssertionError('{0}\nLocate debug screenshot: {1}'.format(error, screenshot_path)) from error


def _locate_button_image_path():
    image_name = os.environ.get('PYAUTOGUI_LOCATE_BUTTON_IMAGE', sys.platform)
    image_path = LOCATE_BUTTON_IMAGES.get(image_name)
    if image_path is None or not os.path.exists(image_path):
        image_path = LOCATE_BUTTON_FALLBACK_IMAGE
    if not os.path.exists(image_path):
        pytest.skip('Missing locate-button screenshot fixture: {0}'.format(image_path))
    return image_path


@GUI_TEST
class TestGuiAppIntegration(unittest.TestCase):
    def setUp(self):
        self.old_failsafe_setting = pyautogui.FAILSAFE
        pyautogui.FAILSAFE = False

    def tearDown(self):
        pyautogui.FAILSAFE = self.old_failsafe_setting

    def test_gui_app_uses_expected_python_version(self):
        with GuiTestAppProcess() as app:
            self.assertTrue(
                app.ready['python_version'].startswith('3.12'),
                'GUI test app used Python {0}, expected {1}.x'.format(app.ready['python_version'], '3.12'),
            )

    def test_type_hello_world_in_input_text(self):
        with GuiTestAppProcess() as app:
            text_input = app.ready['widgets']['text_input']
            pyautogui.click(text_input['center_x'], text_input['center_y'])
            time.sleep(0.25)
            pyautogui.typewrite('hello world', interval=0.01)

            snapshot = _wait_for_text(app.process, app.stdout, 'hello world')

            self.assertEqual(snapshot['state']['text'], 'hello world')

    def test_click_button_increments_click_count(self):
        with GuiTestAppProcess() as app:
            click_target = app.ready['widgets']['click_target']
            pyautogui.click(click_target['center_x'], click_target['center_y'])

            event = _read_json_event(app.stdout, 'button_command', SNAPSHOT_TIMEOUT)

            self.assertEqual(event['widget'], 'click_target')
            self.assertEqual(event['state']['clicks'], 1)
            self.assertEqual(event['state']['status'], 'Button clicks: 1')

    @unittest.skipIf(
        os.environ.get('GITHUB_ACTIONS') == 'true' and sys.platform == 'darwin',
        'need to add TCC configuration first',
    )
    def test_locate_button_image_matches_button_coordinates(self):
        image_path = _locate_button_image_path()
        with GuiTestAppProcess() as app:
            click_target = app.ready['widgets']['click_target']
            located_center = _wait_for_located_center(image_path)

            self.assertLessEqual(abs(located_center.x - click_target['center_x']), LOCATE_CENTER_TOLERANCE)
            self.assertLessEqual(abs(located_center.y - click_target['center_y']), LOCATE_CENTER_TOLERANCE)
