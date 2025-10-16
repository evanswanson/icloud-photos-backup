# Performance Optimization Guide

## Fast Daily Runs

The backup system now supports fast daily runs that only check recent photos instead of scanning your entire iCloud library.

## Speed Comparison

### Full Scan (Original Behavior)
- Scans ALL photos in your iCloud library
- Time: Depends on library size (can be hours for large libraries)
- Use case: Initial backup, monthly full sync

```bash
./smart_workflow.sh --headless --verbose
```

### Fast Daily Run (New --recent Option)
- Only checks photos from the last N days
- Time: Minutes instead of hours
- Use case: Daily automated backups

```bash
# Check only last 30 days (recommended for daily runs)
./smart_workflow.sh --headless --verbose --recent 30

# Check only last 7 days (if running multiple times per day)
./smart_workflow.sh --headless --verbose --recent 7
```

## Recommended Setup

### For Daily Automated Backups
Use `--recent 30` to ensure you catch any delayed syncs or photos added late:

```bash
./smart_workflow.sh --headless --verbose --recent 30
```

### For Multiple Daily Runs
If you run the backup several times per day, use `--recent 7`:

```bash
./smart_workflow.sh --headless --verbose --recent 7
```

### For Monthly Full Sync
Once a month, do a full scan without --recent to catch anything that was missed:

```bash
./smart_workflow.sh --headless --verbose
```

## How It Works

The `--recent N` flag filters photos by their date:
1. Checks `added_date` (when photo was added to iCloud)
2. Falls back to `asset_date` (when photo was taken)
3. Falls back to `created` (creation date)

Photos older than N days are skipped entirely, dramatically reducing processing time.

## Updating Your Cron Job

Edit your crontab to use the fast mode:

```bash
crontab -e
```

Change:
```
0 2 * * * /Users/evanswanson/scripts/icloud-photo-backup/smart_workflow.sh --headless --verbose
```

To:
```
# Daily fast backup (last 30 days only)
0 2 * * * /Users/evanswanson/scripts/icloud-photo-backup/smart_workflow.sh --headless --verbose --recent 30

# Monthly full backup (1st of month at 3am)
0 3 1 * * /Users/evanswanson/scripts/icloud-photo-backup/smart_workflow.sh --headless --verbose
```

## Benefits

- **10-100x faster** for daily runs (depending on library size)
- Still catches all new photos reliably
- Index stays up-to-date
- Email summaries only show truly new photos
- Reduced API load on iCloud

## Still Checks Everything

The fast mode only affects the initial photo scanning phase. It still:
- ✓ Analyzes all downloaded photos for duplicates/blur/screenshots
- ✓ Checks for old large videos to delete
- ✓ Maintains the complete index
- ✓ Sends email summaries
