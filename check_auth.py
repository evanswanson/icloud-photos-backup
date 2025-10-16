#!/usr/bin/env python3
"""
Check iCloud Authentication Status
Quick test to see if cached session is still valid
"""

import sys
import json
from pathlib import Path
from pyicloud import PyiCloudService

# Load configuration
SCRIPT_DIR = Path(__file__).parent.absolute()
CONFIG_FILE = SCRIPT_DIR / "config.json"

with open(CONFIG_FILE, 'r') as f:
    config = json.load(f)

APPLE_ID = config['apple_id']

try:
    print("Checking iCloud authentication...")
    api = PyiCloudService(APPLE_ID)

    # Try to access photos to verify session
    _ = api.photos

    print("✓ Authentication OK - session is valid")
    print(f"  Apple ID: {APPLE_ID}")
    print(f"  Session: Active")
    sys.exit(0)

except Exception as e:
    print("✗ Authentication FAILED")
    print(f"  Error: {str(e)[:100]}")
    print()
    print("Session has expired. Re-authenticate with:")
    print("  ~/scripts/icloud-photo-backup/smart_workflow.sh")
    sys.exit(1)
