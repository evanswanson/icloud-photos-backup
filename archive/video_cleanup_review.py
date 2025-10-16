#!/usr/bin/env python3
"""
Video Cleanup Review Tool
Review and selectively delete problematic videos identified by video_cleanup.py
"""

import json
import shutil
from pathlib import Path
from datetime import datetime

BACKUP_DIR = Path("/Users/evanswanson/icloud-photo-backup")
REPORT_FILE = BACKUP_DIR / "video_cleanup_report.json"
TRASH_DIR = BACKUP_DIR / "trash"
DELETION_LOG = BACKUP_DIR / "video_deletion_log.json"

def load_report():
    """Load cleanup report"""
    if not REPORT_FILE.exists():
        print(f"❌ Report file not found: {REPORT_FILE}")
        print("Please run video_cleanup.py first")
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

def review_short_videos(report):
    """Review and delete short videos"""
    short_vids = report.get('short_videos', [])
    if not short_vids:
        print("No short videos found")
        return []

    print("\n" + "=" * 60)
    print("SHORT VIDEOS (Likely Accidental)")
    print("=" * 60)
    print(f"Found {len(short_vids)} short videos")
    print()

    deleted_files = []

    print("Would you like to:")
    print("  1. Review each video individually")
    print("  2. Delete all short videos")
    print("  3. Skip")
    choice = input("Enter choice (1/2/3): ").strip()

    if choice == '1':
        for idx, item in enumerate(short_vids, 1):
            filepath = item['path']
            duration = item['duration']
            size_mb = item['size_mb']
            print(f"\n[{idx}/{len(short_vids)}] {filepath}")
            print(f"Duration: {duration}s | Size: {size_mb} MB")

            response = input("Delete this video? (y/n/q to quit): ").lower()
            if response == 'q':
                break
            elif response == 'y':
                if move_to_trash(filepath):
                    deleted_files.append(filepath)
                    print("  ✓ Moved to trash")

    elif choice == '2':
        total_size = sum(v['size_mb'] for v in short_vids)
        response = input(f"Delete all {len(short_vids)} short videos ({total_size:.2f} MB)? (yes/no): ").lower()
        if response == 'yes':
            for item in short_vids:
                if move_to_trash(item['path']):
                    deleted_files.append(item['path'])
            print(f"✓ Moved {len(deleted_files)} videos to trash")

    return deleted_files

def review_low_res_videos(report):
    """Review and delete low resolution videos"""
    low_res = report.get('low_res_videos', [])
    if not low_res:
        print("No low resolution videos found")
        return []

    print("\n" + "=" * 60)
    print("LOW RESOLUTION VIDEOS")
    print("=" * 60)
    print(f"Found {len(low_res)} low resolution videos")
    print()

    deleted_files = []

    print("Would you like to:")
    print("  1. Review each video individually")
    print("  2. Delete all low resolution videos")
    print("  3. Skip")
    choice = input("Enter choice (1/2/3): ").strip()

    if choice == '1':
        for idx, item in enumerate(low_res, 1):
            filepath = item['path']
            resolution = item.get('resolution', 'unknown')
            size_mb = item['size_mb']
            duration = item.get('duration', 'unknown')
            print(f"\n[{idx}/{len(low_res)}] {filepath}")
            print(f"Resolution: {resolution} | Duration: {duration}s | Size: {size_mb} MB")

            response = input("Delete this video? (y/n/q to quit): ").lower()
            if response == 'q':
                break
            elif response == 'y':
                if move_to_trash(filepath):
                    deleted_files.append(filepath)
                    print("  ✓ Moved to trash")

    elif choice == '2':
        total_size = sum(v['size_mb'] for v in low_res)
        response = input(f"Delete all {len(low_res)} low-res videos ({total_size:.2f} MB)? (yes/no): ").lower()
        if response == 'yes':
            for item in low_res:
                if move_to_trash(item['path']):
                    deleted_files.append(item['path'])
            print(f"✓ Moved {len(deleted_files)} videos to trash")

    return deleted_files

def review_screen_recordings(report):
    """Review and delete old screen recordings"""
    screen_recs = report.get('old_screen_recordings', [])
    if not screen_recs:
        print("No old screen recordings found")
        return []

    print("\n" + "=" * 60)
    print("OLD SCREEN RECORDINGS")
    print("=" * 60)
    print(f"Found {len(screen_recs)} old screen recordings")
    print()

    deleted_files = []

    print("Would you like to:")
    print("  1. Review each recording individually")
    print("  2. Delete all old screen recordings")
    print("  3. Skip")
    choice = input("Enter choice (1/2/3): ").strip()

    if choice == '1':
        for idx, item in enumerate(screen_recs, 1):
            filepath = item['path']
            age_months = item.get('age_months', 'unknown')
            size_mb = item['size_mb']
            print(f"\n[{idx}/{len(screen_recs)}] {filepath}")
            print(f"Age: {age_months} months | Size: {size_mb} MB")

            response = input("Delete this recording? (y/n/q to quit): ").lower()
            if response == 'q':
                break
            elif response == 'y':
                if move_to_trash(filepath):
                    deleted_files.append(filepath)
                    print("  ✓ Moved to trash")

    elif choice == '2':
        total_size = sum(v['size_mb'] for v in screen_recs)
        response = input(f"Delete all {len(screen_recs)} old recordings ({total_size:.2f} MB)? (yes/no): ").lower()
        if response == 'yes':
            for item in screen_recs:
                if move_to_trash(item['path']):
                    deleted_files.append(item['path'])
            print(f"✓ Moved {len(deleted_files)} videos to trash")

    return deleted_files

def review_large_videos(report):
    """Review large videos (informational only)"""
    large_vids = report.get('large_videos', [])
    if not large_vids:
        print("No large videos found")
        return

    print("\n" + "=" * 60)
    print("LARGE VIDEOS (For Review)")
    print("=" * 60)
    print(f"Found {len(large_vids)} large videos")
    total_size_gb = sum(v['size_mb'] for v in large_vids) / 1024
    print(f"Total size: {total_size_gb:.2f} GB")
    print()
    print("These are just for your awareness. Review manually if needed.")
    print()

    # Show top 10 largest
    sorted_vids = sorted(large_vids, key=lambda x: x['size_mb'], reverse=True)[:10]
    for idx, item in enumerate(sorted_vids, 1):
        filepath = Path(item['path']).name
        size_mb = item['size_mb']
        duration = item.get('duration', 'unknown')
        print(f"{idx}. {filepath} - {size_mb:.2f} MB ({duration}s)")

def save_deletion_log(deleted_files):
    """Save log of deleted files"""
    log_entry = {
        'timestamp': datetime.now().isoformat(),
        'deleted_files': deleted_files,
        'count': len(deleted_files)
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
    print("=" * 60)
    print("Video Cleanup Review Tool")
    print("=" * 60)
    print()

    report = load_report()
    if not report:
        return

    print(f"Report from: {report['scan_date']}")
    print(f"Total videos scanned: {report['total_scanned']}")
    print(f"Total size: {report['total_size_gb']} GB")
    print()
    print("⚠️  Videos will be moved to trash folder, not permanently deleted")
    print(f"Trash location: {TRASH_DIR}")
    print()

    all_deleted = []

    # Review each category
    print("\n--- REVIEWING SHORT VIDEOS ---")
    deleted = review_short_videos(report)
    all_deleted.extend(deleted)

    print("\n--- REVIEWING LOW RESOLUTION VIDEOS ---")
    deleted = review_low_res_videos(report)
    all_deleted.extend(deleted)

    print("\n--- REVIEWING OLD SCREEN RECORDINGS ---")
    deleted = review_screen_recordings(report)
    all_deleted.extend(deleted)

    print("\n--- LARGE VIDEOS ---")
    review_large_videos(report)

    # Summary
    print("\n" + "=" * 60)
    print("CLEANUP SUMMARY")
    print("=" * 60)
    print(f"Total videos moved to trash: {len(all_deleted)}")

    if all_deleted:
        # Calculate space saved
        total_saved_mb = 0
        for vid in report.get('short_videos', []) + report.get('low_res_videos', []) + report.get('old_screen_recordings', []):
            if vid['path'] in all_deleted:
                total_saved_mb += vid['size_mb']

        print(f"Space freed: {total_saved_mb:.2f} MB ({total_saved_mb/1024:.2f} GB)")
        save_deletion_log(all_deleted)
        print(f"Deletion log saved to: {DELETION_LOG}")
        print()
        print("To permanently delete these files:")
        print(f"  rm -rf {TRASH_DIR}")
        print()
        print("To restore files from trash:")
        print(f"  Files are in: {TRASH_DIR}")

if __name__ == "__main__":
    main()
