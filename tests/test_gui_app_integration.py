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


APP_PATH = os.path.join(SCRIPT_FOLDER, 'gui_test_app.py')
READY_TIMEOUT = 10
SNAPSHOT_TIMEOUT = 5
TYPE_TIMEOUT = 5


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


@GUI_TEST
class TestGuiAppIntegration(unittest.TestCase):
    def setUp(self):
        self.old_failsafe_setting = pyautogui.FAILSAFE
        pyautogui.FAILSAFE = False

    def tearDown(self):
        pyautogui.FAILSAFE = self.old_failsafe_setting

    def test_type_hello_world_in_input_text(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            ready_file = os.path.join(tmpdir, 'ready.json')
            process = subprocess.Popen(
                [sys.executable, APP_PATH, '--ready-file', ready_file],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,
            )
            stdout = _start_reader(process.stdout)

            try:
                ready = _read_ready_file(ready_file, process)
                text_input = ready['widgets']['text_input']
                pyautogui.click(text_input['center_x'], text_input['center_y'])
                time.sleep(0.25)
                pyautogui.typewrite('hello world', interval=0.01)

                snapshot = _wait_for_text(process, stdout, 'hello worldx')

                self.assertEqual(snapshot['state']['text'], 'hello worldx')
            finally:
                if process.poll() is None:
                    _write_command(process, 'quit')
                    try:
                        process.wait(timeout=2)
                    except subprocess.TimeoutExpired:
                        process.terminate()
                        process.wait(timeout=2)
