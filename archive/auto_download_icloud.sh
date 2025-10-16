#!/bin/bash

# Auto-restarting iCloud Photo Downloader
# This wrapper will automatically restart the download if it stalls
# No babysitting required!

SCRIPT="/Users/evanswanson/scripts/icloud-photo-backup/icloud_download_resilient.py"
LOG_FILE="/Users/evanswanson/icloud-photo-backup/download_log.txt"
PROGRESS_FILE="/Users/evanswanson/icloud-photo-backup/download_progress.json"
STALL_TIMEOUT=300  # Restart if no log activity for 5 minutes (300 seconds)
MAX_RESTARTS=100   # Maximum number of restarts (to prevent infinite loops)

echo "============================================================"
echo "Auto-Restarting iCloud Photo Downloader"
echo "============================================================"
echo ""
echo "This wrapper will:"
echo "  - Run the download script"
echo "  - Monitor for stalls (no activity for ${STALL_TIMEOUT}s)"
echo "  - Auto-restart if stalled"
echo "  - Continue until all photos are downloaded"
echo ""
echo "Press Ctrl+C to stop completely"
echo ""

restart_count=0

# Function to check if download is complete
is_complete() {
    if [ -f "$PROGRESS_FILE" ]; then
        # Extract last_index and compare with total
        last_index=$(python3 -c "import json; p=json.load(open('$PROGRESS_FILE')); print(p.get('last_index', 0))" 2>/dev/null)
        # If last_index is high enough, we might be done
        # You can adjust this logic as needed
        if [ "$last_index" -ge 8879 ]; then
            return 0
        fi
    fi
    return 1
}

# Function to run download with timeout monitoring
run_with_timeout() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] Starting download (attempt $((restart_count + 1)))..."
    echo ""

    # Start tailing the log file in background
    if [ -f "$LOG_FILE" ]; then
        tail -f "$LOG_FILE" &
        TAIL_PID=$!
    fi

    # Run the download script
    python3 "$SCRIPT" &
    PID=$!

    # Monitor for stalls
    last_log_check=$(date +%s)
    while kill -0 $PID 2>/dev/null; do
        # Check if log file has been updated recently
        if [ -f "$LOG_FILE" ]; then
            last_modified=$(date -r "$LOG_FILE" +%s 2>/dev/null || stat -f %m "$LOG_FILE" 2>/dev/null)
            current_time=$(date +%s)
            time_diff=$((current_time - last_modified))

            # Show stall warning every 60 seconds if no activity
            if [ $time_diff -gt 60 ] && [ $((current_time - last_log_check)) -gt 60 ]; then
                echo ""
                echo "[$(date '+%Y-%m-%d %H:%M:%S')] ⚠️  No activity for ${time_diff}s (will restart at ${STALL_TIMEOUT}s)..."
                last_log_check=$current_time
            fi

            if [ $time_diff -gt $STALL_TIMEOUT ]; then
                echo ""
                echo "[$(date '+%Y-%m-%d %H:%M:%S')] ⚠️  Stalled for ${STALL_TIMEOUT}s - restarting..."
                # Kill tail process
                [ ! -z "$TAIL_PID" ] && kill $TAIL_PID 2>/dev/null
                # Kill download process
                kill $PID 2>/dev/null
                sleep 3
                kill -9 $PID 2>/dev/null
                return 1
            fi
        fi

        sleep 10
    done

    # Process finished naturally - stop tailing
    [ ! -z "$TAIL_PID" ] && kill $TAIL_PID 2>/dev/null
    wait $PID
    return $?
}

# Main loop
while true; do
    # Check if already complete
    if is_complete; then
        echo "[$(date '+%Y-%m-%d %H:%M:%S')] ✓ Download complete! All photos downloaded."
        break
    fi

    # Check restart limit
    if [ $restart_count -ge $MAX_RESTARTS ]; then
        echo "[$(date '+%Y-%m-%d %H:%M:%S')] ⚠️  Reached max restart limit ($MAX_RESTARTS)"
        echo "Please check for errors and restart manually if needed"
        break
    fi

    # Run the download
    run_with_timeout
    exit_code=$?

    if [ $exit_code -eq 0 ]; then
        echo "[$(date '+%Y-%m-%d %H:%M:%S')] ✓ Download completed successfully!"
        break
    else
        restart_count=$((restart_count + 1))
        echo "[$(date '+%Y-%m-%d %H:%M:%S')] Restart #$restart_count - waiting 10 seconds..."
        sleep 10
    fi
done

echo ""
echo "============================================================"
echo "Download Session Complete"
echo "============================================================"
echo "Total restarts: $restart_count"
echo ""

if is_complete; then
    echo "Next steps:"
    echo "  1. Scan for duplicates/quality issues:"
    echo "     python3 /Users/evanswanson/scripts/icloud-photo-backup/photo_cleanup.py"
    echo ""
    echo "  2. Clean up problematic images:"
    echo "     python3 /Users/evanswanson/scripts/icloud-photo-backup/auto_cleanup.py"
else
    echo "Download may not be complete. Check:"
    echo "  Log: $LOG_FILE"
    echo "  Progress: $PROGRESS_FILE"
fi
