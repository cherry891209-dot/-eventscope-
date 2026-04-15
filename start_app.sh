#!/bin/zsh
PORT="${1:-8505}"
LOG_FILE="streamlit.log"
PID_FILE=".streamlit.pid"

if [ -f "$PID_FILE" ] && kill -0 "$(cat "$PID_FILE")" 2>/dev/null; then
  echo "Streamlit is already running on PID $(cat "$PID_FILE")"
  exit 0
fi

nohup streamlit run app.py --server.headless true --server.port "$PORT" > "$LOG_FILE" 2>&1 &
echo $! > "$PID_FILE"
echo "Started EventScope on http://localhost:$PORT"
echo "PID: $(cat "$PID_FILE")"
echo "Log: $LOG_FILE"
