"""
Re-export settings for internal use.
Keeps imports clean throughout the application.
"""
from config.settings import Settings, get_settings

__all__ = ["Settings", "get_settings"]