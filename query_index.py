#!/usr/bin/env python3
"""
Query iCloud Index
View statistics and search metadata from the cached index
"""

import json
import sys
from pathlib import Path
from datetime import datetime

BACKUP_DIR = Path("/Users/evanswanson/icloud-photo-backup")
INDEX_FILE = BACKUP_DIR / "icloud_index.json"

def load_index():
    """Load index file"""
    if not INDEX_FILE.exists():
        print(f"❌ Index file not found: {INDEX_FILE}")
        print("Run: python3 ~/scripts/icloud-photo-backup/build_icloud_index.py")
        return None

    with open(INDEX_FILE, 'r') as f:
        return json.load(f)

def show_statistics(index):
    """Show index statistics"""
    print("=" * 70)
    print("iCloud Library Index Statistics")
    print("=" * 70)
    print()
    print(f"Index created: {index['created_at']}")
    print()

    stats = index.get('statistics', {})
    print(f"Total items: {stats.get('total_items', 'Unknown')}")
    print(f"  Photos: {stats.get('photos', 'Unknown')}")
    print(f"  Videos: {stats.get('videos', 'Unknown')}")
    print(f"  Total size: {stats.get('total_size_gb', 'Unknown')} GB")
    print()

def search_by_filename(index, query):
    """Search for files by name"""
    metadata = index.get('metadata', {})
    results = []

    query_lower = query.lower()
    for filename, meta in metadata.items():
        if query_lower in filename.lower():
            results.append((filename, meta))

    if not results:
        print(f"No files found matching '{query}'")
        return

    print(f"\nFound {len(results)} matching files:")
    print()
    for filename, meta in results[:20]:  # Limit to 20 results
        print(f"📄 {filename}")
        if meta.get('size'):
            print(f"   Size: {meta['size'] / (1024*1024):.2f} MB")
        if meta.get('created'):
            print(f"   Created: {meta['created'][:10]}")
        if meta.get('item_type'):
            print(f"   Type: {meta['item_type']}")
        if meta.get('dimensions'):
            print(f"   Dimensions: {meta['dimensions']}")
        print()

    if len(results) > 20:
        print(f"... and {len(results) - 20} more")

def show_by_year(index):
    """Show breakdown by year"""
    metadata = index.get('metadata', {})
    year_counts = {}
    year_sizes = {}

    for filename, meta in metadata.items():
        created = meta.get('created')
        if created:
            year = created[:4]
            year_counts[year] = year_counts.get(year, 0) + 1
            size = meta.get('size', 0) or 0
            year_sizes[year] = year_sizes.get(year, 0) + size

    print("\nBreakdown by year:")
    print()
    for year in sorted(year_counts.keys(), reverse=True):
        count = year_counts[year]
        size_gb = year_sizes[year] / (1024**3)
        print(f"{year}: {count:4d} items, {size_gb:6.2f} GB")

def show_largest_files(index, limit=20):
    """Show largest files"""
    metadata = index.get('metadata', {})
    items = [(filename, meta) for filename, meta in metadata.items() if meta.get('size')]
    items.sort(key=lambda x: x[1]['size'], reverse=True)

    print(f"\nTop {limit} largest files:")
    print()
    for idx, (filename, meta) in enumerate(items[:limit], 1):
        size_mb = meta['size'] / (1024*1024)
        item_type = meta.get('item_type', 'unknown')
        created = meta.get('created', 'unknown')[:10] if meta.get('created') else 'unknown'
        print(f"{idx:2d}. {filename}")
        print(f"    {size_mb:7.2f} MB | {item_type:10s} | {created}")

def show_videos_by_age(index):
    """Show videos grouped by age"""
    metadata = index.get('metadata', {})
    videos = [(filename, meta) for filename, meta in metadata.items()
              if meta.get('item_type') == 'movie']

    if not videos:
        print("\nNo videos found in index")
        return

    now = datetime.now()
    age_groups = {
        '< 1 year': [],
        '1-2 years': [],
        '> 2 years': []
    }

    for filename, meta in videos:
        created = meta.get('created')
        if created:
            created_date = datetime.fromisoformat(created.replace('Z', '+00:00'))
            # Remove timezone info for comparison
            created_date = created_date.replace(tzinfo=None)
            age_years = (now - created_date).days / 365.25

            if age_years < 1:
                age_groups['< 1 year'].append((filename, meta))
            elif age_years < 2:
                age_groups['1-2 years'].append((filename, meta))
            else:
                age_groups['> 2 years'].append((filename, meta))

    print(f"\nVideos by age ({len(videos)} total):")
    print()
    for group_name, group_items in age_groups.items():
        if group_items:
            total_size = sum(m.get('size', 0) or 0 for _, m in group_items)
            print(f"{group_name:12s}: {len(group_items):4d} videos, {total_size / (1024**3):6.2f} GB")

def main():
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python3 query_index.py stats         - Show statistics")
        print("  python3 query_index.py search <term> - Search by filename")
        print("  python3 query_index.py years         - Breakdown by year")
        print("  python3 query_index.py largest [N]   - Show N largest files (default 20)")
        print("  python3 query_index.py videos        - Show video breakdown by age")
        return

    index = load_index()
    if not index:
        return

    command = sys.argv[1].lower()

    if command == 'stats':
        show_statistics(index)

    elif command == 'search':
        if len(sys.argv) < 3:
            print("Please provide a search term")
            return
        query = ' '.join(sys.argv[2:])
        show_statistics(index)
        search_by_filename(index, query)

    elif command == 'years':
        show_statistics(index)
        show_by_year(index)

    elif command == 'largest':
        limit = int(sys.argv[2]) if len(sys.argv) > 2 else 20
        show_statistics(index)
        show_largest_files(index, limit)

    elif command == 'videos':
        show_statistics(index)
        show_videos_by_age(index)

    else:
        print(f"Unknown command: {command}")
        print("Run without arguments to see usage")

if __name__ == "__main__":
    main()
