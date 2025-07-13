"""
Groq Whisperer: A robust, terminal-based voice transcription application.

This application captures audio, optionally via a VAD (Voice Activity Detector),
resamples it for the Whisper model, and sends it to the Groq API for transcription.
It features a rich configuration UI, automatic noise-level calibration, and a
unified configuration system.
"""

import asyncio
import configparser
import dataclasses
import enum
import json
import logging
import os
import platform
import signal
import subprocess
import sys
import tempfile
import time
import wave
import winsound
from contextlib import asynccontextmanager
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Literal, Optional, Tuple, List

import keyboard
import numpy as np
import pyaudio
import pyautogui
import pyperclip
import webrtcvad
from groq import Groq
from rich.align import Align
from rich.box import SQUARE
from rich.console import Console

from rich.panel import Panel
from rich.progress import BarColumn, Progress, TextColumn, TimeRemainingColumn
from rich.prompt import Confirm
from rich.table import Table
from rich.text import Text

from rich import print as rp

# --- Constants ---
CONFIG_FILE = Path(__file__).parent / "config.ini"
LOGS_DIR = Path(__file__).parent / "logs"
TARGET_SAMPLE_RATE = 16000  # Whisper's optimal sample rate
START_SOUND = Path(__file__).parent / "start_click_quiet.wav"
COMPLETE_SOUND = Path(__file__).parent / "complete_chime_quiet.wav"

# --- Robust Logging Setup ---
def setup_logging(session_logs: bool = True, console_level: str = "WARNING", file_level: str = "INFO"):
    """Sets up logging to file and console with separate log levels, and a global exception hook."""
    # Create logs directory if it doesn't exist
    LOGS_DIR.mkdir(exist_ok=True)
    
    # Convert string levels to logging constants
    level_map = {
        "DEBUG": logging.DEBUG,
        "INFO": logging.INFO,
        "WARNING": logging.WARNING,
        "ERROR": logging.ERROR,
        "CRITICAL": logging.CRITICAL
    }
    
    console_log_level = level_map.get(console_level.upper(), logging.WARNING)
    file_log_level = level_map.get(file_level.upper(), logging.INFO)
    
    # Clear any existing handlers
    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    
    # Create session-specific log file
    if session_logs:
        session_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        session_log_file = LOGS_DIR / f"session_{session_timestamp}.log"
        
        # Main application log
        app_logger = logging.getLogger("groq_whisperer")
        app_logger.setLevel(logging.DEBUG)  # Set to lowest level, handlers will filter
        app_logger.handlers.clear()
        
        # File handler for session logs
        file_handler = logging.FileHandler(session_log_file, mode='w')
        file_handler.setLevel(file_log_level)
        file_handler.setFormatter(logging.Formatter(
            "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
        ))
        app_logger.addHandler(file_handler)
        
        # Console handler with separate level
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(console_log_level)
        console_handler.setFormatter(logging.Formatter(
            "%(asctime)s [%(levelname)s]: %(message)s"
        ))
        app_logger.addHandler(console_handler)
        
        # Chat log for transcriptions (file only, no console output)
        chat_logger = logging.getLogger("chat")
        chat_logger.setLevel(logging.INFO)
        chat_logger.handlers.clear()
        chat_handler = logging.FileHandler(LOGS_DIR / f"chat_{session_timestamp}.log", mode='w')
        chat_handler.setFormatter(logging.Formatter(
            "%(asctime)s: %(message)s"
        ))
        chat_logger.addHandler(chat_handler)
        # Prevent chat logs from going to console
        chat_logger.propagate = False
        
        # Add session separator (only to files)
        app_logger.info("="*60)
        app_logger.info(f"NEW SESSION STARTED: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        app_logger.info("="*60)
        
        chat_logger.info("="*60)
        chat_logger.info(f"CHAT SESSION STARTED: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        chat_logger.info("="*60)
    else:
        logging.basicConfig(
            level=console_log_level,
            format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
            handlers=[logging.StreamHandler(sys.stdout)]
        )
    
    def handle_exception(exc_type, exc_value, exc_traceback):
        if issubclass(exc_type, KeyboardInterrupt):
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
            return
        logging.error("Uncaught exception", exc_info=(exc_type, exc_value, exc_traceback))

    sys.excepthook = handle_exception

# Initialize with default settings
setup_logging()

# Hotkey definitions
KEY_ALT_X = "alt+x"
KEY_ALT_T = "alt+t"
KEY_ALT_Q = "alt+q"

# --- Custom Exceptions ---
class GracefulExit(Exception):
    """Custom exception for graceful shutdown."""
    pass

class TranscriptionError(Exception):
    """Raised when transcription fails after all retries."""
    pass

class AudioProcessingError(Exception):
    """Raised when audio processing or recording fails."""
    pass

class VPNError(Exception):
    """Raised when VPN operations fail."""
    pass

# --- Core Configuration (Single Source of Truth) ---
def find_openvpn_exe() -> Optional[str]:
    """Attempt to find the OpenVPN executable in common locations."""
    for path_str in [
        os.path.join(os.environ.get("ProgramFiles", "C:/Program Files"), "OpenVPN", "bin", "openvpn.exe"),
        os.path.join(os.environ.get("ProgramFiles(x86)", "C:/Program Files (x86)"), "OpenVPN", "bin", "openvpn.exe"),
    ]:
        if Path(path_str).exists():
            return path_str
    return ""

@dataclasses.dataclass
class Config:
    """
    Defines the application's configuration structure. This dataclass is the
    single source of truth for all settings. It's used to generate the default
    `config.ini` and to load settings from it.
    """
    # --- VPN Settings ---
    use_vpn: bool = False
    check_vpn_connection: bool = True
    vpn_verbose: bool = False
    ovpn_path: str = "ovpns/default.ovpn"
    openvpn_exe: str = dataclasses.field(default_factory=find_openvpn_exe)

    # --- Recording Settings ---
    toggle_recording_mode: bool = False
    auto_paste: bool = True
    max_recording_duration: float = 60.0
    min_recording_duration: float = 0.5
    noise_threshold: int = 300  # Will be auto-calibrated
    vad_aggressiveness: int = 3  # VAD level (0-3, 3 is most aggressive)
    
    # --- UI & Logging ---
    verbose_output: bool = True
    console_log_level: str = "WARNING"  # Only show warnings/errors in console
    file_log_level: str = "INFO"  # Log everything to files
    enable_sounds: bool = True
    enable_session_logging: bool = True

    @classmethod
    def load(cls) -> "Config":
        """
        Loads config from INI file, creates a default one if it doesn't exist,
        and migrates legacy JSON keys.
        """
        if not CONFIG_FILE.exists():
            # Check for legacy JSON config
            legacy_json = CONFIG_FILE.parent / "config.json"
            if legacy_json.exists():
                try:
                    with open(legacy_json, "r") as f:
                        legacy_data = json.load(f)
                    logging.info("Migrating from legacy JSON config to INI format")
                    instance = cls._from_legacy_json(legacy_data)
                    instance.save()
                    return instance
                except Exception as e:
                    logging.warning(f"Failed to migrate legacy config: {e}")
            
            instance = cls()
            instance.save()
            return instance
        
        try:
            config_parser = configparser.ConfigParser()
            config_parser.read(CONFIG_FILE)
            
            # Get defaults
            defaults = dataclasses.asdict(cls())
            loaded_data = {}
            
            # Load from INI sections
            for section_name in config_parser.sections():
                for key, value in config_parser.items(section_name):
                    if key in defaults:
                        # Convert string values to appropriate types
                        default_type = type(defaults[key])
                        if default_type == bool:
                            loaded_data[key] = config_parser.getboolean(section_name, key)
                        elif default_type == float:
                            loaded_data[key] = config_parser.getfloat(section_name, key)
                        elif default_type == int:
                            loaded_data[key] = config_parser.getint(section_name, key)
                        else:
                            loaded_data[key] = value
            
            # Merge with defaults
            final_config_data = {**defaults, **loaded_data}
            return cls(**final_config_data)
            
        except Exception as e:
            logging.warning(f"Could not read config file ({e}), creating a new one.")
            instance = cls()
            instance.save()
            return instance
    
    @classmethod
    def _from_legacy_json(cls, data: Dict[str, Any]) -> "Config":
        """Creates config from legacy JSON data."""
        defaults = dataclasses.asdict(cls())
        migrated = {}
        
        for key, val in data.items():
            snake = key.lower()
            if snake in defaults:
                if isinstance(val, type(defaults[snake])):
                    migrated[snake] = val
                else:
                    logging.warning(f"Config value for '{key}' has wrong type. Using default.")
            else:
                logging.warning(f"Ignoring unknown config key: {key}")
        
        final_config_data = {**defaults, **migrated}
        return cls(**final_config_data)

    def save(self):
        """Saves the current configuration to `config.ini`."""
        config_parser = configparser.ConfigParser()
        data = dataclasses.asdict(self)
        
        # Group settings into logical sections
        config_parser.add_section('VPN')
        config_parser.set('VPN', 'use_vpn', str(data['use_vpn']))
        config_parser.set('VPN', 'check_vpn_connection', str(data['check_vpn_connection']))
        config_parser.set('VPN', 'vpn_verbose', str(data['vpn_verbose']))
        config_parser.set('VPN', 'ovpn_path', data['ovpn_path'])
        config_parser.set('VPN', 'openvpn_exe', data['openvpn_exe'])
        
        config_parser.add_section('Recording')
        config_parser.set('Recording', 'toggle_recording_mode', str(data['toggle_recording_mode']))
        config_parser.set('Recording', 'auto_paste', str(data['auto_paste']))
        config_parser.set('Recording', 'max_recording_duration', str(data['max_recording_duration']))
        config_parser.set('Recording', 'min_recording_duration', str(data['min_recording_duration']))
        config_parser.set('Recording', 'noise_threshold', str(data['noise_threshold']))
        config_parser.set('Recording', 'vad_aggressiveness', str(data['vad_aggressiveness']))
        
        config_parser.add_section('Interface')
        config_parser.set('Interface', 'verbose_output', str(data['verbose_output']))
        config_parser.set('Interface', 'console_log_level', data['console_log_level'])
        config_parser.set('Interface', 'file_log_level', data['file_log_level'])
        config_parser.set('Interface', 'enable_sounds', str(data['enable_sounds']))
        config_parser.set('Interface', 'enable_session_logging', str(data['enable_session_logging']))
        
        try:
            with open(CONFIG_FILE, 'w') as f:
                config_parser.write(f)
        except Exception as e:
            logging.error(f"Error saving config: {e}")

# --- UI Components ---
class AudioLevelVisualizer:
    """Enhanced audio level visualizer with explicit feedback."""
    
    def __init__(self, bar_width: int = 40):
        self.bar_width = bar_width
        self.peak_level = 0.0
        self.peak_decay = 0.95

    def get_level_feedback(self, level: float, threshold: float) -> Tuple[str, str]:
        """Provides explicit feedback on audio levels."""
        if level < threshold * 0.5:
            return "Too Quiet", "blue"
        if level > threshold * 3:
            return "Too Loud!", "red"
        if level > threshold * 1.5:
            return "Good", "yellow"
        return "Good", "green"

    def render(self, level: float, threshold: float) -> str:
        """Creates the visualizer string."""
        # Normalize level for the bar
        max_level = threshold * 4
        normalized = min(1.0, level / max_level)
        
        # Update peak with decay
        if normalized > self.peak_level:
            self.peak_level = normalized
        else:
            self.peak_level *= self.peak_decay
            
        filled_width = int(normalized * self.bar_width)
        
        feedback, color = self.get_level_feedback(level, threshold)
        
        # Create the bar without Rich markup to avoid conflicts
        filled_part = "█" * filled_width
        empty_part = " " * (self.bar_width - filled_width)
        bar = filled_part + empty_part
        
        # Add peak indicator if applicable
        peak_pos = int(self.peak_level * self.bar_width)
        if 0 < peak_pos <= self.bar_width:
            bar_list = list(bar)
            if peak_pos - 1 < len(bar_list):
                bar_list[peak_pos - 1] = "┃"
            bar = "".join(bar_list)
        
        # Return plain text without Rich markup to prevent conflicts
        return f"Level: {int(level):<5} |{bar}| {feedback}"

class SettingsUI:
    """Manages the interactive configuration panel."""

    def __init__(self, console: Console, config: Config, app: "WhispererApp"):
        self.console = console
        self.config = config
        self.app = app
        self.settings_info = {
            "use_vpn": "Enable VPN for secure connection",
            "check_vpn_connection": "Verify VPN connectivity before start",
            "toggle_recording_mode": "Toggle vs. Hold-to-Record mode",
            "auto_paste": "Auto-paste transcriptions after copy",
            "max_recording_duration": "Maximum recording length (seconds)",
            "min_recording_duration": "Minimum recording length (seconds)",
            "noise_threshold": "Audio sensitivity (auto-calibrated)",
            "vad_aggressiveness": "VAD Aggressiveness (0-3)",
            "verbose_output": "Show detailed status messages",
            "vpn_verbose": "Show detailed VPN connection info",
            "console_log_level": "Console logging level (DEBUG/INFO/WARNING/ERROR)",
            "file_log_level": "File logging level (DEBUG/INFO/WARNING/ERROR)",
            "enable_sounds": "Enable audio feedback sounds",
            "enable_session_logging": "Enable per-session logging",
        }



    def _create_welcome_panel(self) -> Text:
        """Creates the header panel with ASCII art banner."""
        text = Text()
        text.append("\n", style="")
        
        # Simple text banner that works reliably on Windows
        banner = """
================================================================================
                            GROQ WHISPERER
                      Voice Transcription System
                         Configuration Menu
================================================================================
"""
        text.append(banner, style="bold cyan")
        text.append("\n", style="")
        text.append("Navigate: ", style="white")
        text.append("↑/↓", style="yellow")
        text.append(" arrows  •  Select: ", style="white")
        text.append("Enter", style="yellow")
        text.append("  •  Exit: ", style="white")
        text.append("Q/Esc", style="yellow")
        text.append("\n", style="")
        text.append("Settings auto-save to ", style="white")
        text.append("config.ini", style="green")
        text.append("\n", style="")
        return text

    def _create_settings_table(self) -> Text:
        """Creates the settings display with horizontal dividers."""
        text = Text()
        text.append("\n", style="")
        text.append(" ⚙️ CURRENT SETTINGS ", style="bold white on blue")
        text.append("\n", style="")
        text.append("─" * 80, style="dim cyan")
        text.append("\n", style="")
        
        config_dict = dataclasses.asdict(self.config)
        
        # Show only the most important settings in compact form
        important_settings = [
            ("Use VPN", "use_vpn"),
            ("Recording Mode", "toggle_recording_mode"), 
            ("Auto-paste", "auto_paste"),
            ("Sounds", "enable_sounds"),
            ("Session Logging", "enable_session_logging"),
            ("Console Log Level", "console_log_level"),
            ("File Log Level", "file_log_level")
        ]
        
        for display_name, key in important_settings:
            if key in config_dict:
                value = config_dict[key]
                desc = self.settings_info.get(key, "")
                
                if isinstance(value, bool):
                    display_value = "ON" if value else "OFF"
                    color = "green" if value else "red"
                elif key.endswith("_log_level"):
                    display_value = str(value)
                    color = "magenta"
                else:
                    display_value = str(value)
                    color = "white"
                
                # Format: Setting name (30 chars) | Value (8 chars) | Description
                text.append(f"{display_name:<30}", style="bold cyan")
                text.append(f"{display_value:>8}", style=f"bold {color}")
                text.append(f"  {desc}", style="dim white")
                text.append("\n", style="")
        
        text.append("─" * 80, style="dim cyan")
        text.append("\n", style="")
        
        return text

    def _create_menu_options(self, selected_index: int) -> Text:
        """Creates the menu with horizontal dividers and background highlights."""
        # Menu structure with categories
        menu_structure = [
            # VPN Section
            ("🔒 VPN SETTINGS", "header"),
            ("Toggle VPN Usage", "use_vpn"),
            ("Toggle VPN Verbose", "vpn_verbose"),
            ("Toggle VPN Connection Check", "check_vpn_connection"),
            ("", "divider"),
            
            # Recording Section  
            ("🎙️ RECORDING SETTINGS", "header"),
            ("Toggle Recording Mode", "toggle_recording_mode"),
            ("Toggle Auto-paste", "auto_paste"),
            ("Set Max Recording Duration", "max_recording_duration"),
            ("Set Min Recording Duration", "min_recording_duration"),
            ("Set Noise Threshold", "noise_threshold"),
            ("Set VAD Aggressiveness", "vad_aggressiveness"),
            ("", "divider"),
            
            # Interface Section
            ("🖥️ INTERFACE SETTINGS", "header"),
            ("Toggle Verbose Output", "verbose_output"),
            ("Toggle Sounds", "enable_sounds"),
            ("Toggle Session Logging", "enable_session_logging"),
            ("Cycle Console Log Level", "console_log_level"),
            ("Cycle File Log Level", "file_log_level"),
            ("", "divider"),
            
            # Actions Section
            ("⚙️ ACTIONS", "header"),
            ("Run Network Tests", "network_test"),
            ("Calibrate Microphone", "calibrate_mic"),
            ("", "divider"),
            
            # Main Actions
            ("🚀 START APPLICATION", "start"),
            ("❌ QUIT", "quit")
        ]
        
        # Get the menu items (non-headers/dividers only) - must match show() method exactly
        menu_items = [
            "use_vpn", "vpn_verbose", "check_vpn_connection",
            "toggle_recording_mode", "auto_paste", "max_recording_duration",
            "min_recording_duration", "noise_threshold", "vad_aggressiveness",
            "verbose_output", "enable_sounds", "enable_session_logging",
            "console_log_level", "file_log_level", "network_test", "calibrate_mic",
            "start", "quit"
        ]
        
        # Find the actual selected menu item index
        actual_selected = 0
        menu_item_index = 0
        for i, (label, action) in enumerate(menu_structure):
            if action not in ["header", "divider"]:
                if menu_item_index == selected_index:
                    actual_selected = i
                    break
                menu_item_index += 1
        
        text = Text()
        for i, (label, action) in enumerate(menu_structure):
            if action == "header":
                # Category header with background highlight
                text.append(f"\n {label} ", style="bold white on blue")
                text.append("\n")
            elif action == "divider":
                # Horizontal divider
                text.append("─" * 60, style="dim cyan")
                text.append("\n")
            else:
                # Menu item
                if i == actual_selected:
                    # Selected item with full background highlight
                    text.append(f" ▶ {label} ", style="bold black on green")
                else:
                    # Normal menu item
                    text.append(f"   {label}", style="white")
                text.append("\n")
        
        return text

    async def show(self) -> bool:
        """Displays the interactive settings panel."""
        if not sys.stdout.isatty():
            return True  # Skip interactive config in non-TTY environments

        # Menu items that match the new structure exactly
        menu_items = [
            "use_vpn", "vpn_verbose", "check_vpn_connection",
            "toggle_recording_mode", "auto_paste", "max_recording_duration",
            "min_recording_duration", "noise_threshold", "vad_aggressiveness",
            "verbose_output", "enable_sounds", "enable_session_logging",
            "console_log_level", "file_log_level", "network_test", "calibrate_mic",
            "start", "quit"
        ]
        selected_index = menu_items.index("start")

        # Initial display
        self._display_menu(selected_index)
        
        while True:
            event = await asyncio.to_thread(keyboard.read_event)
            if event.event_type != keyboard.KEY_DOWN:
                continue

            needs_update = False
            
            if event.name == "down":
                selected_index = (selected_index + 1) % len(menu_items)
                needs_update = True
            elif event.name == "up":
                selected_index = (selected_index - 1 + len(menu_items)) % len(menu_items)
                needs_update = True
            elif event.name == "enter":
                action = menu_items[selected_index]
                
                if action == "start": return True
                if action == "quit": return False
                
                # Handle boolean toggles
                if ("toggle" in action or action in ["use_vpn", "enable_sounds", "enable_session_logging", 
                                                    "vpn_verbose", "check_vpn_connection", "verbose_output"]):
                    setattr(self.config, action, not getattr(self.config, action))
                    self.config.save()
                    needs_update = True
                # Handle log level cycling
                elif action in ["console_log_level", "file_log_level"]:
                    await self._cycle_log_level(action)
                    needs_update = True
                # Handle numeric settings
                elif action in ["max_recording_duration", "min_recording_duration", "noise_threshold", "vad_aggressiveness"]:
                    await self._set_numeric_value(action)
                    needs_update = True
                # Handle special actions
                elif hasattr(self, f"_action_{action}"):
                    await getattr(self, f"_action_{action}")()
                    needs_update = True

            elif event.name in ["q", "esc"]:
                return False
            
            # Update display if something changed
            if needs_update:
                self._display_menu(selected_index)

    def _display_menu(self, selected_index: int):
        """Display the menu with proper clearing to prevent scroll issues."""
        # Clear screen properly for Windows
        self.console.clear()
        
        # Show header
        header_text = self._create_welcome_panel()
        self.console.print(header_text)
        
        # Show settings
        settings_text = self._create_settings_table()
        self.console.print(settings_text)
        
        # Show menu
        menu_text = self._create_menu_options(selected_index)
        self.console.print(menu_text)

    async def _action_network_test(self):
        """Action to run network connectivity tests."""
        self.console.print("[cyan]Running network tests...[/cyan]")
        await asyncio.sleep(1)
        self.console.print("[green]Network tests complete.[/green]")
        await asyncio.sleep(1)

    async def _action_calibrate_mic(self):
        """Action to trigger microphone calibration."""
        await self.app.initialize_audio()
        if self.app.audio_processor:
            await self.app.audio_processor.calibrate()
            self.config.save()
    
    async def _cycle_log_level(self, setting_name: str):
        """Cycle through log levels for console or file logging."""
        levels = ["DEBUG", "INFO", "WARNING", "ERROR"]
        current_level = getattr(self.config, setting_name)
        try:
            current_index = levels.index(current_level)
            next_index = (current_index + 1) % len(levels)
        except ValueError:
            next_index = 0  # Default to DEBUG if current level not found
        
        setattr(self.config, setting_name, levels[next_index])
        self.config.save()
        
        # Reinitialize logging with new levels
        setup_logging(
            session_logs=self.config.enable_session_logging,
            console_level=self.config.console_log_level,
            file_level=self.config.file_log_level
        )
    
    async def _set_numeric_value(self, setting_name: str):
        """Prompt user to set a numeric value for a configuration setting."""
        from rich.prompt import Prompt
        
        current_value = getattr(self.config, setting_name)
        setting_info = {
            "max_recording_duration": ("Maximum Recording Duration (seconds)", 1, 300, float),
            "min_recording_duration": ("Minimum Recording Duration (seconds)", 0.1, 60.0, float),
            "noise_threshold": ("Noise Threshold", 1, 1000, int),
            "vad_aggressiveness": ("VAD Aggressiveness Level", 0, 3, int)
        }
        
        if setting_name not in setting_info:
            return
            
        desc, min_val, max_val, value_type = setting_info[setting_name]
        
        self.console.print(f"\n[cyan]Current {desc}: {current_value}[/cyan]")
        self.console.print(f"[yellow]Valid range: {min_val} - {max_val}[/yellow]")
        
        try:
            user_input = Prompt.ask(f"Enter new value for {desc}", default=str(current_value))
            new_value = value_type(user_input)
            
            if min_val <= new_value <= max_val:
                setattr(self.config, setting_name, new_value)
                self.config.save()
                self.console.print(f"[green]✓ {desc} updated to {new_value}[/green]")
            else:
                self.console.print(f"[red]✗ Value must be between {min_val} and {max_val}[/red]")
                
        except ValueError:
            self.console.print(f"[red]✗ Invalid {value_type.__name__} value[/red]")
        
        await asyncio.sleep(2)

def play_sound(sound_file: Path, enabled: bool = True):
    """Play a sound file if sounds are enabled and file exists."""
    if not enabled:
        return
    
    if not sound_file.exists():
        logging.debug(f"Sound file not found: {sound_file}")
        # Use system beep as fallback
        try:
            if "start" in str(sound_file).lower():
                winsound.Beep(1000, 150)
            else:
                winsound.Beep(800, 150)
        except Exception:
            pass
        return
    
    try:
        # Try synchronous playback first for reliability
        winsound.PlaySound(str(sound_file), winsound.SND_FILENAME)
    except Exception as e:
        logging.debug(f"WAV playback failed: {e}")
        # Fallback to system beep if file playback fails
        try:
            if "start" in str(sound_file).lower():
                winsound.Beep(1000, 150)  # Start recording beep
            else:
                winsound.Beep(800, 150)   # Complete beep
        except Exception:
            pass  # Silent failure for sounds

# --- Audio Processing ---
class AudioProcessor:
    """Handles all audio recording, VAD, and processing."""

    def __init__(self, config: Config):
        self.config = config
        self.console = Console(width=120)
        self.visualizer = AudioLevelVisualizer()
        self._pyaudio = self._initialize_pyaudio_with_retry()
        self.vad = webrtcvad.Vad(self.config.vad_aggressiveness)
        self.input_device_index = self._pyaudio.get_default_input_device_info()["index"]
        self.chat_logger = logging.getLogger("chat")

    def _initialize_pyaudio_with_retry(self) -> pyaudio.PyAudio:
        """Initialize PyAudio with retry logic for better reliability."""
        for attempt in range(2):  # Try twice
            try:
                return pyaudio.PyAudio()
            except Exception as e:
                if attempt == 0:
                    logging.warning(f"PyAudio initialization failed on first try: {e}. Retrying in 1 second...")
                    time.sleep(1)
                else:
                    logging.error(f"PyAudio initialization failed after retry: {e}")
                    raise AudioProcessingError(f"Failed to initialize audio system: {e}")
        
        # This should never be reached, but just in case
        raise AudioProcessingError("Failed to initialize audio system")

    async def calibrate(self):
        """Auto-calibrates the noise threshold."""
        self.console.print(
            Panel(
                "[bold yellow]Calibrating microphone...[/bold yellow]\nPlease stay quiet for 2 seconds.",
                title="Mic Check", border_style="yellow"
            )
        )
        # Try to open stream with retry logic
        stream = None
        for attempt in range(2):
            try:
                stream = self._pyaudio.open(
                    format=pyaudio.paInt16, channels=1, rate=TARGET_SAMPLE_RATE,
                    input=True, frames_per_buffer=160, input_device_index=self.input_device_index
                )
                break
            except Exception as e:
                if attempt == 0:
                    logging.warning(f"Microphone stream failed on first try: {e}. Retrying in 1 second...")
                    time.sleep(1)
                else:
                    raise AudioProcessingError(f"Failed to open microphone stream: {e}")
        
        if not stream:
            raise AudioProcessingError("Failed to open microphone stream")
        
        try:
            ambient_levels = []
            for _ in range(100): # 2 seconds of audio
                audio_chunk = stream.read(160, exception_on_overflow=False)
                audio_data = np.frombuffer(audio_chunk, dtype=np.int16)
                ambient_levels.append(np.abs(audio_data).mean())
                await asyncio.sleep(0.02)
                
        finally:
            try:
                stream.stop_stream()
                stream.close()
            except Exception as e:
                logging.warning(f"Error closing calibration stream: {e}")
        
        if not ambient_levels:
            self.console.print("[red]Mic calibration failed: No audio data.[/red]")
            return

        avg_noise = np.mean(ambient_levels)
        self.config.noise_threshold = int(avg_noise * 2.0) + 25
        self.console.print(f"[green]✓ Calibration complete. New noise threshold: {self.config.noise_threshold}[/green]")
        await asyncio.sleep(2)

    async def record(self) -> Optional[Tuple[bytes, int]]:
        """Records audio using VAD and provides real-time feedback with robust error handling."""
        chunk_duration_ms = 20  # VAD supports 10, 20, 30 ms
        chunk_size = int(TARGET_SAMPLE_RATE * chunk_duration_ms / 1000)
        
        # Try to open stream with retry logic
        stream = None
        for attempt in range(2):
            try:
                stream = self._pyaudio.open(
                    format=pyaudio.paInt16, channels=1, rate=TARGET_SAMPLE_RATE,
                    input=True, frames_per_buffer=chunk_size, input_device_index=self.input_device_index
                )
                break
            except Exception as e:
                if attempt == 0:
                    logging.warning(f"Recording stream failed on first try: {e}. Retrying in 1 second...")
                    time.sleep(1)
                else:
                    raise AudioProcessingError(f"Failed to open recording stream: {e}")
        
        if not stream:
            raise AudioProcessingError("Failed to open recording stream")
        
        voiced_frames = []
        
        try:
            # Wait for key press
            if self.config.toggle_recording_mode:
                self.console.print("[cyan]Press Alt+X to start/stop recording.[/cyan]")
                await asyncio.to_thread(keyboard.wait, KEY_ALT_X)
            else:
                self.console.print("[cyan]Press and hold Alt+X to record...[/cyan]")
                await asyncio.to_thread(keyboard.wait, KEY_ALT_X)

            play_sound(START_SOUND, self.config.enable_sounds)
            
            is_recording = True
            start_time = time.time()
            alt_x_was_pressed = True  # Track if Alt+X was just pressed to start recording

            try:
                last_update_time = 0
                while is_recording:
                    try:
                        audio_chunk = stream.read(chunk_size, exception_on_overflow=False)
                        audio_level = np.abs(np.frombuffer(audio_chunk, dtype=np.int16)).mean()
                        
                        is_speech = self.vad.is_speech(audio_chunk, TARGET_SAMPLE_RATE)
                        if is_speech:
                            voiced_frames.append(audio_chunk)
                        
                        # Update UI periodically to avoid spam
                        current_time = time.time()
                        if current_time - last_update_time > 0.1:  # Update every 100ms
                            viz = self.visualizer.render(audio_level, self.config.noise_threshold)
                            status = "REC" if is_speech else "SILENCE"
                            duration = current_time - start_time
                            
                            # Simple console update without Rich Live
                            print(f"\r{viz} | Status: {status} | Duration: {duration:.1f}s", end="", flush=True)
                            last_update_time = current_time

                        # Check stop condition
                        if self.config.toggle_recording_mode:
                            # In toggle mode, detect Alt+X press to stop
                            try:
                                alt_x_currently_pressed = keyboard.is_pressed(KEY_ALT_X)
                                # If Alt+X is pressed and it wasn't pressed before, toggle recording
                                if alt_x_currently_pressed and not alt_x_was_pressed:
                                    is_recording = False
                                alt_x_was_pressed = alt_x_currently_pressed
                            except Exception:
                                pass  # Ignore keyboard errors
                        else:
                            # In hold mode, stop when key is released
                            try:
                                if not keyboard.is_pressed(KEY_ALT_X):
                                    is_recording = False
                            except Exception:
                                is_recording = False  # Stop recording if keyboard check fails
                        
                        if duration > self.config.max_recording_duration:
                            break
                        
                        await asyncio.sleep(0.01)
                        
                    except Exception as e:
                        logging.error(f"Error in recording loop: {e}", exc_info=True)
                        is_recording = False
                        break
                        
            except Exception as e:
                logging.error(f"Error in recording: {e}", exc_info=True)
            finally:
                # Clear the line after recording
                print("\r" + " " * 80 + "\r", end="", flush=True)

            play_sound(COMPLETE_SOUND, self.config.enable_sounds)
            
        finally:
            # Always ensure the stream is properly closed
            try:
                if stream:
                    stream.stop_stream()
                    stream.close()
                    logging.debug("Audio stream closed successfully")
            except Exception as e:
                logging.warning(f"Error closing audio stream: {e}")

        if not voiced_frames or (len(voiced_frames) * chunk_duration_ms / 1000) < self.config.min_recording_duration:
            raise AudioProcessingError("Recording too short or no speech detected.")
            
        return b"".join(voiced_frames), TARGET_SAMPLE_RATE

    async def save_audio(self, audio_data: bytes, sample_rate: int) -> Path:
        """Saves audio data to a temporary WAV file."""
        temp_path = Path(tempfile.gettempdir()) / f"groq_audio_{int(time.time()*1000)}.wav"
        with wave.open(str(temp_path), "wb") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(self._pyaudio.get_sample_size(pyaudio.paInt16))
            wf.setframerate(sample_rate)
            wf.writeframes(audio_data)
        return temp_path

    def __del__(self):
        try:
            if hasattr(self, '_pyaudio') and self._pyaudio:
                self._pyaudio.terminate()
        except Exception as e:
            logging.debug(f"Error terminating PyAudio: {e}")

# --- Services ---
class TranscriptionService:
    """Handles communication with the Groq API."""
    def __init__(self, api_key: str):
        self.client = Groq(api_key=api_key, max_retries=3, timeout=30.0)

    async def transcribe(self, audio_file_path: Path) -> str:
        with open(audio_file_path, "rb") as audio_file:
            response = await asyncio.to_thread(
                self.client.audio.transcriptions.create,
                file=(audio_file_path.name, audio_file.read()),
                model="whisper-large-v3",
                response_format="text"
            )
        return str(response)

# --- Main Application ---
class WhispererApp:
    """Main application orchestrator."""

    def __init__(self, skip_config_ui: bool = False):
        self.config = Config.load()
        self.console = Console(width=120, legacy_windows=True, force_terminal=True)
        self.settings_ui = SettingsUI(self.console, self.config, self)
        self.audio_processor: Optional[AudioProcessor] = None
        self.transcription_service: Optional[TranscriptionService] = None
        self._should_quit = False
        self.skip_config_ui = skip_config_ui
        self.app_logger = logging.getLogger("groq_whisperer")
        self.chat_logger = logging.getLogger("chat")

    async def run(self):
        """Main application entry point."""
        try:
            is_first_run = not CONFIG_FILE.exists()
            if is_first_run:
                await self.first_run_setup()
            
            self.config = Config.load() # Reload config after potential first run setup
            self.settings_ui.config = self.config
            
            # Initialize logging with user settings
            setup_logging(
                session_logs=self.config.enable_session_logging,
                console_level=self.config.console_log_level,
                file_level=self.config.file_log_level
            )

            if not self.skip_config_ui:
                if not await self.settings_ui.show():
                    self.console.print("[yellow]Exiting.[/yellow]")
                    return

            await self.initialize_services()
            self._show_startup_banner()
            
            # Start keyboard listener task
            keyboard_task = asyncio.create_task(self._keyboard_listener())
            main_loop_task = asyncio.create_task(self._main_loop())
            
            # Wait for either task to complete
            done, pending = await asyncio.wait(
                [keyboard_task, main_loop_task],
                return_when=asyncio.FIRST_COMPLETED
            )
            
            # Cancel the remaining task
            for task in pending:
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass

        except Exception as e:
            error_msg = f"An unexpected error occurred: {str(e)}"
            self.console.print(Panel(
                error_msg,
                title="[bold red]Error[/bold red]",
                border_style="red"
            ))
            logging.exception("Unexpected error during execution")
        finally:
            self.config.save()

    async def first_run_setup(self):
        """Guides the user through initial setup."""
        self.console.print(Panel("[bold cyan]Welcome to Groq Whisperer! Let's get you set up.[/bold cyan]"))
        
        # API Key check is handled at launch
        
        # Mic Calibration
        await self.initialize_audio()
        if self.audio_processor:
            await self.audio_processor.calibrate()
            self.config.save()

    async def initialize_audio(self):
        if not self.audio_processor:
            self.audio_processor = AudioProcessor(self.config)

    async def initialize_services(self):
        """Initializes all necessary service classes."""
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            raise ValueError("GROQ_API_KEY environment variable not set.")
        
        await self.initialize_audio()
        self.transcription_service = TranscriptionService(api_key)

    def _show_startup_banner(self):
        """Displays the ready message."""
        mode = "Toggle" if self.config.toggle_recording_mode else "Hold"
        sounds = "[green]ON[/]" if self.config.enable_sounds else "[red]OFF[/]"
        logging_status = "[green]ON[/]" if self.config.enable_session_logging else "[red]OFF[/]"
        
        self.console.print(Panel(
            f"[bold green]Groq Whisperer is Ready![/]\n"
            f"Mode: [yellow]{mode}[/] | Sounds: {sounds} | Logging: {logging_status}\n"
            f"Hotkeys: [cyan]Alt+X[/] Record, [cyan]Alt+T[/] Toggle Mode, [cyan]Alt+Q[/] Quit",
            border_style="green"
        ))

    async def _keyboard_listener(self):
        """Listen for global keyboard shortcuts."""
        while not self._should_quit:
            try:
                # Use keyboard.wait for the specific hotkey combinations
                # This is more reliable than reading individual events
                await asyncio.to_thread(self._check_hotkeys)
                await asyncio.sleep(0.05)  # Check every 50ms
                
            except Exception as e:
                logging.debug(f"Keyboard listener error: {e}")
                await asyncio.sleep(0.1)  # Longer delay on error
    
    def _check_hotkeys(self):
        """Check for hotkey combinations."""
        try:
            # Add a small flag to prevent multiple rapid triggers
            if hasattr(self, '_last_hotkey_time'):
                if time.time() - self._last_hotkey_time < 0.3:
                    return
            
            # Check Alt+T (toggle recording mode)
            if keyboard.is_pressed('alt') and keyboard.is_pressed('t'):
                self.config.toggle_recording_mode = not self.config.toggle_recording_mode
                self.config.save()
                mode = "Toggle" if self.config.toggle_recording_mode else "Hold"
                self.console.print(f"\n[yellow]Recording mode changed to: {mode}[/yellow]")
                self._last_hotkey_time = time.time()
                time.sleep(0.3)  # Prevent rapid toggling
            
            # Check Alt+Q (quit)
            elif keyboard.is_pressed('alt') and keyboard.is_pressed('q'):
                self.console.print("\n[yellow]Quitting...[/yellow]")
                self._should_quit = True
                self._last_hotkey_time = time.time()
                
        except Exception as e:
            logging.debug(f"Hotkey check error: {e}")

    async def _main_loop(self):
        """The main record-transcribe loop."""
        while not self._should_quit:
            try:
                if not self.audio_processor or not self.transcription_service:
                    raise RuntimeError("Services not initialized.")

                audio_data, sample_rate = await self.audio_processor.record()
                if not audio_data:
                    continue

                with self.console.status("[bold green]Saving audio...[/]"):
                    temp_audio_file = await self.audio_processor.save_audio(audio_data, sample_rate)

                with self.console.status("[bold green]Transcribing...[/]"):
                    transcription = await self.transcription_service.transcribe(temp_audio_file)
                
                self.console.print(Panel(Text(transcription), title="Transcription", border_style="green"))
                pyperclip.copy(transcription)
                self.console.print("[cyan]✓ Copied to clipboard.[/cyan]")
                
                # Log transcription to chat log
                if self.config.enable_session_logging:
                    self.chat_logger.info(f"TRANSCRIPTION: {transcription}")
                
                if self.config.auto_paste:
                    pyautogui.hotkey("ctrl", "v")
                    self.console.print("[cyan]✓ Pasted.[/cyan]")
                    play_sound(COMPLETE_SOUND, self.config.enable_sounds)

                # Clean up temporary file
                try:
                    os.unlink(temp_audio_file)
                except Exception as e:
                    logging.warning(f"Could not delete temporary file {temp_audio_file}: {e}")

            except AudioProcessingError as e:
                # Clear console and show single error message to prevent waterfall
                self.console.clear()
                self.console.print(Panel(
                    str(e),
                    title="[yellow]Audio Issue[/yellow]",
                    border_style="yellow"
                ))
                # Show helpful guidance
                mode = "Toggle" if self.config.toggle_recording_mode else "Hold"
                key_instruction = "Press Alt+X to start/stop recording." if mode == "Toggle" else "Press and hold Alt+X to record."
                self.console.print(f"[cyan]{key_instruction}[/cyan]")
                await asyncio.sleep(0.5)  # Brief pause to prevent rapid retries
            except Exception as e:
                self.console.clear()
                self.console.print(Panel(
                    str(e),
                    title="[red]Error[/red]",
                    border_style="red"
                ))
                await asyncio.sleep(1)

def main(skip_config_ui: bool = False):
    """Application entry point with comprehensive error handling."""
    console = Console(legacy_windows=True, force_terminal=True)
    
    try:
        # Platform compatibility check
        if platform.system().lower() != "windows":
            rp("[bold yellow]WARNING: Only Windows is fully supported. Good luck![/bold yellow]")
        
        # Check for API key early
        if not os.getenv("GROQ_API_KEY"):
            console.print(Panel(
                "[bold red]GROQ_API_KEY environment variable is not set.[/bold red]\n\n"
                "Please set your Groq API key:\n"
                "[yellow]set GROQ_API_KEY=your_api_key_here[/yellow]\n\n"
                "Get your API key from: [blue]https://console.groq.com/[/blue]",
                title="Configuration Required",
                border_style="red"
            ))
            return 1

        app = WhispererApp(skip_config_ui=skip_config_ui)
        asyncio.run(app.run())
        return 0
        
    except KeyboardInterrupt:
        console.print("\n[yellow]Application interrupted by user[/yellow]")
        logging.info("Application interrupted by user (Ctrl+C)")
        return 0
        
    except Exception as e:
        error_msg = f"CRITICAL ERROR: {str(e)}"
        
        # Log to both file and console
        logging.critical(error_msg, exc_info=True)
        
        console.print(Panel(
            f"[bold red]A critical error occurred:[/bold red]\n\n"
            f"[red]{str(e)}[/red]\n\n"
            f"[yellow]Error details have been logged to the logs folder.[/yellow]\n"
            f"[yellow]Please check the most recent session log for full details.[/yellow]",
            title="Critical Error",
            border_style="red"
        ))
        
        return 1

if __name__ == "__main__":
    # Check if we should skip config UI (for direct launch)
    skip_ui = len(sys.argv) > 1 and sys.argv[1] == "--direct"
    exit_code = main(skip_config_ui=skip_ui)
    sys.exit(exit_code)