#!/usr/bin/env sh
set -e

INSTALL_DIR="$HOME/.truetrack"
REPO_URL="https://github.com/Vicky-258/TrueTrack.git"

echo "🎵 Installing TrueTrack..."

# -----------------------------
# Check curl
# -----------------------------
command -v curl >/dev/null 2>&1 || {
  echo "❌ curl is required"
  exit 1
}

# -----------------------------
# Install uv
# -----------------------------
if ! command -v uv >/dev/null 2>&1; then
  echo "⬇️ Installing uv..."
  curl -LsSf https://astral.sh/uv/install.sh | sh
  export PATH="$HOME/.local/bin:$PATH"
fi

# -----------------------------
# Clone / update
# -----------------------------
if [ -d "$INSTALL_DIR" ]; then
  echo "🔄 Updating TrueTrack..."
  cd "$INSTALL_DIR"
  git pull
else
  echo "⬇️ Downloading TrueTrack..."
  git clone "$REPO_URL" "$INSTALL_DIR"
  cd "$INSTALL_DIR"
fi

chmod +x install_core.sh run.sh
./install_core.sh

echo ""
echo "✅ TrueTrack installed!"
echo "👉 Run with: $INSTALL_DIR/run.sh"
