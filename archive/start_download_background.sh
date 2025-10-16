#!/bin/bash

# Start iCloud download in background with auto-restart
# This runs the auto-restart wrapper as a background process

SCRIPT_DIR="$HOME/scripts/icloud-photo-backup"
LOG_FILE="$HOME/icloud-photo-backup/download_log.txt"
WRAPPER_SCRIPT="$SCRIPT_DIR/auto_download_icloud.sh"
PID_FILE="$HOME/icloud-photo-backup/download.pid"

# Check if already running
if [ -f "$PID_FILE" ]; then
    PID=$(cat "$PID_FILE")
    if ps -p $PID > /dev/null 2>&1; then
        echo "Download is already running (PID: $PID)"
        echo "To check progress: tail -f $LOG_FILE"
        echo "To stop: kill $PID"
        exit 1
    else
        # Stale PID file
        rm "$PID_FILE"
    fi
fi

echo "Starting iCloud photo download in background..."
echo ""

# Start the auto-restart wrapper in background
nohup "$WRAPPER_SCRIPT" >> "$LOG_FILE" 2>&1 &
PID=$!

# Save PID
echo $PID > "$PID_FILE"

echo "✓ Download started in background"
echo "  PID: $PID"
echo "  Log: $LOG_FILE"
echo "  PID file: $PID_FILE"
echo ""
echo "To monitor progress:"
echo "  tail -f $LOG_FILE"
echo ""
echo "To check if running:"
echo "  ps -p $PID"
echo ""
echo "To stop:"
echo "  kill $PID"
echo "  OR: bash $SCRIPT_DIR/stop_download.sh"
echo ""
echo "The download will auto-restart if it stalls and run until complete."
