# iCloud Photo Backup & Cleanup Tools

Complete automated solution for backing up iCloud photos, removing duplicates, blurry images, and unwanted videos.

## 🚀 Quick Start

### Daily Photo Backup (Recommended)

```bash
# Manual run - downloads photos from last 7 days
python3 ~/scripts/icloud-photo-backup/smart_download.py --recent 7 --verbose

# Automated - runs daily at 9 PM, sends email summary
# See SCHEDULING.md for setup
```

### Monthly Cleanup Workflow

```bash
# Interactive mode (prompts before deletion)
~/scripts/icloud-photo-backup/smart_workflow.sh

# Headless mode (auto-delete, for automation)
~/scripts/icloud-photo-backup/smart_workflow.sh --headless
```

The cleanup workflow handles everything:
- Downloads missing photos/videos from iCloud
- Builds/updates index during download (with metadata)
- Scans photos for duplicates, blurry images, screenshots
- Uses index to identify old large videos and short clips
- Deletes all problematic media from iCloud

**First time?** See the [Getting Started Guide](GETTING-STARTED.md).

**Automate it:** See [SCHEDULING.md](SCHEDULING.md) for automated daily backups and monthly cleanup.

## 📚 Documentation

- **[SETUP.md](SETUP.md)** - First-time installation and configuration
- **[GETTING-STARTED.md](GETTING-STARTED.md)** - Quick start guide for new users
- **[SCHEDULING.md](SCHEDULING.md)** - Setup automated backups (launchd)
- **[CHANGELOG.md](CHANGELOG.md)** - Version history and changes

## 🎯 Active Scripts

| Script | Purpose | When to Use |
|--------|---------|-------------|
| `smart_download.py` | **Download + build index** | Daily (automated at 9 PM) |
| `smart_workflow.sh` | **Complete cleanup workflow** | Monthly maintenance |
| `photo_cleanup.py` | Scan for photo issues | Part of workflow |
| `auto_cleanup.py` | Move photos to trash | Part of workflow |
| `delete_by_criteria.py` | Index-based video deletion | Part of workflow |
| `icloud_delete_fast.py` | Fast deletion from trash | Part of workflow |
| `query_index.py` | Query index statistics | Anytime (offline) |

## 📁 Directory Structure

```
/Users/evanswanson/scripts/icloud-photo-backup/
├── smart_workflow.sh            # ⭐ Main workflow script
├── smart_download.py            # ⭐ Download + index building
├── delete_by_criteria.py        # ⭐ Index-based deletion
├── icloud_delete_fast.py        # ⭐ Fast deletion
├── photo_cleanup.py             # Photo scanning
├── auto_cleanup.py              # Move to trash
├── query_index.py               # Index queries
├── archive/                     # Deprecated scripts
├── README.md                    # This file
├── GETTING-STARTED.md           # Quick start guide
└── CHANGELOG.md                 # Version history

/Users/evanswanson/icloud-photo-backup/
├── 2024/, 2025/, etc/          # Downloaded photos (by year/month)
├── trash/                       # Problematic photos (can restore)
├── logs-archive/                # Old logs and progress files
├── icloud_index.json           # Cached library index (with metadata)
├── cleanup_report.json         # Photo analysis results
├── download_log.txt            # Download progress
├── download_progress.json      # Download resume state
├── delete_by_criteria_log.txt  # Video deletion log
└── delete_log_fast.txt         # Photo deletion log
```

## 🏁 First-Time Setup

### Quick Setup (5 minutes)

1. **Clone and configure:**
```bash
cd ~/scripts
git clone https://github.com/yourusername/icloud-photo-backup.git
cd icloud-photo-backup
cp config.json.template config.json
# Edit config.json with your Apple ID and settings
```

2. **Install dependencies:**
```bash
pip3 install pyicloud opencv-python imagehash Pillow
```

3. **Run first backup:**
```bash
python3 smart_download.py --recent 30 --verbose
# Enter Apple ID password when prompted
# Enter 2FA code from your trusted device
```

**For detailed setup instructions, see [SETUP.md](SETUP.md)**

## 🔄 Regular Maintenance

### Daily Backup (Automated)

Runs automatically every day at 9 PM:
- Downloads photos from last 7 days (~15 seconds)
- Sends email summary of new photos
- Updates index incrementally

### Monthly Full Backup (Automated)

Runs automatically on the 1st of each month at 4 AM:
- Full library sync (downloads any missed photos)
- Complete index rebuild
- Sends email summary

### Monthly Cleanup (Manual - 5-10 minutes)

```bash
# Run the cleanup workflow
~/scripts/icloud-photo-backup/smart_workflow.sh
```

It will:
- Scan for issues in photos
- Delete problematic media (duplicates, blurry, old videos)

**Setup automation:** See [SCHEDULING.md](SCHEDULING.md)

## ⚡ Performance

### Before Streamlined Workflow
- Manual multi-step process: 90-150 minutes
- Separate download, indexing, scanning, deletion steps
- Must remember multiple commands

### After Streamlined Workflow
- Single command: 5-10 minutes (after initial setup)
- Index built during download (no separate step)
- Video criteria uses metadata (no local scanning)

**Result: 85-95% time savings!**

## 🔧 Common Tasks

### Query Index Statistics

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

### Check Download Progress

```bash
tail -f ~/icloud-photo-backup/download_log.txt
```

### Count Downloaded Photos

```bash
find ~/icloud-photo-backup -type f \( -name "*.heic" -o -name "*.jpg" -o -name "*.mov" \) ! -path "*/trash/*" ! -path "*/logs-archive/*" | wc -l
```

### View Cleanup Report

```bash
cat ~/icloud-photo-backup/cleanup_report.json | python3 -m json.tool | less
```

### Restore from Trash

```bash
# View trash
ls -R ~/icloud-photo-backup/trash/

# Restore a file
mv ~/icloud-photo-backup/trash/2025/10/photo.heic \
   ~/icloud-photo-backup/2025/10/
```

### Permanently Delete Trash

```bash
rm -rf ~/icloud-photo-backup/trash/
```

## 📊 What Gets Cleaned Up

### Photo Cleanup Detects:
- **Duplicates** - Perceptual hash matching
- **Blurry images** - Laplacian variance < 100
- **Dark images** - Brightness < 30
- **Old screenshots** - > 6 months old

### Video Cleanup (Index-Based):
- **Old large videos** - > 100MB AND > 2 years old
- **Old short videos** - < 5 seconds AND > 1 year old

### Customization

Edit `delete_by_criteria.py` at line 21-35 to change video criteria:

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

### Typical Results:
- ~6,000 images analyzed
- ~80-100 duplicate groups
- ~95 blurry images
- ~85 old screenshots
- **~180-200 total photos removed**
- Plus large/old videos based on criteria

## 🐛 Troubleshooting

### Authentication Issues

```bash
# Clear session and re-authenticate
rm -rf ~/Library/Application\ Support/pyicloud/
~/scripts/icloud-photo-backup/smart_workflow.sh
```

### Stuck Processes

```bash
# Find running processes
ps aux | grep icloud | grep -v grep

# Kill if needed
kill <PID>
```

### Index Out of Date

```bash
# Just run the workflow - it updates the index automatically
~/scripts/icloud-photo-backup/smart_workflow.sh
```

### Want to Start Fresh

```bash
# Clear progress files
rm ~/icloud-photo-backup/download_progress.json
rm ~/icloud-photo-backup/delete_by_criteria_progress.json

# Re-run workflow
~/scripts/icloud-photo-backup/smart_workflow.sh
```

## 🔐 Safety Features

- ✅ All deletions go to trash folder first (local)
- ✅ iCloud deletions go to "Recently Deleted" (30-day recovery)
- ✅ Progress saved continuously (can resume anytime)
- ✅ Interactive prompts at each step
- ✅ Can skip steps already completed
- ✅ Comprehensive logging

## 📦 Requirements

- macOS with Python 3
- iCloud account with 2FA enabled
- Python packages (install with pip3):
  - `pyicloud` - iCloud API access
  - `opencv-python` - Image analysis
  - `imagehash` - Duplicate detection
  - `Pillow` - Image processing

Optional:
- `ffmpeg` for video duration analysis: `brew install ffmpeg`
- Gmail account for email notifications

## 🚀 Installation

See [SETUP.md](SETUP.md) for complete installation instructions.

## 📝 Version History

### v3.0 - Streamlined Workflow (October 2025)
- ✨ **NEW:** Single command for entire workflow
- ✨ **NEW:** Index built during download (no separate step)
- ✨ **NEW:** Video deletion uses index metadata (no local scanning)
- ✨ **NEW:** Interactive prompts with step skipping
- 📚 Simplified documentation
- 🗄️ Archived legacy scripts

### v2.0 - Optimized Workflow (October 2025)
- ✨ Added cached index system (10x faster deletions)
- ✨ Added all-in-one cleanup workflow
- ✨ Added cycling detection for API reliability
- 🔧 Improved progress tracking and logging

### v1.0 - Initial Release (October 2025)
- Download, cleanup, and deletion scripts
- Photo and video analysis
- Manual multi-step workflow

---

## Quick Command Reference

### Daily Use
```bash
# Manual daily backup (last 7 days)
python3 ~/scripts/icloud-photo-backup/smart_download.py --recent 7 --verbose

# Check automated backup status
launchctl list | grep icloud

# View daily backup logs
tail -f ~/icloud-photo-backup/daily_backup.log

# View monthly backup logs
tail -f ~/icloud-photo-backup/monthly_backup.log
```

### Monthly Cleanup
```bash
# Run cleanup workflow (interactive)
~/scripts/icloud-photo-backup/smart_workflow.sh

# Query index statistics (offline)
python3 ~/scripts/icloud-photo-backup/query_index.py stats

# Monitor download progress
tail -f ~/icloud-photo-backup/download_log.txt
```

### Scheduled Jobs
```bash
# Check job status
launchctl list | grep icloud

# Manually trigger daily backup
launchctl start com.icloud.backup.daily

# Manually trigger monthly backup
launchctl start com.icloud.backup.monthly
```

For detailed instructions, see [GETTING-STARTED.md](GETTING-STARTED.md) and [SCHEDULING.md](SCHEDULING.md).
