#!/usr/bin/env python3
"""
Build iCloud Photo Library Index
Creates a cached mapping of filenames to photo objects for fast lookups
Run this once, then use for quick deletions
"""

import sys
import json
import pickle
from pathlib import Path
from datetime import datetime
from pyicloud import PyiCloudService

BACKUP_DIR = Path("/Users/evanswanson/icloud-photo-backup")
APPLE_ID = "evan.swanson.receipt@gmail.com"
INDEX_FILE = BACKUP_DIR / "icloud_index.json"
INDEX_CACHE = BACKUP_DIR / "icloud_index.pkl"
LOG_FILE = BACKUP_DIR / "index_build_log.txt"

def log(message):
    """Log to both console and file"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_msg = f"[{timestamp}] {message}"
    print(log_msg)
    with open(LOG_FILE, 'a') as f:
        f.write(log_msg + "\n")

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
    print("iCloud Photo Library Index Builder")
    print("=" * 70)
    print()
    print("This will scan your entire iCloud library once and cache it.")
    print("Future deletions will be much faster using this index.")
    print()

    # Authenticate
    api = authenticate()
    print()

    # Build index
    log("Accessing iCloud Photos library...")
    try:
        photos_album = api.photos.all
        log("✓ Connected to iCloud Photos library!")
        print()

        log("Building index with metadata (this will take several minutes)...")
        log("Capturing: filename, size, dates, dimensions, type, id")
        index = {}
        photo_metadata = {}
        count = 0
        seen_filenames = set()
        consecutive_duplicates = 0
        MAX_CONSECUTIVE_DUPLICATES = 500

        for photo in photos_album:
            count += 1

            if count % 500 == 0:
                log(f"  Indexed {count} photos, {len(seen_filenames)} unique...")

            try:
                filename = photo.filename

                # Detect cycling
                if filename in seen_filenames:
                    consecutive_duplicates += 1
                    if consecutive_duplicates >= MAX_CONSECUTIVE_DUPLICATES:
                        log(f"✓ Detected end of library (seen {consecutive_duplicates} repeated photos)")
                        break
                    continue
                else:
                    seen_filenames.add(filename)
                    consecutive_duplicates = 0

                # Store comprehensive metadata
                photo_metadata[filename] = {
                    'filename': filename,
                    'size': getattr(photo, 'size', None),
                    'created': photo.created.isoformat() if hasattr(photo, 'created') and photo.created else None,
                    'asset_date': photo.asset_date.isoformat() if hasattr(photo, 'asset_date') and photo.asset_date else None,
                    'added_date': photo.added_date.isoformat() if hasattr(photo, 'added_date') and photo.added_date else None,
                    'dimensions': getattr(photo, 'dimensions', None),
                    'item_type': getattr(photo, 'item_type', None),  # photo, video, etc.
                    'id': getattr(photo, 'id', None),
                }

                # Store the photo object for deletion (can't serialize, so mark as available)
                index[filename] = True

            except Exception as e:
                log(f"  Error processing photo {count}: {str(e)[:100]}")
                continue

        log(f"✓ Index built successfully!")
        log(f"  Total iterations: {count}")
        log(f"  Unique photos: {len(seen_filenames)}")
        print()

        # Calculate statistics
        photo_count = sum(1 for m in photo_metadata.values() if m.get('item_type') != 'movie')
        video_count = sum(1 for m in photo_metadata.values() if m.get('item_type') == 'movie')
        total_size = sum(m.get('size', 0) or 0 for m in photo_metadata.values())

        # Save index
        index_data = {
            'created_at': datetime.now().isoformat(),
            'photo_count': len(seen_filenames),
            'statistics': {
                'total_items': len(seen_filenames),
                'photos': photo_count,
                'videos': video_count,
                'total_size_gb': round(total_size / (1024**3), 2) if total_size else 0
            },
            'filenames': list(seen_filenames),
            'metadata': photo_metadata
        }

        with open(INDEX_FILE, 'w') as f:
            json.dump(index_data, f, indent=2)

        log(f"✓ Index saved to: {INDEX_FILE}")
        log(f"  Total items: {len(seen_filenames)}")
        log(f"  Photos: {photo_count}")
        log(f"  Videos: {video_count}")
        log(f"  Total size: {round(total_size / (1024**3), 2)} GB" if total_size else "  Total size: Unknown")
        print()
        print("=" * 70)
        print("Index Complete!")
        print("=" * 70)
        print()
        print(f"Index file: {INDEX_FILE}")
        print(f"Total items: {len(seen_filenames)}")
        print(f"  Photos: {photo_count}")
        print(f"  Videos: {video_count}")
        if total_size:
            print(f"  Total size: {round(total_size / (1024**3), 2)} GB")
        print()
        print("Metadata captured per item:")
        print("  - Filename, size, dates (created, asset, added)")
        print("  - Dimensions, type (photo/video), iCloud ID")
        print()
        print("You can now use fast deletion with:")
        print("  python3 ~/scripts/icloud-photo-backup/icloud_delete_fast.py")

    except KeyboardInterrupt:
        log("\n\n⚠️  Index building interrupted by user!")
        sys.exit(0)

    except Exception as e:
        log(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
