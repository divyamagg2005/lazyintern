#!/usr/bin/env python3
"""
Comprehensive component testing script.
Tests each part of the pipeline individually.
"""

from __future__ import annotations

import sys
from pathlib import Path

# Color codes
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
RESET = "\033[0m"


def print_header(text: str):
    print(f"\n{BLUE}{'='*60}{RESET}")
    print(f"{BLUE}{text}{RESET}")
    print(f"{BLUE}{'='*60}{RESET}\n")


def test_env_file():
    """Test 1: Check if .env file exists."""
    print_header("TEST 1: Environment File")
    env_path = Path(__file__).parent / ".env"
    if env_path.exists():
        print(f"{GREEN}✓{RESET} .env file found at: {env_path}")
        return True
    else:
        print(f"{RED}✗{RESET} .env file NOT FOUND")
        print(f"{YELLOW}ACTION:{RESET} Run: cd backend && copy .env.example .env")
        return False


def test_supabase():
    """Test 2: Supabase connection."""
    print_header("TEST 2: Supabase Database")
    try:
        from core.supabase_db import db
        usage = db.get_or_create_daily_usage()
        print(f"{GREEN}✓{RESET} Supabase connected")
        print(f"  - Emails sent today: {usage.emails_sent}/{usage.daily_limit}")
        print(f"  - Hunter calls: {usage.hunter_calls}")
        print(f"  - Groq calls: {usage.groq_calls}")
        return True
    except Exception as e:
        print(f"{RED}✗{RESET} Supabase connection failed")
        print(f"  Error: {e}")
        print(f"{YELLOW}ACTION:{RESET} Check SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY in .env")
        return False


def test_groq_config():
    """Test 3: Groq API configuration."""
    print_header("TEST 3: Groq API Configuration")
    try:
        from core.config import settings
        if settings.groq_api_key:
            key_preview = settings.groq_api_key[:10] + "..." if len(settings.groq_api_key) > 10 else settings.groq_api_key
            print(f"{GREEN}✓{RESET} Groq API key configured")
            print(f"  - Key: {key_preview}")
            print(f"  - Model: {settings.groq_model}")
            return True
        else:
            print(f"{RED}✗{RESET} Groq API key NOT SET")
            print(f"{YELLOW}ACTION:{RESET} Get key from https://console.groq.com/keys")
            print(f"{YELLOW}ACTION:{RESET} Add to .env: GROQ_API_KEY=\"gsk_your_key\"")
            return False
    except Exception as e:
        print(f"{RED}✗{RESET} Groq config failed: {e}")
        return False


def test_groq_api():
    """Test 4: Groq API actual call."""
    print_header("TEST 4: Groq API Call (Email Generation)")
    try:
        from pipeline.groq_client import generate_draft
        from pipeline.pre_scorer import _load_resume
        
        print("Loading resume...")
        resume = _load_resume()
        print(f"{GREEN}✓{RESET} Resume loaded: {resume.get('name')}")
        
        print("\nGenerating test email draft...")
        lead = {
            "id": "test-lead",
            "recruiter_name": "Test Recruiter",
            "email": "test@example.com"
        }
        internship = {
            "id": "test-internship",
            "company": "TestCo",
            "role": "AI Intern",
            "description": "We are looking for an AI intern to work on machine learning projects."
        }
        
        draft = generate_draft(lead, internship, resume)
        
        print(f"{GREEN}✓{RESET} Email draft generated successfully!")
        print(f"\n  Subject: {draft.subject}")
        print(f"  Body preview: {draft.body[:100]}...")
        print(f"  Follow-up preview: {draft.followup_body[:100]}...")
        return True
        
    except Exception as e:
        print(f"{RED}✗{RESET} Groq API call failed")
        print(f"  Error: {e}")
        print(f"{YELLOW}ACTION:{RESET} Check your Groq API key is valid")
        print(f"{YELLOW}ACTION:{RESET} Check you have credits: https://console.groq.com/settings/limits")
        return False


def test_twilio_config():
    """Test 5: Twilio configuration."""
    print_header("TEST 5: Twilio Configuration")
    try:
        from core.config import settings
        
        if not settings.twilio_account_sid:
            print(f"{RED}✗{RESET} TWILIO_ACCOUNT_SID not set")
            print(f"{YELLOW}ACTION:{RESET} Get from https://console.twilio.com/")
            return False
            
        if not settings.twilio_auth_token:
            print(f"{RED}✗{RESET} TWILIO_AUTH_TOKEN not set")
            return False
            
        if not settings.twilio_from_number:
            print(f"{RED}✗{RESET} TWILIO_FROM_NUMBER not set")
            print(f"{YELLOW}ACTION:{RESET} Use sandbox: whatsapp:+14155238886")
            return False
            
        if not settings.approver_to_number:
            print(f"{RED}✗{RESET} APPROVER_TO_NUMBER not set")
            print(f"{YELLOW}ACTION:{RESET} Add your WhatsApp: whatsapp:+919811394884")
            return False
        
        print(f"{GREEN}✓{RESET} Twilio credentials configured")
        print(f"  - Account SID: {settings.twilio_account_sid[:10]}...")
        print(f"  - From: {settings.twilio_from_number}")
        print(f"  - To: {settings.approver_to_number}")
        
        return True
        
    except Exception as e:
        print(f"{RED}✗{RESET} Twilio config failed: {e}")
        return False


def test_twilio_client():
    """Test 6: Twilio client connection."""
    print_header("TEST 6: Twilio Client Connection")
    try:
        from approval.twilio_sender import _twilio_client
        
        client = _twilio_client()
        if client:
            print(f"{GREEN}✓{RESET} Twilio client created successfully")
            print(f"  - Account SID: {client.account_sid[:10]}...")
            return True
        else:
            print(f"{RED}✗{RESET} Twilio client is None (credentials missing)")
            return False
            
    except Exception as e:
        print(f"{RED}✗{RESET} Twilio client creation failed")
        print(f"  Error: {e}")
        print(f"{YELLOW}ACTION:{RESET} Check your Twilio credentials are correct")
        return False


def test_twilio_send():
    """Test 7: Send actual WhatsApp test message."""
    print_header("TEST 7: Send Test WhatsApp Message")
    
    print(f"{YELLOW}WARNING:{RESET} This will send a real WhatsApp message!")
    response = input("Do you want to send a test message? (yes/no): ")
    
    if response.lower() != "yes":
        print(f"{YELLOW}⊘{RESET} Test skipped by user")
        return None
    
    try:
        from approval.twilio_sender import _twilio_client
        from core.config import settings
        
        client = _twilio_client()
        if not client:
            print(f"{RED}✗{RESET} Twilio client not available")
            return False
        
        print("\nSending test message...")
        
        from_number = settings.twilio_from_number
        to_number = settings.approver_to_number
        
        # Ensure WhatsApp format
        if not from_number.startswith("whatsapp:"):
            from_number = f"whatsapp:{from_number}"
        if not to_number.startswith("whatsapp:"):
            to_number = f"whatsapp:{to_number}"
        
        message = client.messages.create(
            from_=from_number,
            to=to_number,
            body="🧪 *LazyIntern Test Message*\n\nIf you received this, Twilio WhatsApp is working correctly! ✅"
        )
        
        print(f"{GREEN}✓{RESET} Test message sent successfully!")
        print(f"  - Message SID: {message.sid}")
        print(f"  - Status: {message.status}")
        print(f"\n{GREEN}CHECK YOUR WHATSAPP NOW!{RESET}")
        
        return True
        
    except Exception as e:
        print(f"{RED}✗{RESET} Failed to send test message")
        print(f"  Error: {e}")
        print(f"\n{YELLOW}COMMON ISSUES:{RESET}")
        print("  1. Did you join the WhatsApp sandbox? Send 'join <code>' to Twilio's number")
        print("  2. Is your phone number in correct format? whatsapp:+919811394884")
        print("  3. Is the sandbox number correct? whatsapp:+14155238886")
        return False


def test_ngrok():
    """Test 8: ngrok configuration."""
    print_header("TEST 8: ngrok Configuration")
    try:
        from core.config import settings
        
        if not settings.public_base_url:
            print(f"{RED}✗{RESET} PUBLIC_BASE_URL not set")
            print(f"{YELLOW}ACTION:{RESET} Run: ngrok http 8000")
            print(f"{YELLOW}ACTION:{RESET} Copy HTTPS URL to .env: PUBLIC_BASE_URL=\"https://...\"")
            return False
        
        print(f"{GREEN}✓{RESET} PUBLIC_BASE_URL configured")
        print(f"  - URL: {settings.public_base_url}")
        
        if "ngrok" in settings.public_base_url:
            print(f"\n{YELLOW}NOTE:{RESET} Make sure ngrok is running!")
            print(f"  Run: ngrok http 8000")
        
        return True
        
    except Exception as e:
        print(f"{RED}✗{RESET} ngrok config failed: {e}")
        return False


def test_resume():
    """Test 9: Resume files."""
    print_header("TEST 9: Resume Files")
    
    # Check resume.json
    resume_json = Path(__file__).parent / "data" / "resume.json"
    if resume_json.exists():
        print(f"{GREEN}✓{RESET} resume.json found")
        try:
            from pipeline.pre_scorer import _load_resume
            resume = _load_resume()
            print(f"  - Name: {resume.get('name')}")
            print(f"  - Skills: {len(resume.get('skills', {}).get('languages', []))} languages")
            print(f"  - Projects: {len(resume.get('projects', []))} projects")
        except Exception as e:
            print(f"{YELLOW}⚠{RESET} resume.json exists but failed to load: {e}")
    else:
        print(f"{RED}✗{RESET} resume.json NOT FOUND")
        print(f"{YELLOW}ACTION:{RESET} Create backend/data/resume.json")
        return False
    
    # Check resume.pdf
    resume_pdf = Path(__file__).parent / "data" / "resume.pdf"
    if resume_pdf.exists():
        print(f"{GREEN}✓{RESET} resume.pdf found ({resume_pdf.stat().st_size} bytes)")
    else:
        print(f"{YELLOW}⚠{RESET} resume.pdf NOT FOUND (emails will send without attachment)")
    
    return True


def main():
    print(f"\n{BLUE}{'='*60}{RESET}")
    print(f"{BLUE}LazyIntern Component Testing{RESET}")
    print(f"{BLUE}{'='*60}{RESET}")
    
    results = {}
    
    # Run all tests
    results["Environment File"] = test_env_file()
    if not results["Environment File"]:
        print(f"\n{RED}CRITICAL: .env file missing. Cannot continue.{RESET}")
        return 1
    
    results["Supabase"] = test_supabase()
    results["Groq Config"] = test_groq_config()
    
    if results["Groq Config"]:
        results["Groq API Call"] = test_groq_api()
    else:
        results["Groq API Call"] = False
    
    results["Twilio Config"] = test_twilio_config()
    
    if results["Twilio Config"]:
        results["Twilio Client"] = test_twilio_client()
        if results["Twilio Client"]:
            results["Twilio Send"] = test_twilio_send()
    else:
        results["Twilio Client"] = False
        results["Twilio Send"] = False
    
    results["ngrok"] = test_ngrok()
    results["Resume Files"] = test_resume()
    
    # Summary
    print_header("SUMMARY")
    
    critical = ["Environment File", "Supabase", "Groq Config", "Groq API Call", "Twilio Config", "Twilio Client"]
    optional = ["Twilio Send", "ngrok", "Resume Files"]
    
    critical_pass = sum(1 for k in critical if results.get(k) == True)
    optional_pass = sum(1 for k in optional if results.get(k) == True)
    
    print(f"Critical Tests: {critical_pass}/{len(critical)} passed")
    print(f"Optional Tests: {optional_pass}/{len(optional)} passed")
    
    print(f"\n{BLUE}{'='*60}{RESET}")
    
    if critical_pass == len(critical):
        print(f"\n{GREEN}✓ ALL CRITICAL TESTS PASSED!{RESET}")
        print(f"\n{GREEN}Your system is ready to generate emails and send WhatsApp approvals!{RESET}")
        print(f"\nNext steps:")
        print(f"  1. Start backend: python -m uvicorn api.app:app --reload")
        print(f"  2. Run one cycle: python -m scheduler.cycle_manager --once")
        print(f"  3. Check your WhatsApp for approval messages!")
        return 0
    else:
        print(f"\n{RED}✗ SOME CRITICAL TESTS FAILED{RESET}")
        print(f"\nPlease fix the issues above before running the pipeline.")
        print(f"\nFailed tests:")
        for test, result in results.items():
            if test in critical and not result:
                print(f"  - {RED}✗{RESET} {test}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
