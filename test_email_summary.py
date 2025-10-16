#!/usr/bin/env python3
"""
Test script to verify the email summary functionality
"""

from send_email_smtp import send_email
import socket

# Test session statistics with geographical locations
session_stats = {
    'new_downloads': 15,
    'total_size_bytes': 45 * 1024 * 1024,  # 45 MB
    'photo_locations': {
        'San Francisco, CA': 7,
        'New York, NY': 5,
        'Unknown Location': 3
    }
}

# Calculate statistics
new_downloads = session_stats['new_downloads']
total_size_bytes = session_stats['total_size_bytes']
total_size_mb = round(total_size_bytes / (1024**2), 2)
photo_locations = session_stats['photo_locations']
backup_dir = "/Users/evanswanson/icloud-photo-backup"

# Get computer name
computer_name = socket.gethostname()

# Build email body
subject = f"iCloud Backup Complete - {new_downloads} new photos"

body = f"""iCloud Photo Backup Summary
{'=' * 50}

New Photos Backed Up: {new_downloads}
Total Size: {total_size_mb} MB
Backup Location: {backup_dir}
Computer: {computer_name}

Photos by Geographical Location:
"""

# Sort locations by count (descending), then alphabetically
sorted_locations = sorted(photo_locations.items(), key=lambda x: (-x[1], x[0]))

# Add location breakdown
for location, count in sorted_locations:
    body += f"  {location}: {count} photo{'s' if count != 1 else ''}\n"

from datetime import datetime
body += f"\nBackup completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"

print("=" * 70)
print("TEST: Email Summary")
print("=" * 70)
print()
print(f"Subject: {subject}")
print()
print("Body:")
print(body)
print()
print("Sending test email...")
print()

# Send email
success = send_email(
    to_email="evan.swanson@gmail.com",
    subject=subject,
    body=body
)

if success:
    print("✓ Test email sent successfully!")
else:
    print("✗ Failed to send test email")
