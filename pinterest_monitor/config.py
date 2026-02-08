#!/usr/bin/env python3
"""
Configuration loader for Pinterest Monitor
"""
import configparser
import os

# Default configuration
DEFAULT_CONFIG = {
    'monitoring': {
        'check_interval': 15,
        'max_boards_per_check': 100
    },
    'server': {
        'host': '0.0.0.0',
        'port': 5001,
        'debug': False
    },
    'scraping': {
        'request_delay': 0.5,
        'user_agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
}

class Config:
    def __init__(self, config_file='config.ini'):
        self.config = configparser.ConfigParser()
        
        # Load defaults
        for section, values in DEFAULT_CONFIG.items():
            self.config[section] = {k: str(v) for k, v in values.items()}
        
        # Override with config file if it exists
        if os.path.exists(config_file):
            self.config.read(config_file)
    
    def get_int(self, section, key):
        """Get integer value"""
        return self.config.getint(section, key)
    
    def get_float(self, section, key):
        """Get float value"""
        return self.config.getfloat(section, key)
    
    def get_bool(self, section, key):
        """Get boolean value"""
        return self.config.getboolean(section, key)
    
    def get(self, section, key):
        """Get string value"""
        return self.config.get(section, key)

# Global config instance
config = Config()
