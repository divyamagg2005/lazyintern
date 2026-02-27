#!/usr/bin/env python3
"""
Quick setup verification script.
Run this after setting up .env to check if all integrations are configured.
"""

from __future__ import annotations

import sys
from pathlib import Path

# Color codes for terminal output
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
RESET = "\033[0m"


def test_env_file():
    """Check if .env file exists."""
    env_path = Path(__file__).parent / ".env"
    if env_path.exists():
        print(f"{GREEN}✓{RESET} .env file found")
        return True
    else:
        print(f"{RED}✗{RESET} .env file not found - copy .env.example to .env")
        return False


def test_supabase():
    """Test Supabase connection."""
    try:
        from core.supabase_db import db
        usage = db.get_or_create_daily_usage()
        print(f"{GREEN}✓{RESET} Supabase connected (emails: {usage.emails_sent}/{usage.daily_limit})")
        return True
    except Exception as e:
        print(f"{RED}✗{RESET} Supabase failed: {e}")
        return False


def test_groq():
    """Test Groq API key."""
    try:
        from core.config import settings
        if settings.groq_api_key:
            print(f"{GREEN}✓{RESET} Groq API key configured")
            return True
        else:
            print(f"{YELLOW}⚠{RESET} Groq API key not set (will use fallback templates)")
            return False
    except Exception as e:
        print(f"{RED}✗{RESET} Groq config failed: {e}")
        return False


def test_twilio():
    """Test Twilio configuration."""
    try:
        from approval.twilio_sender import _twilio_client
        client = _twilio_client()
        if client:
            print(f"{GREEN}✓{RESET} Twilio configured")
            return True
        else:
            print(f"{YELLOW}⚠{RESET} Twilio not configured (approval will be skipped)")
            return False
    except Exception as e:
        print(f"{RED}✗{RESET} Twilio failed: {e}")
        return False


def test_gmail_oauth():
    """Test Gmail OAuth setup."""
    try:
        from core.config import settings
        oauth_path = Path(settings.gmail_oauth_client_path)
        if oauth_path.exists():
            print(f"{GREEN}✓{RESET} Gmail OAuth client JSON found")
            return True
        else:
            print(f"{RED}✗{RESET} Gmail OAuth client JSON not found at {oauth_path}")
            return False
    except Exception as e:
        print(f"{RED}✗{RESET} Gmail config failed: {e}")
        return False


def test_resume_pdf():
    """Check if resume PDF exists."""
    resume_path = Path(__file__).parent / "data" / "resume.pdf"
    if resume_path.exists():
        print(f"{GREEN}✓{RESET} Resume PDF found")
        return True
    else:
        print(f"{YELLOW}⚠{RESET} Resume PDF not found at {resume_path} (emails will send without attachment)")
        return False


def test_resume_json():
    """Check if resume JSON exists."""
    resume_path = Path(__file__).parent / "data" / "resume.json"
    if resume_path.exists():
        print(f"{GREEN}✓{RESET} Resume JSON found")
        return True
    else:
        print(f"{RED}✗{RESET} Resume JSON not found at {resume_path}")
        return False


def test_hunter():
    """Test Hunter API key."""
    try:
        from core.config import settings
        if settings.hunter_api_key:
            print(f"{GREEN}✓{RESET} Hunter API key configured")
            return True
        else:
            print(f"{YELLOW}⚠{RESET} Hunter API key not set (will only use regex extraction)")
            return False
    except Exception as e:
        print(f"{RED}✗{RESET} Hunter config failed: {e}")
        return False


def main():
    print("\n" + "="*50)
    print("LazyIntern Backend Setup Verification")
    print("="*50 + "\n")
    
    results = {
        "Environment": test_env_file(),
        "Supabase": test_supabase(),
        "Groq API": test_groq(),
        "Twilio": test_twilio(),
        "Gmail OAuth": test_gmail_oauth(),
        "Resume PDF": test_resume_pdf(),
        "Resume JSON": test_resume_json(),
        "Hunter API": test_hunter()
    }
    
    print("\n" + "="*50)
    print("Summary")
    print("="*50 + "\n")
    
    required = ["Environment", "Supabase", "Resume JSON"]
    optional = ["Groq API", "Twilio", "Gmail OAuth", "Resume PDF", "Hunter API"]
    
    required_pass = all(results[k] for k in required)
    optional_count = sum(results[k] for k in optional)
    
    if required_pass:
        print(f"{GREEN}✓{RESET} All required components configured")
    else:
        print(f"{RED}✗{RESET} Some required components missing")
    
    print(f"{GREEN}✓{RESET} {optional_count}/{len(optional)} optional components configured")
    
    print("\n" + "="*50)
    
    if required_pass:
        print(f"\n{GREEN}Ready to run!{RESET}")
        print("\nNext steps:")
        print("1. Start backend: python -m uvicorn api.app:app --reload --port 8000")
        print("2. Test one cycle: python -m scheduler.cycle_manager --once")
        print("3. Open dashboard: http://localhost:3000")
    else:
        print(f"\n{RED}Setup incomplete{RESET}")
        print("\nPlease fix the issues above before running.")
        print("See backend/API_SETUP_GUIDE.md for detailed instructions.")
    
    print()
    return 0 if required_pass else 1


if __name__ == "__main__":
    sys.exit(main())
