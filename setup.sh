#!/bin/bash
# CORAL Setup Script
# Automated development environment setup

set -e

echo ""
echo "═══════════════════════════════════════"
echo "  CORAL - Development Setup"
echo "═══════════════════════════════════════"
echo ""

# Check Python version
echo "Checking Python..."
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 not found. Please install Python 3.8+"
    exit 1
fi

PYTHON_VERSION=$(python3 --version | cut -d' ' -f2 | cut -d'.' -f1,2)
echo "✓ Python $PYTHON_VERSION found"

# Check if in project directory
if [ ! -f "config.yaml" ]; then
    echo "❌ Must run from project root (config.yaml not found)"
    exit 1
fi

# Install dependencies
echo ""
echo "Installing dependencies..."
cd coral
pip3 install -r requirements.txt --quiet
cd ..
echo "✓ Dependencies installed"

# Install Maigret (for username search)
echo ""
echo "Installing Maigret dependencies..."
if pip3 install maigret --quiet; then
    echo "✓ Maigret installed"
else
    echo "⚠️  Maigret install failed. Username search will be unavailable."
fi

# Create directories
echo ""
echo "Creating directories..."
mkdir -p data logs backups
echo "✓ Directories created"

# Initialize database
echo ""
echo "Initializing database..."
cd coral
python3 -c "import database; database.init_db()" 2>/dev/null
cd ..
echo "✓ Database initialized"

# Set up git hooks
echo ""
echo "Setting up git hooks..."
if [ -d ".git" ]; then
    chmod +x .git/hooks/pre-commit 2>/dev/null || true
    echo "✓ Git hooks configured"
else
    echo "⚠️  Not a git repository, skipping hooks"
fi

# Create .env template
echo ""
echo "Creating environment template..."
cat > .env.example << 'EOF'
# CORAL Environment Variables
CORAL_PORT=5002
CORAL_HOST=0.0.0.0
CORAL_DEBUG=false

# Database
DATABASE_PATH=coral/coral.db

# Logging
LOG_LEVEL=INFO
LOG_FILE=logs/coral.log
EOF
echo "✓ Environment template created (.env.example)"

echo ""
echo "═══════════════════════════════════════"
echo "  Setup Complete!"
echo "═══════════════════════════════════════"
echo ""
echo "Next steps:"
echo "  1. Review config.yaml"
echo "  2. Start CORAL: ./start_all.sh"
echo "  3. Open http://localhost:5002"
echo ""
echo "Or use Docker:"
echo "  docker-compose up -d"
echo ""
