# Changelog

All notable changes to Groq Whisperer will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [3.0.0] - 2025-07-13

### 🚀 Major Release - Complete Architecture Rewrite

This release represents a complete rewrite of the application with significant improvements across all areas.

### ✨ Added

#### Core Features
- **Real-time Audio Visualizer** - Live audio level display with color-coded feedback and peak indicators
- **Interactive Configuration Panel** - Rich terminal UI with arrow key navigation and live updates
- **Dual Recording Modes** - Toggle mode (press to start/stop) and Hold mode (press and hold)
- **Voice Activity Detection (VAD)** - Intelligent speech detection using WebRTC VAD
- **Auto-calibration** - Dynamic microphone calibration and noise threshold adaptation
- **Session Logging** - Comprehensive logging with separate console and file log levels

#### User Interface Enhancements
- **Rich Terminal UI** - Beautiful, colorful interface using the Rich library
- **Progress Indicators** - Visual feedback for all operations and network tests
- **Audio Level History** - Mini-graph showing recent audio activity
- **Status Icons** - Visual indicators for recording, listening, and quiet states
- **Enhanced Error Messages** - User-friendly error reporting with troubleshooting hints

#### Advanced Configuration
- **INI Configuration Format** - Organized sections for VPN, Recording, and Interface settings
- **Automatic Config Migration** - Seamless upgrade from legacy JSON configuration
- **Separate Log Levels** - Independent console and file logging levels
- **Runtime Configuration** - Settings can be changed without restarting the application
- **Network Connectivity Tests** - Pre-flight checks for API and internet connectivity

#### VPN Integration
- **OpenVPN Support** - Built-in VPN connection management
- **Automatic VPN Discovery** - Finds OpenVPN executable automatically
- **Connection Verification** - Validates VPN connection before starting
- **Secure API Communication** - Routes API calls through VPN when enabled

#### Audio Processing
- **16kHz Sample Rate** - Optimized for Whisper model performance
- **Configurable VAD Aggressiveness** - Adjustable speech detection sensitivity (0-3)
- **Intelligent Noise Reduction** - Dynamic noise floor adaptation
- **Audio Level Smoothing** - Reduces visual noise in audio visualizer
- **Multiple Audio Device Support** - Automatic fallback to available devices

#### Developer Experience
- **Comprehensive Documentation** - Updated README, CLAUDE.md, and inline documentation
- **Smart Launchers** - Automated batch scripts with dependency management
- **UV Package Manager Support** - Fast dependency installation with pip fallback
- **Error Recovery** - Graceful handling of audio system failures
- **Development Guidelines** - Clear patterns for future development

### 🔧 Technical Improvements

#### Architecture
- **Async/Await Pattern** - Modern asynchronous programming throughout
- **Service-Oriented Design** - Clear separation of concerns with dedicated service classes
- **Dataclass Configuration** - Type-safe configuration management
- **Exception Hierarchy** - Custom exceptions for different error types
- **Modular Components** - AudioProcessor, TranscriptionService, SettingsUI separation

#### Performance
- **Optimized Audio Processing** - Reduced latency and improved responsiveness
- **Efficient Memory Usage** - Better handling of audio buffers and cleanup
- **Fast Startup** - Optimized initialization sequence
- **Background Processing** - Non-blocking audio processing and transcription

#### Security & Privacy
- **Environment Variable Security** - API keys stored in environment variables
- **Temporary File Cleanup** - All temporary audio files automatically removed
- **No Persistent Audio Storage** - Audio data never permanently saved
- **VPN Support** - Secure API communication options

### 🐛 Bug Fixes
- **Audio Device Detection** - Improved reliability of microphone detection
- **PyAudio Compatibility** - Better handling of Windows audio system quirks
- **Memory Leaks** - Fixed audio buffer and processing memory issues
- **Keyboard Hotkeys** - More reliable global hotkey registration
- **Configuration Persistence** - Settings now save correctly across sessions

### 📦 Dependencies
- **Added**: `rich>=12.0.0,<14.0.0` - Terminal UI library
- **Added**: `webrtcvad-wheels` - Voice Activity Detection
- **Added**: `numpy>=1.24.0,<2.3.0` - Audio processing (numba compatible)
- **Updated**: All dependencies to latest compatible versions
- **Improved**: Dependency management with UV package manager support

### 🔄 Breaking Changes
- **Configuration Format** - Migrated from JSON to INI format (automatic migration)
- **Command Line Interface** - New `--direct` flag for bypassing configuration UI
- **Audio Processing** - Complete rewrite of audio capture and processing
- **File Structure** - Reorganized logs into dedicated directory with timestamps

### 📝 Documentation
- **README.md** - Complete rewrite with comprehensive feature documentation
- **CLAUDE.md** - Added development guidelines and architecture overview
- **CHANGELOG.md** - New versioned changelog following semantic versioning
- **Inline Documentation** - Comprehensive docstrings and comments throughout code

### 🚧 Migration Notes

#### From v2.x to v3.0
1. **Configuration**: Existing `config.json` files will be automatically migrated to `config.ini` format
2. **Dependencies**: Run the launcher scripts to automatically install new dependencies
3. **API Key**: Ensure `GROQ_API_KEY` environment variable is set
4. **Audio Setup**: First run will guide through microphone calibration

#### Removed Features
- **Legacy JSON Configuration** - Replaced with INI format (automatic migration)
- **Simple Audio Processing** - Replaced with advanced VAD-based system
- **Basic Terminal Output** - Replaced with Rich library UI

---

## [2.x] - Previous Versions

### [2.1.0] - 2025-07-12
- Enhanced UI with basic audio visualization
- Improved error handling and logging
- Added VPN support framework
- Configuration improvements

### [2.0.0] - 2025-07-11
- Major rewrite with modular architecture
- Added configuration system
- Improved audio processing
- Enhanced user interface

---

## [1.x] - Initial Versions

### [1.0.0] - 2025-07-10
- Initial release
- Basic voice transcription functionality
- Simple terminal interface
- Groq API integration

---

## 🔮 Upcoming Features (Roadmap)

### v3.1.0 (Planned)
- **Multi-language Support** - Support for languages beyond English
- **Custom Models** - Support for different Whisper model variants
- **Batch Processing** - Process multiple audio files
- **Export Options** - Save transcriptions to various formats

### v3.2.0 (Planned)
- **GUI Interface** - Optional graphical interface alongside terminal UI
- **Cloud Storage Integration** - Save transcriptions to cloud services
- **Team Features** - Shared configurations and transcriptions
- **Advanced Analytics** - Usage statistics and performance metrics

### Future Considerations
- **Mobile Support** - Android/iOS companion apps
- **Real-time Collaboration** - Multi-user transcription sessions
- **AI Enhancements** - Post-processing with additional AI models
- **Enterprise Features** - SSO, audit logs, compliance features

---

## 📊 Version Comparison

| Feature | v1.x | v2.x | v3.0 |
|---------|------|------|------|
| Terminal UI | Basic | Improved | Rich/Advanced |
| Audio Visualization | ❌ | Basic | Real-time with colors |
| Configuration | ❌ | JSON | INI with migration |
| VPN Support | ❌ | Basic | Full integration |
| Voice Activity Detection | ❌ | ❌ | WebRTC VAD |
| Auto-calibration | ❌ | ❌ | ✅ |
| Session Logging | ❌ | Basic | Comprehensive |
| Async Processing | ❌ | Partial | Full async/await |
| Error Recovery | Basic | Improved | Advanced |
| Documentation | Minimal | Good | Comprehensive |

---

**Note**: This changelog follows [semantic versioning](https://semver.org/) principles:
- **MAJOR** version for incompatible API changes
- **MINOR** version for backwards-compatible functionality additions  
- **PATCH** version for backwards-compatible bug fixes