#!/usr/bin/env sh
set -e

echo "🔧 Setting up dependencies..."

# -----------------------------
# Python check
# -----------------------------
python3 - <<EOF
import sys
assert sys.version_info >= (3,11), "Python >= 3.11 required"
EOF

# -----------------------------
# ffmpeg check
# -----------------------------
command -v ffmpeg >/dev/null 2>&1 || {
  echo "❌ ffmpeg not found. Please install it first."
  exit 1
}

# -----------------------------
# Install deps
# -----------------------------
uv sync

echo "🎉 Dependencies installed"
