@echo off
REM ============================================================================
REM LazyIntern - Complete Startup Script
REM Starts: Ngrok, Backend API, Scheduler, and Dashboard
REM ============================================================================

echo.
echo ========================================================================
echo                    LAZYINTERN STARTUP
echo ========================================================================
echo.
echo Starting all services...
echo.

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not found! Please install Python 3.11+
    pause
    exit /b 1
)

REM Check if Node is available
node --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Node.js not found! Please install Node.js
    pause
    exit /b 1
)

REM Check if ngrok is available
ngrok version >nul 2>&1
if errorlevel 1 (
    echo WARNING: ngrok not found! Twilio webhook won't work.
    echo Install from: https://ngrok.com/download
    echo.
)

echo ========================================================================
echo STEP 1: Starting Ngrok (for Twilio webhook)
echo ========================================================================
echo.

REM Start ngrok in a new window
start "Ngrok - Twilio Webhook" cmd /k "ngrok http 8000 && echo Ngrok stopped. Press any key to close... && pause >nul"

REM Wait for ngrok to start
timeout /t 5 /nobreak >nul

echo Ngrok started! Check the window for your public URL.
echo Update Twilio webhook URL if needed.
echo.

echo ========================================================================
echo STEP 2: Starting Backend API (FastAPI on port 8000)
echo ========================================================================
echo.

REM Start FastAPI backend in a new window
start "Backend API - FastAPI" cmd /k "cd backend && python -m uvicorn api.app:app --host 0.0.0.0 --port 8000 --reload && echo API stopped. Press any key to close... && pause >nul"

REM Wait for API to start
timeout /t 5 /nobreak >nul

echo Backend API started on http://localhost:8000
echo.

echo ========================================================================
echo STEP 3: Starting Scheduler (Pipeline runs every 2 hours)
echo ========================================================================
echo.

REM Start scheduler in a new window
start "Scheduler - Pipeline" cmd /k "cd backend && python run_scheduler_24_7.py && echo Scheduler stopped. Press any key to close... && pause >nul"

REM Wait for scheduler to start
timeout /t 3 /nobreak >nul

echo Scheduler started! Pipeline will run every 2 hours.
echo Daily stats reset at midnight UTC.
echo.

echo ========================================================================
echo STEP 4: Starting Dashboard (Next.js on port 3000)
echo ========================================================================
echo.

REM Check if node_modules exists
if not exist "dashboard\node_modules\" (
    echo Installing dashboard dependencies...
    cd dashboard
    call npm install
    cd ..
    echo.
)

REM Start Next.js dashboard in a new window
start "Dashboard - Next.js" cmd /k "cd dashboard && npm run dev && echo Dashboard stopped. Press any key to close... && pause >nul"

REM Wait for dashboard to start
timeout /t 10 /nobreak >nul

echo Dashboard started on http://localhost:3000
echo.

echo ========================================================================
echo                    ALL SERVICES STARTED!
echo ========================================================================
echo.
echo Services running:
echo   1. Ngrok:      Check ngrok window for public URL
echo   2. Backend:    http://localhost:8000
echo   3. Scheduler:  Running in background (every 2 hours)
echo   4. Dashboard:  http://localhost:3000
echo.
echo ========================================================================
echo                    IMPORTANT NOTES
echo ========================================================================
echo.
echo 1. Update Twilio webhook URL with ngrok URL:
echo    https://[your-ngrok-url].ngrok-free.app/twilio/reply
echo.
echo 2. Check scheduler logs for pipeline activity
echo.
echo 3. Dashboard shows real-time stats at http://localhost:3000
echo.
echo 4. To stop all services: Close all windows or press Ctrl+C
echo.
echo ========================================================================
echo                    MONITORING
echo ========================================================================
echo.
echo While you sleep, the system will:
echo   - Scrape job boards every 2 hours
echo   - Extract emails and score leads
echo   - Generate AI drafts via Groq
echo   - Send SMS approvals (up to 15/day)
echo   - Auto-approve drafts after 2 hours
echo   - Send emails (up to 15/day)
echo   - Reset daily limits at midnight UTC
echo.
echo Check these when you wake up:
echo   - Scheduler window: See pipeline activity
echo   - Dashboard: http://localhost:3000
echo   - Supabase: Check database tables
echo   - Phone: Check SMS messages
echo   - Gmail: Check sent emails
echo.
echo ========================================================================
echo.
echo Press any key to open dashboard in browser...
pause >nul

REM Open dashboard in default browser
start http://localhost:3000

echo.
echo Dashboard opened! Keep this window open to monitor status.
echo.
echo To stop all services: Close all windows or press Ctrl+C in each window
echo.
echo ========================================================================
echo                    HAPPY SLEEPING! 😴
echo ========================================================================
echo.
pause
