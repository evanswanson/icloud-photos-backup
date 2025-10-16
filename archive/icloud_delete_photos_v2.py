#!/usr/bin/env python3
"""
iCloud Photo Deleter v2
- Uses limited iteration with early stopping
- More efficient for small deletion batches
"""

import os
import sys
import json
import time
from pathlib import Path
from datetime import datetime
from pyicloud import PyiCloudService

BACKUP_DIR = Path("/Users/evanswanson/icloud-photo-backup")
TRASH_DIR = BACKUP_DIR / "trash"
APPLE_ID = "evan.swanson.receipt@gmail.com"
DELETE_LOG = BACKUP_DIR / "delete_log_v2.txt"
DELETE_PROGRESS = BACKUP_DIR / "delete_progress_v2.json"

# Configuration
BATCH_SIZE = 10
DELAY_BETWEEN_BATCHES = 2
MAX_PHOTOS_TO_CHECK = 10000  # Stop after checking this many photos

def log(message):
    """Log to both console and file"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_msg = f"[{timestamp}] {message}"
    print(log_msg)
    with open(DELETE_LOG, 'a') as f:
        f.write(log_msg + "\n")

def load_progress():
    """Load deletion progress"""
    if DELETE_PROGRESS.exists():
        with open(DELETE_PROGRESS, 'r') as f:
            return json.load(f)
    return {
        'deleted_files': [],
        'failed_files': [],
        'stats': {
            'deleted': 0,
            'failed': 0,
            'skipped': 0
        }
    }

def save_progress(progress):
    """Save deletion progress"""
    with open(DELETE_PROGRESS, 'w') as f:
        json.dump(progress, f, indent=2)

def get_trash_filenames():
    """Get list of filenames to delete from trash folder"""
    filenames = set()
    for root, dirs, files in os.walk(TRASH_DIR):
        for file in files:
            if file.lower().endswith(('.heic', '.jpeg', '.jpg', '.png', '.mov', '.mp4')):
                filenames.add(file)
    return filenames

def authenticate():
    """Authenticate with iCloud"""
    log("Starting authentication...")

    try:
        api = PyiCloudService(APPLE_ID)
        _ = api.photos
        log("✓ Using existing authenticated session")
        return api
    except:
        pass

    if not sys.stdin.isatty():
        log("ERROR: Not running in an interactive terminal!")
        log("No existing session found. Please authenticate first.")
        sys.exit(1)

    import getpass
    password = getpass.getpass("Enter your Apple ID password: ")

    try:
        api = PyiCloudService(APPLE_ID, password)

        if api.requires_2fa:
            print("\nTwo-factor authentication required.")
            code = input("Enter the code you received on your trusted device: ")
            result = api.validate_2fa_code(code)

            if not result:
                log("Failed to verify security code")
                sys.exit(1)

            if not api.is_trusted_session:
                log("Requesting trusted session...")
                result = api.trust_session()

        log("✓ Authentication successful!")
        return api

    except Exception as e:
        log(f"❌ Authentication failed: {e}")
        sys.exit(1)

def main():
    print("=" * 70)
    print("iCloud Photo Deleter v2 (Optimized)")
    print("=" * 70)
    print()

    # Get list of files to delete
    log("Scanning trash folder for photos to delete...")
    trash_filenames = get_trash_filenames()
    log(f"Found {len(trash_filenames)} photos in trash folder")

    if len(trash_filenames) == 0:
        log("No photos to delete. Exiting.")
        return

    # Load progress
    progress = load_progress()
    deleted_set = set(progress['deleted_files'])
    failed_set = set(progress['failed_files'])

    # Filter out already processed files
    remaining_filenames = trash_filenames - deleted_set - failed_set

    log(f"Previously deleted: {len(deleted_set)}")
    log(f"Previously failed: {len(failed_set)}")
    log(f"Remaining to delete: {len(remaining_filenames)}")
    print()

    if len(remaining_filenames) == 0:
        log("All photos have been processed. Exiting.")
        return

    # Confirm deletion
    print("⚠️  WARNING: This will DELETE photos from your iCloud Photo Library!")
    print(f"   Photos to delete: {len(remaining_filenames)}")
    print(f"   Will check up to {MAX_PHOTOS_TO_CHECK} photos in your library")
    print("   They will be moved to 'Recently Deleted' album for 30 days.")
    print()
    response = input("Are you sure you want to continue? (yes/no): ")

    if response.lower() not in ['yes', 'y']:
        log("Deletion cancelled by user")
        return

    print()

    # Authenticate
    api = authenticate()
    print()

    # Access photos
    log("Accessing iCloud Photos library...")
    try:
        photos_album = api.photos.all
        log("✓ Connected to iCloud Photos library!")
        print()

        # Build photo map with limited iteration
        log(f"Searching for photos to delete (max {MAX_PHOTOS_TO_CHECK} photos)...")
        photo_map = {}
        count = 0
        found_all = False

        for photo in photos_album:
            count += 1

            if count % 500 == 0:
                log(f"  Checked {count} photos, found {len(photo_map)} matches so far...")

            try:
                filename = photo.filename
                if filename in remaining_filenames and filename not in photo_map:
                    photo_map[filename] = photo
                    log(f"  ✓ Found: {filename} ({len(photo_map)}/{len(remaining_filenames)})")

                # Stop if we've found all files
                if len(photo_map) == len(remaining_filenames):
                    log(f"✓ Found all {len(remaining_filenames)} photos to delete!")
                    found_all = True
                    break

            except Exception as e:
                continue

            # Stop after max photos checked
            if count >= MAX_PHOTOS_TO_CHECK:
                log(f"⚠️  Reached limit of {MAX_PHOTOS_TO_CHECK} photos checked")
                break

        log(f"✓ Checked {count} photos total")
        log(f"✓ Matched {len(photo_map)} photos to delete")

        if not found_all and len(photo_map) < len(remaining_filenames):
            log(f"⚠️  Only found {len(photo_map)} of {len(remaining_filenames)} photos")
            log("   Some photos may not be in your iCloud library")

        print()

        if len(photo_map) == 0:
            log("❌ No matching photos found in iCloud library")
            log("Photos may have already been deleted or have different filenames")
            return

        # Delete photos in batches
        log(f"Starting deletion in batches of {BATCH_SIZE}...")
        print()

        deleted = progress['stats']['deleted']
        failed = progress['stats']['failed']
        skipped = progress['stats']['skipped']

        batch = []
        for filename in remaining_filenames:
            if filename not in photo_map:
                log(f"⊘ Skipped (not found in library): {filename}")
                skipped += 1
                continue

            photo = photo_map[filename]
            batch.append((filename, photo))

            # Process batch
            if len(batch) >= BATCH_SIZE:
                for fname, p in batch:
                    try:
                        p.delete()
                        deleted += 1
                        deleted_set.add(fname)
                        log(f"✓ Deleted ({deleted}): {fname}")
                    except Exception as e:
                        failed += 1
                        failed_set.add(fname)
                        log(f"✗ Failed: {fname} - {str(e)[:100]}")

                # Save progress after each batch
                progress['deleted_files'] = list(deleted_set)
                progress['failed_files'] = list(failed_set)
                progress['stats'] = {
                    'deleted': deleted,
                    'failed': failed,
                    'skipped': skipped
                }
                save_progress(progress)

                time.sleep(DELAY_BETWEEN_BATCHES)
                batch = []

        # Process remaining photos in final batch
        if batch:
            for fname, p in batch:
                try:
                    p.delete()
                    deleted += 1
                    deleted_set.add(fname)
                    log(f"✓ Deleted ({deleted}): {fname}")
                except Exception as e:
                    failed += 1
                    failed_set.add(fname)
                    log(f"✗ Failed: {fname} - {str(e)[:100]}")

        # Final save
        progress['deleted_files'] = list(deleted_set)
        progress['failed_files'] = list(failed_set)
        progress['stats'] = {
            'deleted': deleted,
            'failed': failed,
            'skipped': skipped
        }
        save_progress(progress)

        print()
        print("=" * 70)
        print("Deletion Complete!")
        print("=" * 70)
        log(f"Successfully deleted: {deleted}")
        log(f"Skipped (not found): {skipped}")
        log(f"Failed: {failed}")
        print()
        log("Deleted photos are in 'Recently Deleted' album in iCloud Photos")
        log("They will be permanently deleted after 30 days")
        log("You can restore them before then if needed")
        print()

        if failed > 0:
            log(f"⚠️  {failed} photos failed to delete")
            log("You can retry by running this script again")

    except KeyboardInterrupt:
        log("\n\n⚠️  Deletion interrupted by user!")
        log("Saving progress...")
        save_progress(progress)
        log("✓ Progress saved. Run the script again to resume.")
        sys.exit(0)

    except Exception as e:
        log(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        save_progress(progress)
        sys.exit(1)

if __name__ == "__main__":
    main()
