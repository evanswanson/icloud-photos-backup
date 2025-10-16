#!/usr/bin/env python3
"""
Send email via Gmail SMTP
Requires Gmail app password stored in ~/.icloud-email-password
"""

import sys
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from pathlib import Path

def send_email(to_email, subject, body):
    """Send email via Gmail SMTP"""

    from_email = "evan.swanson.receipt@gmail.com"
    password_file = Path.home() / ".icloud-email-password"

    # Check for password file
    if not password_file.exists():
        print("❌ Email password file not found!")
        print(f"   Expected: {password_file}")
        print("")
        print("To set up Gmail SMTP:")
        print("1. Go to: https://myaccount.google.com/apppasswords")
        print("2. Generate an 'App Password' for 'Mail'")
        print("3. Save it to: ~/.icloud-email-password")
        print("   echo 'your-app-password-here' > ~/.icloud-email-password")
        print("   chmod 600 ~/.icloud-email-password")
        return False

    # Read password
    with open(password_file, 'r') as f:
        password = f.read().strip()

    if not password:
        print("❌ Email password file is empty!")
        return False

    try:
        # Create message
        msg = MIMEMultipart()
        msg['From'] = from_email
        msg['To'] = to_email
        msg['Subject'] = subject

        msg.attach(MIMEText(body, 'plain'))

        # Connect to Gmail SMTP
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(from_email, password)
            server.send_message(msg)

        print(f"✓ Email sent to {to_email}")
        return True

    except Exception as e:
        print(f"❌ Failed to send email: {e}")
        return False

if __name__ == "__main__":
    if len(sys.argv) < 4:
        print("Usage: send_email_smtp.py <to_email> <subject> <body>")
        sys.exit(1)

    to_email = sys.argv[1]
    subject = sys.argv[2]
    body = sys.argv[3]

    success = send_email(to_email, subject, body)
    sys.exit(0 if success else 1)
