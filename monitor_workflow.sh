#!/bin/bash
# Monitor Workflow Script
# Watches for hangs, infinite loops, and other issues

BACKUP_DIR="$HOME/icloud-photo-backup"
SCRIPT_DIR="$HOME/scripts/icloud-photo-backup"

echo "======================================================================"
echo "Workflow Monitor"
echo "======================================================================"
echo ""
echo "This will monitor the workflow for:"
echo "  - Infinite loops (cycling through same photos)"
echo "  - Hung processes (no progress for 5+ minutes)"
echo "  - Excessive API calls"
echo "  - Memory/CPU issues"
echo ""
echo "Press Ctrl+C to stop monitoring"
echo ""

# Check if workflow is running
if ! pgrep -f "smart_workflow.sh\|smart_download.py\|delete_by_criteria.py" > /dev/null; then
    echo "⚠️  No workflow processes detected"
    echo ""
    echo "Start the workflow in another terminal:"
    echo "  ~/scripts/icloud-photo-backup/smart_workflow.sh"
    echo ""
    read -p "Press Enter when ready to monitor..."
fi

echo "Starting monitoring..."
echo ""

# Track state
LAST_LINE=""
SAME_LINE_COUNT=0
LAST_SIZE=0
NO_CHANGE_COUNT=0

while true; do
    clear
    echo "======================================================================"
    echo "Workflow Monitor - $(date '+%H:%M:%S')"
    echo "======================================================================"
    echo ""

    # Check for running processes
    echo "=== Running Processes ==="
    PROCS=$(ps aux | grep -E "smart_workflow.sh|smart_download.py|delete_by_criteria.py|icloud_delete_fast.py|photo_cleanup.py" | grep -v grep | grep -v monitor)

    if [ -z "$PROCS" ]; then
        echo "❌ No workflow processes running"
        echo ""
        echo "Either the workflow hasn't started or it finished."
        echo "Press Ctrl+C to exit"
    else
        echo "$PROCS" | awk '{printf "PID %-6s | CPU: %-5s | MEM: %-5s | %s\n", $2, $3"%", $4"%", $11}'

        # Check for high CPU (potential infinite loop)
        HIGH_CPU=$(echo "$PROCS" | awk '$3 > 150 {print $2}')
        if [ ! -z "$HIGH_CPU" ]; then
            echo ""
            echo "⚠️  WARNING: High CPU detected (PID: $HIGH_CPU)"
            echo "   This might indicate an infinite loop!"
        fi

        # Check for high memory
        HIGH_MEM=$(echo "$PROCS" | awk '$4 > 10 {print $2}')
        if [ ! -z "$HIGH_MEM" ]; then
            echo ""
            echo "⚠️  WARNING: High memory usage (PID: $HIGH_MEM)"
        fi
    fi

    echo ""
    echo "=== Log Activity ==="

    # Monitor download log
    if [ -f "$BACKUP_DIR/download_log.txt" ]; then
        CURRENT_LINE=$(tail -1 "$BACKUP_DIR/download_log.txt")
        CURRENT_SIZE=$(stat -f%z "$BACKUP_DIR/download_log.txt" 2>/dev/null || echo 0)

        echo "📥 Download Log (last line):"
        echo "   $CURRENT_LINE"

        # Check for cycling (same line repeated)
        if [ "$CURRENT_LINE" = "$LAST_LINE" ]; then
            SAME_LINE_COUNT=$((SAME_LINE_COUNT + 1))
            if [ $SAME_LINE_COUNT -gt 10 ]; then
                echo ""
                echo "⚠️  WARNING: No new log entries for $((SAME_LINE_COUNT * 5)) seconds"
                echo "   Process might be hung!"
            fi
        else
            SAME_LINE_COUNT=0
        fi

        # Check for file size changes
        if [ "$CURRENT_SIZE" = "$LAST_SIZE" ] && [ ! -z "$PROCS" ]; then
            NO_CHANGE_COUNT=$((NO_CHANGE_COUNT + 1))
            if [ $NO_CHANGE_COUNT -gt 10 ]; then
                echo ""
                echo "⚠️  WARNING: Log file not growing for $((NO_CHANGE_COUNT * 5)) seconds"
                echo "   Process might be stuck!"
            fi
        else
            NO_CHANGE_COUNT=0
        fi

        LAST_LINE="$CURRENT_LINE"
        LAST_SIZE="$CURRENT_SIZE"
    fi

    # Monitor deletion log
    if [ -f "$BACKUP_DIR/delete_by_criteria_log.txt" ]; then
        echo ""
        echo "🗑️  Deletion Log (last line):"
        echo "   $(tail -1 "$BACKUP_DIR/delete_by_criteria_log.txt")"
    fi

    # Monitor fast deletion log
    if [ -f "$BACKUP_DIR/delete_log_fast.txt" ]; then
        echo ""
        echo "⚡ Fast Delete Log (last line):"
        echo "   $(tail -1 "$BACKUP_DIR/delete_log_fast.txt")"
    fi

    echo ""
    echo "=== Progress Indicators ==="

    # Check download progress
    if [ -f "$BACKUP_DIR/download_progress.json" ]; then
        DOWNLOADED=$(cat "$BACKUP_DIR/download_progress.json" | python3 -c "import sys, json; d=json.load(sys.stdin); print(d.get('stats', {}).get('downloaded', 0))" 2>/dev/null || echo "?")
        SKIPPED=$(cat "$BACKUP_DIR/download_progress.json" | python3 -c "import sys, json; d=json.load(sys.stdin); print(d.get('stats', {}).get('skipped', 0))" 2>/dev/null || echo "?")
        LAST_INDEX=$(cat "$BACKUP_DIR/download_progress.json" | python3 -c "import sys, json; d=json.load(sys.stdin); print(d.get('last_index', 0))" 2>/dev/null || echo "?")

        echo "📊 Download: $DOWNLOADED downloaded, $SKIPPED skipped, index: $LAST_INDEX"

        # Check for cycling (index growing but no downloads)
        if [ "$LAST_INDEX" -gt 15000 ] && [ "$DOWNLOADED" -lt 100 ]; then
            echo ""
            echo "⚠️  WARNING: High index ($LAST_INDEX) with low downloads ($DOWNLOADED)"
            echo "   Possible API cycling - but should auto-detect and stop"
        fi
    fi

    # Check deletion progress
    if [ -f "$BACKUP_DIR/delete_by_criteria_progress.json" ]; then
        DELETED=$(cat "$BACKUP_DIR/delete_by_criteria_progress.json" | python3 -c "import sys, json; d=json.load(sys.stdin); print(d.get('stats', {}).get('deleted', 0))" 2>/dev/null || echo "?")
        FAILED=$(cat "$BACKUP_DIR/delete_by_criteria_progress.json" | python3 -c "import sys, json; d=json.load(sys.stdin); print(d.get('stats', {}).get('failed', 0))" 2>/dev/null || echo "?")

        echo "🗑️  Deletion: $DELETED deleted, $FAILED failed"
    fi

    # Check index
    if [ -f "$BACKUP_DIR/icloud_index.json" ]; then
        INDEX_COUNT=$(cat "$BACKUP_DIR/icloud_index.json" | python3 -c "import sys, json; d=json.load(sys.stdin); print(d.get('photo_count', 0))" 2>/dev/null || echo "?")
        INDEX_DATE=$(cat "$BACKUP_DIR/icloud_index.json" | python3 -c "import sys, json; d=json.load(sys.stdin); print(d.get('created_at', 'unknown')[:19])" 2>/dev/null || echo "?")

        echo "📇 Index: $INDEX_COUNT items (created: $INDEX_DATE)"
    fi

    echo ""
    echo "=== Health Checks ==="

    # Check for stuck authentication
    if grep -q "Enter your Apple ID password" "$BACKUP_DIR/download_log.txt" 2>/dev/null; then
        LAST_AUTH=$(grep "Enter your Apple ID password" "$BACKUP_DIR/download_log.txt" | tail -1)
        AUTH_TIME=$(echo "$LAST_AUTH" | grep -oE '\[[0-9-]+ [0-9:]+\]' | tr -d '[]')
        echo "🔐 Authentication prompt detected at: $AUTH_TIME"
    fi

    # Check for errors in logs
    ERROR_COUNT=$(grep -i "error\|failed\|exception" "$BACKUP_DIR/download_log.txt" 2>/dev/null | wc -l | tr -d ' ')
    if [ "$ERROR_COUNT" -gt 0 ]; then
        echo "⚠️  $ERROR_COUNT errors detected in logs"
        echo "   Last error: $(grep -i "error\|failed\|exception" "$BACKUP_DIR/download_log.txt" 2>/dev/null | tail -1)"
    else
        echo "✓ No errors detected"
    fi

    echo ""
    echo "=== Actions ==="
    echo "  [Ctrl+C] Stop monitoring"
    echo "  Kill hung process: kill <PID>"
    echo "  View full log: tail -f ~/icloud-photo-backup/download_log.txt"
    echo ""
    echo "Refreshing in 5 seconds..."

    sleep 5
done
