# LazyIntern 24/7 Setup Script

Clear-Host
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "LazyIntern 24/7 Setup" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "This will start LazyIntern in 24/7 mode with:" -ForegroundColor Yellow
Write-Host "  - Backend API server (for Twilio webhooks)" -ForegroundColor White
Write-Host "  - Automated pipeline cycles every 2 hours" -ForegroundColor White
Write-Host "  - ngrok tunnel (for webhooks)" -ForegroundColor White
Write-Host ""
Write-Host "You need 3 terminal windows running:" -ForegroundColor Yellow
Write-Host "  1. ngrok (for Twilio webhooks)" -ForegroundColor White
Write-Host "  2. Backend API (FastAPI server)" -ForegroundColor White
Write-Host "  3. Scheduler (runs cycles every 2 hours)" -ForegroundColor White
Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

$choice = Read-Host "Ready to start? (Y/N)"

if ($choice -ne "Y" -and $choice -ne "y") {
    Write-Host "Setup cancelled." -ForegroundColor Red
    exit
}

Write-Host ""
Write-Host "Step 1: Starting ngrok..." -ForegroundColor Green
Write-Host "Copy the HTTPS URL and update backend/.env with PUBLIC_BASE_URL" -ForegroundColor Yellow
Start-Sleep -Seconds 2
Start-Process powershell -ArgumentList "-NoExit", "-Command", "Write-Host 'ngrok Tunnel' -ForegroundColor Cyan; Write-Host 'Copy the HTTPS URL (e.g., https://abc123.ngrok-free.dev)' -ForegroundColor Yellow; Write-Host 'Update backend/.env: PUBLIC_BASE_URL=`"https://your-url.ngrok-free.dev`"' -ForegroundColor Yellow; Write-Host ''; ngrok http 8000"

Write-Host ""
Write-Host "Waiting 5 seconds for ngrok to start..." -ForegroundColor Yellow
Start-Sleep -Seconds 5

Write-Host ""
Write-Host "Step 2: Starting Backend API..." -ForegroundColor Green
Start-Sleep -Seconds 2
Start-Process powershell -ArgumentList "-NoExit", "-Command", "Write-Host 'LazyIntern Backend API' -ForegroundColor Cyan; Write-Host 'Running on: http://localhost:8000' -ForegroundColor Green; Write-Host 'Health check: http://localhost:8000/health' -ForegroundColor Green; Write-Host ''; Set-Location backend; python -m uvicorn api.app:app --host 0.0.0.0 --port 8000 --reload"

Write-Host ""
Write-Host "Waiting 5 seconds for backend to start..." -ForegroundColor Yellow
Start-Sleep -Seconds 5

Write-Host ""
Write-Host "Step 3: Starting 24/7 Scheduler..." -ForegroundColor Green
Start-Sleep -Seconds 2
Start-Process powershell -ArgumentList "-NoExit", "-Command", "Write-Host 'LazyIntern 24/7 Scheduler' -ForegroundColor Cyan; Write-Host 'Runs pipeline every 2 hours automatically' -ForegroundColor Green; Write-Host 'Press Ctrl+C to stop' -ForegroundColor Yellow; Write-Host ''; Set-Location backend; python run_scheduler_24_7.py"

Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "LazyIntern is now running 24/7!" -ForegroundColor Green
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "What's running:" -ForegroundColor Yellow
Write-Host "  [OK] ngrok tunnel (Terminal 1)" -ForegroundColor Green
Write-Host "  [OK] Backend API on port 8000 (Terminal 2)" -ForegroundColor Green
Write-Host "  [OK] Scheduler running every 2 hours (Terminal 3)" -ForegroundColor Green
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "  1. Copy ngrok HTTPS URL from Terminal 1" -ForegroundColor White
Write-Host "  2. Update backend/.env: PUBLIC_BASE_URL=`"https://your-url.ngrok-free.dev`"" -ForegroundColor White
Write-Host "  3. Restart Backend API (Terminal 2) if you updated .env" -ForegroundColor White
Write-Host "  4. Wait for approval SMS when internships are found" -ForegroundColor White
Write-Host "  5. Reply YES/NO to approve/reject emails" -ForegroundColor White
Write-Host ""
Write-Host "Monitor progress:" -ForegroundColor Yellow
Write-Host "  - Backend: http://localhost:8000/health" -ForegroundColor White
Write-Host "  - Supabase: https://kjnksjxsnennhtwjtkdr.supabase.co" -ForegroundColor White
Write-Host "  - Logs: Check Terminal 3 (Scheduler)" -ForegroundColor White
Write-Host ""
Write-Host "To stop: Close all 3 terminal windows" -ForegroundColor Yellow
Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan

Read-Host "Press Enter to close this window"
