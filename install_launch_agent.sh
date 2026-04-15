#!/bin/zsh
set -e

PLIST_NAME="com.liaoyijie.eventscope.plist"
SOURCE_PLIST="$(cd "$(dirname "$0")" && pwd)/$PLIST_NAME"
TARGET_DIR="$HOME/Library/LaunchAgents"
TARGET_PLIST="$TARGET_DIR/$PLIST_NAME"

mkdir -p "$TARGET_DIR"
cp "$SOURCE_PLIST" "$TARGET_PLIST"
launchctl unload "$TARGET_PLIST" >/dev/null 2>&1 || true
launchctl load "$TARGET_PLIST"

echo "Installed launch agent: $TARGET_PLIST"
echo "EventScope will auto-start on login and keep running on port 8505."
