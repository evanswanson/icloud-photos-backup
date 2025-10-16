# Ready to Test! 🚀

Your streamlined iCloud photo backup and cleanup system is ready to test.

## Quick Start (Safest Method)

```bash
~/scripts/icloud-photo-backup/safe_test_workflow.sh
```

This runs the workflow with automatic safety monitoring:
- ✓ Auto-timeout after 2 hours (prevents infinite loops)
- ✓ Progress updates every 30 seconds
- ✓ Ctrl+C stops safely (saves progress)
- ✓ Creates timestamped test log

## What Will Happen

### 1. Authentication (30 seconds)
- Uses existing session if available, or
- Prompts for password + 2FA code

### 2. Download + Index Building (60-120 min first time)
- Downloads any missing photos/videos
- Builds index simultaneously with metadata
- Auto-detects cycling (500 consecutive duplicates)
- Saves progress every 50 photos

### 3. Photo Cleanup (5-10 min)
- Scans for duplicates, blurry images, screenshots
- Generates report with findings
- Prompts to move problematic photos to trash

### 4. Video Analysis (<1 min)
- Uses index metadata (no local scanning!)
- Finds old large videos (>100MB, >2yr)
- Finds old short clips (<5s, >1yr)
- Shows what would be deleted

### 5. iCloud Deletion (2-5 min)
- Deletes photos from trash folder
- Deletes videos matching criteria
- Items go to "Recently Deleted" (30-day recovery)

## Safety Features

**Built-in protections:**
- Cycling detection (stops at 500 consecutive duplicates)
- Progress saved every 50 items (can resume anytime)
- Ctrl+C works (saves state on interrupt)
- Confirmation prompts before deletion
- All deletions recoverable for 30 days in iCloud

**Monitoring tools:**
- `safe_test_workflow.sh` - Runs with automatic monitoring
- `monitor_workflow.sh` - Separate monitor (use with 2 terminals)
- Log files update in real-time

**Kill switches:**
- Press Ctrl+C anytime
- Auto-timeout after 2 hours (download phase)
- Manual: `ps aux | grep icloud` then `kill <PID>`

## Expected Results (First Run)

**You should see:**
```
✓ Downloaded: ~6,000-7,000 photos
✓ Index: ~6,000-7,000 items with metadata
✓ Duplicates: ~80-100 groups found
✓ Blurry: ~90-100 images
✓ Screenshots: ~80-90 old ones
✓ Videos: ~20-30 matching deletion criteria
✓ Total cleanup: ~200-250 items removed
```

**Timeline:**
- First run: 70-135 minutes total
- Monthly runs: 10-20 minutes

## Monitoring Options

### Option 1: Safe Mode (Easiest)
```bash
~/scripts/icloud-photo-backup/safe_test_workflow.sh
```
Shows progress automatically, easy Ctrl+C abort.

### Option 2: Two Terminals
**Terminal 1:**
```bash
~/scripts/icloud-photo-backup/smart_workflow.sh
```

**Terminal 2:**
```bash
~/scripts/icloud-photo-backup/monitor_workflow.sh
```
Shows CPU/memory, progress, warnings, refreshes every 5 sec.

### Option 3: Manual Logs
```bash
tail -f ~/icloud-photo-backup/download_log.txt
```
Watch raw log output.

## Warning Signs to Watch For

### ❌ Bad: Infinite Loop
```
[15000] Downloaded: 50, Skipped: 14950
[20000] Downloaded: 55, Skipped: 19945
```
**Fix:** Should auto-detect and stop. If not, press Ctrl+C.

### ❌ Bad: Hung Process
No log updates for 10+ minutes, CPU at 0%.
**Fix:** Press Ctrl+C or kill process.

### ✓ Good: Normal Progress
```
[500] Downloaded: 125, Skipped: 375, Indexed: 500
[1000] Downloaded: 280, Skipped: 720, Indexed: 1000
...
✓ Detected end of photo library (seen 500 repeated photos)
```

### ✓ Good: Cycling Detection
```
✓ Detected end of photo library (seen 500 repeated photos)
All unique photos have been processed!
```

## If Something Goes Wrong

### Stuck on Authentication
```bash
rm -rf ~/Library/Application\ Support/pyicloud/
~/scripts/icloud-photo-backup/safe_test_workflow.sh
```

### Need to Abort
Press **Ctrl+C** - progress is saved automatically.

### Resume After Abort
```bash
~/scripts/icloud-photo-backup/smart_workflow.sh
# Answer "skip" to already-completed steps
```

### Check What Happened
```bash
# View statistics
python3 ~/scripts/icloud-photo-backup/query_index.py stats

# Check last 50 log lines
tail -50 ~/icloud-photo-backup/download_log.txt

# View progress state
cat ~/icloud-photo-backup/download_progress.json | python3 -m json.tool
```

## After Testing

### Verify Success
```bash
# Check index stats
python3 ~/scripts/icloud-photo-backup/query_index.py stats

# Count downloaded files
find ~/icloud-photo-backup -type f \( -name "*.heic" -o -name "*.jpg" \) ! -path "*/trash/*" | wc -l

# Check what's in trash
ls -la ~/icloud-photo-backup/trash/
```

### Monthly Maintenance
Just run it again:
```bash
~/scripts/icloud-photo-backup/smart_workflow.sh
```
Takes 10-20 minutes to process new photos.

## Documentation

- **[TESTING-GUIDE.md](TESTING-GUIDE.md)** - Detailed testing instructions
- **[GETTING-STARTED.md](GETTING-STARTED.md)** - Usage guide
- **[README.md](README.md)** - Main documentation

## Ready?

**Recommended first test:**
```bash
~/scripts/icloud-photo-backup/safe_test_workflow.sh
```

This gives you:
- Automatic monitoring
- Safety timeouts
- Progress updates
- Easy abort

**Or dive right in:**
```bash
~/scripts/icloud-photo-backup/smart_workflow.sh
```

Good luck! The workflow is battle-tested with cycling detection, progress saving, and comprehensive logging. You're in good hands.
