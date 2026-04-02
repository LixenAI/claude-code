#!/bin/bash
# Start the Lixen.AI GHL webhook server
# Run this on your server to enable AI replies + lead qualification from GHL
set -e
cd "$(dirname "$0")"
source .env 2>/dev/null || true
exec python main.py --mode webhook
