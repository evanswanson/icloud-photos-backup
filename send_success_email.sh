#!/bin/bash
# Send email notification on successful deletion
# Usage: ./send_success_email.sh <deleted_count> <total_size_gb> <video_count> <photo_count> <video_size_gb> <photo_size_gb> <reasons_file>

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
EMAIL="evan.swanson@gmail.com"
SUBJECT="✓ iCloud Cleanup Successful"

DELETED_COUNT=$1
TOTAL_SIZE_GB=$2
VIDEO_COUNT=$3
PHOTO_COUNT=$4
VIDEO_SIZE_GB=$5
PHOTO_SIZE_GB=$6
REASONS_FILE=$7

# Build item breakdown
ITEMS_SECTION=""
if [ "$VIDEO_COUNT" -gt 0 ]; then
    ITEMS_SECTION="${ITEMS_SECTION}Videos: ${VIDEO_COUNT} (${VIDEO_SIZE_GB} GB)
"
fi
if [ "$PHOTO_COUNT" -gt 0 ]; then
    ITEMS_SECTION="${ITEMS_SECTION}Photos: ${PHOTO_COUNT} (${PHOTO_SIZE_GB} GB)
"
fi

# Read reasons from file
REASONS=""
if [ -f "$REASONS_FILE" ]; then
    REASONS=$(cat "$REASONS_FILE")
fi

BODY="✓ iCloud Cleanup Complete

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
SUMMARY
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Total Deleted: ${DELETED_COUNT} items
Total Size:    ${TOTAL_SIZE_GB} GB

${ITEMS_SECTION}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
DELETION REASONS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

${REASONS}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
RECOVERY INFO
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Items moved to \"Recently Deleted\" album
Available for 30 days before permanent deletion

View in: iCloud Photos > Albums > Recently Deleted

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Run: ~/scripts/icloud-photo-backup/manage_schedule.sh logs
"

# Send email using Python SMTP
python3 "$SCRIPT_DIR/send_email_smtp.py" "$EMAIL" "$SUBJECT" "$BODY"
