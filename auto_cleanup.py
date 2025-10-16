#!/usr/bin/env python3
"""
Automatic cleanup - moves duplicates and blurry images to trash
"""

import json
import shutil
from pathlib import Path
from datetime import datetime

BACKUP_DIR = Path("/Users/evanswanson/icloud-photo-backup")
REPORT_FILE = BACKUP_DIR / "cleanup_report.json"
TRASH_DIR = BACKUP_DIR / "trash"

def move_to_trash(filepath):
    """Move file to trash directory"""
    TRASH_DIR.mkdir(parents=True, exist_ok=True)

    src = Path(filepath)
    if not src.exists():
        return False

    rel_path = src.relative_to(BACKUP_DIR)
    dst = TRASH_DIR / rel_path
    dst.parent.mkdir(parents=True, exist_ok=True)

    if dst.exists():
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        dst = dst.parent / f"{dst.stem}_{timestamp}{dst.suffix}"

    shutil.move(str(src), str(dst))
    return True

def main():
    print("=" * 60)
    print("Automatic Photo Cleanup")
    print("=" * 60)
    print()

    with open(REPORT_FILE, 'r') as f:
        report = json.load(f)

    deleted_count = 0

    # Move duplicates to trash (keep originals)
    print("Moving duplicate images to trash...")
    for original, dupes in report['duplicates'].items():
        print(f"\nKeeping: {Path(original).name}")
        for dupe in dupes:
            if move_to_trash(dupe):
                print(f"  ✓ Moved: {Path(dupe).name}")
                deleted_count += 1

    # Move blurry images to trash
    print("\nMoving blurry images to trash...")
    for img in report['blurry_images']:
        filepath = img['path']
        score = img['blur_score']
        if move_to_trash(filepath):
            print(f"  ✓ Moved: {Path(filepath).name} (blur score: {score:.2f})")
            deleted_count += 1

    print()
    print("=" * 60)
    print("Cleanup Complete")
    print("=" * 60)
    print(f"Files moved to trash: {deleted_count}")
    print(f"Trash location: {TRASH_DIR}")
    print()
    print("To restore files:")
    print(f"  Files are in {TRASH_DIR}")
    print()
    print("To permanently delete:")
    print(f"  rm -rf {TRASH_DIR}")

if __name__ == "__main__":
    main()
