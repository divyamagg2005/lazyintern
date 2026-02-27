@echo off
cls
echo ============================================================
echo LazyIntern - Automated Internship Outreach Pipeline
echo ============================================================
echo.
echo What would you like to do?
echo.
echo 1. Start Backend (FastAPI server)
echo 2. Run One Pipeline Cycle
echo 3. Start Dashboard
echo 4. Generate Gmail Token
echo 5. Setup Database Schema
echo 6. View Documentation
echo 7. Exit
echo.
echo ============================================================
set /p choice="Enter your choice (1-7): "

if "%choice%"=="1" goto backend
if "%choice%"=="2" goto cycle
if "%choice%"=="3" goto dashboard
if "%choice%"=="4" goto token
if "%choice%"=="5" goto schema
if "%choice%"=="6" goto docs
if "%choice%"=="7" goto end

:backend
echo.
echo Starting Backend...
cd backend
call run_backend.bat
goto end

:cycle
echo.
echo Running Pipeline Cycle...
cd backend
call run_cycle.bat
goto end

:dashboard
echo.
echo Starting Dashboard...
cd dashboard
start cmd /k "npm run dev"
echo Dashboard will open at http://localhost:3000
pause
goto end

:token
echo.
echo Generating Gmail Token...
python generate_gmail_token.py
pause
goto end

:schema
echo.
echo Opening Supabase SQL Editor...
echo.
echo 1. Go to: https://kjnksjxsnennhtwjtkdr.supabase.co
echo 2. Click "SQL Editor"
echo 3. Copy and paste the contents of backend/db/schema.sql
echo 4. Click "Run"
echo.
start https://kjnksjxsnennhtwjtkdr.supabase.co
pause
goto end

:docs
echo.
echo Opening Documentation...
echo.
echo Available guides:
echo - RUN_LAZYINTERN.md - Complete running guide
echo - GMAIL_TOKEN_SETUP.md - Gmail OAuth setup
echo - GMAIL_PUBSUB_SETUP.md - Real-time reply detection
echo - PIPELINE_COMPARISON_REPORT.md - Pipeline overview
echo.
start RUN_LAZYINTERN.md
pause
goto end

:end
echo.
echo Goodbye!
timeout /t 2 >nul
