# iCloud Photo Backup & Cleanup - Complete Workflow

Complete guide for downloading, cleaning up, and managing your iCloud Photo Library.

## Overview

This toolkit provides automated scripts to:
1. Download all photos/videos from iCloud to local backup
2. Identify and remove duplicates, blurry images, and screenshots
3. Analyze videos for quality issues
4. Automatically delete unwanted media from iCloud

**Total scripts available:** 8 scripts for complete photo management

---

## Prerequisites

### Required Software

```bash
# Python 3 (already installed on macOS)
python3 --version

# ffmpeg (for video analysis)
brew install ffmpeg

# pyicloud library (should already be installed)
pip3 install pyicloud
```

### Directory Structure

All files are stored in: `/Users/evanswanson/icloud-photo-backup/`

```
/Users/evanswanson/icloud-photo-backup/
├── 2024/               # Downloaded photos by year
│   ├── 01/            # Organized by month
│   ├── 02/
│   └── ...
├── 2025/
├── trash/             # Moved problematic files (can be restored)
├── cleanup_report.json           # Photo analysis results
├── video_cleanup_report.json     # Video analysis results
├── download_log.txt              # Download progress log
├── download_progress.json        # Resume state for downloads
├── delete_log.txt                # iCloud deletion log
└── delete_progress.json          # iCloud deletion resume state
```

---

## Complete Workflow

### Phase 1: Download Photos from iCloud

#### Step 1.1: Initial Authentication (First Time Only)

```bash
python3 ~/scripts/icloud-photo-backup/icloud_download_resilient.py
```

**What happens:**
- Prompts for Apple ID password
- Asks for 2FA code
- Saves authenticated session for future use
- Press Ctrl+C after a few photos download to save session

**Note:** Session is cached in `~/Library/Application Support/pyicloud/` and reused automatically.

#### Step 1.2: Download All Photos (Recommended Method)

```bash
~/scripts/icloud-photo-backup/auto_download_icloud.sh
```

**Features:**
- Auto-restarts if stalled (no activity for 5 minutes)
- Shows live progress with timestamps
- Resumes from where it left off
- No babysitting required
- Uses saved session (no re-authentication)

**Monitoring progress:**
```bash
# Watch live log
tail -f /Users/evanswanson/icloud-photo-backup/download_log.txt

# Check total downloaded
find /Users/evanswanson/icloud-photo-backup -type f \( -name "*.heic" -o -name "*.HEIC" -o -name "*.jpeg" -o -name "*.jpg" -o -name "*.mov" -o -name "*.MOV" \) ! -path "*/trash/*" | wc -l
```

**Expected behavior:**
- Script may appear to stall while cycling through already-processed photos
- This is normal - it's checking what's already downloaded
- Downloads resume from last checkpoint automatically
- Total expected: ~7,000-9,000 photos (varies by library)

---

### Phase 2: Photo Cleanup

#### Step 2.1: Scan Photos for Issues

```bash
python3 ~/scripts/icloud-photo-backup/photo_cleanup.py
```

**What it detects:**
- **Duplicate images:** Using perceptual hash matching (threshold: 5)
- **Blurry images:** Laplacian variance < 100
- **Black/dark images:** Brightness < 30
- **Old screenshots:** > 6 months old

**Output:** Creates `cleanup_report.json` with detailed findings

**Typical results:**
- Analyzes ~6,000 images (videos show as "errors" - this is normal)
- Finds 80-100 duplicate groups
- Identifies 90-100 blurry images
- Flags old screenshots

**Time:** Takes 5-10 minutes for 6,000+ images

#### Step 2.2: Move Problematic Photos to Trash

```bash
python3 ~/scripts/icloud-photo-backup/auto_cleanup.py
```

**What it does:**
- Moves duplicates to trash (keeps one original)
- Moves blurry images to trash
- Moves dark/black images to trash
- Moves old screenshots to trash
- Preserves directory structure in trash folder

**Important:** Files are NOT deleted, just moved to `trash/` folder for review.

---

### Phase 3: Video Cleanup

#### Step 3.1: Scan Videos for Issues

```bash
python3 ~/scripts/icloud-photo-backup/video_cleanup.py
```

**What it detects:**
- **Short videos:** < 3 seconds (likely accidental)
- **Low resolution:** < 720p
- **Old screen recordings:** > 3 months
- **Large videos:** > 100 MB (for awareness)
- **Potential duplicates:** Same file size

**Output:** Creates `video_cleanup_report.json`

**Typical results:**
- Analyzes ~1,200 videos
- Total size: ~60+ GB
- Usually finds few problematic videos (good quality library)
- May identify large videos taking significant space

**Requirements:** Needs `ffmpeg` installed for full analysis

#### Step 3.2: Review and Remove Videos (Optional)

```bash
python3 ~/scripts/icloud-photo-backup/video_cleanup_review.py
```

**Interactive options:**
- Review each category (short, low-res, screen recordings)
- Delete individually or in bulk
- Skip categories you want to keep
- Moves videos to trash folder (not permanent)

**Note:** Only run if scan found problematic videos to remove.

---

### Phase 4: Delete from iCloud

#### Step 4.1: Delete Trashed Photos/Videos from iCloud

```bash
python3 ~/scripts/icloud-photo-backup/icloud_delete_photos.py
```

**What it does:**
1. Scans `trash/` folder for all media files
2. Asks for confirmation before deleting
3. Uses existing authenticated session
4. Indexes iCloud library to find matching files
5. Deletes in batches of 10 (prevents rate limiting)
6. Saves progress after each batch
7. Moves to "Recently Deleted" in iCloud (30-day recovery)

**Process:**
- Shows count of files to delete
- Requires "yes" confirmation
- May take 5-15 minutes to index full iCloud library
- Deletes with progress tracking
- Can be interrupted (Ctrl+C) and resumed

**Important:**
- Deleted photos go to "Recently Deleted" album in iCloud
- They stay there for 30 days before permanent deletion
- Available on all devices during 30-day period
- Can be restored before permanent deletion

---

## Script Reference

### Download Scripts

| Script | Purpose | When to Use |
|--------|---------|-------------|
| `icloud_download_resilient.py` | Manual resilient downloader | First-time auth, or manual control |
| `auto_download_icloud.sh` | Auto-restarting downloader | **Main download tool** - hands-free |
| `check_status.sh` | Check download progress | Monitor active downloads |

### Photo Cleanup Scripts

| Script | Purpose | When to Use |
|--------|---------|-------------|
| `photo_cleanup.py` | Scan for photo issues | After download completes |
| `auto_cleanup.py` | Remove problematic photos | After scanning photos |

### Video Cleanup Scripts

| Script | Purpose | When to Use |
|--------|---------|-------------|
| `video_cleanup.py` | Scan for video issues | After photo cleanup |
| `video_cleanup_review.py` | Interactive video review | If scan found issues |

### iCloud Deletion Script

| Script | Purpose | When to Use |
|--------|---------|-------------|
| `icloud_delete_photos.py` | Delete from iCloud | After local cleanup complete |

---

## Configuration Options

### Download Settings

Edit `icloud_download_resilient.py`:
```python
RETRY_ATTEMPTS = 3           # Retries per photo
RETRY_DELAY = 5              # Seconds between retries
SAVE_PROGRESS_EVERY = 50     # Checkpoint frequency
```

### Auto-Restart Settings

Edit `auto_download_icloud.sh`:
```bash
STALL_TIMEOUT = 300          # Seconds before restart (5 min)
MAX_RESTARTS = 100           # Maximum restart attempts
```

### Photo Cleanup Settings

Edit `photo_cleanup.py`:
```python
BLUR_THRESHOLD = 100.0       # Lower = more blurry
BLACK_THRESHOLD = 30         # Brightness threshold
SCREENSHOT_AGE_MONTHS = 6    # Screenshot age limit
DUPLICATE_HASH_DIFF = 5      # Perceptual hash sensitivity
```

### Video Cleanup Settings

Edit `video_cleanup.py`:
```python
MIN_DURATION = 3.0           # Min video length (seconds)
MIN_RESOLUTION = 720         # Min height (720p)
SCREEN_RECORDING_AGE_MONTHS = 3  # Screen recording age
LARGE_VIDEO_SIZE_MB = 100    # Large video threshold
```

### iCloud Deletion Settings

Edit `icloud_delete_photos.py`:
```python
BATCH_SIZE = 10              # Delete batch size
DELAY_BETWEEN_BATCHES = 2    # Seconds between batches
```

---

## Troubleshooting

### Download Issues

**Problem:** Script appears stalled with no new downloads

**Solution:**
- Check if it's cycling through already-processed photos (normal behavior)
- Wait for "Detected end of photo library" message
- Or press Ctrl+C and check total downloaded count
- Script saves progress every 50 photos automatically

**Problem:** Authentication fails

**Solution:**
```bash
# Clear cached session
rm -rf ~/Library/Application\ Support/pyicloud/

# Re-authenticate
python3 ~/scripts/icloud-photo-backup/icloud_download_resilient.py
```

**Problem:** Download keeps restarting

**Solution:**
- Check internet connection stability
- Increase `STALL_TIMEOUT` in `auto_download_icloud.sh`
- Try manual mode: `python3 ~/scripts/icloud-photo-backup/icloud_download_resilient.py`

### Cleanup Issues

**Problem:** Too many "errors" during photo scan

**Solution:**
- Errors for video files are normal and expected
- Only ~6,000 images analyzed out of ~7,000+ files is correct
- Videos cannot be analyzed by photo cleanup script

**Problem:** Want to restore files from trash

**Solution:**
```bash
# View trash contents
ls -R /Users/evanswanson/icloud-photo-backup/trash/

# Restore specific file (maintains directory structure)
mv /Users/evanswanson/icloud-photo-backup/trash/2025/10/photo.heic \
   /Users/evanswanson/icloud-photo-backup/2025/10/
```

### Video Analysis Issues

**Problem:** Limited video analysis (no metadata)

**Solution:**
```bash
# Install ffmpeg for full analysis
brew install ffmpeg

# Re-run video scan
python3 ~/scripts/icloud-photo-backup/video_cleanup.py
```

### iCloud Deletion Issues

**Problem:** Script can't find photos to delete

**Solution:**
- Photos may have different filenames in iCloud vs local
- Photos may have been deleted already
- Check `delete_progress.json` for details

**Problem:** Deletion interrupted

**Solution:**
- Progress is saved automatically after each batch
- Simply re-run the script to resume
- Already-deleted files are tracked in `delete_progress.json`

---

## Best Practices

### 1. Regular Maintenance Schedule

**Monthly:**
- Run download script to sync new photos
- Review cleanup reports
- Delete unwanted photos from iCloud

**Quarterly:**
- Run full photo and video cleanup scan
- Review large videos for space savings
- Clean up "Recently Deleted" in iCloud

### 2. Backup Strategy

**Before major cleanup:**
```bash
# Backup cleanup report
cp /Users/evanswanson/icloud-photo-backup/cleanup_report.json \
   /Users/evanswanson/icloud-photo-backup/cleanup_report_backup_$(date +%Y%m%d).json

# Review trash before iCloud deletion
ls -lR /Users/evanswanson/icloud-photo-backup/trash/
```

**After cleanup:**
- Wait 2-3 days before emptying local trash
- Keep "Recently Deleted" in iCloud until confident
- Document what was removed for reference

### 3. Space Management

**Check space usage:**
```bash
# Local backup size
du -sh /Users/evanswanson/icloud-photo-backup/

# Trash folder size
du -sh /Users/evanswanson/icloud-photo-backup/trash/

# By year
du -sh /Users/evanswanson/icloud-photo-backup/2*/
```

**Permanently delete trash:**
```bash
# WARNING: This cannot be undone!
rm -rf /Users/evanswanson/icloud-photo-backup/trash/
```

### 4. Session Management

**Check for active session:**
```bash
ls -la ~/Library/Application\ Support/pyicloud/
```

**Clear session to force re-auth:**
```bash
rm -rf ~/Library/Application\ Support/pyicloud/
```

**Check running processes:**
```bash
ps aux | grep icloud | grep -v grep
```

---

## Key Learnings

### What Works Well

1. **Auto-restart download script** is essential
   - Manual monitoring is tedious
   - Auto-restart handles network issues gracefully
   - Progress saved every 50 photos prevents data loss

2. **Authenticated session persistence** is reliable
   - No need to re-authenticate for every run
   - Session cached in `~/Library/Application Support/pyicloud/`
   - Automatically reused across all scripts

3. **Batch deletion with delays** prevents rate limiting
   - 10 photos per batch is optimal
   - 2-second delays prevent API throttling
   - Progress saved after each batch allows resume

4. **Trash folder approach** is safe
   - Review before permanent deletion
   - Maintains directory structure
   - Easy to restore mistakes

5. **Photo cleanup is effective**
   - Perceptual hashing finds true duplicates
   - Blur detection works well (Laplacian variance)
   - Screenshot detection by age is practical

### What to Watch Out For

1. **Download script cycling behavior**
   - Appears stalled when checking already-downloaded photos
   - This is normal - wait for completion message
   - Check file count to verify if actually downloading

2. **Video files in photo cleanup**
   - Videos show as "errors" in photo cleanup - this is expected
   - Only image files are analyzed
   - Use separate video cleanup for videos

3. **Large video collections**
   - Video indexing can take 5-15 minutes
   - Most libraries have good quality (few issues found)
   - Large videos (>100MB) are flagged but not auto-deleted

4. **iCloud library indexing time**
   - Must iterate through entire library to find photos
   - Can take several minutes for large libraries
   - Shows progress every 500 photos

5. **"Recently Deleted" in iCloud**
   - Deleted items stay 30 days in iCloud
   - Still count against storage quota during this period
   - Must empty "Recently Deleted" to fully free space

### Process Validation

**Confirmed working:**
- Authentication and session persistence ✓
- Download with resume capability ✓
- Photo quality analysis (blur, duplicates) ✓
- Video metadata analysis with ffmpeg ✓
- Batch deletion from iCloud ✓
- Progress tracking and resume ✓

**Expected results from real usage:**
- ~7,000-9,000 photos downloaded
- ~6,000 images analyzed (rest are videos)
- ~80-100 duplicate groups found
- ~95 blurry images identified
- ~85 old screenshots flagged
- ~180 total problematic photos removed
- ~1,200 videos analyzed
- ~60+ GB video storage
- Very few problematic videos (quality library)

---

## Quick Reference Commands

```bash
# Download all photos (recommended)
~/scripts/icloud-photo-backup/auto_download_icloud.sh

# Monitor download progress
tail -f /Users/evanswanson/icloud-photo-backup/download_log.txt

# Count downloaded files
find /Users/evanswanson/icloud-photo-backup -type f \( -name "*.heic" -o -name "*.jpeg" -o -name "*.jpg" -o -name "*.mov" \) ! -path "*/trash/*" | wc -l

# Scan photos for issues
python3 ~/scripts/icloud-photo-backup/photo_cleanup.py

# Move problematic photos to trash
python3 ~/scripts/icloud-photo-backup/auto_cleanup.py

# Scan videos for issues
python3 ~/scripts/icloud-photo-backup/video_cleanup.py

# Review and clean videos
python3 ~/scripts/icloud-photo-backup/video_cleanup_review.py

# Delete from iCloud
python3 ~/scripts/icloud-photo-backup/icloud_delete_photos.py

# Check space usage
du -sh /Users/evanswanson/icloud-photo-backup/
du -sh /Users/evanswanson/icloud-photo-backup/trash/

# View cleanup reports
cat /Users/evanswanson/icloud-photo-backup/cleanup_report.json | python3 -m json.tool
cat /Users/evanswanson/icloud-photo-backup/video_cleanup_report.json | python3 -m json.tool

# Clear authentication session
rm -rf ~/Library/Application\ Support/pyicloud/

# Kill stuck processes
ps aux | grep icloud | grep -v grep
# Then: kill <PID>
```

---

## Apple ID Configuration

**Account:** evan.swanson.receipt@gmail.com

**Requirements:**
- 2FA must be enabled
- App-specific password not needed (uses standard password)
- Session persists across reboots

---

## Summary

This complete workflow provides:
- ✓ Automated iCloud photo/video download
- ✓ Intelligent duplicate detection
- ✓ Quality analysis (blur, darkness)
- ✓ Screenshot management
- ✓ Video quality analysis
- ✓ Automated iCloud deletion
- ✓ Safe trash/restore system
- ✓ Progress tracking and resume capability

**Total time for full workflow:** 2-3 hours (mostly unattended)

**Storage impact:** Removes ~180 photos, potential to remove problematic videos, frees iCloud space after 30 days.

**Safety:** All deletions go through trash folder first, 30-day iCloud recovery period.
