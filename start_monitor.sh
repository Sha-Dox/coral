#!/bin/bash
# CORAL - Start individual OSINT monitor (standalone mode)
# Usage: ./start_monitor.sh [instagram|pinterest|spotify]

cd "$(dirname "$0")"

MONITOR=$1

if [ -z "$MONITOR" ]; then
    echo "CORAL - Individual Monitor Starter"
    echo ""
    echo "Usage: $0 [instagram|pinterest|spotify]"
    echo ""
    echo "Examples:"
    echo "  $0 instagram    # Start Instagram monitor only"
    echo "  $0 pinterest    # Start Pinterest monitor only"
    echo "  $0 spotify      # Start Spotify monitor only"
    exit 1
fi

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo ""
echo -e "${CYAN}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${CYAN}║   CORAL - Starting ${MONITOR^} Monitor (Standalone)               ${NC}"
echo -e "${CYAN}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""

# Get port from config
PORT=$(python3 -c "from config_loader import config; print(config.get('$MONITOR.port'))" 2>/dev/null)

if [ -z "$PORT" ]; then
    echo -e "${RED}❌ Error: Could not read port for $MONITOR from config.yaml${NC}"
    exit 1
fi

# Check if already running
if lsof -ti:$PORT > /dev/null 2>&1; then
    echo -e "${YELLOW}⚠️  Port $PORT already in use${NC}"
    echo "Kill existing process? (y/N)"
    read -r response
    if [[ "$response" =~ ^[Yy]$ ]]; then
        PID=$(lsof -ti:$PORT)
        kill $PID 2>/dev/null
        sleep 1
    else
        exit 0
    fi
fi

# Start the monitor
case $MONITOR in
    instagram)
        echo -e "${YELLOW}📸 Starting Instagram Monitor...${NC}"
        cd instagram_monitor
        if [ ! -f "instagram_monitor.conf" ]; then
            python3 instagram_monitor.py --generate-config instagram_monitor.conf > /tmp/instagram_monitor_generate.log 2>&1
        fi
        nohup python3 instagram_monitor.py --config-file instagram_monitor.conf --web-dashboard --web-dashboard-port "$PORT" > /tmp/instagram_standalone.log 2>&1 &
        PID=$!
        ;;
    pinterest)
        echo -e "${YELLOW}📌 Starting Pinterest Monitor...${NC}"
        cd pinterest_monitor
        nohup python3 app.py > /tmp/pinterest_standalone.log 2>&1 &
        PID=$!
        ;;
    spotify)
        echo -e "${YELLOW}🎵 Starting Spotify Monitor...${NC}"
        cd spotify_monitor
        if [ ! -f "spotify_profile_monitor.conf" ]; then
            python3 spotify_monitor.py --generate-config spotify_profile_monitor.conf > /tmp/spotify_monitor_generate.log 2>&1
        fi
        nohup python3 spotify_monitor.py --config-file spotify_profile_monitor.conf > /tmp/spotify_standalone.log 2>&1 &
        PID=$!
        ;;
    *)
        echo -e "${RED}❌ Unknown monitor: $MONITOR${NC}"
        echo "Valid options: instagram, pinterest, spotify"
        exit 1
        ;;
esac

sleep 2

# Check if started successfully
if ps -p $PID > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Started successfully${NC}"
    echo ""
    echo "Monitor:  ${MONITOR^}"
    echo "Port:     $PORT"
    echo "PID:      $PID"
    echo "Logs:     /tmp/${MONITOR}_standalone.log"
    echo ""
    echo -e "${YELLOW}Mode:     STANDALONE (no webhooks to hub)${NC}"
    echo ""
    echo "View logs: tail -f /tmp/${MONITOR}_standalone.log"
    echo "Stop:      kill $PID"
else
    echo -e "${RED}❌ Failed to start${NC}"
    echo "Check logs: cat /tmp/${MONITOR}_standalone.log"
    exit 1
fi
