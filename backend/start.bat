@echo off
REM Quick start script for LazyIntern backend (Windows)

echo 🚀 Starting LazyIntern Backend...
echo.

REM Activate virtual environment
if exist ".venv\Scripts\activate.bat" (
    call .venv\Scripts\activate.bat
    echo ✓ Virtual environment activated
) else (
    echo ✗ Virtual environment not found. Run: python -m venv .venv
    exit /b 1
)

REM Check if .env exists
if not exist ".env" (
    echo ✗ .env file not found. Copy .env.example to .env and fill in your API keys
    exit /b 1
)

echo ✓ Environment file found
echo.

REM Run setup verification
echo Running setup verification...
python test_setup.py

if errorlevel 1 (
    echo.
    echo ⚠️  Setup verification failed. Please fix the issues above.
    exit /b 1
)

echo.
echo ✓ Setup verification passed
echo.
echo Starting API server on http://localhost:8000
echo Press Ctrl+C to stop
echo.

REM Start the API server
python -m uvicorn api.app:app --reload --port 8000
