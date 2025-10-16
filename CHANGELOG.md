# Changelog

## v2.1 - Complete Integrated Workflow (October 2025)

### ✨ New Features
- **Integrated video cleanup** into main workflow
- **Aggressive video criteria**: Old large videos (>100MB, >2yr) and short clips (<5s, >1yr)
- **Single command** now handles photos AND videos together
- Automatic detection of problematic media across entire library

### 🔧 Changes
- `complete_cleanup.sh` now includes video scanning and cleanup
- Added `video_cleanup_aggressive.py` for stringent video filtering
- Added `video_cleanup_aggressive_review.py` for interactive review
- Updated all documentation to reflect integrated workflow

### 📊 Expected Results
**Photo cleanup:**
- ~180-200 photos removed (duplicates, blurry, screenshots)

**Video cleanup (new):**
- ~20-40 old large videos (potential 5-15 GB savings)
- ~5-10 old short clips
- **Total video savings: 5-15 GB**

### 🎯 One-Command Workflow
```bash
~/scripts/icloud-photo-backup/complete_cleanup.sh
```

Now handles:
1. Photo scanning (duplicates, blurry, screenshots)
2. Video scanning (old large, old short)
3. Moving all problematic media to trash
4. Optional iCloud deletion (photos + videos)

---

## v2.0 - Performance Optimization (October 2025)

### ✨ New Features
- **Cached index system** for 10x faster iCloud deletions
- **build_icloud_index.py**: One-time scan creates reusable index
- **icloud_delete_fast.py**: Uses index for instant lookups
- **complete_cleanup.sh**: All-in-one interactive workflow

### 🚀 Performance Improvements
- **Deletion speed**: 2-3 minutes (vs 15-20 minutes)
- **90% time savings** on iCloud deletions
- **Cycling detection**: No more infinite loops
- **Progress tracking**: See each photo as it's found

### 🔧 Improvements
- Better error handling and recovery
- Continuous progress saving
- Interactive prompts for all steps
- Organized archive structure

### 📚 Documentation
- Created comprehensive README.md
- Added OPTIMIZED-WORKFLOW.md guide
- Updated COMPLETE-WORKFLOW.md
- Cleaned up deprecated scripts

---

## v1.0 - Initial Release (October 2025)

### Features
- Download all photos from iCloud
- Scan for photo quality issues
- Automatic cleanup of problematic images
- Video analysis tools
- Manual iCloud deletion

### Scripts
- `auto_download_icloud.sh` - Auto-restart downloader
- `icloud_download_resilient.py` - Resilient download with retry
- `photo_cleanup.py` - Photo quality analysis
- `auto_cleanup.py` - Automated photo cleanup
- `video_cleanup.py` - Video analysis
- `icloud_delete_photos.py` - iCloud deletion

### Known Issues
- iCloud API cycling could cause infinite loops
- Deletion required scanning entire library each time
- No integrated workflow (required multiple commands)

---

## Upgrade Path

### From v1.0 → v2.0
1. Run `build_icloud_index.py` once
2. Start using `complete_cleanup.sh`
3. Enjoy 10x faster deletions

### From v2.0 → v2.1
- No changes needed
- `complete_cleanup.sh` automatically includes video cleanup
- Can still use photo-only workflow if desired

---

## Statistics

### Time Savings
- **v1.0**: 90-150 minutes per cleanup
- **v2.0**: 15-25 minutes per cleanup (85% faster)
- **v2.1**: 15-25 minutes per cleanup + video cleanup included

### Space Savings
- **Photos**: ~180-200 files removed
- **Videos (v2.1)**: ~5-15 GB additional savings
- **Total**: Varies by library, typically 6-20 GB freed

### User Experience
- **v1.0**: 4-5 separate commands, manual tracking
- **v2.0**: 1 command, interactive prompts
- **v2.1**: 1 command, photos + videos integrated
