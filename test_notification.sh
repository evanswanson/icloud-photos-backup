#!/bin/bash
# Test notification system

echo "Testing failure notification..."
osascript -e 'display notification "iCloud cleanup failed. Check logs for details." with title "iCloud Cleanup Failed" sound name "Basso"'

echo ""
echo "Testing success notification..."
osascript -e 'display notification "Successfully cleaned up iCloud photos" with title "iCloud Cleanup Complete" sound name "Glass"'

echo ""
echo "Notifications sent! Check your notification center."
