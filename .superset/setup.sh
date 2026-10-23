#!/usr/bin/env bash
# Prepare a new Superset workspace. Safe to re-run.
set -euo pipefail

# No packages to install: the site builder needs only python3 and pandoc.
for tool in python3 pandoc; do
    if ! command -v "$tool" >/dev/null 2>&1; then
        echo "warning: $tool not found on PATH; bin/site.py needs it" >&2
    fi
done

# Copy untracked env files (if any) from the main checkout.
if [ -n "${SUPERSET_ROOT_PATH:-}" ] && [ "$SUPERSET_ROOT_PATH" != "$PWD" ]; then
    for f in "$SUPERSET_ROOT_PATH"/.env "$SUPERSET_ROOT_PATH"/.env.*; do
        [ -f "$f" ] || continue
        name=$(basename "$f")
        if [ ! -e "$name" ]; then
            cp "$f" "$name"
            echo "copied $name from $SUPERSET_ROOT_PATH"
        fi
    done
fi

echo "workspace setup done"
