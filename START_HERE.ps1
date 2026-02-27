# LazyIntern - PowerShell Launcher

Clear-Host
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "LazyIntern - Automated Internship Outreach Pipeline" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "What would you like to do?" -ForegroundColor Yellow
Write-Host ""
Write-Host "1. 🚀 Start Full Stack 24/7 (ngrok + Backend + Scheduler + Dashboard)" -ForegroundColor Green
Write-Host "2. Start 24/7 Mode (ngrok + Backend + Scheduler only)"
Write-Host "3. Start Backend Only (FastAPI server)"
Write-Host "4. Run One Pipeline Cycle"
Write-Host "5. Start Dashboard Only"
Write-Host "6. Generate Gmail Token"
Write-Host "7. Setup Database Schema"
Write-Host "8. View Documentation"
Write-Host "9. Exit"
Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan

$choice = Read-Host "Enter your choice (1-9)"

switch ($choice) {
    "1" {
        Write-Host "`nStarting Full Stack 24/7..." -ForegroundColor Green
        & ".\RUN_FULL_STACK.ps1"
    }
    "2" {
        Write-Host "`nStarting 24/7 Mode..." -ForegroundColor Green
        & ".\RUN_24_7.ps1"
    }
    "3" {
        Write-Host "`nStarting Backend..." -ForegroundColor Green
        Set-Location backend
        python -m uvicorn api.app:app --host 0.0.0.0 --port 8000 --reload
    }
    "4" {
        Write-Host "`nRunning Pipeline Cycle..." -ForegroundColor Green
        Set-Location backend
        python -m scheduler.cycle_manager --once
        Write-Host "`nCycle complete! Check Supabase for results." -ForegroundColor Green
        Read-Host "Press Enter to continue"
    }
    "5" {
        Write-Host "`nStarting Dashboard..." -ForegroundColor Green
        Set-Location dashboard
        Start-Process powershell -ArgumentList "-NoExit", "-Command", "npm run dev"
        Write-Host "Dashboard will open at http://localhost:3000" -ForegroundColor Green
        Read-Host "Press Enter to continue"
    }
    "6" {
        Write-Host "`nGenerating Gmail Token..." -ForegroundColor Green
        python generate_gmail_token.py
        Read-Host "Press Enter to continue"
    }
    "7" {
        Write-Host "`nOpening Supabase SQL Editor..." -ForegroundColor Green
        Write-Host ""
        Write-Host "1. Go to: https://kjnksjxsnennhtwjtkdr.supabase.co"
        Write-Host "2. Click 'SQL Editor'"
        Write-Host "3. Copy and paste the contents of backend/db/schema.sql"
        Write-Host "4. Click 'Run'"
        Write-Host ""
        Start-Process "https://kjnksjxsnennhtwjtkdr.supabase.co"
        Read-Host "Press Enter to continue"
    }
    "8" {
        Write-Host "`nOpening Documentation..." -ForegroundColor Green
        Write-Host ""
        Write-Host "Available guides:"
        Write-Host "- SETUP_24_7.md - 24/7 operation guide"
        Write-Host "- QUICK_START.md - Quick reference"
        Write-Host "- RUN_LAZYINTERN.md - Complete running guide"
        Write-Host "- SETUP_CHECKLIST.md - Setup checklist"
        Write-Host ""
        Start-Process "SETUP_24_7.md"
        Read-Host "Press Enter to continue"
    }
    "9" {
        Write-Host "`nGoodbye!" -ForegroundColor Green
        Start-Sleep -Seconds 1
    }
    default {
        Write-Host "`nInvalid choice. Please run the script again." -ForegroundColor Red
        Read-Host "Press Enter to exit"
    }
}
