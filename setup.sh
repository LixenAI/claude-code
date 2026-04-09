#!/bin/bash
# GHL Email Warmup — Full Setup & Lead Generation
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

# Install dependencies
echo "Installing dependencies..."
pip3 install -q requests python-dotenv
echo "Done."
echo ""

# ── Collect credentials ──────────────────────────────────────────────────────
echo "Enter your credentials. Press Enter to keep an existing value."
echo ""

load_existing() {
  # Read a value from .env if it exists
  local key="$1"
  if [ -f .env ]; then
    grep -E "^${key}=" .env 2>/dev/null | cut -d'=' -f2- | tr -d '"' || true
  fi
}

existing_ghl_key=$(load_existing GHL_API_KEY)
existing_loc_id=$(load_existing GHL_LOCATION_ID)
existing_google=$(load_existing GOOGLE_PLACES_API_KEY)
existing_hunter=$(load_existing HUNTER_API_KEY)
existing_city=$(load_existing TARGET_CITY)

echo "--- GoHighLevel ---"
read -p "GHL API Key     [${existing_ghl_key:0:8}...]: " ghl_key
read -p "GHL Location ID [${existing_loc_id:0:8}...]: " loc_id

echo ""
echo "--- Google Places API (free) ---"
echo "  Get yours at: console.cloud.google.com → Enable 'Places API' → Create Key"
read -p "Google Places API Key [${existing_google:0:8}...]: " google_key

echo ""
echo "--- Hunter.io (free — 25 searches/month) ---"
echo "  Get yours at: hunter.io → Sign up → Dashboard → API"
read -p "Hunter.io API Key [${existing_hunter:0:8}...]: " hunter_key

echo ""
echo "--- Target City ---"
read -p "City to search for leads [${existing_city:-Miami, FL}]: " target_city

# Use existing values if user pressed Enter
ghl_key=${ghl_key:-$existing_ghl_key}
loc_id=${loc_id:-$existing_loc_id}
google_key=${google_key:-$existing_google}
hunter_key=${hunter_key:-$existing_hunter}
target_city=${target_city:-${existing_city:-Miami, FL}}

# Validate required fields
if [[ -z "$ghl_key" || -z "$loc_id" ]]; then
  echo ""
  echo "ERROR: GHL API Key and Location ID are required."
  exit 1
fi

# Write .env
cat > .env <<EOF
GHL_API_KEY=${ghl_key}
GHL_LOCATION_ID=${loc_id}
GOOGLE_PLACES_API_KEY=${google_key}
HUNTER_API_KEY=${hunter_key}
TARGET_CITY=${target_city}
EOF

echo ""
echo "Credentials saved."
echo ""

# ── Choose what to run ───────────────────────────────────────────────────────
if [[ -n "$google_key" && -n "$hunter_key" ]]; then
  echo "Running lead generation (Google Places + Hunter.io → GHL)..."
  echo ""
  python3 generate_leads.py
else
  echo "Google/Hunter keys not provided — skipping lead generation."
  echo "Running contact search on existing GHL contacts instead..."
  echo ""
  python3 create_smartlist.py
fi
