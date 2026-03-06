"""
Test improved email generation with clear internship mention
"""
import sys
import json
sys.path.insert(0, 'backend')

from pipeline.groq_client import _generate_fallback_draft
from pathlib import Path

def test_improved_email():
    print("=" * 80)
    print("IMPROVED EMAIL GENERATION TEST")
    print("=" * 80)
    
    # Load actual resume
    resume_path = Path("backend/data/resume.json")
    with open(resume_path, 'r', encoding='utf-8') as f:
        resume = json.load(f)
    
    # Test Case 1: AI/ML Company
    print("\n" + "=" * 80)
    print("TEST 1: AI/ML COMPANY")
    print("=" * 80)
    
    lead1 = {
        "id": 1,
        "recruiter_name": "Sarah Chen"
    }
    
    internship1 = {
        "id": 1,
        "company": "OpenAI",
        "role": "ML Engineer Intern",
        "description": "Build and deploy large language models using PyTorch"
    }
    
    draft1 = _generate_fallback_draft(lead1, internship1, resume)
    
    print(f"\n📧 Subject: {draft1.subject}")
    print(f"\n📝 Body:\n{draft1.body}")
    print(f"\n🔄 Follow-up:\n{draft1.followup_body}")
    
    # Check for key elements
    print("\n✅ VERIFICATION:")
    has_internship = "internship" in draft1.subject.lower() or "internship" in draft1.body.lower()
    has_student = "student" in draft1.body.lower()
    has_year = "3rd year" in draft1.body.lower() or "third year" in draft1.body.lower()
    has_degree = "b.tech" in draft1.body.lower() or "computer science" in draft1.body.lower()
    
    print(f"   Mentions 'internship': {'✅' if has_internship else '❌'}")
    print(f"   Mentions 'student': {'✅' if has_student else '❌'}")
    print(f"   Mentions year (3rd): {'✅' if has_year else '❌'}")
    print(f"   Mentions degree/CS: {'✅' if has_degree else '❌'}")
    
    # Test Case 2: Finance Company
    print("\n" + "=" * 80)
    print("TEST 2: FINANCE COMPANY")
    print("=" * 80)
    
    lead2 = {
        "id": 2,
        "recruiter_name": "John Smith"
    }
    
    internship2 = {
        "id": 2,
        "company": "Goldman Sachs",
        "role": "Quantitative Analyst Intern",
        "description": "Build trading algorithms and financial models"
    }
    
    draft2 = _generate_fallback_draft(lead2, internship2, resume)
    
    print(f"\n📧 Subject: {draft2.subject}")
    print(f"\n📝 Body:\n{draft2.body}")
    
    # Test Case 3: Startup
    print("\n" + "=" * 80)
    print("TEST 3: STARTUP COMPANY")
    print("=" * 80)
    
    lead3 = {
        "id": 3,
        "recruiter_name": "Alex"
    }
    
    internship3 = {
        "id": 3,
        "company": "YC Startup",
        "role": "Full Stack Engineer Intern",
        "description": "Build web applications using React and Node.js"
    }
    
    draft3 = _generate_fallback_draft(lead3, internship3, resume)
    
    print(f"\n📧 Subject: {draft3.subject}")
    print(f"\n📝 Body:\n{draft3.body}")
    
    print("\n" + "=" * 80)
    print("TEST COMPLETE")
    print("=" * 80)
    
    if has_internship and has_student and (has_year or has_degree):
        print("\n✅ ALL KEY ELEMENTS PRESENT")
        return True
    else:
        print("\n❌ MISSING KEY ELEMENTS")
        return False

if __name__ == "__main__":
    success = test_improved_email()
    sys.exit(0 if success else 1)
