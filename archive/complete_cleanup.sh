#!/bin/bash
# Complete Photo Cleanup Workflow
# Scans, cleans, and optionally deletes from iCloud in one go

set -e  # Exit on error

SCRIPT_DIR="$HOME/scripts/icloud-photo-backup"
BACKUP_DIR="$HOME/icloud-photo-backup"

echo "======================================================================"
echo "Complete iCloud Photo & Video Cleanup Workflow"
echo "======================================================================"
echo ""
echo "This will:"
echo "  1. Scan photos for duplicates, blurry images, screenshots"
echo "  2. Scan videos for old large videos and short clips"
echo "  3. Move problematic media to trash"
echo "  4. Optionally delete from iCloud"
echo ""
read -p "Continue? (yes/no): " CONTINUE

if [[ "$CONTINUE" != "yes" ]]; then
    echo "Cancelled."
    exit 0
fi

echo ""
echo "======================================================================"
echo "Step 1: Scanning Photos"
echo "======================================================================"
python3 "$SCRIPT_DIR/photo_cleanup.py"

if [ $? -ne 0 ]; then
    echo "❌ Photo scan failed!"
    exit 1
fi

echo ""
read -p "Review the photo report above. Move problematic photos to trash? (yes/no): " CLEANUP_PHOTOS

# Video cleanup
echo ""
echo "======================================================================"
echo "Step 2: Scanning Videos (Aggressive)"
echo "======================================================================"
echo "Looking for:"
echo "  - Large videos (>100MB) older than 2 years"
echo "  - Short videos (<5 sec) older than 1 year"
echo ""
python3 "$SCRIPT_DIR/video_cleanup_aggressive.py"

if [ $? -ne 0 ]; then
    echo "❌ Video scan failed!"
    exit 1
fi

echo ""
read -p "Review the video report above. Move problematic videos to trash? (yes/no): " CLEANUP_VIDEOS

# Execute cleanups
if [[ "$CLEANUP_PHOTOS" == "yes" ]]; then
    echo ""
    echo "======================================================================"
    echo "Step 3a: Moving Photos to Trash"
    echo "======================================================================"
    python3 "$SCRIPT_DIR/auto_cleanup.py"

    if [ $? -ne 0 ]; then
        echo "❌ Photo cleanup failed!"
        exit 1
    fi

    echo ""
    echo "✓ Photos moved to trash: $BACKUP_DIR/trash/"
fi

if [[ "$CLEANUP_VIDEOS" == "yes" ]]; then
    echo ""
    echo "======================================================================"
    echo "Step 3b: Moving Videos to Trash"
    echo "======================================================================"
    python3 "$SCRIPT_DIR/video_cleanup_aggressive_review.py"

    if [ $? -ne 0 ]; then
        echo "❌ Video cleanup failed!"
        exit 1
    fi

    echo ""
    echo "✓ Videos moved to trash: $BACKUP_DIR/trash/"
fi

if [[ "$CLEANUP_PHOTOS" == "yes" || "$CLEANUP_VIDEOS" == "yes" ]]; then
    echo ""
    read -p "Delete all trashed media from iCloud? (yes/no): " DELETE_ICLOUD

    if [[ "$DELETE_ICLOUD" == "yes" ]]; then
        echo ""
        echo "======================================================================"
        echo "Step 4: Deleting from iCloud"
        echo "======================================================================"
        echo ""
        echo "Checking for index..."

        if [ -f "$BACKUP_DIR/icloud_index.json" ]; then
            echo "✓ Index found - using fast deletion"
            python3 "$SCRIPT_DIR/icloud_delete_fast.py"
        else
            echo "⚠️  No index found - using standard deletion (slower)"
            echo ""
            read -p "Build index for faster future deletions? (yes/no): " BUILD_INDEX

            if [[ "$BUILD_INDEX" == "yes" ]]; then
                echo ""
                echo "Building index (one-time operation)..."
                python3 "$SCRIPT_DIR/build_icloud_index.py"
                echo ""
                echo "Now deleting with fast method..."
                python3 "$SCRIPT_DIR/icloud_delete_fast.py"
            else
                echo "Using slower deletion method..."
                python3 "$SCRIPT_DIR/icloud_delete_photos_v2.py"
            fi
        fi

        if [ $? -ne 0 ]; then
            echo "❌ iCloud deletion failed!"
            exit 1
        fi

        echo ""
        echo "✓ Media deleted from iCloud"
        echo "  (They're in 'Recently Deleted' for 30 days)"
    fi
else
    echo "Skipped cleanup."
fi

echo ""
echo "======================================================================"
echo "Cleanup Complete!"
echo "======================================================================"
echo ""
echo "Summary:"
echo "  - Photo scan report: $BACKUP_DIR/cleanup_report.json"
echo "  - Video scan report: $BACKUP_DIR/video_cleanup_aggressive_report.json"
echo "  - Trash folder: $BACKUP_DIR/trash/"
echo ""
echo "To view trash contents:"
echo "  ls -lh $BACKUP_DIR/trash/"
echo ""
echo "To permanently delete trash:"
echo "  rm -rf $BACKUP_DIR/trash/"
echo ""
