# iCloud Photo Backup & Cleanup Tools

Complete solution for backing up iCloud photos and removing duplicates, blurry images, and screenshots.

## ⚡ NEW: Optimized Workflow (10x Faster!)

**See [OPTIMIZED-WORKFLOW.md](OPTIMIZED-WORKFLOW.md) for the new streamlined process!**

### Quick Start (New Method)

```bash
# One command does it all:
~/scripts/icloud-photo-backup/complete_cleanup.sh
```

**Time:** 5-10 minutes (vs 90+ minutes with old method)

---

## Original Workflow (Still Available)

### 1. Initial Authentication (Required First Time)

Before using the auto-restart script, authenticate once:

```bash
python3 ~/scripts/icloud-photo-backup/icloud_download_resilient.py
```

- Enter your Apple ID password
- Enter 2FA code when prompted
- Let it download a few photos, then press Ctrl+C
- Session is now saved for auto-restart

### 2. Download All Photos from iCloud (Auto-Restart)

**Recommended - No babysitting required:**

```bash
~/scripts/icloud-photo-backup/auto_download_icloud.sh
```

- Auto-restarts if stalled (no activity for 5 minutes)
- Shows live progress with timestamps
- Resumes from where it left off
- Runs until all 8,879 photos are downloaded
- Uses saved session (no re-authentication needed)

**Alternative - Manual (requires monitoring):**

```bash
python3 ~/scripts/icloud-photo-backup/icloud_download_resilient.py
```

### 3. Scan for Issues

After download completes:

```bash
python3 ~/scripts/icloud-photo-backup/photo_cleanup.py
```

Scans for:
- Duplicate images (perceptual hash matching)
- Blurry images (Laplacian variance < 100)
- Black/dark images (brightness < 30)
- Old screenshots (> 6 months)

Creates report: `/Users/evanswanson/icloud-photo-backup/cleanup_report.json`

### 4. Clean Up Problematic Photos

```bash
python3 ~/scripts/icloud-photo-backup/auto_cleanup.py
```

- Moves duplicates to trash (keeps originals)
- Moves blurry images to trash
- Files go to `/Users/evanswanson/icloud-photo-backup/trash/`
- Can be restored if needed

## Scripts Reference

### Download Scripts

| Script | Purpose | When to Use |
|--------|---------|-------------|
| `auto_download_icloud.sh` | Auto-restarting downloader | **Main download tool** - use this! |
| `icloud_download_resilient.py` | Manual resilient downloader | If you want more control |

### Cleanup Scripts

| Script | Purpose | When to Use |
|--------|---------|-------------|
| `photo_cleanup.py` | Scan for issues | After download completes |
| `auto_cleanup.py` | Remove problematic images | After scanning |

## Directory Structure

```
/Users/evanswanson/icloud-photo-backup/
├── 2025/
│   ├── 01/
│   ├── 02/
│   └── ...
├── 2024/
│   └── ...
├── trash/              # Deleted files (can be restored)
├── cleanup_report.json # Analysis results
├── download_log.txt    # Download progress log
└── download_progress.json # Resume state
```

## Configuration

Edit these values in the scripts if needed:

### Download Settings (`icloud_download_resilient.py`)
- `RETRY_ATTEMPTS = 3` - Number of retries per photo
- `RETRY_DELAY = 5` - Seconds between retries
- `SAVE_PROGRESS_EVERY = 50` - Checkpoint frequency

### Auto-Restart Settings (`auto_download_icloud.sh`)
- `STALL_TIMEOUT = 300` - Seconds before restart (5 minutes)
- `MAX_RESTARTS = 100` - Maximum restart attempts

### Cleanup Settings (`photo_cleanup.py`)
- `BLUR_THRESHOLD = 100.0` - Lower = more blurry
- `BLACK_THRESHOLD = 30` - Brightness threshold
- `SCREENSHOT_AGE_MONTHS = 6` - Screenshot age limit
- `DUPLICATE_HASH_DIFF = 5` - Perceptual hash sensitivity

## Monitoring Progress

### Watch live log:
```bash
tail -f /Users/evanswanson/icloud-photo-backup/download_log.txt
```

### Check progress file:
```bash
cat /Users/evanswanson/icloud-photo-backup/download_progress.json
```

### Count downloaded photos:
```bash
find /Users/evanswanson/icloud-photo-backup -type f \( -name "*.heic" -o -name "*.jpeg" -o -name "*.jpg" \) ! -path "*/trash/*" | wc -l
```

## Troubleshooting

### Download stalls repeatedly
- Check internet connection
- Increase `STALL_TIMEOUT` in auto_download_icloud.sh
- Try manual mode and restart when needed

### Authentication fails
- Make sure you have 2FA enabled on your Apple ID
- Check password is correct
- Try removing stored session: `rm -rf ~/Library/Application\ Support/pyicloud/`

### Photos not appearing
- Check download_log.txt for errors
- Verify photos are in iCloud via Photos app
- Check disk space

### Restore from trash
Files in trash maintain directory structure:
```bash
# View trash contents
ls -R /Users/evanswanson/icloud-photo-backup/trash/

# Restore a specific file
mv /Users/evanswanson/icloud-photo-backup/trash/2025/10/photo.heic \
   /Users/evanswanson/icloud-photo-backup/2025/10/
```

### Permanently delete trash
```bash
rm -rf /Users/evanswanson/icloud-photo-backup/trash/
```

## Workflow Summary

1. **Download**: Run `auto_download_icloud.sh` → authenticate → walk away
2. **Wait**: Let it run until all photos downloaded (check log occasionally)
3. **Scan**: Run `photo_cleanup.py` to analyze
4. **Review**: Check `cleanup_report.json`
5. **Clean**: Run `auto_cleanup.py` to remove issues
6. **Verify**: Check trash folder before permanent deletion
7. **Done**: You now have a clean, de-duplicated backup!

## Files Location

All files in: `/Users/evanswanson/icloud-photo-backup/`

- Original photos organized by year/month
- Trash folder with removed photos
- Progress and log files

Total expected: ~8,879 photos (minus duplicates/blurry)
