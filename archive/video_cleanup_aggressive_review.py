#!/usr/bin/env python3
"""
Aggressive Video Cleanup Review Tool
Review and delete videos identified by video_cleanup_aggressive.py
"""

import json
import shutil
from pathlib import Path
from datetime import datetime

BACKUP_DIR = Path("/Users/evanswanson/icloud-photo-backup")
REPORT_FILE = BACKUP_DIR / "video_cleanup_aggressive_report.json"
TRASH_DIR = BACKUP_DIR / "trash"
DELETION_LOG = BACKUP_DIR / "video_deletion_aggressive_log.json"

def load_report():
    """Load cleanup report"""
    if not REPORT_FILE.exists():
        print(f"❌ Report file not found: {REPORT_FILE}")
        print("Please run video_cleanup_aggressive.py first")
        return None

    with open(REPORT_FILE, 'r') as f:
        return json.load(f)

def move_to_trash(filepath):
    """Move file to trash directory"""
    TRASH_DIR.mkdir(parents=True, exist_ok=True)

    src = Path(filepath)
    if not src.exists():
        return False

    rel_path = src.relative_to(BACKUP_DIR) if src.is_relative_to(BACKUP_DIR) else src.name
    dst = TRASH_DIR / rel_path
    dst.parent.mkdir(parents=True, exist_ok=True)

    if dst.exists():
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        dst = dst.parent / f"{dst.stem}_{timestamp}{dst.suffix}"

    shutil.move(str(src), str(dst))
    return True

def review_old_large_videos(report):
    """Review and delete old large videos"""
    old_large = report.get('old_large_videos', [])
    if not old_large:
        print("No old large videos found")
        return []

    criteria = report.get('criteria', {})
    size_mb = criteria.get('large_video_size_mb', 100)
    age_years = criteria.get('large_video_age_years', 2)

    print("\n" + "=" * 70)
    print(f"OLD LARGE VIDEOS (>{size_mb}MB, >{age_years} years old)")
    print("=" * 70)
    print(f"Found {len(old_large)} old large videos")
    total_size_gb = sum(v['size_mb'] for v in old_large) / 1024
    print(f"Total size: {total_size_gb:.2f} GB")
    print()

    deleted_files = []

    print("Would you like to:")
    print("  1. Review each video individually")
    print("  2. Delete all old large videos")
    print("  3. Skip")
    choice = input("Enter choice (1/2/3): ").strip()

    if choice == '1':
        for idx, item in enumerate(old_large, 1):
            filepath = item['path']
            size_mb = item['size_mb']
            age_years = item['age_years']
            duration = item.get('duration', 'unknown')

            filename = Path(filepath).name
            print(f"\n[{idx}/{len(old_large)}] {filename}")
            print(f"  Path: {filepath}")
            print(f"  Size: {size_mb:.1f} MB")
            print(f"  Age: {age_years:.1f} years")
            print(f"  Duration: {duration}s" if duration != 'unknown' else "  Duration: unknown")

            response = input("Delete this video? (y/n/q to quit): ").lower()
            if response == 'q':
                break
            elif response == 'y':
                if move_to_trash(filepath):
                    deleted_files.append(filepath)
                    print("  ✓ Moved to trash")

    elif choice == '2':
        response = input(f"Delete all {len(old_large)} old large videos ({total_size_gb:.2f} GB)? (yes/no): ").lower()
        if response == 'yes':
            for item in old_large:
                if move_to_trash(item['path']):
                    deleted_files.append(item['path'])
            print(f"✓ Moved {len(deleted_files)} videos to trash")

    return deleted_files

def review_old_short_videos(report):
    """Review and delete old short videos"""
    old_short = report.get('old_short_videos', [])
    if not old_short:
        print("No old short videos found")
        return []

    criteria = report.get('criteria', {})
    duration = criteria.get('short_video_duration', 5)
    age_years = criteria.get('short_video_age_years', 1)

    print("\n" + "=" * 70)
    print(f"OLD SHORT VIDEOS (<{duration}s, >{age_years} year old)")
    print("=" * 70)
    print(f"Found {len(old_short)} old short videos")
    total_size_mb = sum(v['size_mb'] for v in old_short)
    print(f"Total size: {total_size_mb:.2f} MB")
    print()

    deleted_files = []

    print("Would you like to:")
    print("  1. Review each video individually")
    print("  2. Delete all old short videos")
    print("  3. Skip")
    choice = input("Enter choice (1/2/3): ").strip()

    if choice == '1':
        for idx, item in enumerate(old_short, 1):
            filepath = item['path']
            size_mb = item['size_mb']
            age_years = item['age_years']
            vid_duration = item.get('duration', 'unknown')

            filename = Path(filepath).name
            print(f"\n[{idx}/{len(old_short)}] {filename}")
            print(f"  Path: {filepath}")
            print(f"  Size: {size_mb:.1f} MB")
            print(f"  Duration: {vid_duration}s")
            print(f"  Age: {age_years:.1f} years")

            response = input("Delete this video? (y/n/q to quit): ").lower()
            if response == 'q':
                break
            elif response == 'y':
                if move_to_trash(filepath):
                    deleted_files.append(filepath)
                    print("  ✓ Moved to trash")

    elif choice == '2':
        response = input(f"Delete all {len(old_short)} old short videos ({total_size_mb:.2f} MB)? (yes/no): ").lower()
        if response == 'yes':
            for item in old_short:
                if move_to_trash(item['path']):
                    deleted_files.append(item['path'])
            print(f"✓ Moved {len(deleted_files)} videos to trash")

    return deleted_files

def save_deletion_log(deleted_files, report):
    """Save log of deleted files"""
    log_entry = {
        'timestamp': datetime.now().isoformat(),
        'criteria': report.get('criteria', {}),
        'deleted_files': deleted_files,
        'count': len(deleted_files),
        'space_freed_mb': sum(
            item['size_mb']
            for item in report.get('old_large_videos', []) + report.get('old_short_videos', [])
            if item['path'] in deleted_files
        )
    }

    if DELETION_LOG.exists():
        with open(DELETION_LOG, 'r') as f:
            log = json.load(f)
    else:
        log = []

    log.append(log_entry)

    with open(DELETION_LOG, 'w') as f:
        json.dump(log, f, indent=2)

def main():
    print("=" * 70)
    print("Aggressive Video Cleanup Review Tool")
    print("=" * 70)
    print()

    report = load_report()
    if not report:
        return

    print(f"Report from: {report['scan_date']}")
    print(f"Total videos scanned: {report['total_scanned']}")
    print(f"Total size: {report['total_size_gb']} GB")
    print()

    criteria = report.get('criteria', {})
    print("Cleanup criteria:")
    print(f"  - Large videos: >{criteria.get('large_video_size_mb')}MB, >{criteria.get('large_video_age_years')}yr")
    print(f"  - Short videos: <{criteria.get('short_video_duration')}s, >{criteria.get('short_video_age_years')}yr")
    print()
    print("⚠️  Videos will be moved to trash folder, not permanently deleted")
    print(f"Trash location: {TRASH_DIR}")
    print()

    all_deleted = []

    # Review old large videos
    print("\n--- REVIEWING OLD LARGE VIDEOS ---")
    deleted = review_old_large_videos(report)
    all_deleted.extend(deleted)

    # Review old short videos
    print("\n--- REVIEWING OLD SHORT VIDEOS ---")
    deleted = review_old_short_videos(report)
    all_deleted.extend(deleted)

    # Summary
    print("\n" + "=" * 70)
    print("CLEANUP SUMMARY")
    print("=" * 70)
    print(f"Total videos moved to trash: {len(all_deleted)}")

    if all_deleted:
        # Calculate space saved
        total_saved_mb = sum(
            item['size_mb']
            for item in report.get('old_large_videos', []) + report.get('old_short_videos', [])
            if item['path'] in all_deleted
        )

        print(f"Space freed: {total_saved_mb:.2f} MB ({total_saved_mb/1024:.2f} GB)")
        save_deletion_log(all_deleted, report)
        print(f"Deletion log saved to: {DELETION_LOG}")
        print()
        print("Next steps:")
        print("  1. Review trash folder to confirm deletions")
        print("  2. Delete from iCloud using:")
        print("     ~/scripts/icloud-photo-backup/complete_cleanup.sh")
        print()
        print("To permanently delete these files:")
        print(f"  rm -rf {TRASH_DIR}")
        print()
        print("To restore files from trash:")
        print(f"  Files are in: {TRASH_DIR}")

if __name__ == "__main__":
    main()
