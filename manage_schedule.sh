#!/bin/bash
# Manage iCloud Cleanup Schedule (launchd)

PLIST_FILE="$HOME/Library/LaunchAgents/com.icloud.cleanup.plist"
LABEL="com.icloud.cleanup"

show_help() {
    echo "iCloud Cleanup Schedule Manager"
    echo ""
    echo "Usage: $0 <command>"
    echo ""
    echo "Commands:"
    echo "  status      Check if scheduled task is loaded"
    echo "  start       Load and enable the scheduled task"
    echo "  stop        Unload and disable the scheduled task"
    echo "  restart     Restart the scheduled task"
    echo "  test        Run the workflow once manually (headless)"
    echo "  logs        View recent logs"
    echo "  schedule    Show when task will run next"
    echo ""
    echo "Current schedule: Every Sunday at 2:00 AM"
    echo ""
    exit 0
}

case "$1" in
    status)
        echo "Checking launchd status..."
        if launchctl list | grep -q "$LABEL"; then
            echo "✓ Scheduled task is LOADED"
            echo ""
            echo "Schedule: Every Sunday at 2:00 AM"
            echo "Logs: ~/icloud-photo-backup/launchd.log"
            echo ""
            launchctl list | grep "$LABEL"
        else
            echo "✗ Scheduled task is NOT loaded"
            echo ""
            echo "To enable: $0 start"
        fi

        echo ""
        echo "Checking iCloud authentication..."
        python3 ~/scripts/icloud-photo-backup/check_auth.py 2>/dev/null

        echo ""
        echo "Checking for recent failures..."
        if [ -f "$HOME/icloud-photo-backup/LAST_FAILURE.txt" ]; then
            echo "⚠️  LAST RUN FAILED:"
            cat "$HOME/icloud-photo-backup/LAST_FAILURE.txt"
            echo ""
            echo "Check error log: tail -50 ~/icloud-photo-backup/launchd.error.log"
        else
            echo "✓ No recent failures detected"
        fi
        ;;

    start)
        if launchctl list | grep -q "$LABEL"; then
            echo "Already loaded. Use 'restart' to reload."
        else
            echo "Loading scheduled task..."
            launchctl load "$PLIST_FILE"
            echo "✓ Scheduled task loaded"
            echo ""
            echo "Schedule: Every Sunday at 2:00 AM"
            echo "Logs: ~/icloud-photo-backup/launchd.log"
        fi
        ;;

    stop)
        echo "Unloading scheduled task..."
        launchctl unload "$PLIST_FILE" 2>/dev/null
        echo "✓ Scheduled task stopped"
        ;;

    restart)
        echo "Restarting scheduled task..."
        launchctl unload "$PLIST_FILE" 2>/dev/null
        sleep 1
        launchctl load "$PLIST_FILE"
        echo "✓ Scheduled task restarted"
        ;;

    test)
        echo "Running workflow manually in headless mode..."
        echo ""
        ~/scripts/icloud-photo-backup/smart_workflow.sh --headless
        ;;

    logs)
        echo "=== Standard Output (last 50 lines) ==="
        tail -50 ~/icloud-photo-backup/launchd.log 2>/dev/null || echo "No logs yet"
        echo ""
        echo "=== Error Output (last 20 lines) ==="
        tail -20 ~/icloud-photo-backup/launchd.error.log 2>/dev/null || echo "No errors yet"
        ;;

    schedule)
        if [ ! -f "$PLIST_FILE" ]; then
            echo "Schedule file not found: $PLIST_FILE"
            exit 1
        fi

        echo "Current Schedule:"
        echo ""
        echo "Every Sunday at 2:00 AM"
        echo ""
        echo "Next scheduled run:"
        # Calculate next Sunday
        current_day=$(date +%u)  # 1=Monday, 7=Sunday
        if [ $current_day -eq 7 ]; then
            days_until=7
        else
            days_until=$((7 - current_day))
        fi
        next_run=$(date -v+${days_until}d -v2H -v0M -v0S "+%A, %B %d at %I:%M %p")
        echo "  $next_run"
        echo ""
        echo "To change schedule, edit:"
        echo "  $PLIST_FILE"
        echo "Then run: $0 restart"
        ;;

    *)
        show_help
        ;;
esac
