#!/usr/bin/env python3
"""
Delete from iCloud by Criteria (Index-Based)
Uses index metadata to identify and delete files without local analysis
"""

import sys
import json
import time
import subprocess
from pathlib import Path
from datetime import datetime, timedelta
from pyicloud import PyiCloudService

# Load configuration
SCRIPT_DIR = Path(__file__).parent.absolute()
CONFIG_FILE = SCRIPT_DIR / "config.json"

with open(CONFIG_FILE, 'r') as f:
    config = json.load(f)

BACKUP_DIR = Path(config['backup_directory'])
APPLE_ID = config['apple_id']
INDEX_FILE = BACKUP_DIR / "icloud_index.json"
DELETE_LOG = BACKUP_DIR / "delete_by_criteria_log.txt"
DELETE_PROGRESS = BACKUP_DIR / "delete_by_criteria_progress.json"

# Default criteria (can be overridden)
DEFAULT_CRITERIA = {
    'photos': {
        'enabled': True,
        'rules': [
            # Add photo-specific rules here if needed
        ]
    },
    'videos': {
        'enabled': True,
        'rules': [
            {'type': 'age_and_size', 'min_age_years': 2, 'min_size_mb': 100},  # Old large videos
            {'type': 'age_and_duration', 'min_age_years': 1, 'max_duration_sec': 5}  # Old short videos
        ]
    }
}

BATCH_SIZE = 10
DELAY_BETWEEN_BATCHES = 2

def log(message):
    """Log to both console and file"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_msg = f"[{timestamp}] {message}"
    print(log_msg)
    with open(DELETE_LOG, 'a') as f:
        f.write(log_msg + "\n")

def load_index():
    """Load index"""
    if not INDEX_FILE.exists():
        return None
    with open(INDEX_FILE, 'r') as f:
        return json.load(f)

def load_progress():
    """Load deletion progress"""
    progress_file = Path(DELETE_PROGRESS)
    if progress_file.exists():
        with open(progress_file, 'r') as f:
            return json.load(f)
    return {
        'deleted_files': [],
        'failed_files': [],
        'stats': {'deleted': 0, 'failed': 0, 'skipped': 0}
    }

def save_progress(progress):
    """Save deletion progress"""
    with open(DELETE_PROGRESS, 'w') as f:
        json.dump(progress, f, indent=2)

def get_file_age_years(date_str):
    """Calculate age in years from ISO date string"""
    if not date_str:
        return None
    try:
        file_date = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
        age_days = (datetime.now() - file_date.replace(tzinfo=None)).days
        return age_days / 365.25
    except:
        return None

def matches_criteria(metadata, criteria):
    """Check if item matches deletion criteria"""
    item_type = metadata.get('item_type')

    if item_type == 'movie' and criteria.get('videos', {}).get('enabled'):
        for rule in criteria['videos']['rules']:
            if rule['type'] == 'age_and_size':
                age_years = get_file_age_years(metadata.get('created'))
                size_mb = (metadata.get('size') or 0) / (1024 * 1024)

                if age_years and age_years >= rule['min_age_years'] and size_mb >= rule['min_size_mb']:
                    return True, f"Old large video: {age_years:.1f}yr, {size_mb:.1f}MB"

            elif rule['type'] == 'age_and_duration':
                age_years = get_file_age_years(metadata.get('created'))
                # Note: Duration not in index, would need local file analysis
                # For now, skip duration-based rules
                continue

    elif item_type != 'movie' and criteria.get('photos', {}).get('enabled'):
        for rule in criteria.get('photos', {}).get('rules', []):
            # Add photo rules here if needed
            pass

    return False, None

def send_success_email(candidates, deleted_count):
    """Send email notification with deletion summary"""
    if deleted_count == 0:
        return

    try:
        # Calculate stats
        video_candidates = [(f, m, r) for f, m, r in candidates if m.get('item_type') == 'movie']
        photo_candidates = [(f, m, r) for f, m, r in candidates if m.get('item_type') != 'movie']

        video_count = len(video_candidates)
        photo_count = len(photo_candidates)

        video_size_gb = sum((m.get('size') or 0) for _, m, _ in video_candidates) / (1024**3)
        photo_size_gb = sum((m.get('size') or 0) for _, m, _ in photo_candidates) / (1024**3)
        total_size_gb = video_size_gb + photo_size_gb

        # Create reasons summary file
        reasons_file = BACKUP_DIR / "deletion_reasons_temp.txt"
        with open(reasons_file, 'w') as f:
            # Group by reason
            reason_counts = {}
            for _, _, reason in candidates:
                reason_counts[reason] = reason_counts.get(reason, 0) + 1

            for reason, count in sorted(reason_counts.items(), key=lambda x: x[1], reverse=True):
                f.write(f"• {reason}: {count} items\n")

        # Call email script
        script_path = Path(__file__).parent / "send_success_email.sh"
        subprocess.run([
            str(script_path),
            str(deleted_count),
            f"{total_size_gb:.2f}",
            str(video_count),
            str(photo_count),
            f"{video_size_gb:.2f}",
            f"{photo_size_gb:.2f}",
            str(reasons_file)
        ], check=False)

        # Clean up temp file
        reasons_file.unlink(missing_ok=True)

        log("✓ Success email sent")

    except Exception as e:
        log(f"⚠️  Failed to send email: {e}")

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
    print("iCloud Deletion by Criteria (Index-Based)")
    print("=" * 70)
    print()

    # Load index
    index = load_index()
    if not index:
        print("❌ Index file not found!")
        print("Please run smart download first:")
        print("  python3 ~/scripts/icloud-photo-backup/smart_download.py")
        sys.exit(1)

    log(f"✓ Loaded index with {index['photo_count']} items")
    log(f"  Index created: {index['created_at']}")
    print()

    # Analyze index to find candidates for deletion
    log("Analyzing index with deletion criteria...")
    metadata = index.get('metadata', {})
    candidates = []

    criteria = DEFAULT_CRITERIA

    log("Criteria:")
    log("  Videos: Old large (>100MB, >2yr) OR Old short (<5s, >1yr)")
    log("  Photos: (none currently - uses local cleanup)")
    print()

    for filename, meta in metadata.items():
        matches, reason = matches_criteria(meta, criteria)
        if matches:
            candidates.append((filename, meta, reason))

    log(f"✓ Found {len(candidates)} items matching criteria")

    if len(candidates) == 0:
        log("No items match deletion criteria. Exiting.")
        return

    # Show summary
    total_size = sum((m.get('size') or 0) for _, m, _ in candidates)
    print()
    print(f"Items to delete: {len(candidates)}")
    print(f"Total size: {total_size / (1024**3):.2f} GB")
    print()

    # Show breakdown
    video_candidates = [(f, m, r) for f, m, r in candidates if m.get('item_type') == 'movie']
    photo_candidates = [(f, m, r) for f, m, r in candidates if m.get('item_type') != 'movie']

    if video_candidates:
        print(f"Videos: {len(video_candidates)} ({sum((m.get('size') or 0) for _, m, _ in video_candidates) / (1024**3):.2f} GB)")
    if photo_candidates:
        print(f"Photos: {len(photo_candidates)} ({sum((m.get('size') or 0) for _, m, _ in photo_candidates) / (1024**3):.2f} GB)")
    print()

    # Show sample
    print("Sample of items to delete (first 10):")
    for idx, (filename, meta, reason) in enumerate(candidates[:10], 1):
        size_mb = (meta.get('size') or 0) / (1024 * 1024)
        created = meta.get('created', 'unknown')[:10] if meta.get('created') else 'unknown'
        print(f"  {idx}. {filename} - {size_mb:.1f}MB ({created}) - {reason}")

    if len(candidates) > 10:
        print(f"  ... and {len(candidates) - 10} more")

    print()

    # Confirm deletion
    print("⚠️  WARNING: This will DELETE items from your iCloud Photo Library!")
    print("   They will be moved to 'Recently Deleted' album for 30 days.")
    print()
    response = input("Are you sure you want to continue? (yes/no): ")

    if response.lower() not in ['yes', 'y']:
        log("Deletion cancelled by user")
        return

    print()

    # Load progress
    progress = load_progress()
    deleted_set = set(progress['deleted_files'])
    failed_set = set(progress['failed_files'])

    # Filter out already processed
    remaining_candidates = [(f, m, r) for f, m, r in candidates
                           if f not in deleted_set and f not in failed_set]

    log(f"Previously deleted: {len(deleted_set)}")
    log(f"Previously failed: {len(failed_set)}")
    log(f"Remaining to delete: {len(remaining_candidates)}")
    print()

    if len(remaining_candidates) == 0:
        log("All items already processed!")
        return

    # Authenticate
    api = authenticate()
    print()

    # Access photos
    log("Accessing iCloud Photos library...")
    try:
        photos_album = api.photos.all
        log("✓ Connected to iCloud Photos library!")
        print()

        # Build map of files to delete
        remaining_filenames = set(f for f, _, _ in remaining_candidates)

        log(f"Searching for {len(remaining_filenames)} items to delete...")
        photo_map = {}
        count = 0

        for photo in photos_album:
            count += 1

            if count % 500 == 0:
                log(f"  Checked {count} photos, found {len(photo_map)}/{len(remaining_filenames)}...")

            try:
                filename = photo.filename

                if filename in remaining_filenames and filename not in photo_map:
                    photo_map[filename] = photo
                    if len(photo_map) % 10 == 0:
                        log(f"  ✓ Found {len(photo_map)}/{len(remaining_filenames)}...")

                if len(photo_map) == len(remaining_filenames):
                    log(f"✓ Found all {len(remaining_filenames)} items!")
                    break

            except Exception as e:
                continue

            if count >= 15000:  # Safety limit
                log(f"⚠️  Reached search limit")
                break

        log(f"✓ Search complete: matched {len(photo_map)} items")
        print()

        if len(photo_map) == 0:
            log("❌ No matching items found in iCloud library")
            return

        # Delete in batches
        log(f"Starting deletion in batches of {BATCH_SIZE}...")
        print()

        deleted = progress['stats']['deleted']
        failed = progress['stats']['failed']
        skipped = progress['stats']['skipped']

        batch = []
        for filename, _, reason in remaining_candidates:
            if filename not in photo_map:
                log(f"⊘ Skipped (not found): {filename}")
                skipped += 1
                continue

            photo = photo_map[filename]
            batch.append((filename, photo, reason))

            if len(batch) >= BATCH_SIZE:
                for fname, p, rsn in batch:
                    try:
                        p.delete()
                        deleted += 1
                        deleted_set.add(fname)
                        log(f"✓ Deleted ({deleted}): {fname} - {rsn}")
                    except Exception as e:
                        failed += 1
                        failed_set.add(fname)
                        log(f"✗ Failed: {fname} - {str(e)[:100]}")

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

        # Process remaining
        if batch:
            for fname, p, rsn in batch:
                try:
                    p.delete()
                    deleted += 1
                    deleted_set.add(fname)
                    log(f"✓ Deleted ({deleted}): {fname} - {rsn}")
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
        log("Deleted items are in 'Recently Deleted' album in iCloud Photos")
        log("They will be permanently deleted after 30 days")
        print()

        # Send success email
        if deleted > 0:
            send_success_email(candidates, deleted)

    except KeyboardInterrupt:
        log("\n\n⚠️  Deletion interrupted!")
        log("Saving progress...")
        save_progress(progress)
        log("✓ Progress saved. Run again to resume.")
        sys.exit(0)

    except Exception as e:
        log(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        save_progress(progress)
        sys.exit(1)

if __name__ == "__main__":
    main()
