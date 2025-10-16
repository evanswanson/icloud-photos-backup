# Automated Scheduling

Run iCloud photo backups automatically using macOS launchd.

## Current Schedule

Two automated jobs are configured:

### 1. Daily Backup (`com.icloud.backup.daily`)
- **Schedule:** Every day at 9:00 PM Pacific
- **Command:** `smart_download.py --recent 7 --verbose`
- **Duration:** ~15 seconds
- **Purpose:** Download photos from last 7 days, send email summary

### 2. Monthly Full Backup (`com.icloud.backup.monthly`)
- **Schedule:** 1st of each month at 4:00 AM
- **Command:** `smart_download.py --verbose`
- **Duration:** 5-30 minutes (depending on new photos)
- **Purpose:** Full library sync to catch any missed photos

## Managing Scheduled Jobs

### Check Status
```bash
launchctl list | grep icloud
```

Should show:
```
-	0	com.icloud.backup.daily
-	0	com.icloud.backup.monthly
```

### View Logs

**Daily backup:**
```bash
tail -f ~/icloud-photo-backup/daily_backup.log
tail -f ~/icloud-photo-backup/daily_backup_error.log
```

**Monthly backup:**
```bash
tail -f ~/icloud-photo-backup/monthly_backup.log
tail -f ~/icloud-photo-backup/monthly_backup_error.log
```

**Download log (both jobs):**
```bash
tail -f ~/icloud-photo-backup/download_log.txt
```

### Manually Trigger Jobs

```bash
# Test daily backup now
launchctl start com.icloud.backup.daily

# Test monthly backup now
launchctl start com.icloud.backup.monthly
```

### Stop/Start Jobs

```bash
# Stop daily backup
launchctl unload ~/Library/LaunchAgents/com.icloud.backup.daily.plist

# Start daily backup
launchctl load ~/Library/LaunchAgents/com.icloud.backup.daily.plist

# Same for monthly
launchctl unload ~/Library/LaunchAgents/com.icloud.backup.monthly.plist
launchctl load ~/Library/LaunchAgents/com.icloud.backup.monthly.plist
```

## Configuration Files

Located in `~/Library/LaunchAgents/`:
- `com.icloud.backup.daily.plist` - Daily backup at 9 PM
- `com.icloud.backup.monthly.plist` - Monthly backup on 1st at 4 AM

## Customizing the Schedule

Edit the plist files to change timing:

### Change Daily Time

Edit `~/Library/LaunchAgents/com.icloud.backup.daily.plist`:

```xml
<!-- Current: 9 PM daily -->
<key>StartCalendarInterval</key>
<dict>
    <key>Hour</key>
    <integer>21</integer>  <!-- Change this (0-23) -->
    <key>Minute</key>
    <integer>0</integer>   <!-- Change this (0-59) -->
</dict>
```

Examples:
- 6 AM: `<integer>6</integer>`
- 11:30 PM: `<integer>23</integer>` + `<integer>30</integer>`

### Change Daily to Different Days

Run only on specific weekdays:

```xml
<!-- Monday, Wednesday, Friday at 9 PM -->
<key>StartCalendarInterval</key>
<array>
    <dict>
        <key>Weekday</key>
        <integer>1</integer>  <!-- Monday -->
        <key>Hour</key>
        <integer>21</integer>
        <key>Minute</key>
        <integer>0</integer>
    </dict>
    <dict>
        <key>Weekday</key>
        <integer>3</integer>  <!-- Wednesday -->
        <key>Hour</key>
        <integer>21</integer>
        <key>Minute</key>
        <integer>0</integer>
    </dict>
    <dict>
        <key>Weekday</key>
        <integer>5</integer>  <!-- Friday -->
        <key>Hour</key>
        <integer>21</integer>
        <key>Minute</key>
        <integer>0</integer>
    </dict>
</array>
```

**Weekday values:** 0=Sunday, 1=Monday, 2=Tuesday, 3=Wednesday, 4=Thursday, 5=Friday, 6=Saturday

### Change Monthly Timing

Edit `~/Library/LaunchAgents/com.icloud.backup.monthly.plist`:

```xml
<!-- Current: 1st of month at 4 AM -->
<key>StartCalendarInterval</key>
<dict>
    <key>Day</key>
    <integer>1</integer>   <!-- Day of month (1-31) -->
    <key>Hour</key>
    <integer>4</integer>   <!-- Change this -->
    <key>Minute</key>
    <integer>0</integer>
</dict>
```

### After Changing Configuration

Reload the job:
```bash
launchctl unload ~/Library/LaunchAgents/com.icloud.backup.daily.plist
launchctl load ~/Library/LaunchAgents/com.icloud.backup.daily.plist
```

## What Gets Automated

### Daily Backup (--recent 7)
1. Authenticates with iCloud (uses cached session)
2. Fetches photos from last 7 days
3. Downloads new photos to `/Users/evanswanson/icloud-photo-backup/YYYY/MM/`
4. Updates index with new metadata
5. Sends email summary with:
   - Number of new photos
   - Total size downloaded
   - Geographic locations
   - Computer name

**Fast:** Stops after 100 consecutive old photos (~15 seconds)

### Monthly Full Backup
1. Same as daily but scans entire library
2. Catches any photos missed by daily runs
3. Rebuilds complete index
4. Takes longer (5-30 minutes depending on new photos)

## Email Notifications

Both jobs send email summaries when they find new photos.

**Configure email settings in:** `/Users/evanswanson/scripts/icloud-photo-backup/send_email_smtp.py`

Email includes:
- Number of new photos backed up
- Total size (MB)
- Backup location
- Computer name
- Photos by geographical location

## Authentication

The iCloud session is cached and typically lasts for weeks/months.

**If authentication expires:**
1. Backup jobs will fail silently (check logs)
2. Re-authenticate manually:
```bash
python3 ~/scripts/icloud-photo-backup/smart_download.py --recent 7
# Enter password + 2FA when prompted
```
3. Schedule will work again on next run

**Check authentication:**
```bash
python3 ~/scripts/icloud-photo-backup/check_auth.py
```

## Progress Files

Jobs use progress tracking to resume if interrupted:

- `~/icloud-photo-backup/download_progress.json` - Download state

**Note:** Daily runs with `--recent` reset progress to start from newest photos.

## Monitoring

### Check Recent Runs
```bash
# Daily backup log
tail -20 ~/icloud-photo-backup/daily_backup.log

# Monthly backup log
tail -20 ~/icloud-photo-backup/monthly_backup.log

# Download details
tail -50 ~/icloud-photo-backup/download_log.txt
```

### Check Index Status
```bash
python3 ~/scripts/icloud-photo-backup/query_index.py stats
```

### Verify Job Timing
```bash
# List all scheduled jobs with timing
launchctl list | grep icloud

# Check specific job
plutil -p ~/Library/LaunchAgents/com.icloud.backup.daily.plist | grep -A 5 StartCalendarInterval
```

## Why launchd vs cron?

**launchd advantages (macOS native):**
- ✅ Runs even if Mac was asleep at scheduled time (runs when Mac wakes)
- ✅ Better environment handling (PATH, permissions)
- ✅ Better logging and error handling
- ✅ Easier permission management
- ✅ Recommended by Apple for macOS

**cron limitations:**
- ❌ Doesn't run if Mac is asleep
- ❌ Requires Full Disk Access permissions
- ❌ Being phased out by Apple

## Troubleshooting

### Jobs Not Running

Check if loaded:
```bash
launchctl list | grep icloud
```

If missing, load them:
```bash
launchctl load ~/Library/LaunchAgents/com.icloud.backup.daily.plist
launchctl load ~/Library/LaunchAgents/com.icloud.backup.monthly.plist
```

### Check Error Logs
```bash
cat ~/icloud-photo-backup/daily_backup_error.log
cat ~/icloud-photo-backup/monthly_backup_error.log
```

### Python Path Issues

If jobs fail with "python3: command not found", update the plist:

```bash
# Find python3 path
which python3

# Edit plist and update ProgramArguments:
# <string>/usr/local/bin/python3</string>  # or your path
```

### Authentication Expired

Re-authenticate:
```bash
python3 ~/scripts/icloud-photo-backup/smart_download.py --recent 7
# Enter password + 2FA
```

### Test Manually First

Before relying on automation:
```bash
# Test daily backup
python3 ~/scripts/icloud-photo-backup/smart_download.py --recent 7 --verbose

# Test monthly backup
python3 ~/scripts/icloud-photo-backup/smart_download.py --verbose
```

If manual runs work, automation should too.

## Disable Automation

To stop automated backups:

```bash
# Unload both jobs
launchctl unload ~/Library/LaunchAgents/com.icloud.backup.daily.plist
launchctl unload ~/Library/LaunchAgents/com.icloud.backup.monthly.plist

# Optionally delete the plist files
rm ~/Library/LaunchAgents/com.icloud.backup.daily.plist
rm ~/Library/LaunchAgents/com.icloud.backup.monthly.plist
```

## Re-enable Automation

If you previously disabled:

```bash
launchctl load ~/Library/LaunchAgents/com.icloud.backup.daily.plist
launchctl load ~/Library/LaunchAgents/com.icloud.backup.monthly.plist
```

## Performance Optimization

### Daily Backup Benefits
- **Fast:** ~15 seconds (only checks last 7 days)
- **Efficient:** Early exit when hitting old photos
- **Incremental:** Updates index continuously
- **Reliable:** Email confirmation of each run

### Monthly Backup Benefits
- **Complete:** Catches any missed photos
- **Safety net:** Full library verification
- **Index rebuild:** Ensures metadata is current

## Old Cleanup Job

The previous `com.icloud.cleanup.plist` has been replaced with these backup jobs.

Cleanup (removing duplicates/blurry photos) should be run manually:
```bash
~/scripts/icloud-photo-backup/smart_workflow.sh
```

This gives you control over what gets deleted rather than automating deletion.

---

## Quick Command Reference

```bash
# Check job status
launchctl list | grep icloud

# View daily backup log
tail -f ~/icloud-photo-backup/daily_backup.log

# View monthly backup log
tail -f ~/icloud-photo-backup/monthly_backup.log

# Manually trigger daily backup
launchctl start com.icloud.backup.daily

# Manually trigger monthly backup
launchctl start com.icloud.backup.monthly

# Check index stats
python3 ~/scripts/icloud-photo-backup/query_index.py stats
```
