# Email Notifications Setup

Get email notifications when iCloud cleanup runs (success or failure).

## Quick Setup

Run the setup script:

```bash
~/scripts/icloud-photo-backup/setup_email.sh
```

This interactive script will:
1. Guide you to create a Gmail App Password
2. Save it securely to `~/.icloud-email-password`
3. Test email delivery

## Manual Setup

If you prefer to set it up manually:

### 1. Create Gmail App Password

1. Go to: https://myaccount.google.com/apppasswords
2. Sign in with `evan.swanson@gmail.com`
3. **Note:** You need 2-Step Verification enabled first
   - Enable at: https://myaccount.google.com/security
4. Select app: **Mail**
5. Select device: **Mac**
6. Click **Generate**
7. Copy the 16-character password (looks like: `abcd efgh ijkl mnop`)

### 2. Save Password

```bash
echo 'your-app-password-here' > ~/.icloud-email-password
chmod 600 ~/.icloud-email-password
```

Replace `your-app-password-here` with the 16-character password (remove spaces).

### 3. Test Email

```bash
~/scripts/icloud-photo-backup/test_success_email.sh
```

Check your email at `evan.swanson@gmail.com`.

## What Emails You'll Receive

### Success Email (when items deleted)

```
Subject: ✓ iCloud Cleanup Successful

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
SUMMARY
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Total Deleted: 9 items
Total Size:    1.20 GB

Videos: 9 (1.20 GB)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
DELETION REASONS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

• Old large video: 2.2yr, 110MB: 7 items
• Old large video: 3.8yr, 132MB: 2 items

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
RECOVERY INFO
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Items moved to "Recently Deleted" album
Available for 30 days before permanent deletion
```

### Failure Email (when cleanup fails)

```
Subject: ❌ iCloud Cleanup Failed

The scheduled iCloud cleanup task failed.

Last error:
[error details from log]

To re-authenticate:
~/scripts/icloud-photo-backup/smart_workflow.sh
```

## Troubleshooting

### "App passwords are not available"

You need to enable 2-Step Verification first:
1. Go to: https://myaccount.google.com/security
2. Enable **2-Step Verification**
3. Then create an App Password

### "Authentication failed"

- Check password has no spaces: `cat ~/.icloud-email-password`
- Should be 16 characters
- Try regenerating the App Password

### "No email received"

- Check spam folder
- Wait a few minutes (can be delayed)
- Verify internet connection
- Run test: `~/scripts/icloud-photo-backup/test_success_email.sh`

### Test email manually

```bash
python3 ~/scripts/icloud-photo-backup/send_email_smtp.py \
    evan.swanson@gmail.com \
    "Test Subject" \
    "Test body message"
```

## Security

- Password stored in: `~/.icloud-email-password`
- File permissions: `600` (only you can read)
- Uses Gmail App Password (not your main password)
- Can be revoked anytime at: https://myaccount.google.com/apppasswords

## Changing Email Address

Edit these files and replace `evan.swanson@gmail.com`:
- `send_success_email.sh` (line 6)
- `send_email_notification.sh` (line 5)
- `send_email_smtp.py` (line 14)
- `setup_email.sh` (throughout)
