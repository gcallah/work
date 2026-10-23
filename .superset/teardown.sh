#!/usr/bin/env bash
# Stop the docs server started by run.sh, if it is still running.
set -uo pipefail

PIDFILE=.superset/run.pid

if [ -f "$PIDFILE" ]; then
    pid=$(cat "$PIDFILE")
    if kill -0 "$pid" 2>/dev/null; then
        kill "$pid" && echo "stopped docs server (pid $pid)"
    fi
    rm -f "$PIDFILE"
fi
exit 0
