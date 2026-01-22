#!/bin/bash

# ==============================================================================
# Logging Helper
# ==============================================================================

# ANSI Colors
BOLD="\033[1m"
RED="\033[31m"
GREEN="\033[32m"
YELLOW="\033[33m"
BLUE="\033[34m"
RESET="\033[0m"

log_info() {
    echo -e "${BLUE}[INFO]${RESET} ${BOLD}$1${RESET}"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${RESET} ${BOLD}$1${RESET}"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${RESET} ${BOLD}$1${RESET}"
}

log_error() {
    echo -e "${RED}[ERROR]${RESET} ${BOLD}$1${RESET}" >&2
}

fail() {
    log_error "$1"
    exit 1
}
