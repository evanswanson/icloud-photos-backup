#!/bin/bash
# Test success email notification

SCRIPT_DIR="$HOME/scripts/icloud-photo-backup"

# Create test reasons file
REASONS_FILE="/tmp/test_reasons.txt"
cat > "$REASONS_FILE" << 'EOF'
• Old large video: 2.2yr, 110MB: 7 items
• Old large video: 3.8yr, 132MB: 2 items
EOF

# Test with sample data
echo "Testing success email..."
echo "Check your email at evan.swanson@gmail.com"
echo ""

"$SCRIPT_DIR/send_success_email.sh" \
    9 \
    1.20 \
    9 \
    0 \
    1.20 \
    0.00 \
    "$REASONS_FILE"

rm -f "$REASONS_FILE"
echo ""
echo "✓ Test email sent!"
