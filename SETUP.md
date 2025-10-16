# Setup Guide

Quick setup guide for getting iCloud Photo Backup running on your machine.

## Prerequisites

- macOS with Python 3
- iCloud account with 2FA enabled
- Gmail account for email notifications (optional)

## Installation

### 1. Clone the Repository

```bash
cd ~/scripts
git clone https://github.com/yourusername/icloud-photo-backup.git
cd icloud-photo-backup
```

### 2. Install Python Dependencies

```bash
pip3 install pyicloud opencv-python imagehash Pillow
```

Optional (for video duration analysis):
```bash
brew install ffmpeg
```

### 3. Configure Settings

Copy the config template and fill in your details:

```bash
cp config.json.template config.json
```

Edit `config.json` with your information:

```json
{
  "apple_id": "your.email@icloud.com",
  "notification_email": "your.email@gmail.com",
  "backup_directory": "/Users/yourusername/icloud-photo-backup",
  "email_smtp": {
    "from_email": "your.email@gmail.com",
    "smtp_server": "smtp.gmail.com",
    "smtp_port": 587,
    "password_file": "~/.icloud-email-password"
  }
}
```

**Important fields:**
- `apple_id`: Your iCloud/Apple ID email
- `notification_email`: Where to send backup summaries
- `backup_directory`: Where to store downloaded photos (needs lots of space!)

### 4. Setup Email Notifications (Optional)

If you want email summaries of backups:

1. Create a Gmail App Password:
   - Go to https://myaccount.google.com/security
   - Enable 2-Step Verification
   - Go to App Passwords
   - Create a new app password for "iCloud Backup"

2. Save the password:
```bash
echo "your-app-password-here" > ~/.icloud-email-password
chmod 600 ~/.icloud-email-password
```

### 5. Create Backup Directory

```bash
mkdir -p ~/icloud-photo-backup
```

### 6. Test Authentication

```bash
python3 smart_download.py --recent 7 --verbose
```

You'll be prompted for:
- Apple ID password
- 2FA code from your trusted device

This creates a cached session that lasts for weeks/months.

## First Run

### Download Your Photos

```bash
# Download all photos (may take hours for large libraries)
python3 smart_download.py --verbose

# Or just download recent photos (faster)
python3 smart_download.py --recent 30 --verbose
```

This will:
- Download photos to `~/icloud-photo-backup/YYYY/MM/`
- Build an index in `~/icloud-photo-backup/icloud_index.json`
- Send email summary (if configured)

## Setup Automation

### Daily Backups

Edit the schedule files to match your paths, then load them:

```bash
# Edit these files first to set correct paths
nano ~/Library/LaunchAgents/com.icloud.backup.daily.plist
nano ~/Library/LaunchAgents/com.icloud.backup.monthly.plist

# Load the jobs
launchctl load ~/Library/LaunchAgents/com.icloud.backup.daily.plist
launchctl load ~/Library/LaunchAgents/com.icloud.backup.monthly.plist
```

See [SCHEDULING.md](SCHEDULING.md) for details.

## Verify Installation

### Check Authentication
```bash
python3 check_auth.py
```

### Check Index
```bash
python3 query_index.py stats
```

### Check Scheduled Jobs
```bash
launchctl list | grep icloud
```

Should show:
```
-	0	com.icloud.backup.daily
-	0	com.icloud.backup.monthly
```

## Troubleshooting

### Config File Not Found

If you see "ERROR: Configuration file not found", make sure:
1. You created `config.json` from `config.json.template`
2. The file is in the same directory as the Python scripts

### Authentication Fails

- Make sure 2FA is enabled on your Apple ID
- Use your Apple ID password, not an app-specific password
- Wait a few seconds between 2FA attempts

### Email Not Sending

- Verify Gmail App Password is correct
- Check `~/.icloud-email-password` exists and is readable
- Test with: `python3 test_email_summary.py`

### Permission Denied

```bash
chmod +x smart_workflow.sh
```

## Next Steps

Once setup is complete:

1. **Daily**: Automated backups run at 9 PM
2. **Monthly**: Full backup runs on the 1st at 4 AM
3. **Cleanup**: Run `./smart_workflow.sh` monthly to remove duplicates/blurry photos

See [README.md](README.md) for full documentation.
