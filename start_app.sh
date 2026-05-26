#!/bin/zsh
set -e

PORT="${1:-8505}"
LOG_FILE="streamlit.log"
PID_FILE=".streamlit.pid"
APP_DIR="$(cd "$(dirname "$0")" && pwd)"
STREAMLIT_BIN="${STREAMLIT_BIN:-$(command -v streamlit)}"

if [ -f "$PID_FILE" ] && kill -0 "$(cat "$PID_FILE")" 2>/dev/null; then
  echo "Streamlit is already running on PID $(cat "$PID_FILE")"
  exit 0
fi

if [ -f "$PID_FILE" ]; then
  rm -f "$PID_FILE"
fi

cd "$APP_DIR"
nohup "$STREAMLIT_BIN" run app.py \
  --server.headless true \
  --server.port "$PORT" \
  --server.address 0.0.0.0 \
  > "$LOG_FILE" 2>&1 &
echo $! > "$PID_FILE"
echo "Started EventScope on http://localhost:$PORT"
echo "PID: $(cat "$PID_FILE")"
echo "Log: $LOG_FILE"
