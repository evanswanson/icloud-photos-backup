#!/bin/bash
# Setup Gmail SMTP for email notifications

PASSWORD_FILE="$HOME/.icloud-email-password"

echo "=================================="
echo "Gmail SMTP Setup"
echo "=================================="
echo ""
echo "This will configure email notifications for iCloud cleanup."
echo ""
echo "You need a Gmail App Password (not your regular password)."
echo ""
echo "Steps to get an App Password:"
echo "1. Go to: https://myaccount.google.com/apppasswords"
echo "2. Sign in to your Google account (evan.swanson@gmail.com)"
echo "3. Click 'Select app' → Choose 'Mail'"
echo "4. Click 'Select device' → Choose 'Mac'"
echo "5. Click 'Generate'"
echo "6. Copy the 16-character password"
echo ""
echo "Note: You may need to enable 2-Step Verification first at:"
echo "      https://myaccount.google.com/security"
echo ""

# Check if already configured
if [ -f "$PASSWORD_FILE" ]; then
    echo "⚠️  Password file already exists at: $PASSWORD_FILE"
    echo ""
    read -p "Do you want to overwrite it? (yes/no): " response
    if [[ ! "$response" =~ ^[Yy] ]]; then
        echo "Setup cancelled."
        exit 0
    fi
    echo ""
fi

# Prompt for password
echo "Enter your Gmail App Password (16 characters):"
read -s APP_PASSWORD
echo ""

# Validate
if [ -z "$APP_PASSWORD" ]; then
    echo "❌ No password entered. Setup cancelled."
    exit 1
fi

# Save password
echo "$APP_PASSWORD" > "$PASSWORD_FILE"
chmod 600 "$PASSWORD_FILE"

echo "✓ Password saved to: $PASSWORD_FILE"
echo "✓ File permissions set to 600 (private)"
echo ""

# Test email
echo "Testing email..."
echo ""

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
TEST_BODY="This is a test email from your iCloud cleanup system.

If you receive this, email notifications are working correctly!

Setup completed: $(date)
"

python3 "$SCRIPT_DIR/send_email_smtp.py" "evan.swanson@gmail.com" "✓ iCloud Email Test" "$TEST_BODY"

if [ $? -eq 0 ]; then
    echo ""
    echo "=================================="
    echo "✓ Setup Complete!"
    echo "=================================="
    echo ""
    echo "Check your email at evan.swanson@gmail.com"
    echo ""
    echo "You will now receive emails when:"
    echo "  • Items are successfully deleted (with summary)"
    echo "  • The scheduled cleanup fails"
else
    echo ""
    echo "❌ Email test failed!"
    echo "Please check:"
    echo "  1. Your App Password is correct"
    echo "  2. You have internet connection"
    echo "  3. 2-Step Verification is enabled on your Google account"
    echo ""
    echo "To try again: $0"
fi
