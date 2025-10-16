#!/usr/bin/env python3
"""
iCloud Photo Deleter
- Deletes photos from iCloud that are in the local trash folder
- Uses existing authentication session
- Shows progress and saves state
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
DELETE_LOG = BACKUP_DIR / "delete_log.txt"
DELETE_PROGRESS = BACKUP_DIR / "delete_progress.json"

# Configuration
BATCH_SIZE = 10  # Delete in small batches
DELAY_BETWEEN_BATCHES = 2  # seconds

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
    filenames = []
    for root, dirs, files in os.walk(TRASH_DIR):
        for file in files:
            if file.lower().endswith(('.heic', '.jpeg', '.jpg', '.png', '.mov', '.mp4')):
                filenames.append(file)
    return filenames

def authenticate():
    """Authenticate with iCloud"""
    log("Starting authentication...")

    # Try to use existing session first
    try:
        api = PyiCloudService(APPLE_ID)

        # Test if session is valid
        _ = api.photos
        log("✓ Using existing authenticated session")
        return api
    except:
        pass

    # Need interactive password entry
    if not sys.stdin.isatty():
        log("ERROR: Not running in an interactive terminal!")
        log("No existing session found. Please authenticate first by running:")
        log("  python3 ~/scripts/icloud-photo-backup/icloud_download_resilient.py")
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
    print("iCloud Photo Deleter")
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
    remaining_filenames = [f for f in trash_filenames if f not in deleted_set and f not in failed_set]

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

        # Build a mapping of filename -> photo object
        log("Building photo index (this may take a few minutes)...")
        photo_map = {}
        count = 0
        seen_filenames = set()
        consecutive_duplicates = 0
        MAX_CONSECUTIVE_DUPLICATES = 500  # Stop if we see 500 already-seen photos in a row

        for photo in photos_album:
            count += 1
            if count % 500 == 0:
                log(f"  Indexed {count} photos...")

            try:
                filename = photo.filename

                # Detect if we're cycling - if we see the same files repeatedly, stop
                if filename in seen_filenames:
                    consecutive_duplicates += 1
                    if consecutive_duplicates >= MAX_CONSECUTIVE_DUPLICATES:
                        log(f"✓ Detected end of photo library (seen {consecutive_duplicates} repeated photos)")
                        break
                    continue
                else:
                    seen_filenames.add(filename)
                    consecutive_duplicates = 0  # Reset counter

                # Check if this is one we need to delete
                if filename in remaining_filenames:
                    photo_map[filename] = photo

                # Stop if we've found all files
                if len(photo_map) == len(remaining_filenames):
                    log(f"✓ Found all {len(remaining_filenames)} photos to delete")
                    break

            except Exception as e:
                continue

        log(f"✓ Indexed {count} photos total")
        log(f"✓ Found {len(seen_filenames)} unique photos in library")
        log(f"✓ Matched {len(photo_map)} photos to delete")
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
                log(f"⊘ Skipped (not found in iCloud): {filename}")
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
                        log(f"✓ Deleted ({deleted}/{len(remaining_filenames)}): {fname}")
                    except Exception as e:
                        failed += 1
                        failed_set.add(fname)
                        log(f"✗ Failed ({failed} total): {fname} - {str(e)[:100]}")

                # Save progress after each batch
                progress['deleted_files'] = list(deleted_set)
                progress['failed_files'] = list(failed_set)
                progress['stats'] = {
                    'deleted': deleted,
                    'failed': failed,
                    'skipped': skipped
                }
                save_progress(progress)

                # Delay between batches
                if batch:
                    time.sleep(DELAY_BETWEEN_BATCHES)

                batch = []

        # Process remaining photos in final batch
        if batch:
            for fname, p in batch:
                try:
                    p.delete()
                    deleted += 1
                    deleted_set.add(fname)
                    log(f"✓ Deleted ({deleted}/{len(remaining_filenames)}): {fname}")
                except Exception as e:
                    failed += 1
                    failed_set.add(fname)
                    log(f"✗ Failed ({failed} total): {fname} - {str(e)[:100]}")

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
            log("Failed photos are logged in delete_progress.json")
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

        # Save progress on error
        log("Saving progress before exit...")
        save_progress(progress)
        sys.exit(1)

if __name__ == "__main__":
    main()
