"""Small cross-platform GUI target for PyAutoGUI integration tests.

Run it as a subprocess from tests through uvx:

    uvx --python 3.10 --from tests/gui_test_app gui-test-app --ready-file /tmp/pyautogui-ready.json

The app prints newline-delimited JSON events to stdout and accepts newline
commands on stdin: ``snapshot``, ``clear``, or ``quit``. Commands may also be
JSON objects with a ``command`` field.
"""

from __future__ import annotations

import argparse
import json
import os
import platform
import queue
import sys
import tempfile
import threading
import time
from typing import Any

READY_SETTLE_MS = 750
TOPMOST_RELEASE_MS = 1500

try:
    import tkinter as tk
    from tkinter import ttk
except ImportError as exc:  # pragma: no cover - depends on host Python build.
    tk = None
    ttk = None
    TKINTER_IMPORT_ERROR = exc
else:
    TKINTER_IMPORT_ERROR = None


class GuiTestApp:
    def __init__(self, args: argparse.Namespace) -> None:
        self.args = args
        self.commands: queue.Queue[Any] = queue.Queue()
        self.clicks = 0
        self.double_clicks = 0
        self.right_clicks = 0
        self.key_events = 0
        self.drag_events = 0
        self.scroll_events = 0
        self.ready_emitted = False
        self.drag_start: tuple[int, int] | None = None

        self.root = tk.Tk()
        self.root.title(args.title)
        self.root.geometry(args.geometry)
        self.root.minsize(420, 320)
        self.root.protocol('WM_DELETE_WINDOW', self.quit)

        self.status_var = tk.StringVar(value='Ready')
        self.entry_var = tk.StringVar()
        self.check_var = tk.BooleanVar(value=False)

        self._build_ui()
        self._bind_events()

    def _build_ui(self) -> None:
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(3, weight=1)

        header = ttk.Label(self.root, text='PyAutoGUI integration target', anchor='center')
        header.grid(row=0, column=0, sticky='ew', padx=12, pady=(12, 6))

        form = ttk.Frame(self.root, padding=(12, 0))
        form.grid(row=1, column=0, sticky='ew')
        form.columnconfigure(1, weight=1)

        ttk.Label(form, text='Input').grid(row=0, column=0, sticky='w', padx=(0, 8))
        self.entry = ttk.Entry(form, textvariable=self.entry_var, name='text_input')
        self.entry.grid(row=0, column=1, sticky='ew')

        controls = ttk.Frame(self.root, padding=12)
        controls.grid(row=2, column=0, sticky='ew')
        controls.columnconfigure(3, weight=1)

        self.click_button = ttk.Button(controls, text='Click target', name='click_target', command=self._button_command)
        self.click_button.grid(row=0, column=0, sticky='w', padx=(0, 8))

        self.clear_button = ttk.Button(controls, text='Clear', name='clear_button', command=self.clear)
        self.clear_button.grid(row=0, column=1, sticky='w', padx=(0, 8))

        self.check = ttk.Checkbutton(
            controls,
            text='Toggle',
            variable=self.check_var,
            name='toggle_target',
            command=lambda: self.emit_event('toggle', widget='toggle_target'),
        )
        self.check.grid(row=0, column=2, sticky='w')

        body = ttk.Frame(self.root, padding=(12, 0, 12, 12))
        body.grid(row=3, column=0, sticky='nsew')
        body.columnconfigure(0, weight=2)
        body.columnconfigure(1, weight=1)
        body.rowconfigure(0, weight=1)

        self.canvas = tk.Canvas(body, name='drag_canvas', bg='#1f2937', highlightthickness=0)
        self.canvas.grid(row=0, column=0, sticky='nsew', padx=(0, 12))
        self.canvas.create_rectangle(26, 26, 126, 96, fill='#38bdf8', outline='#0f172a', width=2, tags=('drag_box',))
        self.canvas.create_text(76, 61, text='drag', fill='#0f172a', tags=('drag_box',))

        side = ttk.Frame(body)
        side.grid(row=0, column=1, sticky='nsew')
        side.rowconfigure(0, weight=1)
        side.columnconfigure(0, weight=1)

        self.listbox = tk.Listbox(side, name='scroll_list', height=7, exportselection=False)
        for index in range(1, 31):
            self.listbox.insert('end', 'Row {0:02d}'.format(index))
        self.listbox.grid(row=0, column=0, sticky='nsew')

        scrollbar = ttk.Scrollbar(side, orient='vertical', command=self.listbox.yview)
        scrollbar.grid(row=0, column=1, sticky='ns')
        self.listbox.configure(yscrollcommand=scrollbar.set)

        self.status = ttk.Label(self.root, textvariable=self.status_var, name='status_label', anchor='w')
        self.status.grid(row=4, column=0, sticky='ew', padx=12, pady=(0, 12))

    def _bind_events(self) -> None:
        self.click_button.bind('<Button-1>', lambda event: self._count_click('mouse_down'), add='+')
        self.click_button.bind('<Double-Button-1>', lambda event: self._count_double_click(), add='+')
        self.click_button.bind('<Button-3>', lambda event: self._count_right_click(), add='+')
        self.entry.bind('<FocusIn>', lambda event: self.emit_event('focus', widget='text_input'), add='+')
        self.entry.bind('<KeyRelease>', self._key_released, add='+')
        self.entry.bind('<Return>', lambda event: self.emit_event('enter', widget='text_input'), add='+')
        self.canvas.bind('<ButtonPress-1>', self._start_drag, add='+')
        self.canvas.bind('<B1-Motion>', self._drag_motion, add='+')
        self.canvas.bind('<ButtonRelease-1>', self._end_drag, add='+')
        self.canvas.bind('<MouseWheel>', self._mouse_wheel, add='+')
        self.canvas.bind('<Button-4>', self._mouse_wheel, add='+')
        self.canvas.bind('<Button-5>', self._mouse_wheel, add='+')
        self.listbox.bind('<MouseWheel>', self._mouse_wheel, add='+')
        self.listbox.bind('<Button-4>', self._mouse_wheel, add='+')
        self.listbox.bind('<Button-5>', self._mouse_wheel, add='+')
        self.root.bind('<Control-q>', lambda event: self.quit(), add='+')
        self.root.bind('<Command-q>', lambda event: self.quit(), add='+')

    def _button_command(self) -> None:
        self.clicks += 1
        self.status_var.set('Button clicks: {0}'.format(self.clicks))
        self.emit_event('button_command', widget='click_target')

    def _count_click(self, event_name: str) -> None:
        self.emit_event(event_name, widget='click_target')

    def _count_double_click(self) -> None:
        self.double_clicks += 1
        self.status_var.set('Double clicks: {0}'.format(self.double_clicks))
        self.emit_event('double_click', widget='click_target')

    def _count_right_click(self) -> None:
        self.right_clicks += 1
        self.status_var.set('Right clicks: {0}'.format(self.right_clicks))
        self.emit_event('right_click', widget='click_target')

    def _key_released(self, event: tk.Event) -> None:
        self.key_events += 1
        self.status_var.set('Input: {0}'.format(self.entry_var.get()))
        self.emit_event('key_release', widget='text_input', key=getattr(event, 'keysym', None))

    def _start_drag(self, event: tk.Event) -> None:
        self.drag_start = (event.x, event.y)
        self.emit_event('drag_start', widget='drag_canvas', x=event.x, y=event.y)

    def _drag_motion(self, event: tk.Event) -> None:
        self.drag_events += 1
        if self.drag_start is not None:
            start_x, start_y = self.drag_start
            self.canvas.move('drag_box', event.x - start_x, event.y - start_y)
            self.drag_start = (event.x, event.y)
        self.status_var.set('Drag events: {0}'.format(self.drag_events))
        self.emit_event('drag_motion', widget='drag_canvas', x=event.x, y=event.y)

    def _end_drag(self, event: tk.Event) -> None:
        self.drag_start = None
        self.emit_event('drag_end', widget='drag_canvas', x=event.x, y=event.y)

    def _mouse_wheel(self, event: tk.Event) -> None:
        self.scroll_events += 1
        widget_name = str(event.widget).rsplit('.', 1)[-1]
        self.status_var.set('Scroll events: {0}'.format(self.scroll_events))
        self.emit_event('scroll', widget=widget_name)

    def clear(self) -> None:
        self.clicks = 0
        self.double_clicks = 0
        self.right_clicks = 0
        self.key_events = 0
        self.drag_events = 0
        self.scroll_events = 0
        self.entry_var.set('')
        self.check_var.set(False)
        self.status_var.set('Cleared')
        self.emit_event('clear')

    def snapshot(self) -> dict[str, Any]:
        self.root.update_idletasks()
        widgets = {
            'window': self.root,
            'text_input': self.entry,
            'click_target': self.click_button,
            'clear_button': self.clear_button,
            'toggle_target': self.check,
            'drag_canvas': self.canvas,
            'scroll_list': self.listbox,
            'status_label': self.status,
        }
        return {
            'pid': os.getpid(),
            'platform': sys.platform,
            'platform_system': platform.system(),
            'time': time.time(),
            'state': self.state(),
            'widgets': {name: self.geometry(widget) for name, widget in widgets.items()},
        }

    def state(self) -> dict[str, Any]:
        return {
            'clicks': self.clicks,
            'double_clicks': self.double_clicks,
            'right_clicks': self.right_clicks,
            'key_events': self.key_events,
            'drag_events': self.drag_events,
            'scroll_events': self.scroll_events,
            'text': self.entry_var.get(),
            'checked': self.check_var.get(),
            'status': self.status_var.get(),
        }

    def geometry(self, widget: tk.Widget) -> dict[str, int]:
        x = widget.winfo_rootx()
        y = widget.winfo_rooty()
        width = widget.winfo_width()
        height = widget.winfo_height()
        return {
            'x': x,
            'y': y,
            'width': width,
            'height': height,
            'center_x': x + width // 2,
            'center_y': y + height // 2,
        }

    def emit_event(self, event: str, **details: Any) -> None:
        payload = {'event': event, 'state': self.state()}
        payload.update(details)
        self.write_json(payload)

    def write_json(self, payload: dict[str, Any]) -> None:
        print(json.dumps(payload, sort_keys=True), flush=True)

    def write_ready_file(self, payload: dict[str, Any]) -> None:
        if not self.args.ready_file:
            return
        ready_dir = os.path.dirname(os.path.abspath(self.args.ready_file))
        os.makedirs(ready_dir, exist_ok=True)
        fd, tmp_path = tempfile.mkstemp(prefix='.gui-test-app-', suffix='.json', dir=ready_dir, text=True)
        try:
            with os.fdopen(fd, 'w') as tmp_file:
                json.dump(payload, tmp_file, sort_keys=True)
                tmp_file.write('\n')
            os.replace(tmp_path, self.args.ready_file)
        except Exception:
            try:
                os.unlink(tmp_path)
            finally:
                raise

    def emit_ready(self) -> None:
        if self.ready_emitted:
            return
        self.ready_emitted = True
        self.root.attributes('-topmost', True)
        self.root.lift()
        self.root.focus_force()
        self.entry.focus_force()
        self.root.update_idletasks()
        self.root.after(READY_SETTLE_MS, self.write_ready_snapshot_event)
        self.root.after(TOPMOST_RELEASE_MS, self.release_topmost)

    def release_topmost(self) -> None:
        self.root.attributes('-topmost', False)

    def write_ready_snapshot_event(self) -> None:
        self.root.lift()
        self.root.focus_force()
        self.entry.focus_force()
        self.root.update_idletasks()
        payload = {'event': 'ready', **self.snapshot()}
        self.write_ready_file(payload)
        self.write_json(payload)

    def process_command(self, command: Any) -> None:
        if isinstance(command, dict):
            command_name = command.get('command')
        else:
            command_name = str(command).strip()

        if command_name == 'snapshot':
            self.write_json({'event': 'snapshot', **self.snapshot()})
        elif command_name == 'clear':
            self.clear()
        elif command_name in {'quit', 'exit', 'close'}:
            self.quit()
        elif command_name:
            self.write_json({'event': 'unknown_command', 'command': command_name, 'state': self.state()})

    def poll_commands(self) -> None:
        while True:
            try:
                command = self.commands.get_nowait()
            except queue.Empty:
                break
            self.process_command(command)
        self.root.after(50, self.poll_commands)

    def quit(self) -> None:
        self.write_json({'event': 'quit', 'state': self.state()})
        self.root.destroy()

    def run(self) -> None:
        start_stdin_reader(self.commands)
        self.root.after(250, self.emit_ready)
        self.root.after(50, self.poll_commands)
        if self.args.timeout:
            self.root.after(int(self.args.timeout * 1000), self.quit)
        self.root.mainloop()


def start_stdin_reader(commands: queue.Queue[Any]) -> None:
    def read_stdin() -> None:
        for line in sys.stdin:
            line = line.strip()
            if not line:
                continue
            try:
                commands.put(json.loads(line))
            except json.JSONDecodeError:
                commands.put(line)

    thread = threading.Thread(target=read_stdin, name='gui-test-app-stdin', daemon=True)
    thread.start()


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description='Cross-platform GUI target for PyAutoGUI integration tests.')
    parser.add_argument('--ready-file', help='Write ready snapshot JSON to this path once the window is visible.')
    parser.add_argument('--timeout', type=float, default=0.0, help='Automatically close after this many seconds.')
    parser.add_argument('--geometry', default='520x390+80+80', help='Tk geometry string for the test window.')
    parser.add_argument('--title', default='PyAutoGUI Test App', help='Window title.')
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    if TKINTER_IMPORT_ERROR is not None:
        print('tkinter is required for the GUI test app: {0}'.format(TKINTER_IMPORT_ERROR), file=sys.stderr)
        return 2

    try:
        app = GuiTestApp(args)
        app.run()
    except tk.TclError as exc:
        print('Unable to start Tk GUI for the GUI test app: {0}'.format(exc), file=sys.stderr)
        return 2
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
