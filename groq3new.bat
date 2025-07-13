@echo off
REM Groq Whisperer - Simple Launcher
echo.
echo ================================================
echo   Groq Whisperer - Voice Transcription
echo ================================================
echo.

REM Change to the directory containing this batch file
cd /d "%~dp0"

REM Check if Python is available
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.8+ and try again
    pause
    exit /b 1
)

REM Check if Groq API key is set
if "%GROQ_API_KEY%"=="" (
    echo.
    echo ERROR: GROQ_API_KEY environment variable is not set.
    echo Please set your Groq API key before running this application.
    echo.
    echo Example: set GROQ_API_KEY=your_api_key_here
    echo.
    pause
    exit /b 1
)

REM Check dependencies only if packages seem missing
python -c "import groq, rich, keyboard" >nul 2>&1
if %errorlevel% neq 0 (
    echo Dependencies missing, installing...
    REM Check if UV is available, fallback to pip if not
    uv --version >nul 2>&1
    if %errorlevel% equ 0 (
        echo Using UV package manager...
        if exist "requirements.txt" (
            uv pip install -r requirements.txt --upgrade --quiet
        )
    ) else (
        echo Using pip...
        if exist "requirements.txt" (
            pip install -r requirements.txt --upgrade --quiet
        )
    )
) else (
    echo Dependencies OK, skipping installation
)

REM Run the application
echo Starting Groq Whisperer...
echo Press Ctrl+C to quit
echo.
python -u groq3new.py

REM Always pause regardless of exit code to prevent shell from closing
echo.
if %errorlevel% neq 0 (
    echo [ERROR] Application exited with error code %errorlevel%
    echo Check the logs folder for error details
) else (
    echo Application closed successfully
)
echo.
echo Press any key to close this window...
pause