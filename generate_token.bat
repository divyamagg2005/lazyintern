@echo off
echo ============================================================
echo Gmail Token Generator for LazyIntern
echo ============================================================
echo.
echo This will generate your Gmail OAuth token.
echo A browser window will open - log in and click Allow.
echo.
pause

python generate_gmail_token.py

echo.
echo ============================================================
pause
