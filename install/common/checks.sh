#!/bin/bash

# ==============================================================================
# System Checks & Dependency Management
# ==============================================================================

source "$(dirname "$0")/common/logging.sh"

check_preflight() {
    log_info "Phase 0: Preflight Checks"

    # OS Detection
    if [[ "$OSTYPE" != "linux-gnu"* ]] && [[ "$OSTYPE" != "darwin"* ]]; then
        fail "Unsupported OS: $OSTYPE. Only Linux and macOS are supported."
    fi

    # Architecture
    ARCH=$(uname -m)
    log_info "Detected Architecture: $ARCH"

    # Disk Space (Simple check for > 2GB free in HOME)
    FREE_SPACE=$(df -k "$HOME" | awk 'NR==2 {print $4}')
    if [[ "$FREE_SPACE" -lt 2000000 ]]; then
        fail "Insufficient disk space. Need at least 2GB free in $HOME."
    fi

    # Connectivity
    if ! curl -Is google.com > /dev/null; then
        fail "No internet connectivity detected."
    fi

    log_success "Preflight checks passed."
}

install_packages() {
    log_info "Phase 1: Dependency Detection & Install"
    
    local missing_packages=()

    # Detect Package Manager
    if [[ "$OSTYPE" == "darwin"* ]]; then
        if ! command -v brew &> /dev/null; then
            fail "Homebrew is required for macOS installation. Please install it first."
        fi
        PKG_MANAGER="brew"
        INSTALL_CMD="brew install"
    elif command -v apt-get &> /dev/null; then
        PKG_MANAGER="apt"
        INSTALL_CMD="sudo apt-get install -y"
        UPDATE_CMD="sudo apt-get update"
    elif command -v dnf &> /dev/null; then
        PKG_MANAGER="dnf"
        INSTALL_CMD="sudo dnf install -y"
    elif command -v pacman &> /dev/null; then
        PKG_MANAGER="pacman"
        INSTALL_CMD="sudo pacman -S --noconfirm"
    else
        fail "Unsupported package manager. Please install dependencies manually."
    fi

    # 1. GIT
    if ! command -v git &> /dev/null; then
        log_warn "Git not found. Installing..."
        $INSTALL_CMD git
    fi

    # 2. PYTHON 3.12+
    # Check current python3 version
    local py_ver=""
    if command -v python3 &> /dev/null; then
        py_ver=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
    fi

    # Logic to compare version (must be >= 3.12)
    local install_python=false
    if [[ -z "$py_ver" ]]; then
        install_python=true
    else
        # minimal float comparison logic
        if (( $(echo "$py_ver < 3.12" | bc -l) )); then
            install_python=true
            log_warn "Python $py_ver detected, but Truetrack requires >= 3.12."
        else
            log_success "Python $py_ver detected."
        fi
    fi

    if [[ "$install_python" == "true" ]]; then
        log_info "Installing Python 3.12+..."
        if [[ "$PKG_MANAGER" == "apt" ]]; then
             # Ubuntu LTS often needs deadsnakes for newer python
             if ! $INSTALL_CMD python3.12 python3.12-venv python3.12-dev; then
                log_warn "Standard repositories failed. Attempting to add PPA (User interaction may be required)..."
                sudo add-apt-repository ppa:deadsnakes/ppa -y
                $UPDATE_CMD
                $INSTALL_CMD python3.12 python3.12-venv python3.12-dev
             fi
        else
            # Best effort for other distros
            $INSTALL_CMD python3
        fi
    fi
    
    # 3. UV (Preferred) or PIP
    if ! command -v uv &> /dev/null; then
        log_warn "uv not found. Installing..."
        curl -LsSf https://astral.sh/uv/install.sh | sh
        source "$HOME/.cargo/env" 2>/dev/null || true
    fi

    # 4. NODE (LTS) & PNPM
    if ! command -v node &> /dev/null; then
        log_warn "Node.js not found. Installing..."
        # Using nvm or direct install is complex. Relying on package manager for system node, 
        # or suggesting user action if system node is ancient.
        $INSTALL_CMD nodejs npm
    fi

    if ! command -v pnpm &> /dev/null; then
        log_warn "pnpm not found. Installing via standard method..."
        if command -v npm &> /dev/null; then
             sudo npm install -g pnpm
        else
             curl -fsSL https://get.pnpm.io/install.sh | sh -
        fi
    fi

    log_success "Dependencies installed."
}
