#!/usr/bin/env python3
"""
Resilient iCloud Photo Downloader
- Automatically resumes from where it left off
- Skips already downloaded photos
- Handles network errors gracefully
- Saves progress regularly
"""

import os
import sys
import json
import time
from pathlib import Path
from datetime import datetime
from pyicloud import PyiCloudService

BACKUP_DIR = Path("/Users/evanswanson/icloud-photo-backup")
APPLE_ID = "evan.swanson.receipt@gmail.com"
PROGRESS_FILE = BACKUP_DIR / "download_progress.json"
LOG_FILE = BACKUP_DIR / "download_log.txt"

# Configuration
RETRY_ATTEMPTS = 3
RETRY_DELAY = 5  # seconds
SAVE_PROGRESS_EVERY = 50  # Save progress every N photos

def log(message):
    """Log to both console and file"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_msg = f"[{timestamp}] {message}"
    print(log_msg)
    with open(LOG_FILE, 'a') as f:
        f.write(log_msg + "\n")

def load_progress():
    """Load download progress from file"""
    if PROGRESS_FILE.exists():
        with open(PROGRESS_FILE, 'r') as f:
            return json.load(f)
    return {
        'downloaded_files': [],
        'failed_files': [],
        'last_index': 0,
        'stats': {
            'downloaded': 0,
            'skipped': 0,
            'failed': 0
        }
    }

def save_progress(progress):
    """Save download progress to file"""
    with open(PROGRESS_FILE, 'w') as f:
        json.dump(progress, f, indent=2)

def file_exists_and_valid(filepath):
    """Check if file exists and has content"""
    return filepath.exists() and filepath.stat().st_size > 0

def download_photo_with_retry(photo, output_path, max_retries=RETRY_ATTEMPTS):
    """Download a photo with retry logic"""
    for attempt in range(max_retries):
        try:
            download = photo.download()
            with open(output_path, 'wb') as f:
                f.write(download.raw.read())
            return True
        except Exception as e:
            if attempt < max_retries - 1:
                log(f"  Retry {attempt + 1}/{max_retries} after error: {str(e)[:100]}")
                time.sleep(RETRY_DELAY)
            else:
                log(f"  Failed after {max_retries} attempts: {str(e)[:100]}")
                return False
    return False

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
        log("  python3 /Users/evanswanson/icloud_download_resilient.py")
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
    print("Resilient iCloud Photo Downloader")
    print("=" * 70)
    print()
    print(f"Apple ID: {APPLE_ID}")
    print(f"Backup Directory: {BACKUP_DIR}")
    print(f"Log File: {LOG_FILE}")
    print(f"Progress File: {PROGRESS_FILE}")
    print()

    # Create backup directory
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)

    # Load previous progress
    progress = load_progress()

    if progress['last_index'] > 0:
        log(f"Resuming from previous session...")
        log(f"Previously downloaded: {progress['stats']['downloaded']}")
        log(f"Previously skipped: {progress['stats']['skipped']}")
        log(f"Previously failed: {progress['stats']['failed']}")
        log(f"Last index: {progress['last_index']}")
        print()

    # Authenticate
    api = authenticate()
    print()

    # Access photos
    log("Accessing iCloud Photos library...")
    try:
        photos_album = api.photos.all

        log("✓ Connected to iCloud Photos library!")
        log("Starting download (photos will be counted as we go)...")
        print()

        downloaded = progress['stats']['downloaded']
        skipped = progress['stats']['skipped']
        failed = progress['stats']['failed']

        downloaded_set = set(progress['downloaded_files'])
        start_idx = progress['last_index']

        log(f"Progress will be saved every {SAVE_PROGRESS_EVERY} photos")
        print()

        # Iterate directly through the album
        photo_num = 0
        seen_filenames = set()
        consecutive_duplicates = 0
        MAX_CONSECUTIVE_DUPLICATES = 500  # Stop if we see 500 already-processed photos in a row

        for photo in photos_album:
            photo_num += 1

            # Skip photos before our resume point
            if photo_num <= start_idx:
                continue

            try:
                filename = photo.filename

                # Detect if we're looping - if we see the same files repeatedly, stop
                if filename in seen_filenames:
                    consecutive_duplicates += 1
                    if consecutive_duplicates > MAX_CONSECUTIVE_DUPLICATES:
                        log(f"\n✓ Detected end of photo library (seen {consecutive_duplicates} repeated photos)")
                        log("All unique photos have been processed!")
                        break
                    # Skip already-seen photos
                    if photo_num % 50 == 0:
                        log(f"[{photo_num}] Downloaded: {downloaded}, Skipped: {skipped}, Failed: {failed} (cycling through seen photos)")
                    continue
                else:
                    seen_filenames.add(filename)
                    consecutive_duplicates = 0  # Reset counter when we see a new file

                # Skip if already downloaded
                if filename in downloaded_set:
                    skipped += 1
                    if photo_num % 50 == 0:
                        log(f"[{photo_num}] Downloaded: {downloaded}, Skipped: {skipped}, Failed: {failed}")
                    continue

                created = photo.created
                year = created.strftime("%Y")
                month = created.strftime("%m")
                folder = BACKUP_DIR / year / month
                folder.mkdir(parents=True, exist_ok=True)

                output_path = folder / filename

                # Skip if file exists and is valid
                if file_exists_and_valid(output_path):
                    skipped += 1
                    downloaded_set.add(filename)
                    if photo_num % 50 == 0:
                        log(f"[{photo_num}] Downloaded: {downloaded}, Skipped: {skipped}, Failed: {failed}")
                    continue

                # Download with retry
                success = download_photo_with_retry(photo, output_path)

                if success:
                    downloaded += 1
                    downloaded_set.add(filename)
                    # Log every successful download
                    log(f"[{photo_num}] Downloaded: {downloaded}, Skipped: {skipped}, Failed: {failed} | {filename}")
                else:
                    failed += 1
                    progress['failed_files'].append({
                        'filename': filename,
                        'index': photo_num,
                        'timestamp': datetime.now().isoformat()
                    })
                    log(f"[{photo_num}] ✗ Failed: {filename}")

                # Save progress periodically
                if photo_num % SAVE_PROGRESS_EVERY == 0:
                    progress['last_index'] = photo_num
                    progress['downloaded_files'] = list(downloaded_set)
                    progress['stats'] = {
                        'downloaded': downloaded,
                        'skipped': skipped,
                        'failed': failed
                    }
                    save_progress(progress)
                    log(f"  → Progress saved (checkpoint at photo #{photo_num})")

            except KeyboardInterrupt:
                log("\n\n⚠️  Download interrupted by user!")
                log("Saving progress...")
                progress['last_index'] = photo_num
                progress['downloaded_files'] = list(downloaded_set)
                progress['stats'] = {
                    'downloaded': downloaded,
                    'skipped': skipped,
                    'failed': failed
                }
                save_progress(progress)
                log("✓ Progress saved. Run the script again to resume.")
                sys.exit(0)

            except Exception as e:
                failed += 1
                log(f"[{photo_num}] ✗ Unexpected error: {str(e)[:200]}")
                continue

        # Final save
        progress['last_index'] = photo_num
        progress['downloaded_files'] = list(downloaded_set)
        progress['stats'] = {
            'downloaded': downloaded,
            'skipped': skipped,
            'failed': failed
        }
        save_progress(progress)

        print()
        print("=" * 70)
        print("Download Complete!")
        print("=" * 70)
        log(f"Total photos processed: {photo_num}")
        log(f"Downloaded: {downloaded}")
        log(f"Skipped (already exists): {skipped}")
        log(f"Failed: {failed}")
        print()
        log(f"Backup location: {BACKUP_DIR}")

        if failed > 0:
            log(f"\n⚠️  {failed} photos failed to download")
            log("Failed photos are logged in the progress file")
            log("You can retry by running this script again")

        print()
        log("Next steps:")
        log("  1. Scan for duplicates/quality issues:")
        log("     python3 /Users/evanswanson/photo_cleanup.py")
        log("")
        log("  2. Clean up problematic images:")
        log("     python3 /Users/evanswanson/auto_cleanup.py")

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
