# LazyIntern Full Stack 24/7 Setup Script

Clear-Host
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "LazyIntern Full Stack 24/7 Setup" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "This will start the complete LazyIntern stack:" -ForegroundColor Yellow
Write-Host "  1. ngrok tunnel (for Twilio webhooks)" -ForegroundColor White
Write-Host "  2. Backend API (FastAPI server)" -ForegroundColor White
Write-Host "  3. Scheduler (runs cycles every 2 hours)" -ForegroundColor White
Write-Host "  4. Dashboard (Next.js frontend) [OPTIONAL]" -ForegroundColor White
Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

$includeDashboard = Read-Host "Include Dashboard? (Y/N)"
$startDashboard = ($includeDashboard -eq "Y" -or $includeDashboard -eq "y")

Write-Host ""
Write-Host "Ready to start all components?" -ForegroundColor Yellow
$choice = Read-Host "(Y/N)"

if ($choice -ne "Y" -and $choice -ne "y") {
    Write-Host "Setup cancelled." -ForegroundColor Red
    exit
}

Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "Starting LazyIntern Full Stack..." -ForegroundColor Green
Write-Host "============================================================" -ForegroundColor Cyan

# Terminal 1: ngrok
Write-Host ""
Write-Host "[1/4] Starting ngrok tunnel..." -ForegroundColor Green
Start-Sleep -Seconds 1
Start-Process powershell -ArgumentList "-NoExit", "-Command", @"
Write-Host '============================================================' -ForegroundColor Cyan
Write-Host 'Terminal 1: ngrok Tunnel' -ForegroundColor Cyan
Write-Host '============================================================' -ForegroundColor Cyan
Write-Host ''
Write-Host 'IMPORTANT: Copy the HTTPS URL below!' -ForegroundColor Yellow
Write-Host 'Example: https://abc123.ngrok-free.dev' -ForegroundColor Yellow
Write-Host ''
Write-Host 'Then update backend/.env:' -ForegroundColor Yellow
Write-Host 'PUBLIC_BASE_URL=`"https://your-url.ngrok-free.dev`"' -ForegroundColor White
Write-Host ''
Write-Host '============================================================' -ForegroundColor Cyan
Write-Host ''
ngrok http 8000
"@

Write-Host "  [OK] ngrok started (Terminal 1)" -ForegroundColor Green
Start-Sleep -Seconds 3

# Terminal 2: Backend API
Write-Host ""
Write-Host "[2/4] Starting Backend API..." -ForegroundColor Green
Start-Sleep -Seconds 1
Start-Process powershell -ArgumentList "-NoExit", "-Command", @"
Write-Host '============================================================' -ForegroundColor Cyan
Write-Host 'Terminal 2: Backend API (FastAPI)' -ForegroundColor Cyan
Write-Host '============================================================' -ForegroundColor Cyan
Write-Host ''
Write-Host 'Running on: http://localhost:8000' -ForegroundColor Green
Write-Host 'Health check: http://localhost:8000/health' -ForegroundColor Green
Write-Host 'API docs: http://localhost:8000/docs' -ForegroundColor Green
Write-Host ''
Write-Host 'Handles:' -ForegroundColor Yellow
Write-Host '  - Twilio webhooks (SMS approval)' -ForegroundColor White
Write-Host '  - Gmail webhooks (reply detection)' -ForegroundColor White
Write-Host '  - Dashboard API endpoints' -ForegroundColor White
Write-Host ''
Write-Host '============================================================' -ForegroundColor Cyan
Write-Host ''
Set-Location backend
python -m uvicorn api.app:app --host 0.0.0.0 --port 8000 --reload
"@

Write-Host "  [OK] Backend API started (Terminal 2)" -ForegroundColor Green
Start-Sleep -Seconds 3

# Terminal 3: Scheduler
Write-Host ""
Write-Host "[3/4] Starting 24/7 Scheduler..." -ForegroundColor Green
Start-Sleep -Seconds 1
Start-Process powershell -ArgumentList "-NoExit", "-Command", @"
Write-Host '============================================================' -ForegroundColor Cyan
Write-Host 'Terminal 3: Pipeline Scheduler' -ForegroundColor Cyan
Write-Host '============================================================' -ForegroundColor Cyan
Write-Host ''
Write-Host 'Runs pipeline automatically every 2 hours' -ForegroundColor Green
Write-Host ''
Write-Host 'What it does:' -ForegroundColor Yellow
Write-Host '  1. Discovers internships from job boards' -ForegroundColor White
Write-Host '  2. Scores and validates emails' -ForegroundColor White
Write-Host '  3. Generates personalized emails with AI' -ForegroundColor White
Write-Host '  4. Sends approval SMS' -ForegroundColor White
Write-Host '  5. Sends approved emails' -ForegroundColor White
Write-Host '  6. Processes replies and follow-ups' -ForegroundColor White
Write-Host ''
Write-Host 'Press Ctrl+C to stop' -ForegroundColor Yellow
Write-Host ''
Write-Host '============================================================' -ForegroundColor Cyan
Write-Host ''
Set-Location backend
python run_scheduler_24_7.py
"@

Write-Host "  [OK] Scheduler started (Terminal 3)" -ForegroundColor Green
Start-Sleep -Seconds 2

# Terminal 4: Dashboard (Optional)
if ($startDashboard) {
    Write-Host ""
    Write-Host "[4/4] Starting Dashboard..." -ForegroundColor Green
    Start-Sleep -Seconds 1
    Start-Process powershell -ArgumentList "-NoExit", "-Command", @"
Write-Host '============================================================' -ForegroundColor Cyan
Write-Host 'Terminal 4: Dashboard (Next.js)' -ForegroundColor Cyan
Write-Host '============================================================' -ForegroundColor Cyan
Write-Host ''
Write-Host 'Dashboard URL: http://localhost:3000' -ForegroundColor Green
Write-Host ''
Write-Host 'Shows real-time metrics:' -ForegroundColor Yellow
Write-Host '  - Internships discovered' -ForegroundColor White
Write-Host '  - Emails sent/pending' -ForegroundColor White
Write-Host '  - Reply rates' -ForegroundColor White
Write-Host '  - API usage' -ForegroundColor White
Write-Host '  - Pipeline funnel' -ForegroundColor White
Write-Host ''
Write-Host 'Auto-refreshes every 10 seconds' -ForegroundColor Green
Write-Host ''
Write-Host '============================================================' -ForegroundColor Cyan
Write-Host ''
Set-Location dashboard
npm run dev
"@
    Write-Host "  [OK] Dashboard started (Terminal 4)" -ForegroundColor Green
    Start-Sleep -Seconds 2
} else {
    Write-Host ""
    Write-Host "[4/4] Dashboard skipped (you can start it later)" -ForegroundColor Yellow
}

# Summary
Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "LazyIntern Full Stack is Running! 🚀" -ForegroundColor Green
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "Active Components:" -ForegroundColor Yellow
Write-Host "  [OK] Terminal 1: ngrok tunnel" -ForegroundColor Green
Write-Host "  [OK] Terminal 2: Backend API (port 8000)" -ForegroundColor Green
Write-Host "  [OK] Terminal 3: Scheduler (every 2 hours)" -ForegroundColor Green
if ($startDashboard) {
    Write-Host "  [OK] Terminal 4: Dashboard (port 3000)" -ForegroundColor Green
}

Write-Host ""
Write-Host "IMPORTANT - Next Steps:" -ForegroundColor Yellow
Write-Host ""
Write-Host "1. Go to Terminal 1 (ngrok)" -ForegroundColor White
Write-Host "   Copy the HTTPS URL (e.g., https://abc123.ngrok-free.dev)" -ForegroundColor White
Write-Host ""
Write-Host "2. Update backend/.env file:" -ForegroundColor White
Write-Host "   PUBLIC_BASE_URL=`"https://your-ngrok-url.ngrok-free.dev`"" -ForegroundColor White
Write-Host ""
Write-Host "3. Restart Terminal 2 (Backend API):" -ForegroundColor White
Write-Host "   - Close Terminal 2" -ForegroundColor White
Write-Host "   - Run: cd backend && python -m uvicorn api.app:app --reload" -ForegroundColor White
Write-Host ""
Write-Host "4. Wait for approval SMS when internships are found" -ForegroundColor White
Write-Host "   Reply YES to approve, NO to reject" -ForegroundColor White
Write-Host ""

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "Access Points:" -ForegroundColor Yellow
Write-Host "  - Backend API: http://localhost:8000" -ForegroundColor White
Write-Host "  - API Docs: http://localhost:8000/docs" -ForegroundColor White
Write-Host "  - Health Check: http://localhost:8000/health" -ForegroundColor White
if ($startDashboard) {
    Write-Host "  - Dashboard: http://localhost:3000" -ForegroundColor White
}
Write-Host "  - Supabase: https://kjnksjxsnennhtwjtkdr.supabase.co" -ForegroundColor White
Write-Host ""

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "To Stop Everything:" -ForegroundColor Yellow
Write-Host "  Close all terminal windows (Ctrl+C in each)" -ForegroundColor White
Write-Host ""
Write-Host "To Monitor:" -ForegroundColor Yellow
Write-Host "  - Check Terminal 3 for scheduler logs" -ForegroundColor White
Write-Host "  - Check Supabase for data" -ForegroundColor White
if ($startDashboard) {
    Write-Host "  - Open Dashboard at http://localhost:3000" -ForegroundColor White
}
Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan

Write-Host ""
Read-Host "Press Enter to close this setup window (other terminals will keep running)"
