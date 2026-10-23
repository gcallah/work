#!/usr/bin/env bash
# Rebuild the GitHub Pages site into docs/ and serve it locally.
# Each workspace gets its own port so parallel workspaces don't collide.
set -euo pipefail

PIDFILE=.superset/run.pid

if command -v pandoc >/dev/null 2>&1; then
    ./bin/site.py
else
    echo "warning: pandoc not found; serving docs/ without rebuilding" >&2
fi

# Start from a port derived from the workspace name, then scan upward
# for one that is free.
name=${SUPERSET_WORKSPACE_NAME:-$(basename "$PWD")}
start=$((8100 + $(printf '%s' "$name" | cksum | cut -d' ' -f1) % 800))
port=$(python3 - "$start" <<'PY'
import socket, sys
start = int(sys.argv[1])
for port in range(start, start + 100):
    with socket.socket() as s:
        try:
            s.bind(("127.0.0.1", port))
        except OSError:
            continue
        print(port)
        break
else:
    sys.exit("no free port found")
PY
)

echo "serving docs/ at http://localhost:$port/"
echo $$ > "$PIDFILE"
exec python3 -m http.server "$port" --bind 127.0.0.1 --directory docs
