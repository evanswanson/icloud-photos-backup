#!/bin/bash
# Send email notification on failure

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
EMAIL="evan.swanson@gmail.com"
SUBJECT="❌ iCloud Cleanup Failed"
LOG_FILE="$HOME/icloud-photo-backup/launchd.error.log"

BODY="The scheduled iCloud cleanup task failed.

Last error:
$(tail -10 "$LOG_FILE" 2>/dev/null)

Check full logs at:
$LOG_FILE

To re-authenticate:
~/scripts/icloud-photo-backup/smart_workflow.sh
"

# Send email using Python SMTP
python3 "$SCRIPT_DIR/send_email_smtp.py" "$EMAIL" "$SUBJECT" "$BODY"
