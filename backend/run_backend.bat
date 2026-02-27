@echo off
echo ============================================================
echo Starting LazyIntern Backend (FastAPI)
echo ============================================================
echo.
echo Backend will run on: http://localhost:8000
echo Health check: http://localhost:8000/health
echo.
echo Press Ctrl+C to stop
echo ============================================================
echo.

python -m uvicorn api.app:app --host 0.0.0.0 --port 8000 --reload
