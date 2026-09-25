#!/bin/bash
# WorkmAIn AI Dependencies Fix Script (CORRECTED)
# Fixes httpx version compatibility and uses correct google-genai package

set -e  # Exit on error

echo "============================================================"
echo "WorkmAIn AI Dependencies - Complete Fix"
echo "============================================================"
echo ""

# Activate virtual environment
if [ ! -d ".venv" ]; then
    echo "✗ ERROR: Virtual environment not found"
    echo "  Run from ~/Projects/workmain directory"
    exit 1
fi

source .venv/bin/activate

echo "Step 1: Checking current versions..."
pip show httpx anthropic google-genai 2>/dev/null || echo "  Some packages not installed yet"
echo ""

echo "Step 2: Uninstalling old/conflicting packages..."
pip uninstall -y httpx httpx-sse h11 h2 google-generativeai 2>/dev/null || true
echo "✓ Removed old versions"
echo ""

echo "Step 3: Installing compatible versions..."

# Install httpx first with specific version
pip install "httpx==0.27.0" --break-system-packages
echo "✓ httpx 0.27.0 installed"

# Install anthropic SDK (will use compatible httpx)
pip install "anthropic>=0.40.0" --break-system-packages
echo "✓ anthropic installed"

# Install Google GenAI SDK (CORRECT PACKAGE NAME)
pip install "google-genai>=0.1.0" --break-system-packages
echo "✓ google-genai installed"

echo ""
echo "Step 4: Verifying installation..."
python3 << 'VERIFY'
import sys

# Check httpx
try:
    import httpx
    print(f"✓ httpx version: {httpx.__version__}")
except ImportError as e:
    print(f"✗ httpx import failed: {e}")
    sys.exit(1)

# Check anthropic
try:
    import anthropic
    print(f"✓ anthropic version: {anthropic.__version__}")
    from anthropic import Anthropic
    print("✓ Anthropic client import works")
except ImportError as e:
    print(f"✗ anthropic import failed: {e}")
    sys.exit(1)
except TypeError as e:
    if "proxies" in str(e):
        print(f"✗ httpx compatibility issue still present: {e}")
        sys.exit(1)
    print(f"✓ Anthropic import OK (validation error expected)")

# Check google-genai
try:
    from google import genai
    print(f"✓ google-genai package installed")
    print("✓ Gemini client import works")
except ImportError as e:
    print(f"✗ google-genai import failed: {e}")
    print("  Make sure you installed 'google-genai' not 'google-generativeai'")
    sys.exit(1)

print("\n✓ All AI dependencies working!")
VERIFY

echo ""
echo "============================================================"
echo "✓ Dependencies fixed successfully!"
echo "============================================================"
echo ""
echo "Next steps:"
echo "  1. Run: python3 tests/test_ai_clients.py"
echo "  2. If tests pass, commit the changes"
