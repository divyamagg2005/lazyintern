@echo off
echo ============================================================
echo Running LazyIntern Pipeline Cycle
echo ============================================================
echo.
echo This will:
echo   1. Discover internships from job boards
echo   2. Score and validate emails
echo   3. Generate personalized emails
echo   4. Send approval SMS
echo   5. Process approved emails
echo.
echo ============================================================
echo.

python -m scheduler.cycle_manager --once

echo.
echo ============================================================
echo Cycle complete! Check Supabase for results.
echo ============================================================
pause
