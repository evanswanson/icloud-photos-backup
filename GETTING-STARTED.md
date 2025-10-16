# Getting Started with Streamlined iCloud Workflow

## Quick Start

Run the complete automated workflow with a single command:

```bash
~/scripts/icloud-photo-backup/smart_workflow.sh
```

This will:
1. Download any missing photos/videos from iCloud
2. Build/update index during download (with metadata)
3. Analyze photos locally for duplicates/blur/screenshots
4. Use index to identify old large videos and short clips
5. Delete all problematic media from iCloud

## What It Does

### Step 1: Download + Index Building
- Downloads photos/videos you don't have yet
- Builds index **simultaneously** during download (no separate step)
- Captures metadata: filename, size, dates, dimensions, type
- Resumes from where it left off if interrupted
- **Index location:** `~/icloud-photo-backup/icloud_index.json`

### Step 2: Photo Analysis (Local Files)
- Scans for duplicate images (perceptual hashing)
- Detects blurry photos (Laplacian variance < 100)
- Finds old screenshots (>1 year old)
- Moves problematic photos to trash folder

### Step 3: Video Analysis (Index-Based)
Uses the index metadata to find:
- Large videos (>100MB) older than 2 years
- Short videos (<5 sec) older than 1 year
- **No local scanning needed** - uses metadata from Step 1

### Step 4: Delete from iCloud
- Deletes photos from trash folder
- Deletes videos identified by criteria
- Items moved to "Recently Deleted" (30 day retention)

## Interactive Prompts

The workflow asks for confirmation at each step:
- Download new photos? (yes/no/skip)
- Scan photos for issues? (yes/no/skip)
- Move problematic photos to trash? (yes/no)
- Identify videos to delete? (yes/no/skip)
- Proceed with iCloud deletion? (yes/no)

You can skip steps if you've already run them.

## File Locations

```
~/icloud-photo-backup/
├── 2023/01/           # Downloaded photos organized by year/month
├── 2024/05/
├── trash/             # Photos flagged for deletion
├── icloud_index.json  # Cached index with metadata
├── download_progress.json
└── delete_by_criteria_log.txt
```

## Querying the Index

View statistics without hitting iCloud API:

```bash
# Show overall statistics
python3 ~/scripts/icloud-photo-backup/query_index.py stats

# Breakdown by year
python3 ~/scripts/icloud-photo-backup/query_index.py years

# Show largest files
python3 ~/scripts/icloud-photo-backup/query_index.py largest 20

# Video breakdown by age
python3 ~/scripts/icloud-photo-backup/query_index.py videos

# Search by filename
python3 ~/scripts/icloud-photo-backup/query_index.py search "IMG_1234"
```

## Customizing Video Deletion Criteria

Edit `delete_by_criteria.py` at line 21-35 to change criteria:

```python
DEFAULT_CRITERIA = {
    'videos': {
        'enabled': True,
        'rules': [
            {'type': 'age_and_size', 'min_age_years': 2, 'min_size_mb': 100},
            {'type': 'age_and_duration', 'min_age_years': 1, 'max_duration_sec': 5}
        ]
    }
}
```

## Tips

- **First run**: Will take longer to download everything and build index
- **Subsequent runs**: Much faster - only downloads new photos, updates index
- **Interrupted?**: Just run again - resumes from checkpoint (saves every 50 photos)
- **Index refresh**: Download step automatically updates index with new photos
- **Safety**: All deletions go to "Recently Deleted" album (30 day recovery)

## Troubleshooting

**Stuck processes:**
```bash
ps aux | grep icloud
kill <PID>
```

**Authentication issues:**
- Script will prompt for password if no valid session
- Supports 2FA - enter code when prompted
- Session cached at `~/Library/Application Support/pyicloud/`

**Index out of date:**
- Just run download step again - it updates the index

**Want to start fresh:**
```bash
rm ~/icloud-photo-backup/download_progress.json
rm ~/icloud-photo-backup/delete_by_criteria_progress.json
```

## What's Different from Old Workflow?

**Before:**
1. Run download script
2. Run separate index building script
3. Run photo cleanup
4. Run video cleanup
5. Run deletion script for photos
6. Run deletion script for videos

**Now:**
1. Run `smart_workflow.sh` - it does everything

**Key improvements:**
- Index built during download (no separate step)
- Video criteria uses index metadata (no local video scanning)
- Single command for entire workflow
- Progress saved at every step
- Can skip steps you've already done
