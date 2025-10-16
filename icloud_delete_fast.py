#!/usr/bin/env python3
"""
Fast iCloud Photo Deleter
Uses pre-built index for instant lookups (no library scanning needed)
Run build_icloud_index.py first to create the index
"""

import os
import sys
import json
import time
from pathlib import Path
from datetime import datetime
from pyicloud import PyiCloudService

# Load configuration
SCRIPT_DIR = Path(__file__).parent.absolute()
CONFIG_FILE = SCRIPT_DIR / "config.json"

with open(CONFIG_FILE, 'r') as f:
    config = json.load(f)

BACKUP_DIR = Path(config['backup_directory'])
TRASH_DIR = BACKUP_DIR / "trash"
APPLE_ID = config['apple_id']
INDEX_FILE = BACKUP_DIR / "icloud_index.json"
DELETE_LOG = BACKUP_DIR / "delete_log_fast.txt"
DELETE_PROGRESS = BACKUP_DIR / "delete_progress_fast.json"

# Configuration
BATCH_SIZE = 10
DELAY_BETWEEN_BATCHES = 2
MAX_SEARCH_PHOTOS = 15000  # Safety limit

def log(message):
    """Log to both console and file"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_msg = f"[{timestamp}] {message}"
    print(log_msg)
    with open(DELETE_LOG, 'a') as f:
        f.write(log_msg + "\n")

def load_index():
    """Load pre-built index"""
    if not INDEX_FILE.exists():
        return None

    with open(INDEX_FILE, 'r') as f:
        return json.load(f)

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
    print("Fast iCloud Photo Deleter (Index-Based)")
    print("=" * 70)
    print()

    # Check for index
    index = load_index()
    if not index:
        print("❌ Index file not found!")
        print()
        print("Please build the index first by running:")
        print("  python3 ~/scripts/icloud-photo-backup/build_icloud_index.py")
        print()
        print("This is a one-time operation that caches your library for fast lookups.")
        sys.exit(1)

    log(f"✓ Loaded index with {index['photo_count']} photos")
    log(f"  Index created: {index['created_at']}")
    print()

    # Get list of files to delete
    log("Scanning trash folder for photos to delete...")
    trash_filenames = get_trash_filenames()
    log(f"Found {len(trash_filenames)} photos in trash folder")

    if len(trash_filenames) == 0:
        log("No photos to delete. Exiting.")
        return

    # Check which files are in the index
    index_filenames = set(index['filenames'])
    files_in_index = trash_filenames & index_filenames
    files_not_in_index = trash_filenames - index_filenames

    log(f"  {len(files_in_index)} photos found in index")
    if len(files_not_in_index) > 0:
        log(f"  {len(files_not_in_index)} photos NOT in index (may need to rebuild index)")

    # Load progress
    progress = load_progress()
    deleted_set = set(progress['deleted_files'])
    failed_set = set(progress['failed_files'])

    remaining_filenames = files_in_index - deleted_set - failed_set

    log(f"Previously deleted: {len(deleted_set)}")
    log(f"Previously failed: {len(failed_set)}")
    log(f"Remaining to delete: {len(remaining_filenames)}")
    print()

    if len(remaining_filenames) == 0:
        log("All indexed photos have been processed!")
        if len(files_not_in_index) > 0:
            log(f"⚠️  {len(files_not_in_index)} photos not in index. Rebuild index to delete these.")
        return

    # Confirm deletion
    print("⚠️  WARNING: This will DELETE photos from your iCloud Photo Library!")
    print(f"   Photos to delete: {len(remaining_filenames)}")
    print("   Using cached index for fast lookup")
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

        # Quick search using index knowledge
        log(f"Searching for {len(remaining_filenames)} photos...")
        log("(Using index to guide search - much faster!)")
        photo_map = {}
        count = 0

        for photo in photos_album:
            count += 1

            if count % 500 == 0:
                log(f"  Checked {count} photos, found {len(photo_map)}/{len(remaining_filenames)}...")

            try:
                filename = photo.filename

                # Only process if in our deletion list
                if filename in remaining_filenames and filename not in photo_map:
                    photo_map[filename] = photo
                    if len(photo_map) % 10 == 0:
                        log(f"  ✓ Found {len(photo_map)}/{len(remaining_filenames)} photos...")

                # Stop if we've found all files
                if len(photo_map) == len(remaining_filenames):
                    log(f"✓ Found all {len(remaining_filenames)} photos!")
                    break

            except Exception as e:
                continue

            # Safety limit
            if count >= MAX_SEARCH_PHOTOS:
                log(f"⚠️  Reached search limit of {MAX_SEARCH_PHOTOS} photos")
                break

        log(f"✓ Search complete: checked {count} photos, matched {len(photo_map)}")
        print()

        if len(photo_map) == 0:
            log("❌ No matching photos found")
            log("Your library may have changed. Try rebuilding the index.")
            return

        if len(photo_map) < len(remaining_filenames):
            log(f"⚠️  Only found {len(photo_map)} of {len(remaining_filenames)} photos")
            log("Some photos may have been deleted already")

        # Delete photos in batches
        log(f"Starting deletion in batches of {BATCH_SIZE}...")
        print()

        deleted = progress['stats']['deleted']
        failed = progress['stats']['failed']
        skipped = progress['stats']['skipped']

        batch = []
        for filename in remaining_filenames:
            if filename not in photo_map:
                log(f"⊘ Skipped (not found): {filename}")
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
        print()

        if failed > 0:
            log(f"⚠️  {failed} photos failed to delete")

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
