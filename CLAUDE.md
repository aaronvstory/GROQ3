# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Windows-based voice transcription application called "Groq Whisperer" that uses Groq's Whisper API to convert speech to text. The application features real-time audio visualization, VPN support, and an interactive configuration interface.

## Common Development Commands

### Running the Application
```bash
# Main launcher (checks dependencies and runs app)
groq3new.bat

# Direct launcher (bypasses config UI for auto-startup)
groq3new-direct.bat

# Direct execution with config UI
python groq3new.py

# Direct execution bypassing config UI
python groq3new.py --direct
```

### Installing Dependencies
```bash
# Install from requirements.txt (preferred - handles UV fallback to pip)
pip install -r requirements.txt

# Using UV package manager (faster, if available)
uv pip install -r requirements.txt

# For PyAudio issues on Windows, you may need:
pip install --global-option="build_ext" pyaudio
```

### Environment Setup
- Set `GROQ_API_KEY` environment variable before running
- Python 3.8+ required
- Windows is the primary supported platform
- Virtual environment is auto-created in `venv/` directory by launchers

## Architecture Overview

### Core Components

**Main Application (`groq3new.py:541-663`)**
- `WhispererApp` - Main orchestrator class that manages the application lifecycle
- Handles initialization, configuration UI, and the main record-transcribe loop

**Audio Processing (`groq3new.py:364-523`)**
- `AudioProcessor` - Manages microphone input, VAD (Voice Activity Detection), and real-time visualization
- Uses PyAudio for audio capture and webrtcvad for speech detection
- Auto-calibrates noise thresholds and provides visual feedback

**Configuration System (`groq3new.py:150-320`)**
- `Config` dataclass - Single source of truth for all settings
- Handles migration from legacy JSON to INI format
- Saves/loads from `config.ini` with organized sections

**User Interface (`groq3new.py:191-363`)**
- `SettingsUI` - Interactive configuration panel with Rich library
- `AudioLevelVisualizer` - Real-time audio level display with color coding
- Arrow key navigation, live updates

**Transcription Service (`groq3new.py:524-539`)**
- `TranscriptionService` - Handles Groq API communication
- Async transcription with retry logic
- Uses whisper-large-v3 model

### Key Features Architecture

**Voice Activity Detection Flow:**
1. Audio capture in 20ms chunks
2. VAD analysis for speech detection
3. Real-time visualization and feedback
4. Automatic recording termination

**Configuration Management:**
- Dataclass-based config with automatic migration from JSON to INI
- Interactive UI for runtime configuration changes
- Persistent storage in INI format with logical sections (VPN, Recording, Interface)
- Separate console and file logging levels

**Error Handling Strategy:**
- Custom exceptions for different error types
- Retry logic for audio system initialization
- Graceful degradation for non-critical features

## File Structure

- `groq3new.py` - Main application (~800 lines)
- `groq3new.bat` - Windows launcher script with config UI
- `groq3new-direct.bat` - Direct launcher bypassing config UI
- `requirements.txt` - Python dependencies
- `config.ini` - Application configuration in INI format
- `logs/` - Session and chat logs with timestamps
- `ovpns/` - VPN configuration files
- `venv/` - Virtual environment (auto-created)
- Sound files: `start_click_quiet.wav`, `complete_chime_quiet.wav`

## Development Notes

### Audio System
- Uses 16kHz sample rate (optimal for Whisper)
- VAD aggressiveness levels 0-3 (3 most aggressive)
- Automatic noise threshold calibration
- PyAudio retry logic for reliability

### Configuration System
- All settings defined in `Config` dataclass
- Automatic migration from legacy JSON to INI format
- INI format with sections: VPN, Recording, Interface
- Separate console and file logging levels (console defaults to WARNING)
- Type validation on load with proper error handling

### UI/UX Patterns
- Rich library for terminal UI
- Live updates with async refresh
- Color-coded feedback (blue/green/yellow/red)
- Keyboard shortcuts: Alt+X (record), Alt+T (toggle mode), Alt+Q (quit)

### VPN Integration
- Optional OpenVPN support
- Automatic executable discovery
- Connection verification before startup
- Secure API communication path

### Testing Approach
No formal test framework is configured. Testing is primarily:
- Manual testing via the interactive UI
- Network connectivity tests in settings
- Microphone calibration verification
- Audio level monitoring during recording

### Development Guidelines

**Code Organization:**
- Single-file architecture in `groq3new.py` (~1000+ lines)
- Configuration uses dataclass pattern with automatic INI file persistence
- Rich library for all UI components and formatting
- Async/await pattern for main application flow

**Key Development Patterns:**
- Exception handling with custom exception classes for different error types
- Logging with separate console/file levels (console defaults to WARNING)
- Configuration migration system (JSON to INI format)
- Service initialization pattern: Config → Audio → Transcription → UI

**Working with Audio:**
- All audio processing goes through `AudioProcessor` class
- VAD (Voice Activity Detection) is core to recording functionality
- Audio calibration is automatic but can be manually triggered
- Uses PyAudio with retry logic for Windows compatibility

**Configuration System:**
- `Config` dataclass is the single source of truth
- INI format with sections: VPN, Recording, Interface
- Auto-migration from legacy JSON format
- Settings persist immediately when changed through UI

**UI/UX Standards:**
- All user output uses Rich library formatting
- Color coding: blue (info), green (success), yellow (warning), red (error)
- Keyboard shortcuts are globally registered with the `keyboard` library
- Real-time updates use async refresh patterns