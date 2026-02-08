#!/usr/bin/env python3
"""
Configuration for CORAL
Loads from central config.yaml file
"""
import os
import sys
from pathlib import Path

# Add parent directory to path to import config_loader
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from config_loader import config
    
    # Server settings
    PORT = config.get('hub.port', 5002)
    HOST = config.get('hub.host', '0.0.0.0')
    DEBUG = config.get('hub.debug', False)
    
    # Database
    DATABASE_NAME = config.get('hub.database', 'coral.db')
    
    # Webhook settings (optional)
    DEFAULT_WEBHOOK_SECRET = config.get('hub.webhook_secret', '')
    
except (ImportError, FileNotFoundError) as e:
    print(f"Warning: Could not load config.yaml, using defaults: {e}")
    # Fallback to environment variables
    PORT = int(os.environ.get('CORAL_PORT', 5002))
    HOST = os.environ.get('CORAL_HOST', '0.0.0.0')
    DEBUG = os.environ.get('CORAL_DEBUG', 'False').lower() == 'true'
    DATABASE_NAME = os.environ.get('CORAL_DB', 'coral.db')
    DEFAULT_WEBHOOK_SECRET = os.environ.get('CORAL_WEBHOOK_SECRET', '')

