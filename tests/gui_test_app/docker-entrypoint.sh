#!/bin/sh
set -eu

display="${DISPLAY:-:0}"
display_number="${display#:}"
display_number="${display_number%%.*}"
vnc_port="${GUI_TEST_APP_VNC_PORT:-$((5900 + display_number))}"

Xvnc "$display" \
    -listen tcp \
    -ac \
    -localhost no \
    -SecurityTypes None \
    -rfbport "$vnc_port" \
    -geometry "$GUI_TEST_APP_GEOMETRY" \
    -depth "$GUI_TEST_APP_DEPTH" \
    >/tmp/xvnc.log 2>&1 &
xvnc_pid="$!"

cleanup() {
    kill "$xvnc_pid" 2>/dev/null || true
}
trap cleanup EXIT INT TERM

for _ in $(seq 1 100); do
    if xdpyinfo -display "$display" >/dev/null 2>&1; then
        break
    fi
    if ! kill -0 "$xvnc_pid" 2>/dev/null; then
        cat /tmp/xvnc.log >&2
        exit 1
    fi
    sleep 0.1
done

if ! xdpyinfo -display "$display" >/dev/null 2>&1; then
    cat /tmp/xvnc.log >&2
    exit 1
fi

if [ "$#" -eq 0 ]; then
    set -- gui-test-app
fi

if [ "$1" = "gui-test-app" ]; then
    set -- "$@" \
        --ready-file "$GUI_TEST_APP_READY_FILE"
    if [ "$GUI_TEST_APP_TIMEOUT" != "0" ]; then
        set -- "$@" --timeout "$GUI_TEST_APP_TIMEOUT"
    fi
fi

exec "$@"
