#!/bin/bash
# Weekly content generation + posting job
# Called by cron every Monday at 07:00 AM
set -e
cd "$(dirname "$0")"
source .env 2>/dev/null || true

LOG_FILE="logs/weekly_$(date +%Y%m%d_%H%M%S).log"
mkdir -p logs
echo "[$(date)] Starting weekly content run" >> "$LOG_FILE"
python main.py --mode run-now 2>&1 | tee -a "$LOG_FILE"
echo "[$(date)] Done" >> "$LOG_FILE"
