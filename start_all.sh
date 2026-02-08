#!/bin/bash
# CORAL - Start All OSINT Services
#
# Centralised OSINT Repository and Automation Layer
# This script starts all OSINT monitoring services based on
# the configuration in config.yaml

cd "$(dirname "$0")"

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo ""
echo -e "${CYAN}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${CYAN}║            CORAL - OSINT Service Manager                   ║${NC}"
echo -e "${CYAN}║   Centralised OSINT Repository and Automation Layer       ║${NC}"
echo -e "${CYAN}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""

# Read configuration
HUB_ENABLED=$(python3 -c "from config_loader import config; print(config.get('hub.enabled', True))" 2>/dev/null || echo "True")
HUB_PORT=$(python3 -c "from config_loader import config; print(config.get('hub.port'))" 2>/dev/null || echo "3456")
INSTAGRAM_ENABLED=$(python3 -c "from config_loader import config; print(config.get('instagram.enabled', True))" 2>/dev/null || echo "True")
INSTAGRAM_PORT=$(python3 -c "from config_loader import config; print(config.get('instagram.port'))" 2>/dev/null || echo "8000")
PINTEREST_ENABLED=$(python3 -c "from config_loader import config; print(config.get('pinterest.enabled', True))" 2>/dev/null || echo "True")
PINTEREST_PORT=$(python3 -c "from config_loader import config; print(config.get('pinterest.port'))" 2>/dev/null || echo "5001")
SPOTIFY_ENABLED=$(python3 -c "from config_loader import config; print(config.get('spotify.enabled', True))" 2>/dev/null || echo "True")
SPOTIFY_PORT=$(python3 -c "from config_loader import config; print(config.get('spotify.port'))" 2>/dev/null || echo "8001")

PIDS=()
STARTED=0

# Start CORAL
if [ "$HUB_ENABLED" = "True" ]; then
    echo -e "${YELLOW}🚀 Starting CORAL Hub...${NC}"
    cd coral
    python3 app.py > /tmp/coral.log 2>&1 &
    HUB_PID=$!
    PIDS+=($HUB_PID)
    echo -e "  ${GREEN}✓${NC} Port: $HUB_PORT, PID: $HUB_PID"
    STARTED=$((STARTED + 1))
    cd ..
else
    echo -e "${YELLOW}⊘ CORAL Hub disabled in config${NC}"
fi

# Start Pinterest Monitor
if [ "$PINTEREST_ENABLED" = "True" ]; then
    echo -e "${YELLOW}📌 Starting Pinterest Monitor...${NC}"
    cd pinterest_monitor
    python3 app.py > /tmp/pinterest_monitor.log 2>&1 &
    PINTEREST_PID=$!
    PIDS+=($PINTEREST_PID)
    echo -e "  ${GREEN}✓${NC} Port: $PINTEREST_PORT, PID: $PINTEREST_PID"
    STARTED=$((STARTED + 1))
    cd ..
else
    echo -e "${YELLOW}⊘ Pinterest Monitor disabled in config${NC}"
fi

# Start Instagram Monitor (web dashboard + API)
if [ "$INSTAGRAM_ENABLED" = "True" ]; then
    echo -e "${YELLOW}📸 Starting Instagram Monitor...${NC}"
    cd instagram_monitor
    if [ ! -f "instagram_monitor.conf" ]; then
        python3 instagram_monitor.py --generate-config instagram_monitor.conf > /tmp/instagram_monitor_generate.log 2>&1
    fi
    python3 instagram_monitor.py --config-file instagram_monitor.conf --web-dashboard --web-dashboard-port "$INSTAGRAM_PORT" > /tmp/instagram_monitor.log 2>&1 &
    INSTAGRAM_PID=$!
    PIDS+=($INSTAGRAM_PID)
    echo -e "  ${GREEN}✓${NC} Port: $INSTAGRAM_PORT, PID: $INSTAGRAM_PID"
    STARTED=$((STARTED + 1))
    cd ..
else
    echo -e "${YELLOW}⊘ Instagram Monitor disabled in config${NC}"
fi

# Start Spotify Monitor
if [ "$SPOTIFY_ENABLED" = "True" ]; then
    echo -e "${YELLOW}🎵 Starting Spotify Monitor...${NC}"
    cd spotify_monitor
    if [ ! -f "spotify_profile_monitor.conf" ]; then
        python3 spotify_monitor.py --generate-config spotify_profile_monitor.conf > /tmp/spotify_monitor_generate.log 2>&1
    fi
    python3 spotify_monitor.py --config-file spotify_profile_monitor.conf > /tmp/spotify_monitor.log 2>&1 &
    SPOTIFY_PID=$!
    PIDS+=($SPOTIFY_PID)
    echo -e "  ${GREEN}✓${NC} Port: $SPOTIFY_PORT, PID: $SPOTIFY_PID"
    STARTED=$((STARTED + 1))
    cd ..
else
    echo -e "${YELLOW}⊘ Spotify Monitor disabled in config${NC}"
fi

echo ""
echo -e "${CYAN}═══════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}✓ Started $STARTED service(s)${NC}"
echo ""

# Show URLs for enabled services
[ "$HUB_ENABLED" = "True" ] && echo -e "CORAL Dashboard:          ${BLUE}http://localhost:$HUB_PORT${NC}"
[ "$PINTEREST_ENABLED" = "True" ] && echo -e "📌 Pinterest Monitor:     ${BLUE}http://localhost:$PINTEREST_PORT${NC}"
[ "$INSTAGRAM_ENABLED" = "True" ] && echo -e "📸 Instagram Monitor:     ${BLUE}http://localhost:$INSTAGRAM_PORT${NC}"
[ "$SPOTIFY_ENABLED" = "True" ] && echo -e "🎵 Spotify Monitor:       ${BLUE}http://localhost:$SPOTIFY_PORT${NC}"

echo ""
echo -e "${YELLOW}⚙️  Configuration:${NC} Edit config.yaml to enable/disable services"

# Build kill command
if [ ${#PIDS[@]} -gt 0 ]; then
    KILL_CMD="kill ${PIDS[*]}"
    echo -e "${YELLOW}🛑 Stop services:${NC} $KILL_CMD"
fi

echo ""
echo -e "${YELLOW}📋 Logs:${NC}"
[ "$HUB_ENABLED" = "True" ] && echo "  CORAL:     tail -f /tmp/coral.log"
[ "$PINTEREST_ENABLED" = "True" ] && echo "  Pinterest: tail -f /tmp/pinterest_monitor.log"
[ "$INSTAGRAM_ENABLED" = "True" ] && echo "  Instagram: tail -f /tmp/instagram_monitor.log"
[ "$SPOTIFY_ENABLED" = "True" ] && echo "  Spotify:   tail -f /tmp/spotify_monitor.log"
echo -e "${CYAN}═══════════════════════════════════════════════════════════${NC}"
echo ""
