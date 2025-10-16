#!/usr/bin/env python3
"""
Update Index with iCloud Metadata
Fetches proper dates from iCloud API for all items in index
Does NOT download files - just updates metadata
"""

import sys
import json
from pathlib import Path
from datetime import datetime
from pyicloud import PyiCloudService

BACKUP_DIR = Path("/Users/evanswanson/icloud-photo-backup")
APPLE_ID = "evan.swanson.receipt@gmail.com"
INDEX_FILE = BACKUP_DIR / "icloud_index.json"
LOG_FILE = BACKUP_DIR / "metadata_update_log.txt"

def log(message):
    """Log to both console and file"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_msg = f"[{timestamp}] {message}"
    print(log_msg)
    with open(LOG_FILE, 'a') as f:
        f.write(log_msg + "\n")

def load_index():
    """Load index"""
    if not INDEX_FILE.exists():
        return None
    with open(INDEX_FILE, 'r') as f:
        return json.load(f)

def save_index(index_data):
    """Save index"""
    with open(INDEX_FILE, 'w') as f:
        json.dump(index_data, f, indent=2)

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
    print("Update Index with iCloud Metadata")
    print("=" * 70)
    print()
    print("This will fetch proper dates from iCloud for all items.")
    print("Files will NOT be re-downloaded.")
    print()

    # Load index
    index_data = load_index()
    if not index_data:
        print("❌ Index file not found!")
        print("Run: ~/scripts/icloud-photo-backup/smart_workflow.sh")
        sys.exit(1)

    metadata = index_data.get('metadata', {})
    log(f"Loaded index with {len(metadata)} items")

    # Count items needing updates
    needs_update = sum(1 for m in metadata.values() if m.get('asset_date') is None)
    log(f"Items needing metadata update: {needs_update}")

    if needs_update == 0:
        log("✓ All items already have iCloud metadata!")
        return

    print()
    print(f"Will update metadata for {needs_update} items")
    print("This will take 5-10 minutes (reading from iCloud API)")
    print()
    response = input("Continue? (yes/no): ")

    if response.lower() not in ['yes', 'y']:
        log("Cancelled by user")
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

        log("Fetching metadata from iCloud...")
        log("(This iterates through library but doesn't download files)")
        print()

        updated = 0
        checked = 0
        consecutive_duplicates = 0
        MAX_CONSECUTIVE_DUPLICATES = 500
        seen_filenames = set(metadata.keys())

        for photo in photos_album:
            checked += 1

            if checked % 500 == 0:
                log(f"  Checked {checked} photos, updated {updated}/{needs_update}...")

            try:
                filename = photo.filename

                # Detect cycling
                if filename not in seen_filenames:
                    consecutive_duplicates += 1
                    if consecutive_duplicates > MAX_CONSECUTIVE_DUPLICATES:
                        log(f"\n✓ Detected end of photo library")
                        break
                    continue
                else:
                    consecutive_duplicates = 0

                # Skip if already has metadata
                if filename in metadata and metadata[filename].get('asset_date') is not None:
                    continue

                # Update metadata from iCloud
                if filename in metadata:
                    metadata[filename].update({
                        'size': getattr(photo, 'size', None),
                        'created': photo.created.isoformat() if hasattr(photo, 'created') and photo.created else None,
                        'asset_date': photo.asset_date.isoformat() if hasattr(photo, 'asset_date') and photo.asset_date else None,
                        'added_date': photo.added_date.isoformat() if hasattr(photo, 'added_date') and photo.added_date else None,
                        'dimensions': getattr(photo, 'dimensions', None),
                        'item_type': getattr(photo, 'item_type', None),
                        'id': getattr(photo, 'id', None),
                    })
                    updated += 1

                    if updated % 50 == 0:
                        # Save progress periodically
                        index_data['metadata'] = metadata
                        save_index(index_data)
                        log(f"  → Progress saved ({updated} items updated)")

                    if updated >= needs_update:
                        log(f"✓ Updated all {needs_update} items!")
                        break

            except KeyboardInterrupt:
                log("\n\n⚠️  Update interrupted by user!")
                log("Saving progress...")
                index_data['metadata'] = metadata
                save_index(index_data)
                log("✓ Progress saved. Run again to resume.")
                sys.exit(0)

            except Exception as e:
                continue

        # Final save
        index_data['metadata'] = metadata
        index_data['updated_at'] = datetime.now().isoformat()
        save_index(index_data)

        print()
        print("=" * 70)
        print("Metadata Update Complete!")
        print("=" * 70)
        log(f"Checked {checked} photos from iCloud")
        log(f"Updated {updated} items with proper dates")
        print()
        log("Now run video analysis:")
        log("  python3 ~/scripts/icloud-photo-backup/query_index.py videos")

    except Exception as e:
        log(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
