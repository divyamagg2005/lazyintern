@echo off
REM Send All Pending Emails and Cleanup Database
REM This script helps you send pending emails and then clean the database

echo ============================================================
echo LazyIntern - Send Pending Emails and Cleanup Database
echo ============================================================
echo.
echo This will help you:
echo 1. Send all pending approved emails
echo 2. Clean up the database to start fresh
echo.
echo ============================================================
echo.

:menu
echo What would you like to do?
echo.
echo 1. Send all pending emails (respects spacing and limits)
echo 2. Cleanup database (DELETE ALL DATA - use after sending emails)
echo 3. Do both (send emails first, then cleanup)
echo 4. Exit
echo.
set /p choice="Enter your choice (1-4): "

if "%choice%"=="1" goto send_emails
if "%choice%"=="2" goto cleanup
if "%choice%"=="3" goto both
if "%choice%"=="4" goto exit
echo Invalid choice. Please try again.
echo.
goto menu

:send_emails
echo.
echo ============================================================
echo Sending all pending emails...
echo ============================================================
cd backend
python send_all_pending_emails.py
cd ..
echo.
pause
goto menu

:cleanup
echo.
echo ============================================================
echo Cleaning up database...
echo ============================================================
cd backend
python cleanup_all_data.py
cd ..
echo.
pause
goto menu

:both
echo.
echo ============================================================
echo Step 1: Sending all pending emails...
echo ============================================================
cd backend
python send_all_pending_emails.py
echo.
echo ============================================================
echo Step 2: Cleaning up database...
echo ============================================================
python cleanup_all_data.py
cd ..
echo.
pause
goto menu

:exit
echo.
echo Goodbye!
timeout /t 2 >nul
