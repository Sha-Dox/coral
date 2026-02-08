#!/bin/bash
# CORAL - Start only monitors (no hub)
# Useful for running monitors independently without the central hub

cd "$(dirname "$0")"

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo ""
echo -e "${CYAN}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${CYAN}║   CORAL - Starting Monitors Only (No Hub)                 ║${NC}"
echo -e "${CYAN}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""

# Check which monitors are enabled
INSTAGRAM_ENABLED=$(python3 -c "from config_loader import config; print(config.get('instagram.enabled', True))" 2>/dev/null)
PINTEREST_ENABLED=$(python3 -c "from config_loader import config; print(config.get('pinterest.enabled', True))" 2>/dev/null)
SPOTIFY_ENABLED=$(python3 -c "from config_loader import config; print(config.get('spotify.enabled', True))" 2>/dev/null)

STARTED=0

# Instagram
if [ "$INSTAGRAM_ENABLED" = "True" ]; then
    echo -e "${YELLOW}📸 Starting Instagram Monitor...${NC}"
    cd instagram_monitor
    nohup python3 instagram_monitor.py > /tmp/instagram_monitor.log 2>&1 &
    echo -e "  ${GREEN}✓${NC} PID: $!"
    STARTED=$((STARTED + 1))
    cd ..
fi

# Pinterest
if [ "$PINTEREST_ENABLED" = "True" ]; then
    echo -e "${YELLOW}📌 Starting Pinterest Monitor...${NC}"
    cd pinterest_monitor
    nohup python3 app.py > /tmp/pinterest_monitor.log 2>&1 &
    echo -e "  ${GREEN}✓${NC} PID: $!"
    STARTED=$((STARTED + 1))
    cd ..
fi

# Spotify
if [ "$SPOTIFY_ENABLED" = "True" ]; then
    echo -e "${YELLOW}🎵 Starting Spotify Monitor...${NC}"
    cd spotify_monitor
    nohup python3 spotify_monitor.py > /tmp/spotify_monitor.log 2>&1 &
    echo -e "  ${GREEN}✓${NC} PID: $!"
    STARTED=$((STARTED + 1))
    cd ..
fi

if [ $STARTED -eq 0 ]; then
    echo -e "${YELLOW}⚠️  No monitors enabled in config.yaml${NC}"
    exit 0
fi

echo ""
echo -e "${CYAN}═══════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}✓ Started $STARTED monitor(s)${NC}"
echo ""
echo -e "${YELLOW}📍 Mode:${NC} Running in standalone mode"
echo -e "${YELLOW}💡 Note:${NC} Webhooks to hub disabled (set in config.yaml)"
echo ""
echo -e "${YELLOW}📋 Logs:${NC}"
[ "$INSTAGRAM_ENABLED" = "True" ] && echo "  Instagram: tail -f /tmp/instagram_monitor.log"
[ "$PINTEREST_ENABLED" = "True" ] && echo "  Pinterest: tail -f /tmp/pinterest_monitor.log"
[ "$SPOTIFY_ENABLED" = "True" ] && echo "  Spotify:   tail -f /tmp/spotify_monitor.log"
echo -e "${CYAN}═══════════════════════════════════════════════════════════${NC}"
echo ""
