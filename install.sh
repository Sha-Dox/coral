#!/usr/bin/env bash
set -e

# CORAL Installer
# Usage: curl -fsSL https://raw.githubusercontent.com/<user>/coral/main/install.sh | bash

CORAL_DIR="${CORAL_DIR:-$HOME/coral}"
BRANCH="${BRANCH:-main}"
REPO="${REPO:-https://github.com/<user>/coral.git}"

GREEN='\033[0;32m'
BLUE='\033[0;34m'
DIM='\033[2m'
RESET='\033[0m'

info() { echo -e "${BLUE}>>>${RESET} $1"; }
ok()   { echo -e "${GREEN} ✓${RESET} $1"; }
dim()  { echo -e "${DIM}   $1${RESET}"; }

echo ""
echo -e "${GREEN}  ╔═══════════════════════════╗${RESET}"
echo -e "${GREEN}  ║       CORAL Installer      ║${RESET}"
echo -e "${GREEN}  ╚═══════════════════════════╝${RESET}"
echo ""

# Check Python
if ! command -v python3 &>/dev/null; then
    echo "Error: python3 is required but not found."
    exit 1
fi

PYTHON_VERSION=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
info "Python $PYTHON_VERSION found"

# Clone or update
if [ -d "$CORAL_DIR/.git" ]; then
    info "Updating existing installation..."
    cd "$CORAL_DIR"
    git pull --ff-only origin "$BRANCH" 2>/dev/null || true
    ok "Repository updated"
else
    info "Cloning CORAL..."
    git clone --depth 1 -b "$BRANCH" "$REPO" "$CORAL_DIR" 2>/dev/null || {
        # If git clone fails (no remote), just use current directory
        if [ -d "./recoral" ]; then
            CORAL_DIR="$(pwd)"
            info "Using local installation"
        else
            echo "Error: Could not clone repository and no local install found."
            exit 1
        fi
    }
    ok "Cloned to $CORAL_DIR"
fi

cd "$CORAL_DIR"

# Set up venv
info "Setting up virtual environment..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
    ok "Virtual environment created"
else
    ok "Virtual environment exists"
fi

source venv/bin/activate

# Install dependencies
info "Installing dependencies..."
pip install --quiet --upgrade pip
pip install --quiet -r recoral/requirements.txt
ok "Dependencies installed"

# Set up .env
if [ ! -f ".env" ]; then
    if [ -f ".env.example" ]; then
        cp .env.example .env
        ok "Created .env from template"
        dim "Edit .env to configure ports, Spotify cookie, etc."
    fi
else
    ok ".env already exists"
fi

# Done
echo ""
echo -e "${GREEN}  Installation complete!${RESET}"
echo ""
echo "  To start CORAL:"
echo ""
echo -e "    ${DIM}cd $CORAL_DIR${RESET}"
echo -e "    ${DIM}source venv/bin/activate${RESET}"
echo -e "    ${DIM}python3 recoral/app.py${RESET}"
echo ""
echo -e "  Then open ${BLUE}http://localhost:3456${RESET}"
echo ""
