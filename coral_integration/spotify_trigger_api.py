#!/usr/bin/env python3
"""
Spotify Monitor Trigger Wrapper
Provides a simple API endpoint for OSINT Hub to trigger checks
"""
from flask import Flask, jsonify, request
import subprocess
import os
import logging
import sys
from pathlib import Path

# Load central configuration
sys.path.insert(0, str(Path(__file__).parent.parent))
try:
    from config_loader import config
    PORT = config.get('spotify.port', 8001)
except (ImportError, FileNotFoundError):
    PORT = 8001
    print("Warning: Could not load config.yaml, using default port 8001")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Path to your spotify_monitor.py script
MONITOR_SCRIPT = os.path.join(os.path.dirname(__file__), 'spotify_monitor.py')

@app.route('/api/trigger', methods=['POST'])
def trigger_check():
    """Trigger Spotify monitor check"""
    try:
        logger.info("Manual check triggered by OSINT Hub")
        
        # Run the monitor in background
        # Customize with your specific arguments
        subprocess.Popen(
            ['python3', MONITOR_SCRIPT, '--check-once'],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        
        return jsonify({
            'success': True,
            'message': 'Spotify check triggered'
        })
    except Exception as e:
        logger.error(f"Error triggering check: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'platform': 'spotify'
    })

if __name__ == '__main__':
    print("\n" + "="*60)
    print("  Spotify Monitor Trigger API")
    print("="*60)
    print(f"  Listening on: http://localhost:{PORT}")
    print(f"  Trigger endpoint: POST http://localhost:{PORT}/api/trigger")
    print("="*60 + "\n")
    
    app.run(host='0.0.0.0', port=PORT, debug=False)
