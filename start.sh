#!/usr/bin/env bash
set -euo pipefail

DIR="$(cd "$(dirname "$0")" && pwd)"

# activate venv if it exists
PYTHON="python3"
if [ -f "$DIR/venv/bin/python3" ]; then
    PYTHON="$DIR/venv/bin/python3"
fi

if command -v pm2 &>/dev/null && [ "${CORAL_NO_PM2:-0}" != "1" ]; then
    # stop existing instance if running
    pm2 delete coral 2>/dev/null || true

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
    exit 0
fi

if [ "${CORAL_NO_PM2:-0}" = "1" ]; then
    echo "  CORAL_NO_PM2=1 set, starting in foreground mode."
else
    echo "  pm2 not found, starting in foreground mode."
    echo "  install pm2 (npm install -g pm2) for daemon mode."
fi

echo ""
echo "  coral is running → http://localhost:${CORAL_PORT:-3456}"
echo "  press Ctrl+C to stop"
echo ""

exec "$PYTHON" "$DIR/recoral/app.py"
