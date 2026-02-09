#!/usr/bin/env bash
set -e

DIR="$(cd "$(dirname "$0")" && pwd)"

if ! command -v pm2 &>/dev/null; then
    echo "pm2 not found. install it: npm install -g pm2"
    exit 1
fi

# stop existing instance if running
pm2 delete coral 2>/dev/null || true

# activate venv if it exists
PYTHON="python3"
if [ -f "$DIR/venv/bin/python3" ]; then
    PYTHON="$DIR/venv/bin/python3"
fi

pm2 start "$DIR/recoral/app.py" \
    --name coral \
    --interpreter "$PYTHON" \
    --cwd "$DIR"

pm2 save --force 2>/dev/null || true

echo ""
echo "  coral is running → http://localhost:${CORAL_PORT:-3456}"
echo "  pm2 logs coral   → view logs"
echo "  pm2 stop coral   → stop"
echo ""
