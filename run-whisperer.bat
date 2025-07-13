@echo off
REM Groq Whisperer - Improved Launcher
REM Changes to the directory where the script is located and runs the application

echo.
echo ================================================
echo   🎙️ Groq Whisperer - Voice Transcription 🎙️
echo ================================================
echo.
echo Starting Groq Whisperer...
echo (Hold Ctrl+C to quit)
echo.

REM Change to the directory containing this batch file
cd /d "%~dp0"

REM Run the Python launcher with unbuffered output
python -u launch.py

REM Check the exit code
if %errorlevel% neq 0 (
    echo.
    echo ================================================
    echo   ❌ Application exited with an error
    echo ================================================
    echo.
    echo Common solutions:
    echo   1. Ensure Python 3.8+ is installed
    echo   2. Install requirements: pip install -r requirements.txt
    echo   3. Set GROQ_API_KEY environment variable
    echo   4. Run as administrator if needed
    echo.
    pause
    exit /b %errorlevel%
)

echo.
echo ================================================
echo   ✅ Application closed successfully
echo ================================================
echo Thanks for using Groq Whisperer!
echo.
pause 