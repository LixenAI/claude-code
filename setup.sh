#!/bin/bash
# GHL Email Warmup Smart List — Full Setup
# Run with: bash setup.sh

set -e

echo ""
echo "======================================"
echo "  GHL Email Warmup — Setup & Run"
echo "======================================"
echo ""

# Check for python3
if ! command -v python3 &>/dev/null; then
  echo "ERROR: python3 is not installed."
  echo "Download it from https://python.org/downloads then re-run this script."
  exit 1
fi

# Check for pip3
if ! command -v pip3 &>/dev/null; then
  echo "ERROR: pip3 is not installed. Try: python3 -m ensurepip"
  exit 1
fi

# Install dependencies
echo "Installing dependencies..."
pip3 install -q requests python-dotenv
echo "Done."
echo ""

# Collect credentials
echo "Enter your GoHighLevel credentials."
echo "(Find them in GHL → Settings → Integrations → API Keys)"
echo ""

read -p "Paste your GHL API Key:      " api_key
read -p "Paste your GHL Location ID:  " location_id

if [[ -z "$api_key" || -z "$location_id" ]]; then
  echo ""
  echo "ERROR: Both values are required. Re-run and fill them in."
  exit 1
fi

# Write .env
cat > .env <<EOF
GHL_API_KEY=${api_key}
GHL_LOCATION_ID=${location_id}
EOF

echo ""
echo "Credentials saved. Running script..."
echo ""

python3 create_smartlist.py
