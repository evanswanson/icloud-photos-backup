#!/bin/bash
# Smart iCloud Workflow
# Complete automated workflow: Download → Index → Analyze → Delete
# Everything driven by index metadata

set -e

SCRIPT_DIR="$HOME/scripts/icloud-photo-backup"
BACKUP_DIR="$HOME/icloud-photo-backup"
INDEX_FILE="$BACKUP_DIR/icloud_index.json"

# Parse arguments
HEADLESS=false
VERBOSE=false
RECENT_DAYS=""

show_help() {
    echo "Smart iCloud Workflow"
    echo ""
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  -h, --help        Show this help message"
    echo "  --headless        Run in headless mode (auto-answer yes to all prompts)"
    echo "                    Useful for cron jobs and automation"
    echo "  --verbose         Send email summary of new photos backed up"
    echo "  --recent DAYS     Only check photos from last N days (much faster!)"
    echo "                    Recommended: 30 for daily runs, 7 for multiple daily runs"
    echo ""
    echo "Examples:"
    echo "  $0                               # Interactive mode (full scan)"
    echo "  $0 --recent 30                   # Fast mode (last 30 days only)"
    echo "  $0 --headless --recent 30        # Automated fast daily run"
    echo "  $0 --headless --recent 30 --verbose  # Automated with email"
    echo "  $0 --verbose                     # Interactive with email summary"
    echo ""
    echo "What it does:"
    echo "  1. Download any missing photos/videos from iCloud"
    echo "  2. Build/update index during download (with metadata)"
    echo "  3. Analyze photos locally for duplicates/blur/screenshots"
    echo "  4. Move problematic photos to trash"
    echo "  5. Identify old large videos and short clips"
    echo "  6. Delete from iCloud (prompts unless --headless)"
    echo ""
    exit 0
}

while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--help|-\?)
            show_help
            ;;
        --headless)
            HEADLESS=true
            shift
            ;;
        --verbose)
            VERBOSE=true
            shift
            ;;
        --recent)
            RECENT_DAYS="$2"
            shift 2
            ;;
        *)
            echo "Unknown option: $1"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

echo "======================================================================"
echo "Smart iCloud Workflow (Fully Automated)"
echo "======================================================================"
echo ""
if [[ "$HEADLESS" == "true" ]]; then
    echo "Mode: HEADLESS (no prompts, auto-delete enabled)"
else
    echo "Mode: INTERACTIVE (will prompt before deletion)"
fi
if [[ "$VERBOSE" == "true" ]]; then
    echo "Email notifications: ENABLED"
else
    echo "Email notifications: DISABLED"
fi
if [[ -n "$RECENT_DAYS" ]]; then
    echo "Fast Mode: Only checking last $RECENT_DAYS days of photos"
else
    echo "Full Mode: Checking all photos (slower)"
fi
echo ""
echo "This workflow will:"
echo "  1. Download any missing photos/videos from iCloud"
echo "  2. Build/update index during download (with metadata)"
echo "  3. Analyze photos locally for duplicates/blur/screenshots"
echo "  4. Move problematic photos to trash"
echo "  5. Identify old large videos and short clips"
echo "  6. Delete from iCloud"
echo ""

# Step 1: Smart Download + Index Building
echo ""
echo "======================================================================"
echo "Step 1: Download Photos & Build Index"
echo "======================================================================"
echo ""

# Build command with optional flags
DOWNLOAD_CMD="python3 \"$SCRIPT_DIR/smart_download.py\""
if [[ "$VERBOSE" == "true" ]]; then
    DOWNLOAD_CMD="$DOWNLOAD_CMD --verbose"
fi
if [[ -n "$RECENT_DAYS" ]]; then
    DOWNLOAD_CMD="$DOWNLOAD_CMD --recent $RECENT_DAYS"
fi

eval $DOWNLOAD_CMD

if [ $? -ne 0 ]; then
    echo "❌ Download failed!"
    exit 1
fi

echo ""
echo "✓ Download and index complete"

# Step 2: Analyze Photos Locally
echo ""
echo "======================================================================"
echo "Step 2: Analyze Photos (Duplicates, Blur, Screenshots)"
echo "======================================================================"
echo ""

python3 "$SCRIPT_DIR/photo_cleanup.py"

if [ $? -ne 0 ]; then
    echo "❌ Photo scan failed!"
    exit 1
fi

echo ""
echo "Moving problematic photos to trash..."
python3 "$SCRIPT_DIR/auto_cleanup.py"

if [ $? -ne 0 ]; then
    echo "❌ Photo cleanup failed!"
    exit 1
fi

echo ""
echo "✓ Photos moved to trash"

# Step 3: Index-Based Video Analysis & Deletion
echo ""
echo "======================================================================"
echo "Step 3: Analyze Videos Using Index"
echo "======================================================================"
echo ""
echo "Using index metadata to find:"
echo "  - Large videos (>100MB) older than 2 years"
echo "  - Short videos (<5 sec) older than 1 year"
echo ""

# Show what would be deleted
echo "Analyzing index..."
python3 "$SCRIPT_DIR/delete_by_criteria.py" <<< "no"

DELETE_VIDEOS=false
echo ""

if [[ "$HEADLESS" == "true" ]]; then
    echo "Headless mode: Auto-confirming video deletion"
    DELETE_VIDEOS=true
else
    read -p "Delete these videos from iCloud? (yes/no): " CONFIRM_VIDEO_DELETE
    if [[ "$CONFIRM_VIDEO_DELETE" == "yes" ]]; then
        DELETE_VIDEOS=true
    fi
fi

# Step 4: Delete from iCloud
echo ""
echo "======================================================================"
echo "Step 4: Delete from iCloud"
echo "======================================================================"
echo ""

# Check if there's anything to delete
PHOTOS_IN_TRASH=$(find "$BACKUP_DIR/trash" -type f \( -name "*.heic" -o -name "*.jpg" -o -name "*.png" \) 2>/dev/null | wc -l)
PHOTOS_IN_TRASH=$(echo $PHOTOS_IN_TRASH | tr -d ' ')

echo "Items pending deletion:"
echo "  Photos in trash: $PHOTOS_IN_TRASH"
if [[ "$DELETE_VIDEOS" == "true" ]]; then
    echo "  Videos from index: (see count above)"
fi
echo ""

if [[ "$PHOTOS_IN_TRASH" -gt 0 || "$DELETE_VIDEOS" == "true" ]]; then
    if [[ "$HEADLESS" == "true" ]]; then
        echo "Headless mode: Auto-confirming iCloud deletion"
        DO_DELETE="yes"
    else
        read -p "Proceed with iCloud deletion? (yes/no): " DO_DELETE
    fi

    if [[ "$DO_DELETE" == "yes" ]]; then
        # Delete photos from trash folder
        if [[ "$PHOTOS_IN_TRASH" -gt 0 ]]; then
            echo ""
            echo "Deleting photos from trash..."
            python3 "$SCRIPT_DIR/icloud_delete_fast.py"

            if [ $? -ne 0 ]; then
                echo "❌ Photo deletion failed!"
                exit 1
            fi
        fi

        # Delete videos by criteria
        if [[ "$DELETE_VIDEOS" == "true" ]]; then
            echo ""
            echo "Deleting videos by criteria..."
            python3 "$SCRIPT_DIR/delete_by_criteria.py" <<< "yes"

            if [ $? -ne 0 ]; then
                echo "❌ Video deletion failed!"
                exit 1
            fi
        fi

        echo ""
        echo "✓ iCloud deletion complete"
        echo "  Items are in 'Recently Deleted' for 30 days"
    else
        echo "Skipped iCloud deletion"
    fi
else
    echo "Nothing to delete - skipping"
fi

# Summary
echo ""
echo "======================================================================"
echo "Smart Workflow Complete!"
echo "======================================================================"
echo ""
echo "Summary:"
echo "  - Index: $INDEX_FILE"
echo "  - Local backup: $BACKUP_DIR"
echo "  - Trash folder: $BACKUP_DIR/trash/"
echo ""
echo "What happened:"
echo "  ✓ Downloaded new photos and updated index"
echo "  ✓ Scanned photos for issues and moved to trash"
if [[ "$DELETE_VIDEOS" == "true" ]]; then
    echo "  ✓ Identified videos for deletion using index"
fi
if [[ "$DO_DELETE" == "yes" ]]; then
    echo "  ✓ Deleted items from iCloud"
fi
echo ""
echo "To view index statistics:"
echo "  python3 $SCRIPT_DIR/query_index.py stats"
echo ""
echo "To permanently delete local trash:"
echo "  rm -rf $BACKUP_DIR/trash/"
echo ""
