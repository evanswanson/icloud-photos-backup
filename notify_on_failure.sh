#!/bin/bash
# Wrapper script that sends notification on failure

SCRIPT_DIR="$HOME/scripts/icloud-photo-backup"
LOG_FILE="$HOME/icloud-photo-backup/launchd.log"
ERROR_LOG="$HOME/icloud-photo-backup/launchd.error.log"

# Run the workflow
"$SCRIPT_DIR/smart_workflow.sh" --headless

EXIT_CODE=$?

if [ $EXIT_CODE -ne 0 ]; then
    # Get last error from log
    LAST_ERROR=$(tail -5 "$ERROR_LOG" 2>/dev/null | head -1)

    # Try multiple notification methods for reliability

    # Method 1: osascript notification
    osascript -e 'display notification "iCloud cleanup failed. Check logs for details." with title "iCloud Cleanup Failed" sound name "Basso"' 2>/dev/null

    # Method 2: osascript alert (more visible - requires clicking OK)
    osascript -e 'display alert "iCloud Cleanup Failed" message "The scheduled iCloud cleanup task failed. Check logs:\n~/icloud-photo-backup/launchd.error.log" as critical' 2>/dev/null &

    # Method 3: Create a flag file that can be checked
    echo "$(date): Cleanup failed with exit code $EXIT_CODE" > "$HOME/icloud-photo-backup/LAST_FAILURE.txt"

    # Method 4: Send email notification
    "$SCRIPT_DIR/send_email_notification.sh" 2>/dev/null

    # Also log the failure
    echo "[$(date)] FAILED with exit code $EXIT_CODE" >> "$LOG_FILE"

    exit $EXIT_CODE
else
    # Remove failure flag on success
    rm -f "$HOME/icloud-photo-backup/LAST_FAILURE.txt" 2>/dev/null

    # Success notification (optional - comment out if too noisy)
    # osascript -e 'display notification "Successfully cleaned up iCloud photos" with title "iCloud Cleanup Complete" sound name "Glass"' 2>/dev/null

    echo "[$(date)] Completed successfully" >> "$LOG_FILE"
    exit 0
fi
