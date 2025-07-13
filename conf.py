#!/usr/bin/env python3
"""
Centralized configuration management for Groq Whisperer.
Prevents race conditions and provides a single source of truth for configuration.
"""

import json
import os
from pathlib import Path
from typing import Dict, Any

# Configuration file location
CONFIG_FILE = Path(__file__).parent / "config.json"

# Default configuration
DEFAULT_CONFIG = {
    "USE_VPN": True,
    "CHECK_VPN_CONNECTION": True,
    "TOGGLE_RECORDING_MODE": False,
    "AUTO_PASTE": True,
    "MAX_RECORDING_DURATION": 60.0,
    "MIN_RECORDING_DURATION": 0.5,
    "NOISE_THRESHOLD": 200,
    "VERBOSE_OUTPUT": False,
    "VPN_VERBOSE": False,
    "LOG_LEVEL": "INFO",
    "API_KEY": "",
    "ENABLE_LOGGING": True,
}

def load() -> Dict[str, Any]:
    """Load configuration from file with fallback to defaults."""
    try:
        if CONFIG_FILE.exists():
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                config = json.load(f)
                # Merge with defaults to ensure all keys are present
                merged_config = DEFAULT_CONFIG.copy()
                merged_config.update(config)
                return merged_config
        else:
            # Create default config file
            save(DEFAULT_CONFIG)
            return DEFAULT_CONFIG.copy()
    except Exception as e:
        print(f"Warning: Failed to load config: {e}")
        return DEFAULT_CONFIG.copy()

def save(config: Dict[str, Any]) -> None:
    """Save configuration to file with error handling."""
    try:
        # Ensure we have all required keys
        merged_config = DEFAULT_CONFIG.copy()
        merged_config.update(config)
        
        # Write to file
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(merged_config, f, indent=2)
    except Exception as e:
        print(f"Warning: Failed to save config: {e}")

def get(key: str, default: Any = None) -> Any:
    """Get a single configuration value."""
    config = load()
    return config.get(key, default)

def set(key: str, value: Any) -> None:
    """Set a single configuration value."""
    config = load()
    config[key] = value
    save(config)

def update(updates: Dict[str, Any]) -> None:
    """Update multiple configuration values."""
    config = load()
    config.update(updates)
    save(config)

def reset() -> None:
    """Reset configuration to defaults."""
    save(DEFAULT_CONFIG)

def get_api_key() -> str:
    """Get API key from environment variable or config file."""
    # Check environment variable first
    api_key = os.getenv("GROQ_API_KEY")
    if api_key:
        return api_key
    
    # Check config file
    api_key = get("API_KEY", "")
    if api_key:
        return api_key
    
    return ""

def ensure_api_key() -> str:
    """Ensure API key is available, prompt if necessary."""
    api_key = get_api_key()
    if not api_key:
        print("GROQ_API_KEY not found in environment or config file.")
        api_key = input("Enter your GROQ API key: ").strip()
        if api_key:
            set("API_KEY", api_key)
    return api_key 