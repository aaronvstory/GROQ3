@echo off
REM Groq Whisperer - Direct Launch (No Configuration UI)
REM This launcher starts transcribing immediately in the background

REM Change to the directory containing this batch file
cd /d "%~dp0"

REM Check if Python is available
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.8+ and try again
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
    exit /b 1
)

REM Check dependencies only if packages seem missing (silently)
python -c "import groq, rich, keyboard" >nul 2>&1
if %errorlevel% neq 0 (
    uv --version >nul 2>&1
    if %errorlevel% equ 0 (
        if exist "requirements.txt" (
            uv pip install -r requirements.txt --upgrade --quiet >nul 2>&1
        )
    ) else (
        if exist "requirements.txt" (
            pip install -r requirements.txt --upgrade --quiet >nul 2>&1
        )
    )
)

REM Run the application in direct mode (bypass config UI)
echo Starting Groq Whisperer (Direct Mode)...
python -u groq3new.py --direct

REM Always pause to prevent shell from closing
echo.
if %errorlevel% neq 0 (
    echo [ERROR] Groq Whisperer exited with error code %errorlevel%
    echo Check the logs folder for error details
) else (
    echo Groq Whisperer closed successfully
)
echo.
echo Press any key to close this window...
pause