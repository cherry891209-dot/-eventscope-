#!/bin/zsh
PID_FILE=".streamlit.pid"

if [ ! -f "$PID_FILE" ]; then
  echo "No PID file found."
  exit 0
fi

PID="$(cat "$PID_FILE")"
if kill -0 "$PID" 2>/dev/null; then
  kill "$PID"
  echo "Stopped Streamlit PID $PID"
else
  echo "Process $PID is not running."
fi

rm -f "$PID_FILE"
