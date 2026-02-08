#!/bin/bash

echo "🎯 Pinterest Monitor - Quick Start"
echo "=================================="
echo ""

# Check if dependencies are installed
if ! python3 -c "import flask" 2>/dev/null; then
    echo "📦 Installing dependencies..."
    pip3 install -r requirements.txt
    echo ""
fi

# Check if another instance is running
if lsof -Pi :5001 -sTCP:LISTEN -t >/dev/null 2>&1; then
    echo "⚠️  Port 5001 is already in use."
    echo "   The monitor may already be running at http://localhost:5001"
    echo ""
    read -p "   Stop existing process and restart? (y/n) " -n 1 -r
    echo ""
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "   Stopping existing process..."
        kill $(lsof -t -i:5001) 2>/dev/null
        sleep 2
    else
        echo "   Exiting. Open http://localhost:5001 in your browser."
        exit 0
    fi
fi

echo "🚀 Starting Pinterest Monitor..."
echo ""
python3 app.py
