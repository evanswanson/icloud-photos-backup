#!/usr/bin/env python3
"""
Rebuild Index from Local Files
Scans local backup directory and creates index from downloaded files
"""

import json
import os
from pathlib import Path
from datetime import datetime

BACKUP_DIR = Path("/Users/evanswanson/icloud-photo-backup")
INDEX_FILE = BACKUP_DIR / "icloud_index.json"

print("=" * 70)
print("Rebuild Index from Local Files")
print("=" * 70)
print()
print(f"Scanning: {BACKUP_DIR}")
print()

# Find all media files
print("Finding all photos and videos...")
media_extensions = {'.heic', '.jpg', '.jpeg', '.png', '.mov', '.mp4', '.m4v'}
all_files = []

for root, dirs, files in os.walk(BACKUP_DIR):
    # Skip trash and logs
    if 'trash' in root or 'logs-archive' in root:
        continue

    for file in files:
        if Path(file).suffix.lower() in media_extensions:
            filepath = Path(root) / file
            all_files.append(filepath)

print(f"✓ Found {len(all_files)} media files")
print()

# Build index metadata
print("Building index metadata...")
metadata = {}
filenames = set()

for i, filepath in enumerate(all_files, 1):
    if i % 500 == 0:
        print(f"  Processed {i}/{len(all_files)}...")

    filename = filepath.name
    filenames.add(filename)

    # Get file stats
    stats = filepath.stat()

    # Determine item type from extension
    ext = filepath.suffix.lower()
    if ext in {'.mov', '.mp4', '.m4v'}:
        item_type = 'movie'
    else:
        item_type = 'image'

    # Get creation time from file metadata
    created = datetime.fromtimestamp(stats.st_birthtime).isoformat() if hasattr(stats, 'st_birthtime') else None

    metadata[filename] = {
        'filename': filename,
        'size': stats.st_size,
        'created': created,
        'asset_date': None,  # Not available from local files
        'added_date': None,  # Not available from local files
        'dimensions': None,  # Could extract but expensive
        'item_type': item_type,
        'id': None,  # Not available from local files
        'local_path': str(filepath)
    }

print(f"✓ Processed {len(all_files)} files")
print()

# Calculate statistics
photo_count = sum(1 for m in metadata.values() if m.get('item_type') != 'movie')
video_count = sum(1 for m in metadata.values() if m.get('item_type') == 'movie')
total_size = sum(m.get('size', 0) or 0 for m in metadata.values())

# Create index
index_data = {
    'created_at': datetime.now().isoformat(),
    'photo_count': len(filenames),
    'statistics': {
        'total_items': len(filenames),
        'photos': photo_count,
        'videos': video_count,
        'total_size_gb': round(total_size / (1024**3), 2) if total_size else 0
    },
    'filenames': list(filenames),
    'metadata': metadata,
    'note': 'Rebuilt from local files - some metadata (dates, iCloud ID) may be incomplete'
}

# Save index
with open(INDEX_FILE, 'w') as f:
    json.dump(index_data, f, indent=2)

print("=" * 70)
print("Index Rebuild Complete!")
print("=" * 70)
print()
print(f"Index file: {INDEX_FILE}")
print(f"Total items: {len(filenames)}")
print(f"  Photos: {photo_count}")
print(f"  Videos: {video_count}")
print(f"  Total size: {round(total_size / (1024**3), 2)} GB")
print()
print("Note: Dates are from file creation time, not original photo dates.")
print("      Run download again to capture full iCloud metadata.")
print()
print("You can now use:")
print("  python3 ~/scripts/icloud-photo-backup/query_index.py stats")
print("  python3 ~/scripts/icloud-photo-backup/delete_by_criteria.py")
print()
