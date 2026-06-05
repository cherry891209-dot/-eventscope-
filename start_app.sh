#!/bin/zsh
set -e

PORT="${1:-8505}"
APP_DIR="$(cd "$(dirname "$0")" && pwd)"
LOG_FILE="$APP_DIR/streamlit.log"
PID_FILE="$APP_DIR/.streamlit.pid"
STREAMLIT_BIN="${STREAMLIT_BIN:-/opt/miniconda3/bin/streamlit}"

if [ ! -x "$STREAMLIT_BIN" ]; then
  STREAMLIT_BIN="$(command -v streamlit)"
fi

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
  --server.fileWatcherType none \
  > "$LOG_FILE" 2>&1 &
echo $! > "$PID_FILE"
echo "Started EventScope on http://localhost:$PORT"
echo "PID: $(cat "$PID_FILE")"
echo "Log: $LOG_FILE"
