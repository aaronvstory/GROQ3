# 🎙️ Groq Whisperer v3 - Advanced Voice Transcription

A powerful, Windows-based voice transcription application powered by Groq's Whisper API featuring real-time audio visualization, VPN support, and an intuitive configuration interface.

![Version](https://img.shields.io/badge/version-3.0.0-blue)
![Python](https://img.shields.io/badge/python-3.8+-green)
![Platform](https://img.shields.io/badge/platform-Windows-lightgrey)
![License](https://img.shields.io/badge/license-MIT-blue)

## ✨ Key Features

### 🎯 Core Functionality
- **Real-time Voice Transcription** - Convert speech to text using Groq's advanced Whisper models
- **Dual Recording Modes** - Toggle mode (press to start/stop) or Hold mode (press and hold)
- **Auto-paste Functionality** - Automatically paste transcriptions after copying to clipboard
- **Smart Audio Processing** - Intelligent Voice Activity Detection (VAD) and noise reduction

### 🎨 Enhanced User Interface
- **Rich Terminal UI** - Beautiful, colorful interface with Rich library formatting
- **Interactive Configuration Panel** - Arrow key navigation with live settings updates
- **Real-time Audio Visualizer** - Live audio level bars with color-coded feedback
- **Progress Indicators** - Visual feedback for all operations

### 🔧 Advanced Features
- **VPN Support** - Built-in OpenVPN integration for secure connections
- **Configurable Audio Parameters** - Adjustable noise thresholds, recording durations, and sensitivity
- **Network Connectivity Tests** - Pre-flight checks for API and internet connectivity
- **Comprehensive Logging** - Session and chat logs with configurable levels
- **Auto-calibration** - Intelligent microphone calibration and noise threshold adaptation

### 🚀 Easy Setup
- **Smart Launchers** - Automated batch scripts with dependency management
- **UV Package Manager Support** - Fast dependency installation with fallback to pip
- **Error Handling** - Comprehensive error detection and user-friendly messages
- **First-run Setup** - Guided initial configuration

## 📦 Installation

### Prerequisites
- **Python 3.8+** - Download from [python.org](https://www.python.org/downloads/)
- **GROQ API Key** - Get yours from [Groq Console](https://console.groq.com/)
- **Microphone** - Any working microphone device
- **Optional: OpenVPN** - For VPN features

### Quick Start

1. **Clone the Repository**
   ```bash
   git clone https://github.com/yourusername/groq-whisperer-v3.git
   cd groq-whisperer-v3
   ```

2. **Set Your API Key**
   ```bash
   # Windows Command Prompt
   set GROQ_API_KEY=your_api_key_here
   
   # PowerShell
   $env:GROQ_API_KEY="your_api_key_here"
   ```

3. **Run the Application**
   ```bash
   # Interactive mode with configuration UI
   groq3new.bat
   
   # Direct mode (bypasses config UI)
   groq3new-direct.bat
   ```

The launcher will automatically:
- Check Python installation
- Install required dependencies (using UV or pip)
- Set up the application environment
- Start the voice transcription interface

## 🎮 Usage Guide

### Configuration Interface
1. **First Launch** - Interactive configuration panel appears
2. **Navigation** - Use ↑/↓ arrow keys to browse settings
3. **Toggle Settings** - Press Enter to change boolean options
4. **Network Tests** - Run connectivity tests before starting
5. **Start Application** - Begin voice transcription

### Recording Voice
- **Toggle Mode**: Press `Alt+X` to start recording, press again to stop
- **Hold Mode**: Press and hold `Alt+X` to record, release to stop
- **Real-time Feedback**: Audio visualizer shows current levels with color coding
- **Auto-transcription**: Results appear immediately and copy to clipboard

### Hotkeys
- `Alt+X` - Start/stop recording (mode dependent)
- `Alt+T` - Switch between Toggle and Hold modes
- `Alt+Q` - Quit application
- `Q` or `Esc` - Exit configuration panel

## ⚙️ Configuration Options

### Connection Settings
- **VPN Usage** - Enable/disable VPN connectivity
- **VPN Connection Check** - Verify VPN before starting
- **VPN Verbosity** - Show detailed VPN connection info

### Recording Settings
- **Recording Mode** - Toggle vs Hold-to-Record
- **Max Recording Duration** - Maximum length in seconds (default: 60s)
- **Min Recording Duration** - Minimum length in seconds (default: 0.2s)  
- **Noise Threshold** - Audio sensitivity level (auto-calibrated)

### Interface Settings
- **Auto-paste** - Automatically paste transcriptions
- **Verbose Output** - Show detailed status messages
- **Session Logging** - Enable detailed logging to files
- **Console/File Log Levels** - Separate logging levels for console and files

## 🎨 Audio Visualizer

The real-time audio visualizer provides instant feedback:

### Visual Elements
- **Level Bar** - Current audio intensity with smooth updates
- **Peak Indicator** - Shows maximum recent audio level
- **History Display** - Mini-graph of recent audio activity
- **Status Icons** - 🎤 Recording, 🎧 Listening, 🔇 Quiet

### Color Coding
- **Blue** - Low level audio (quiet background)
- **Green** - Normal recording level (optimal)
- **Yellow** - High level audio (may be loud)
- **Red** - Very high level (potential distortion)

## 🔧 Technical Architecture

### Core Components
- **WhispererApp** - Main application orchestrator
- **AudioProcessor** - Handles microphone input and VAD
- **TranscriptionService** - Manages Groq API communication
- **SettingsUI** - Interactive configuration interface
- **Config** - Centralized configuration management

### Audio Processing
- **16kHz Sample Rate** - Optimized for Whisper model
- **Voice Activity Detection** - WebRTC VAD with configurable aggressiveness
- **Automatic Calibration** - Dynamic noise threshold adaptation
- **Real-time Visualization** - Live audio level monitoring

## 📁 Project Structure

```
groq-whisperer-v3/
├── groq3new.py              # Main application (~1000+ lines)
├── groq3new.bat             # Interactive launcher
├── groq3new-direct.bat      # Direct launcher (no config UI)
├── requirements.txt         # Python dependencies
├── config.ini              # Application configuration
├── CLAUDE.md               # Development guidance
├── CHANGELOG.md            # Version history
├── README.md               # This file
├── logs/                   # Session and chat logs
├── ovpns/                  # VPN configuration files
├── venv/                   # Virtual environment (auto-created)
├── start_click_quiet.wav   # UI sound effects
└── complete_chime_quiet.wav
```

## 🛠️ Development

### Dependencies
- `groq` - Groq API client
- `rich` - Terminal UI library
- `keyboard` - Global hotkey handling
- `pyaudio` - Audio capture
- `webrtcvad-wheels` - Voice Activity Detection
- `numpy` - Audio processing
- `pyautogui` - Auto-paste functionality
- `pyperclip` - Clipboard operations

### Running from Source
```bash
# Install dependencies
pip install -r requirements.txt

# Run with configuration UI
python groq3new.py

# Run directly (bypass config)
python groq3new.py --direct
```

## 🛠️ Troubleshooting

### Common Issues

**Python Not Found**
```bash
# Install Python 3.8+ from python.org
# Ensure Python is added to PATH
```

**PyAudio Installation Fails**
```bash
# Install Microsoft Visual C++ Build Tools
# Or try: pip install --global-option="build_ext" pyaudio
```

**API Key Issues**
```bash
# Set environment variable
set GROQ_API_KEY=your_key_here

# Or create .env file
echo GROQ_API_KEY=your_key_here > .env
```

**Audio Device Issues**
- Check microphone connections and drivers
- Test microphone in Windows Sound settings
- Try running as administrator

### Log Files
- `logs/session_YYYYMMDD_HHMMSS.log` - Session logs
- `logs/chat_YYYYMMDD_HHMMSS.log` - Transcription logs
- Check logs for detailed error information

## 🔒 Security & Privacy

- API keys stored securely in environment variables
- No audio data permanently stored on disk
- VPN support for secure API communication
- All temporary files automatically cleaned up
- Session logs can be disabled in configuration

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📞 Support

If you encounter issues:

1. Check the [troubleshooting section](#troubleshooting)
2. Review log files in the `logs/` directory
3. Ensure all prerequisites are met
4. Verify your GROQ_API_KEY is set correctly
5. Open an issue on GitHub with log details

## 🎉 Acknowledgments

- [Groq](https://groq.com/) for the powerful Whisper API
- [Rich](https://rich.readthedocs.io/) for beautiful terminal UI
- [PyAudio](https://people.csail.mit.edu/hubert/pyaudio/) for audio processing
- [WebRTC VAD](https://webrtc.org/) for voice activity detection
- All contributors and users of this project

---

**Happy transcribing! 🎙️✨**

Built with ❤️ using Groq's Whisper API