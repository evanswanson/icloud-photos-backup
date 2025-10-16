#!/bin/bash

# Check iCloud download status
# Shows if it's running, hung, or completed

LOG_FILE="$HOME/icloud-photo-backup/download_log.txt"
PROGRESS_FILE="$HOME/icloud-photo-backup/download_progress.json"

echo "============================================================"
echo "iCloud Download Status Check"
echo "============================================================"
echo ""

# Check if log file exists
if [ ! -f "$LOG_FILE" ]; then
    echo "❌ No download log found - download hasn't started"
    exit 1
fi

# Get last log entry timestamp
last_line=$(tail -1 "$LOG_FILE")
echo "Last log entry:"
echo "$last_line"
echo ""

# Extract timestamp from last line
last_timestamp=$(echo "$last_line" | grep -oE '\[[0-9]{4}-[0-9]{2}-[0-9]{2} [0-9]{2}:[0-9]{2}:[0-9]{2}\]' | tr -d '[]')

if [ -z "$last_timestamp" ]; then
    echo "⚠️  Could not parse last timestamp"
else
    # Calculate seconds since last activity
    last_epoch=$(date -j -f "%Y-%m-%d %H:%M:%S" "$last_timestamp" +%s 2>/dev/null)
    current_epoch=$(date +%s)
    seconds_ago=$((current_epoch - last_epoch))

    echo "Time since last activity: ${seconds_ago}s"
    echo ""

    # Determine status
    if [ $seconds_ago -lt 60 ]; then
        echo "✅ Status: ACTIVE (activity within last minute)"
    elif [ $seconds_ago -lt 180 ]; then
        echo "⚠️  Status: SLOW (no activity for ${seconds_ago}s)"
        echo "   This may be normal for large files"
    elif [ $seconds_ago -lt 300 ]; then
        echo "⚠️  Status: POSSIBLY STALLED (no activity for ${seconds_ago}s)"
        echo "   Auto-restart will kick in at 300s (5 minutes)"
    else
        echo "❌ Status: HUNG (no activity for ${seconds_ago}s / $((seconds_ago/60)) minutes)"
        echo "   Auto-restart should have triggered"
        echo "   Check if process is still running"
    fi
fi

echo ""

# Check progress
if [ -f "$PROGRESS_FILE" ]; then
    echo "Progress Statistics:"
    python3 << 'EOF'
import json
with open("/Users/evanswanson/icloud-photo-backup/download_progress.json") as f:
    p = json.load(f)
print(f"  Last checkpoint: Photo #{p['last_index']}")
print(f"  Downloaded: {p['stats']['downloaded']}")
print(f"  Skipped: {p['stats']['skipped']}")
print(f"  Failed: {p['stats']['failed']}")
total = p['last_index']
est_total = 8879
progress_pct = (total / est_total * 100) if est_total > 0 else 0
print(f"  Progress: {total}/{est_total} ({progress_pct:.1f}%)")
print(f"  Estimated remaining: ~{est_total - total}")
EOF
fi

echo ""

# Check if process is running
if pgrep -f "icloud_download_resilient.py\|auto_download_icloud.sh" > /dev/null; then
    echo "✅ Download process is running"
    echo ""
    echo "Process details:"
    ps aux | grep -E "icloud_download_resilient.py|auto_download_icloud.sh" | grep -v grep
else
    echo "❌ Download process is NOT running"
    echo ""
    echo "To restart:"
    echo "  ~/scripts/icloud-photo-backup/auto_download_icloud.sh"
fi

echo ""
echo "============================================================"
echo "Quick Commands:"
echo "============================================================"
echo "Watch live progress:"
echo "  tail -f $LOG_FILE"
echo ""
echo "Run this check again:"
echo "  ~/scripts/icloud-photo-backup/check_status.sh"
