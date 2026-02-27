@echo off
echo ========================================
echo    LazyIntern - Starting System
echo ========================================
echo.

REM Check if .env exists in backend folder
if not exist "backend\.env" (
    echo ERROR: .env file not found in backend folder!
    echo.
    echo Please create backend/.env with your API keys.
    echo You can copy from .env.example:
    echo   copy backend\.env.example backend\.env
    echo   notepad backend\.env
    pause
    exit /b 1
)

REM Check if node_modules exists
if not exist "dashboard\node_modules" (
    echo ERROR: Node modules not found!
    echo Please run: cd dashboard ^&^& npm install
    pause
    exit /b 1
)

echo ========================================
echo    IMPORTANT: Start ngrok first!
echo ========================================
echo.
echo Before continuing, make sure ngrok is running:
echo   1. Open a new terminal
echo   2. Run: ngrok http 8000
echo   3. Copy the HTTPS URL
echo   4. Add to backend/.env as PUBLIC_BASE_URL
echo   5. Configure Twilio webhook with that URL
echo.
echo Press any key when ngrok is ready...
pause >nul

echo.
echo Starting Backend API...
start "LazyIntern Backend" cmd /k "cd backend && python -m uvicorn api.app:app --reload --port 8000"

timeout /t 3 /nobreak >nul

echo Starting Frontend Dashboard...
start "LazyIntern Dashboard" cmd /k "cd dashboard && npm run dev"

timeout /t 2 /nobreak >nul

echo.
echo ========================================
echo    System Started!
echo ========================================
echo.
echo ngrok:        (should be running in separate terminal)
echo Backend API:  http://localhost:8000
echo Dashboard:    http://localhost:3000
echo.
echo Press any key to open dashboard in browser...
pause >nul

start http://localhost:3000

echo.
echo To run a pipeline cycle, open a new terminal and run:
echo   cd backend
echo   python -m scheduler.cycle_manager --once
echo.
echo Press any key to exit...
pause >nul
