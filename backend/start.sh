#!/bin/bash
# Quick start script for LazyIntern backend

echo "🚀 Starting LazyIntern Backend..."
echo ""

# Activate virtual environment
if [ -d ".venv" ]; then
    source .venv/bin/activate
    echo "✓ Virtual environment activated"
else
    echo "✗ Virtual environment not found. Run: python -m venv .venv"
    exit 1
fi

# Check if .env exists
if [ ! -f ".env" ]; then
    echo "✗ .env file not found. Copy .env.example to .env and fill in your API keys"
    exit 1
fi

echo "✓ Environment file found"
echo ""

# Run setup verification
echo "Running setup verification..."
python test_setup.py

if [ $? -ne 0 ]; then
    echo ""
    echo "⚠️  Setup verification failed. Please fix the issues above."
    exit 1
fi

echo ""
echo "✓ Setup verification passed"
echo ""
echo "Starting API server on http://localhost:8000"
echo "Press Ctrl+C to stop"
echo ""

# Start the API server
python -m uvicorn api.app:app --reload --port 8000
