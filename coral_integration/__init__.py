"""
CORAL Integration Module
=========================

This module contains all code needed to integrate monitors with CORAL hub.
Monitors can work completely standalone without importing anything from here.

Key Components:
- coral_notifier.py: Send events to CORAL
- coral_checker.py: Auto-detection logic
- config_loader.py: Configuration management
"""

__version__ = '1.0.0'
__all__ = ['CoralNotifier']

try:
    from .coral_notifier import CoralNotifier
except ImportError:
    # Graceful degradation if dependencies missing
    CoralNotifier = None
