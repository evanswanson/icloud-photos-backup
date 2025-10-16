# Testing Guide

How to safely test the streamlined workflow with monitoring and safety checks.

## Option 1: Safe Test Mode (Recommended for First Test)

This runs the workflow with automatic safety monitoring:

```bash
~/scripts/icloud-photo-backup/safe_test_workflow.sh
```

**Safety features:**
- Auto-timeout after 2 hours (prevents runaway downloads)
- Monitors for hung processes (no progress for 10 min)
- Easy Ctrl+C abort (saves progress automatically)
- Creates timestamped test log
- Shows progress every 30 seconds

**What to watch for:**
- Process should start downloading photos
- Log should show regular progress updates
- Will auto-detect cycling and stop after ~500 consecutive duplicates
- Press Ctrl+C anytime to stop safely

## Option 2: Two-Terminal Monitoring

Run workflow in one terminal, monitor in another.

**Terminal 1 - Run Workflow:**
```bash
~/scripts/icloud-photo-backup/smart_workflow.sh
```

**Terminal 2 - Monitor:**
```bash
~/scripts/icloud-photo-backup/monitor_workflow.sh
```

**What the monitor shows:**
- Running processes (PID, CPU, memory)
- Last log entries (download, deletion)
- Progress indicators (downloaded count, index size)
- Warning alerts (high CPU, hung processes, errors)
- Refreshes every 5 seconds

## Option 3: Manual Log Watching

Watch the log files directly:

```bash
# Watch download progress
tail -f ~/icloud-photo-backup/download_log.txt

# In another terminal, watch for errors
tail -f ~/icloud-photo-backup/download_log.txt | grep -i "error\|warning"
```

## What to Expect on First Run

### Phase 1: Download + Index (60-120 min)
```
[2025-10-15 11:30:00] Starting authentication...
[2025-10-15 11:30:05] ✓ Using existing authenticated session
[2025-10-15 11:30:10] Accessing iCloud Photos library...
[2025-10-15 11:30:15] Starting download + index building...
[2025-10-15 11:31:00] [50] Downloaded: 1, Skipped: 49, Failed: 0, Indexed: 50
[2025-10-15 11:32:00] [100] Downloaded: 5, Skipped: 95, Failed: 0, Indexed: 100
...
[2025-10-15 13:00:00] ✓ Detected end of photo library (seen 500 repeated photos)
[2025-10-15 13:00:00] All unique photos have been processed!
```

**Good signs:**
- "Downloaded" count increasing
- "Indexed" count increasing
- Eventually hits cycling detection (500 consecutive repeats)
- Stops automatically

**Bad signs:**
- Index keeps growing past 15,000 without cycling detection
- CPU stays at 100% for >30 minutes with no log updates
- "Failed" count very high (>10% of total)

### Phase 2: Photo Cleanup (5-10 min)
```
Scanning 6,051 images for issues...
Found 84 duplicate groups (96 images total)
Found 95 blurry images
Found 85 old screenshots (>6 months)
```

**Good signs:**
- Completes in reasonable time
- Finds some duplicates/blurry (expected)
- No crashes

### Phase 3: Video Analysis (30 sec - 1 min)
```
Analyzing index with deletion criteria...
✓ Found 23 items matching criteria
Items to delete: 23
Total size: 2.34 GB
```

**Good signs:**
- Uses index (very fast, no local scanning)
- Shows criteria matches
- Gives size estimate

### Phase 4: Deletion (2-5 min)
```
Starting deletion in batches of 10...
✓ Deleted (1): IMG_1234.heic - Old large video: 2.3yr, 125.4MB
✓ Deleted (2): IMG_5678.mov - Old large video: 3.1yr, 201.2MB
...
Successfully deleted: 23
```

**Good signs:**
- Deletes in batches (10 at a time)
- Shows progress for each item
- Completes without errors

## Signs of Problems

### Infinite Loop
**Symptom:** Index growing past 20,000 with very few downloads
```
[15000] Downloaded: 50, Skipped: 14950
[16000] Downloaded: 55, Skipped: 15945
[17000] Downloaded: 58, Skipped: 16942
```

**Fix:** The script has built-in cycling detection (500 consecutive duplicates). If it doesn't trigger:
- Press Ctrl+C to stop
- Check `download_progress.json` for resume state
- Report issue

### Hung Process
**Symptom:** No log updates for 10+ minutes, CPU at 0%

**Fix:**
```bash
# Find the process
ps aux | grep icloud | grep -v grep

# Kill it
kill <PID>

# Workflow saves progress every 50 photos, can resume
```

### High CPU Continuous
**Symptom:** CPU at 150%+ for 30+ minutes with no progress

**Fix:**
- Likely processing large video files
- Wait a bit longer, or
- Press Ctrl+C to stop and investigate

### Authentication Stuck
**Symptom:** Prompts for password but doesn't accept it

**Fix:**
```bash
# Clear session
rm -rf ~/Library/Application\ Support/pyicloud/

# Try again
~/scripts/icloud-photo-backup/smart_workflow.sh
```

## Aborting Safely

**Method 1 - Ctrl+C:**
Just press Ctrl+C. The scripts have interrupt handlers that save progress.

**Method 2 - Kill Process:**
```bash
ps aux | grep -E "smart_workflow|smart_download|delete_by_criteria" | grep -v grep
kill <PID>
```

Progress is saved every 50 photos, so you'll resume from last checkpoint.

## Resuming After Abort

Just run the workflow again:
```bash
~/scripts/icloud-photo-backup/smart_workflow.sh
```

It will:
- Load previous progress
- Show what was already done
- Let you skip completed steps
- Continue from where it left off

## Verifying Success

After workflow completes:

```bash
# Check index statistics
python3 ~/scripts/icloud-photo-backup/query_index.py stats

# Count local files
find ~/icloud-photo-backup -type f \( -name "*.heic" -o -name "*.jpg" -o -name "*.mov" \) ! -path "*/trash/*" | wc -l

# Check trash
find ~/icloud-photo-backup/trash -type f | wc -l

# View deletion logs
cat ~/icloud-photo-backup/delete_by_criteria_log.txt
cat ~/icloud-photo-backup/delete_log_fast.txt
```

## Test Modes

### Dry Run (No Deletion)
Answer "no" to deletion prompts. Everything else runs normally.

### Skip Download (Test Cleanup Only)
If you already have photos downloaded:
```bash
~/scripts/icloud-photo-backup/smart_workflow.sh
# Answer "skip" to download step
# Answer "yes" to other steps
```

### Index Only (No Cleanup)
```bash
~/scripts/icloud-photo-backup/smart_workflow.sh
# Answer "yes" to download
# Answer "skip" to all other steps
```

## Getting Help

**Check logs:**
```bash
tail -100 ~/icloud-photo-backup/download_log.txt
tail -100 ~/icloud-photo-backup/delete_by_criteria_log.txt
```

**Check progress files:**
```bash
cat ~/icloud-photo-backup/download_progress.json | python3 -m json.tool
cat ~/icloud-photo-backup/delete_by_criteria_progress.json | python3 -m json.tool
```

**Check for stuck processes:**
```bash
ps aux | grep icloud | grep -v grep
```

## Expected Timeline

**First run (empty library):**
- Download + Index: 60-120 minutes
- Photo Cleanup: 5-10 minutes
- Video Analysis: 30 seconds
- Deletion: 2-5 minutes
- **Total: ~70-135 minutes**

**Subsequent runs (monthly):**
- Download + Index: 5-15 minutes (only new photos)
- Photo Cleanup: 2-5 minutes
- Video Analysis: 30 seconds
- Deletion: 1-2 minutes
- **Total: ~10-20 minutes**

Good luck with testing! The safe test mode is recommended for peace of mind.
