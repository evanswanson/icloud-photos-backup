#!/usr/bin/env python3
"""
Smart iCloud Downloader with Index Building
- Downloads photos/videos from iCloud
- Builds index simultaneously during download
- Skips already downloaded files
- Resumes from where it left off
"""

import os
import sys
import json
import time
import argparse
from pathlib import Path
from datetime import datetime
from pyicloud import PyiCloudService

# Load configuration
SCRIPT_DIR = Path(__file__).parent.absolute()
CONFIG_FILE = SCRIPT_DIR / "config.json"

def load_config():
    """Load configuration from config.json"""
    if not CONFIG_FILE.exists():
        print(f"ERROR: Configuration file not found: {CONFIG_FILE}")
        print(f"Please copy config.json.template to config.json and fill in your details.")
        sys.exit(1)

    with open(CONFIG_FILE, 'r') as f:
        return json.load(f)

config = load_config()
BACKUP_DIR = Path(config['backup_directory'])
APPLE_ID = config['apple_id']
PROGRESS_FILE = BACKUP_DIR / "download_progress.json"
INDEX_FILE = BACKUP_DIR / "icloud_index.json"
LOG_FILE = BACKUP_DIR / "download_log.txt"

# Configuration
RETRY_ATTEMPTS = 3
RETRY_DELAY = 5
SAVE_PROGRESS_EVERY = 50

def log(message):
    """Log to both console and file"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_msg = f"[{timestamp}] {message}"
    print(log_msg)
    with open(LOG_FILE, 'a') as f:
        f.write(log_msg + "\n")

def load_progress():
    """Load download progress"""
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
    """Save download progress"""
    with open(PROGRESS_FILE, 'w') as f:
        json.dump(progress, f, indent=2)

def load_index():
    """Load existing index"""
    if INDEX_FILE.exists():
        with open(INDEX_FILE, 'r') as f:
            return json.load(f)
    return {
        'created_at': datetime.now().isoformat(),
        'photo_count': 0,
        'statistics': {
            'total_items': 0,
            'photos': 0,
            'videos': 0,
            'total_size_gb': 0
        },
        'filenames': [],
        'metadata': {}
    }

def save_index(index_data):
    """Save index"""
    with open(INDEX_FILE, 'w') as f:
        json.dump(index_data, f, indent=2)

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

def send_summary_email(session_stats, verbose=False):
    """Send email summary of backup session"""
    if not verbose:
        return

    try:
        from send_email_smtp import send_email
        import socket

        # Calculate statistics
        new_downloads = session_stats['new_downloads']
        total_size_bytes = session_stats['total_size_bytes']
        total_size_mb = round(total_size_bytes / (1024**2), 2)
        photo_locations = session_stats['photo_locations']

        # Get computer name
        computer_name = socket.gethostname()

        # Build email body
        subject = f"iCloud Backup Complete - {new_downloads} new photos"

        body = f"""iCloud Photo Backup Summary
{'=' * 50}

New Photos Backed Up: {new_downloads}
Total Size: {total_size_mb} MB
Backup Location: {BACKUP_DIR}
Computer: {computer_name}

Photos by Geographical Location:
"""

        # Sort locations by count (descending), then alphabetically
        sorted_locations = sorted(photo_locations.items(), key=lambda x: (-x[1], x[0]))

        # Add location breakdown
        for location, count in sorted_locations:
            body += f"  {location}: {count} photo{'s' if count != 1 else ''}\n"

        body += f"\nBackup completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"

        # Send email
        success = send_email(
            to_email=config['notification_email'],
            subject=subject,
            body=body
        )

        if success:
            log("✓ Summary email sent successfully")
        else:
            log("⚠️  Failed to send summary email")

    except Exception as e:
        log(f"⚠️  Error sending summary email: {e}")

def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(
        description='Smart iCloud Downloader with Index Building',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  %(prog)s                    # Normal mode (no email)
  %(prog)s --verbose          # Send email summary of new photos
  %(prog)s --recent 30        # Only check photos from last 30 days (fast daily run)
  %(prog)s --recent 30 --verbose  # Fast daily run with email
        '''
    )

    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Send confirmation email with summary of new photos backed up'
    )

    parser.add_argument(
        '--recent',
        type=int,
        metavar='DAYS',
        help='Only process photos from the last N days (faster for daily runs)'
    )

    return parser.parse_args()

def main():
    # Parse arguments
    args = parse_arguments()

    print("=" * 70)
    print("Smart iCloud Downloader + Index Builder")
    print("=" * 70)
    print()
    print(f"Apple ID: {APPLE_ID}")
    print(f"Backup Directory: {BACKUP_DIR}")
    print(f"Downloads + Builds Index Simultaneously")
    if args.verbose:
        print(f"Verbose Mode: Email summary will be sent")
    if args.recent:
        print(f"Fast Mode: Only checking photos from last {args.recent} days")
    print()

    # Create backup directory
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)

    # Load previous progress and index
    progress = load_progress()
    index_data = load_index()

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
        if args.recent:
            from datetime import timedelta, timezone
            cutoff_date = datetime.now(timezone.utc) - timedelta(days=args.recent)
            log(f"✓ Connected! Will filter to photos from last {args.recent} days")
            log(f"   (Skipping photos older than {cutoff_date.strftime('%Y-%m-%d')})")
        else:
            log("✓ Connected to iCloud Photos library!")

        log("Starting download + index building...")
        print()

        downloaded = progress['stats']['downloaded']
        skipped = progress['stats']['skipped']
        failed = progress['stats']['failed']

        downloaded_set = set(progress['downloaded_files'])
        start_idx = progress['last_index']

        photo_metadata = index_data.get('metadata', {})
        indexed_filenames = set(index_data.get('filenames', []))

        # Track session statistics for email summary
        session_stats = {
            'new_downloads': 0,
            'total_size_bytes': 0,
            'photo_locations': {}  # geographical location -> count
        }

        # Calculate cutoff date for filtering if --recent is used
        from datetime import timedelta, timezone
        cutoff_date = None
        if args.recent:
            cutoff_date = datetime.now(timezone.utc) - timedelta(days=args.recent)
            log(f"Will skip photos older than: {cutoff_date.strftime('%Y-%m-%d')}")

        log(f"Progress will be saved every {SAVE_PROGRESS_EVERY} photos")
        print()

        photo_num = 0
        # Initialize seen_filenames from existing index to properly track duplicates
        seen_filenames = indexed_filenames.copy()
        consecutive_duplicates = 0
        MAX_CONSECUTIVE_DUPLICATES = 500
        skipped_by_date = 0
        consecutive_old_photos = 0
        MAX_CONSECUTIVE_OLD = 100  # Stop after 100 consecutive old photos

        for photo in photos_album:
            photo_num += 1

            # Skip photos before our resume point
            if photo_num <= start_idx:
                continue

            try:
                filename = photo.filename

                # Skip photos outside date range if --recent is set
                # Since photos are in descending order (newest first), we can stop early
                if cutoff_date:
                    photo_date = None
                    # Try to get the most relevant date
                    if hasattr(photo, 'added_date') and photo.added_date:
                        photo_date = photo.added_date
                    elif hasattr(photo, 'asset_date') and photo.asset_date:
                        photo_date = photo.asset_date
                    elif hasattr(photo, 'created') and photo.created:
                        photo_date = photo.created

                    # Make photo_date timezone-aware if it's naive for proper comparison
                    if photo_date:
                        if photo_date.tzinfo is None:
                            photo_date = photo_date.replace(tzinfo=timezone.utc)

                    if photo_date and photo_date < cutoff_date:
                        skipped_by_date += 1
                        consecutive_old_photos += 1

                        # Early exit: if we've seen many consecutive old photos, we're done
                        if consecutive_old_photos >= MAX_CONSECUTIVE_OLD:
                            log(f"\n✓ Reached cutoff date - {consecutive_old_photos} consecutive photos older than {cutoff_date.strftime('%Y-%m-%d')}")
                            log(f"   All photos from the last {args.recent} days have been processed!")
                            break

                        if skipped_by_date % 100 == 0:
                            log(f"  Skipped {skipped_by_date} photos older than cutoff date")
                        continue
                    else:
                        # Reset counter when we see a new photo within the date range
                        consecutive_old_photos = 0

                # Detect cycling
                if filename in seen_filenames:
                    consecutive_duplicates += 1
                    if consecutive_duplicates > MAX_CONSECUTIVE_DUPLICATES:
                        log(f"\n✓ Detected end of photo library (seen {consecutive_duplicates} repeated photos)")
                        log("All unique photos have been processed!")
                        break
                    continue
                else:
                    seen_filenames.add(filename)
                    indexed_filenames.add(filename)
                    consecutive_duplicates = 0

                # Capture metadata for index
                photo_metadata[filename] = {
                    'filename': filename,
                    'size': getattr(photo, 'size', None),
                    'created': photo.created.isoformat() if hasattr(photo, 'created') and photo.created else None,
                    'asset_date': photo.asset_date.isoformat() if hasattr(photo, 'asset_date') and photo.asset_date else None,
                    'added_date': photo.added_date.isoformat() if hasattr(photo, 'added_date') and photo.added_date else None,
                    'dimensions': getattr(photo, 'dimensions', None),
                    'item_type': getattr(photo, 'item_type', None),
                    'id': getattr(photo, 'id', None),
                    'location': getattr(photo, 'location', None),
                }

                # Skip if already downloaded
                if filename in downloaded_set:
                    skipped += 1
                    if photo_num % 50 == 0:
                        log(f"[{photo_num}] Downloaded: {downloaded}, Skipped: {skipped}, Failed: {failed}, Indexed: {len(indexed_filenames)}")
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
                        log(f"[{photo_num}] Downloaded: {downloaded}, Skipped: {skipped}, Failed: {failed}, Indexed: {len(indexed_filenames)}")
                    continue

                # Download with retry
                success = download_photo_with_retry(photo, output_path)

                if success:
                    downloaded += 1
                    downloaded_set.add(filename)

                    # Track session statistics
                    session_stats['new_downloads'] += 1
                    photo_size = getattr(photo, 'size', 0) or 0
                    session_stats['total_size_bytes'] += photo_size

                    # Track geographical location
                    location = getattr(photo, 'location', None)
                    if location:
                        # Location can be a dict or string, try to format it nicely
                        if isinstance(location, dict):
                            # Extract city/state or lat/long
                            location_key = location.get('locality') or location.get('administrativeArea') or f"{location.get('latitude', 'Unknown')}, {location.get('longitude', 'Unknown')}"
                        else:
                            location_key = str(location)
                    else:
                        location_key = "Unknown Location"

                    session_stats['photo_locations'][location_key] = session_stats['photo_locations'].get(location_key, 0) + 1

                    log(f"[{photo_num}] Downloaded: {downloaded}, Skipped: {skipped}, Failed: {failed} | {filename}")
                else:
                    failed += 1
                    progress['failed_files'].append({
                        'filename': filename,
                        'index': photo_num,
                        'timestamp': datetime.now().isoformat()
                    })
                    log(f"[{photo_num}] ✗ Failed: {filename}")

                # Save progress and index periodically
                if photo_num % SAVE_PROGRESS_EVERY == 0:
                    progress['last_index'] = photo_num
                    progress['downloaded_files'] = list(downloaded_set)
                    progress['stats'] = {
                        'downloaded': downloaded,
                        'skipped': skipped,
                        'failed': failed
                    }
                    save_progress(progress)

                    # Update index
                    index_data['metadata'] = photo_metadata
                    index_data['filenames'] = list(indexed_filenames)
                    index_data['photo_count'] = len(indexed_filenames)
                    save_index(index_data)

                    log(f"  → Progress + Index saved (checkpoint at photo #{photo_num})")

            except KeyboardInterrupt:
                log("\n\n⚠️  Download interrupted by user!")
                log("Saving progress and index...")
                progress['last_index'] = photo_num
                progress['downloaded_files'] = list(downloaded_set)
                progress['stats'] = {
                    'downloaded': downloaded,
                    'skipped': skipped,
                    'failed': failed
                }
                save_progress(progress)

                # Save final index
                index_data['metadata'] = photo_metadata
                index_data['filenames'] = list(indexed_filenames)
                index_data['photo_count'] = len(indexed_filenames)
                save_index(index_data)

                log("✓ Progress and index saved. Run again to resume.")
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

        # Calculate final statistics
        photo_count = sum(1 for m in photo_metadata.values() if m.get('item_type') != 'movie')
        video_count = sum(1 for m in photo_metadata.values() if m.get('item_type') == 'movie')
        total_size = sum(m.get('size', 0) or 0 for m in photo_metadata.values())

        index_data['metadata'] = photo_metadata
        index_data['filenames'] = list(indexed_filenames)
        index_data['photo_count'] = len(indexed_filenames)
        index_data['statistics'] = {
            'total_items': len(indexed_filenames),
            'photos': photo_count,
            'videos': video_count,
            'total_size_gb': round(total_size / (1024**3), 2) if total_size else 0
        }
        save_index(index_data)

        print()
        print("=" * 70)
        print("Download + Index Complete!")
        print("=" * 70)
        log(f"Total photos processed: {photo_num}")
        log(f"Downloaded: {downloaded}")
        log(f"Skipped (already exists): {skipped}")
        if args.recent and skipped_by_date > 0:
            log(f"Skipped (older than {args.recent} days): {skipped_by_date}")
        log(f"Failed: {failed}")
        log(f"Index contains: {len(indexed_filenames)} items ({photo_count} photos, {video_count} videos)")
        print()
        log(f"Backup location: {BACKUP_DIR}")
        log(f"Index location: {INDEX_FILE}")

        if failed > 0:
            log(f"\n⚠️  {failed} photos failed to download")

        # Send summary email if verbose mode is enabled
        if session_stats['new_downloads'] > 0:
            send_summary_email(session_stats, verbose=args.verbose)
        elif args.verbose:
            log("\nNo new photos downloaded this session - skipping email")

    except Exception as e:
        log(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        save_progress(progress)
        sys.exit(1)

if __name__ == "__main__":
    main()
