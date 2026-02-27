"""
Test script to verify platform email rejection.
Ensures emails from job board platforms (linkedin.com, internshala.com, etc.)
are rejected and only company emails are kept.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from pipeline.email_extractor import extract_from_internship, _is_platform_email, _extract_domain_from_url


def test_domain_extraction():
    print("=" * 70)
    print("Test 1: Domain Extraction from URLs")
    print("=" * 70)
    
    test_cases = [
        ("https://www.linkedin.com/jobs/123", "linkedin.com"),
        ("https://internshala.com/internships/ml", "internshala.com"),
        ("https://wellfound.com/jobs?role=AI", "wellfound.com"),
        ("https://www.workatastartup.com/jobs?role=eng", "workatastartup.com"),
        ("https://unstop.com/internships", "unstop.com"),
        ("http://remoteok.com/remote-ai-jobs", "remoteok.com"),
        ("", ""),
    ]
    
    all_passed = True
    for url, expected in test_cases:
        result = _extract_domain_from_url(url)
        status = "✓" if result == expected else "✗"
        print(f"{status} {url[:50]:50s} -> {result:20s} (expected: {expected})")
        if result != expected:
            all_passed = False
    
    return all_passed


def test_platform_email_detection():
    print("\n" + "=" * 70)
    print("Test 2: Platform Email Detection")
    print("=" * 70)
    
    test_cases = [
        # Should REJECT (platform emails)
        ("ecombes@linkedin.com", "https://linkedin.com/jobs/123", True, "REJECT"),
        ("hr@internshala.com", "https://internshala.com/internships/ml", True, "REJECT"),
        ("support@wellfound.com", "https://wellfound.com/jobs", True, "REJECT"),
        ("careers@unstop.com", "https://unstop.com/internships", True, "REJECT"),
        ("admin@workatastartup.com", "https://workatastartup.com/jobs", True, "REJECT"),
        
        # Should KEEP (company emails)
        ("hr@blitzenx.com", "https://linkedin.com/jobs/123", False, "KEEP"),
        ("careers@somestartup.ai", "https://wellfound.com/jobs", False, "KEEP"),
        ("hiring@techcompany.io", "https://internshala.com/internships", False, "KEEP"),
        ("jobs@innovexis.com", "https://linkedin.com/jobs/456", False, "KEEP"),
        ("recruit@ailab.org", "https://unstop.com/internships", False, "KEEP"),
    ]
    
    all_passed = True
    print("\n✗ Should REJECT (platform emails):")
    print("-" * 70)
    for email, source, expected, action in test_cases:
        if action == "REJECT":
            result = _is_platform_email(email, source)
            status = "✓ PASS" if result == expected else "✗ FAIL"
            print(f"{status} | {email:30s} from {_extract_domain_from_url(source):20s} -> {result}")
            if result != expected:
                all_passed = False
    
    print("\n✓ Should KEEP (company emails):")
    print("-" * 70)
    for email, source, expected, action in test_cases:
        if action == "KEEP":
            result = _is_platform_email(email, source)
            status = "✓ PASS" if result == expected else "✗ FAIL"
            print(f"{status} | {email:30s} from {_extract_domain_from_url(source):20s} -> {result}")
            if result != expected:
                all_passed = False
    
    return all_passed


def test_email_extraction_with_rejection():
    print("\n" + "=" * 70)
    print("Test 3: Email Extraction with Platform Rejection")
    print("=" * 70)
    
    test_cases = [
        {
            "name": "LinkedIn job with platform email (should reject)",
            "internship": {
                "description": "Contact us at ecombes@linkedin.com for more info",
                "link": "https://linkedin.com/jobs/123",
                "source_url": "https://linkedin.com/jobs/123"
            },
            "expected_email": None,  # Should be rejected
            "should_extract": False
        },
        {
            "name": "LinkedIn job with company email (should keep)",
            "internship": {
                "description": "Apply at careers@blitzenx.com",
                "link": "https://linkedin.com/jobs/456",
                "source_url": "https://linkedin.com/jobs/456"
            },
            "expected_email": "careers@blitzenx.com",
            "should_extract": True
        },
        {
            "name": "Internshala with platform email (should reject)",
            "internship": {
                "description": "Questions? Email support@internshala.com",
                "link": "https://internshala.com/internships/ml-123",
                "source_url": "https://internshala.com/internships/ml-123"
            },
            "expected_email": None,
            "should_extract": False
        },
        {
            "name": "Internshala with company email (should keep)",
            "internship": {
                "description": "Send resume to hr@techstartup.in",
                "link": "https://internshala.com/internships/ai-456",
                "source_url": "https://internshala.com/internships/ai-456"
            },
            "expected_email": "hr@techstartup.in",
            "should_extract": True
        },
        {
            "name": "Wellfound with mixed emails (should keep company, reject platform)",
            "internship": {
                "description": "Contact hiring@innovexis.com or support@wellfound.com",
                "link": "https://wellfound.com/jobs/789",
                "source_url": "https://wellfound.com/jobs/789"
            },
            "expected_email": "hiring@innovexis.com",  # Should pick company email
            "should_extract": True
        }
    ]
    
    all_passed = True
    for i, test in enumerate(test_cases, 1):
        result = extract_from_internship(test["internship"])
        
        if test["should_extract"]:
            if result and result.email == test["expected_email"]:
                print(f"✓ PASS Test {i}: {test['name']}")
                print(f"   Extracted: {result.email}")
            else:
                print(f"✗ FAIL Test {i}: {test['name']}")
                print(f"   Expected: {test['expected_email']}")
                print(f"   Got: {result.email if result else 'None'}")
                all_passed = False
        else:
            if result is None:
                print(f"✓ PASS Test {i}: {test['name']}")
                print(f"   Correctly rejected platform email")
            else:
                print(f"✗ FAIL Test {i}: {test['name']}")
                print(f"   Should have rejected but got: {result.email}")
                all_passed = False
    
    return all_passed


def main():
    print("\n" + "=" * 70)
    print("PLATFORM EMAIL REJECTION TEST SUITE")
    print("=" * 70)
    
    test1_passed = test_domain_extraction()
    test2_passed = test_platform_email_detection()
    test3_passed = test_email_extraction_with_rejection()
    
    print("\n" + "=" * 70)
    print("FINAL RESULTS")
    print("=" * 70)
    print(f"Test 1 (Domain Extraction): {'✓ PASSED' if test1_passed else '✗ FAILED'}")
    print(f"Test 2 (Platform Detection): {'✓ PASSED' if test2_passed else '✗ FAILED'}")
    print(f"Test 3 (Email Extraction): {'✓ PASSED' if test3_passed else '✗ FAILED'}")
    
    if test1_passed and test2_passed and test3_passed:
        print("\n✓ ALL TESTS PASSED")
        print("✓ Platform emails (linkedin.com, internshala.com, etc.) are rejected")
        print("✓ Company emails are correctly extracted")
        print("=" * 70)
        return True
    else:
        print("\n✗ SOME TESTS FAILED")
        print("=" * 70)
        return False


if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n✗ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
