"""
Central Configuration Loader for OSINT Hub
==========================================

This module loads configuration from config.yaml and provides
easy access to settings for all services.

Usage:
    from config_loader import config

    port = config.get('hub.port')
    instagram_port = config.get('instagram.port')
"""

import yaml
import os
from pathlib import Path


class ConfigLoader:
    def __init__(self, config_file="config.yaml"):
        self.config_file = config_file
        self._config = None
        self._load()

    def _load(self):
        """Load configuration from YAML file"""
        # Find config file (support both root and current directory)
        config_path = Path(self.config_file)

        if not config_path.exists():
            # Try parent directory
            config_path = Path(__file__).parent / self.config_file

        if not config_path.exists():
            # Try one level up (for subdirectories)
            config_path = Path(__file__).parent.parent / self.config_file

        if not config_path.exists():
            raise FileNotFoundError(
                f"Configuration file '{self.config_file}' not found"
            )

        with open(config_path, "r") as f:
            self._config = yaml.safe_load(f)

    def _resolve_keys(self, keys):
        value = self._config
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return None, False
        return value, True

    def get(self, key, default=None):
        """
        Get configuration value using dot notation

        Examples:
            config.get('hub.port')
            config.get('instagram.webhook.url')
        """
        keys = key.split(".")
        value, found = self._resolve_keys(keys)
        alt_keys = None
        if not found and keys and keys[0] == "hub":
            alt_keys = ["coral"] + keys[1:]
            value, found = self._resolve_keys(alt_keys)
        if not found:
            return default

        # Support environment variable overrides
        env_key = "OSINT_" + "_".join(k.upper() for k in keys)
        env_value = os.getenv(env_key)
        if env_value is None and alt_keys:
            env_key = "OSINT_" + "_".join(k.upper() for k in alt_keys)
            env_value = os.getenv(env_key)

        if env_value is not None:
            # Try to convert to original type
            if isinstance(value, int):
                return int(env_value)
            elif isinstance(value, bool):
                return env_value.lower() in ("true", "1", "yes")
            return env_value

        return value

    def is_hub_enabled(self):
        """Check if hub is enabled"""
        return self.get("hub.enabled", True)

    def is_monitor_standalone(self, monitor_name):
        """Check if monitor should run in standalone mode (no webhooks)"""
        return self.get(f"{monitor_name}.standalone", False)

    def is_webhook_enabled(self, monitor_name):
        """Check if webhooks are enabled for a monitor"""
        if self.is_monitor_standalone(monitor_name):
            return False
        return self.get(f"{monitor_name}.webhook.enabled", True)

    def get_section(self, section):
        """Get entire configuration section"""
        if section == "hub" and "hub" not in self._config and "coral" in self._config:
            section = "coral"
        return self._config.get(section, {})

    def reload(self):
        """Reload configuration from file"""
        self._load()


# Global config instance
config = ConfigLoader()


# Convenience functions
def get_hub_config():
    """Get hub configuration"""
    return config.get_section("hub")


def get_monitor_config(monitor_name):
    """Get monitor configuration (instagram, pinterest, spotify)"""
    return config.get_section(monitor_name)


def get_trigger_urls():
    """Get all trigger URLs for the hub database"""
    return {
        "instagram": f"http://localhost:{config.get('instagram.port')}/api/trigger-check",
        "pinterest": f"http://localhost:{config.get('pinterest.port')}/api/check-now",
        "spotify": None,
    }


def should_send_webhook(monitor_name):
    """Check if a monitor should send webhooks to the hub"""
    return config.is_webhook_enabled(monitor_name)
