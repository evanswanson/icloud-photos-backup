# Archived Scripts

This folder contains deprecated scripts that have been replaced by the streamlined workflow.

## Why These Were Archived

As of v3.0 (October 2025), the workflow was completely streamlined into a single command:
```bash
~/scripts/icloud-photo-backup/smart_workflow.sh
```

This new workflow makes the following scripts obsolete.

## Archived Scripts

### Download Scripts (Replaced by `smart_download.py`)
- **icloud_download_resilient.py** - Original download script
- **auto_download_icloud.sh** - Automated download wrapper
- **start_download_background.sh** - Background download script

**Replaced by:** `smart_download.py` which downloads AND builds index simultaneously

### Index Building (No Longer Separate Step)
- **build_icloud_index.py** - Standalone index builder

**Replaced by:** Index now built during download in `smart_download.py`

### Video Cleanup (Replaced by Index-Based Deletion)
- **video_cleanup.py** - Standard video scanning
- **video_cleanup_review.py** - Standard video review/deletion
- **video_cleanup_aggressive.py** - Aggressive video scanning
- **video_cleanup_aggressive_review.py** - Aggressive review/deletion

**Replaced by:** `delete_by_criteria.py` which uses index metadata (no local scanning)

### Workflow Scripts (Replaced by Smart Workflow)
- **complete_cleanup.sh** - v2.0 all-in-one workflow
- **check_status.sh** - Progress checking script

**Replaced by:** `smart_workflow.sh` with interactive prompts and better integration

### Deletion Scripts (Replaced by Fast Deletion)
- **icloud_delete_photos.py** - v1.0 deletion (had infinite loop bug)
- **icloud_delete_photos_v2.py** - v1.5 deletion (fixed loop, but slow)

**Replaced by:** `icloud_delete_fast.py` (10x faster, uses cached index)

### Documentation (Consolidated)
- **COMPLETE-WORKFLOW.md** - v1.0 workflow guide
- **OPTIMIZED-WORKFLOW.md** - v2.0 optimization guide
- **icloud-photo-backup-README.md** - Original README

**Replaced by:**
- `README.md` - Main documentation
- `GETTING-STARTED.md` - Quick start guide
- `CHANGELOG.md` - Version history

## Key Improvements in v3.0

### Before (v2.0 and earlier)
```bash
# Step 1: Download photos
~/scripts/icloud-photo-backup/auto_download_icloud.sh

# Step 2: Build index (separate step)
python3 ~/scripts/icloud-photo-backup/build_icloud_index.py

# Step 3: Run cleanup workflow
~/scripts/icloud-photo-backup/complete_cleanup.sh
```

### After (v3.0)
```bash
# One command does everything
~/scripts/icloud-photo-backup/smart_workflow.sh
```

**Benefits:**
- Index built during download (no separate step)
- Video deletion uses index metadata (no local scanning)
- Interactive prompts with ability to skip steps
- Better progress tracking and logging
- Simpler mental model

## Can I Still Use These Scripts?

Yes, these scripts are preserved in the archive folder and should still work. However:

- They are **no longer maintained**
- They are **less efficient** than the new workflow
- They may have **known issues** that won't be fixed
- Documentation may be **out of date**

**Recommendation:** Use the new streamlined workflow instead.

## Migration Guide

If you were using the old workflow:

### Old v2.0 Workflow
```bash
~/scripts/icloud-photo-backup/complete_cleanup.sh
```

### New v3.0 Workflow
```bash
~/scripts/icloud-photo-backup/smart_workflow.sh
```

That's it! The new workflow is a drop-in replacement.

### Cleanup Old Files

If you want to clean up old progress/log files:

```bash
# These files are no longer used
rm ~/icloud-photo-backup/video_cleanup_report.json
rm ~/icloud-photo-backup/video_cleanup_aggressive_report.json
rm ~/icloud-photo-backup/index_build_log.txt
```

The new workflow uses:
- `icloud_index.json` - Index with metadata
- `download_progress.json` - Download state
- `delete_by_criteria_progress.json` - Deletion state
- `cleanup_report.json` - Photo cleanup results
- Various `*_log.txt` files for logging

---

**Archive Date:** October 15, 2025
**Reason:** Superseded by v3.0 streamlined workflow
