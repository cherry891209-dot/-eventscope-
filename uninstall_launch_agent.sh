#!/bin/zsh
set -e

PLIST_NAME="com.liaoyijie.eventscope.plist"
TARGET_PLIST="$HOME/Library/LaunchAgents/$PLIST_NAME"

if [ -f "$TARGET_PLIST" ]; then
  launchctl unload "$TARGET_PLIST" >/dev/null 2>&1 || true
  rm -f "$TARGET_PLIST"
  echo "Removed launch agent: $TARGET_PLIST"
else
  echo "Launch agent not found: $TARGET_PLIST"
fi
