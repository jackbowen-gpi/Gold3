#!/bin/bash
# Gold3 Data Masking Runner for Linux/Mac
# This script provides an easy way to run data masking on Unix-like systems

echo "========================================"
echo "Gold3 Data Masking Runner (Linux/Mac)"
echo "========================================"
echo

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python 3 is not installed or not in PATH"
    echo "Please install Python 3.6+ and try again"
    exit 1
fi

# Check if required files exist
if [ ! -f "data_masking.sql" ]; then
    echo "ERROR: data_masking.sql not found in current directory"
    echo "Please ensure the masking script is in the same directory"
    exit 1
fi

if [ ! -f "verify_masking.sql" ]; then
    echo "ERROR: verify_masking.sql not found in current directory"
    echo "Please ensure the verification script is in the same directory"
    exit 1
fi

echo "Available options:"
echo "[1] Run full masking process (with backup)"
echo "[2] Run masking without backup (not recommended)"
echo "[3] Dry run (show what would be done)"
echo "[4] Verify only (check current masking status)"
echo "[5] Cancel"
echo

read -p "Enter your choice (1-5): " choice

case $choice in
    1)
        echo
        echo "Starting full masking process with backup..."
        python3 run_data_masking.py
        ;;
    2)
        echo
        echo "Starting masking process WITHOUT backup..."
        echo "WARNING: This is risky! Make sure you have a manual backup!"
        sleep 5
        python3 run_data_masking.py --no-backup
        ;;
    3)
        echo
        echo "Starting dry run..."
        python3 run_data_masking.py --dry-run
        ;;
    4)
        echo
        echo "Running verification only..."
        python3 run_data_masking.py --verify-only
        ;;
    5)
        echo
        echo "Operation cancelled."
        ;;
    *)
        echo
        echo "Invalid choice. Please run the script again and choose 1-5."
        exit 1
        ;;
esac

echo
echo "Press Enter to exit..."
read
