# Send All Pending Emails and Cleanup Database
# This script helps you send pending emails and then clean the database

Clear-Host
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "LazyIntern - Send Pending Emails and Cleanup Database" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "This will help you:" -ForegroundColor Yellow
Write-Host "1. Send all pending approved emails"
Write-Host "2. Clean up the database to start fresh"
Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

function Show-Menu {
    Write-Host "What would you like to do?" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "1. 📧 Send all pending emails (respects spacing and limits)" -ForegroundColor Green
    Write-Host "2. 🗑️  Cleanup database (DELETE ALL DATA - use after sending emails)" -ForegroundColor Red
    Write-Host "3. 🔄 Do both (send emails first, then cleanup)" -ForegroundColor Cyan
    Write-Host "4. ❌ Exit"
    Write-Host ""
    Write-Host "============================================================" -ForegroundColor Cyan
}

function Send-PendingEmails {
    Write-Host ""
    Write-Host "============================================================" -ForegroundColor Cyan
    Write-Host "Sending all pending emails..." -ForegroundColor Green
    Write-Host "============================================================" -ForegroundColor Cyan
    Set-Location backend
    python send_all_pending_emails.py
    Set-Location ..
    Write-Host ""
    Read-Host "Press Enter to continue"
}

function Cleanup-Database {
    Write-Host ""
    Write-Host "============================================================" -ForegroundColor Cyan
    Write-Host "Cleaning up database..." -ForegroundColor Red
    Write-Host "============================================================" -ForegroundColor Cyan
    Set-Location backend
    python cleanup_all_data.py
    Set-Location ..
    Write-Host ""
    Read-Host "Press Enter to continue"
}

function Do-Both {
    Write-Host ""
    Write-Host "============================================================" -ForegroundColor Cyan
    Write-Host "Step 1: Sending all pending emails..." -ForegroundColor Green
    Write-Host "============================================================" -ForegroundColor Cyan
    Set-Location backend
    python send_all_pending_emails.py
    
    Write-Host ""
    Write-Host "============================================================" -ForegroundColor Cyan
    Write-Host "Step 2: Cleaning up database..." -ForegroundColor Red
    Write-Host "============================================================" -ForegroundColor Cyan
    python cleanup_all_data.py
    Set-Location ..
    Write-Host ""
    Read-Host "Press Enter to continue"
}

# Main loop
while ($true) {
    Clear-Host
    Write-Host "============================================================" -ForegroundColor Cyan
    Write-Host "LazyIntern - Send Pending Emails and Cleanup Database" -ForegroundColor Cyan
    Write-Host "============================================================" -ForegroundColor Cyan
    Write-Host ""
    
    Show-Menu
    
    $choice = Read-Host "Enter your choice (1-4)"
    
    switch ($choice) {
        "1" {
            Send-PendingEmails
        }
        "2" {
            Cleanup-Database
        }
        "3" {
            Do-Both
        }
        "4" {
            Write-Host ""
            Write-Host "Goodbye!" -ForegroundColor Green
            Start-Sleep -Seconds 1
            exit
        }
        default {
            Write-Host ""
            Write-Host "Invalid choice. Please try again." -ForegroundColor Red
            Start-Sleep -Seconds 2
        }
    }
}
