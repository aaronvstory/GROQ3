# Gemini Project Brief: Groq Whisperer

## 1. Project Summary

This project is a sophisticated, terminal-based voice transcription application named "Groq Whisperer". It captures audio from a microphone, sends it to the Groq API for transcription using the Whisper model, and then displays the result. The application features a rich user interface built with the `rich` library, including a configuration panel, real-time audio visualization, and status updates. It is designed to be launched via a smart batch script (`groq3new.bat`) that calls a Python launcher (`launch.py`), which handles dependency installation within a virtual environment.

## 2. Key Technologies

- **Language:** Python
- **Core API:** Groq API (for Whisper-based transcription)
- **Terminal UI:** `rich`
- **Audio Processing:** `pyaudio` for recording, `numpy` for audio level calculation.
- **User Input:** `keyboard` for global hotkeys.
- **Automation:** `pyautogui` and `pyperclip` for auto-pasting the transcription.
- **Networking:** `aiohttp` for asynchronous network checks, `groq` SDK.
- **Environment Management:** `venv` (managed by `launch.py`).

## 3. Project Structure

- `launch.py`: The smart launcher script. It checks for Python, the GROQ_API_KEY, creates a `venv`, installs dependencies from `requirements.txt`, and then executes `groq3new.py`.
- `groq3new.py`: The main application file. It contains all the core logic for the UI (using `rich`), audio recording (`pyaudio`), hotkey handling (`keyboard`), transcription (`groq`), and configuration management.
- `groq3new.bat`: A batch script to easily run the `launch.py` script.
- `requirements.txt`: A list of all necessary Python packages.
- `config.json`: Stores user-configurable settings such as recording thresholds, VPN usage, and UI preferences.
- `README.md`: Detailed user-facing documentation.
- `venv/`: The virtual environment directory, created automatically by the launcher.

## 4. Setup and Execution

The intended way to run the application is by executing the `groq3new.bat` file. This triggers the following automated process:

1.  **Launcher (`launch.py`) starts.**
2.  **Python Version Check:** Ensures Python 3.8+ is installed.
3.  **API Key Check:** Verifies if the `GROQ_API_KEY` environment variable is set. If not, it prompts the user to enter it for the current session.
4.  **Virtual Environment:** Creates a `./venv/` directory if it doesn't exist.
5.  **Dependency Installation:** Installs all packages listed in `requirements.txt` into the virtual environment using `pip`.
6.  **Application Start:** Executes the main application script, `groq3new.py`, using the Python interpreter from the virtual environment.

**To run manually:**
1. Set the `GROQ_API_KEY` environment variable.
2. Run `python launch.py`.

## 5. Key Functionality

- **Real-time Transcription:** Captures voice via microphone and transcribes it using Groq's Whisper API.
- **Recording Modes:** Supports both "toggle" (press to start/stop) and "hold" (press and hold to record) modes, switchable via a hotkey (`Alt+T`).
- **Interactive Configuration Panel:** A `rich`-based UI at startup allows users to configure settings like VPN usage, recording mode, auto-paste, and audio thresholds.
- **Real-time Audio Visualizer:** While recording, it displays a live bar graph of the microphone's audio level, including peak indicators and color-coding for intensity.
- **Auto-Paste:** Automatically copies the transcription to the clipboard and can paste it into the active window.
- **VPN Integration:** Includes logic to manage and connect to an OpenVPN connection for secure API calls.
- **Hotkeys:**
    - `Alt+X`: Start/stop recording.
    - `Alt+T`: Switch recording mode.
    - `Alt+Q`: Quit the application.
