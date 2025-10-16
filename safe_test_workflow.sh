#!/bin/bash
# Safe Test Workflow - Simplified
# Just runs the workflow with a timeout safety net

SCRIPT_DIR="$HOME/scripts/icloud-photo-backup"
BACKUP_DIR="$HOME/icloud-photo-backup"

echo "Starting workflow with 2-hour safety timeout..."
echo "Press Ctrl+C anytime to stop safely."
echo ""

# Create a log for this test run
TEST_LOG="$BACKUP_DIR/safe_test_$(date +%Y%m%d_%H%M%S).log"

# Cleanup function
cleanup() {
    echo ""
    echo "Stopping safely..."
    PIDS=$(pgrep -f "smart_workflow.sh\|smart_download.py\|delete_by_criteria.py" | grep -v $$)
    if [ ! -z "$PIDS" ]; then
        kill $PIDS 2>/dev/null
        sleep 2
        kill -9 $PIDS 2>/dev/null || true
    fi
    echo "✓ Stopped. Test log: $TEST_LOG"
    exit 0
}

trap cleanup INT TERM

# Run workflow with timeout
timeout 7200 "$SCRIPT_DIR/smart_workflow.sh" 2>&1 | tee "$TEST_LOG"

EXIT_CODE=$?

if [ $EXIT_CODE -eq 124 ]; then
    echo ""
    echo "⚠️  Safety timeout (2 hours) reached"
    echo "Check logs: $TEST_LOG"
else
    echo ""
    echo "✓ Complete! Log: $TEST_LOG"
fi
