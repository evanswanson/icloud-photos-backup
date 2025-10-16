# iCloud Photo Backup & Cleanup

Automated solution for backing up iCloud photos locally and removing duplicates, blurry images, and unwanted videos.

## Features

- 🔄 **Automated Daily Backups** - Fast incremental backups (15 seconds)
- 📅 **Monthly Full Sync** - Complete library verification
- 📧 **Email Notifications** - Summary of new photos backed up
- 🔍 **Smart Cleanup** - Remove duplicates, blurry images, old screenshots
- 🎥 **Video Management** - Delete old large videos and short clips
- 💾 **Resume Support** - Picks up where it left off if interrupted
- 🏷️ **Metadata Index** - Fast searching without scanning entire library

## Quick Start

### Installation

```bash
# Clone repository
cd ~/scripts
git clone https://github.com/yourusername/icloud-photo-backup.git
cd icloud-photo-backup

# Install dependencies
pip3 install pyicloud opencv-python imagehash Pillow

# Configure
cp config.json.template config.json
# Edit config.json with your Apple ID and settings
```

### First Backup

```bash
# Download recent photos
python3 smart_download.py --recent 30 --verbose
```

You'll be prompted for your Apple ID password and 2FA code.

### Setup Automation

See [SCHEDULING.md](SCHEDULING.md) for automated daily/monthly backups using macOS launchd.

## Documentation

- **[SETUP.md](SETUP.md)** - Complete installation guide
- **[SCHEDULING.md](SCHEDULING.md)** - Automated backup setup
- **[GETTING-STARTED.md](GETTING-STARTED.md)** - Quick start guide

## How It Works

### Daily Backups (Fast)
- Downloads photos from last 7 days
- ~15 second runtime with early exit optimization
- Updates index incrementally
- Sends email summary

### Monthly Backups (Complete)
- Full library sync
- Catches any missed photos
- Rebuilds index
- Takes 5-30 minutes depending on new photos

### Cleanup Workflow (Manual)
- Scans for duplicates using perceptual hashing
- Detects blurry images (Laplacian variance)
- Identifies old screenshots and short videos
- Uses index for fast video criteria matching
- All deletions go to iCloud "Recently Deleted" (30-day recovery)

## Requirements

- macOS with Python 3
- iCloud account with 2FA enabled
- Sufficient disk space for photo backup
- Optional: Gmail account for email notifications

## Configuration

Edit `config.json`:

```json
{
  "apple_id": "your.email@icloud.com",
  "notification_email": "your.email@gmail.com",
  "backup_directory": "/Users/yourusername/icloud-photo-backup"
}
```

## Safety Features

- ✅ Items deleted from iCloud go to "Recently Deleted" (30-day recovery)
- ✅ Local trash folder for manual recovery
- ✅ Progress tracking (resume anytime)
- ✅ Interactive prompts before deletion
- ✅ Comprehensive logging

## Performance

**Before optimization:**
- Full library scan: 90-150 minutes
- Daily checks: Had to cycle through entire library

**After optimization:**
- Daily backup: ~15 seconds (early exit when hitting old photos)
- Monthly full backup: 5-30 minutes
- ~85-95% time savings

## License

MIT License - feel free to use and modify!

## Contributing

Contributions welcome! Please open an issue or PR.

## Acknowledgments

Built with [pyicloud](https://github.com/picklepete/pyicloud) for iCloud API access.
