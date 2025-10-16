# GitHub Repository Checklist

Before pushing to GitHub, verify these steps:

## ✅ Configuration Files

- [x] `.gitignore` created (excludes sensitive files)
- [x] `config.json.template` created (example for users)
- [x] `config.json` added to `.gitignore` (your personal config won't be committed)
- [x] `.icloud-email-password` added to `.gitignore`

## ✅ Code Updates

- [x] `smart_download.py` - uses config.json
- [x] `check_auth.py` - uses config.json
- [x] `delete_by_criteria.py` - uses config.json
- [x] `icloud_delete_fast.py` - uses config.json

## ✅ Documentation

- [x] `README.md` - updated with config setup
- [x] `SETUP.md` - new file for installation
- [x] `SCHEDULING.md` - updated with new schedule
- [x] `README-GITHUB.md` - GitHub-friendly README
- [x] `GITHUB-CHECKLIST.md` - this file

## 🔍 Pre-Commit Verification

### 1. Check for Hardcoded Credentials

```bash
cd ~/scripts/icloud-photo-backup

# Search for your email (should only be in config.json)
grep -r "evan.swanson" --exclude-dir=.git --exclude="*.json" .

# If found in Python/shell files, they need to be updated
```

### 2. Verify .gitignore

```bash
# These should NOT show up in git status
git status

# Should not see:
# - config.json
# - *.log files
# - *_progress.json files
# - .icloud-email-password
```

### 3. Test Config Loading

```bash
# Rename your config temporarily
mv config.json config.json.backup

# Try running a script (should error with helpful message)
python3 check_auth.py

# Restore config
mv config.json.backup config.json
```

Expected output:
```
ERROR: Configuration file not found: .../config.json
Please copy config.json.template to config.json and fill in your details.
```

## 📝 Git Commands

### Initialize Repository

```bash
cd ~/scripts/icloud-photo-backup

# Initialize git
git init

# Add all files
git add .

# Create first commit
git commit -m "Initial commit - iCloud photo backup automation"
```

### Create GitHub Repository

1. Go to https://github.com/new
2. Repository name: `icloud-photo-backup`
3. Description: "Automated iCloud photo backup with smart cleanup"
4. Choose:
   - ✅ Public (so others can use it)
   - ❌ Don't initialize with README (we have one)

### Push to GitHub

```bash
# Add remote (replace with your username)
git remote add origin https://github.com/yourusername/icloud-photo-backup.git

# Push to GitHub
git branch -M main
git push -u origin main
```

## 📢 Optional: Make it Discoverable

### Add Topics

On GitHub repository page:
- Settings → Topics
- Add: `icloud`, `photo-backup`, `macos`, `python`, `automation`, `photo-management`

### Update README on GitHub

After pushing, optionally rename for better GitHub display:

```bash
mv README-GITHUB.md README-FOR-GITHUB.md
git mv README.md README-DETAILED.md
git mv README-FOR-GITHUB.md README.md
git commit -m "Use GitHub-optimized README"
git push
```

## ✅ Post-Push Verification

After pushing to GitHub:

1. ✅ Go to your repository on GitHub
2. ✅ Check that README displays nicely
3. ✅ Verify no sensitive files are visible (config.json, passwords, logs)
4. ✅ Test cloning as a new user would:

```bash
cd /tmp
git clone https://github.com/yourusername/icloud-photo-backup.git
cd icloud-photo-backup
ls -la

# Should see config.json.template but NOT config.json
# Should see .gitignore
```

## 🎉 Done!

Your repository is ready! Others can now:
1. Clone your repo
2. Copy `config.json.template` to `config.json`
3. Fill in their credentials
4. Run backups

## 📊 Optional Enhancements

Consider adding:
- [ ] LICENSE file (MIT recommended)
- [ ] CONTRIBUTING.md
- [ ] GitHub Actions for testing
- [ ] Screenshot examples
- [ ] Star the repo if you like it!
