"""
Test script to verify location extraction from role titles.
This fixes the issue where LinkedIn leads score only 40 (high_priority_role)
and never reach 60 to trigger Hunter API calls.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from pipeline.pre_scorer import pre_score

def test_location_extraction():
    print("=" * 70)
    print("Testing Location Extraction from Role Titles")
    print("=" * 70)
    
    # Test cases simulating LinkedIn leads with location in title
    test_cases = [
        {
            "name": "AI Internship in Mumbai",
            "internship": {
                "role": "artificial intelligence (ai) internship in mumbai",
                "company": "tech startup",
                "location": "",  # Empty location field (LinkedIn without login)
                "link": "https://linkedin.com/jobs/123"
            },
            "expected_min_score": 60,  # 40 (high_priority_role) + 20 (location)
            "should_trigger_hunter": True
        },
        {
            "name": "ML Intern - Remote India",
            "internship": {
                "role": "machine learning intern - (paid - india/remote)",
                "company": "ai company",
                "location": "",
                "link": "https://linkedin.com/jobs/456"
            },
            "expected_min_score": 60,  # 40 + 20 (remote or india)
            "should_trigger_hunter": True
        },
        {
            "name": "AI/ML Intern in Bangalore",
            "internship": {
                "role": "ai/ml intern in bangalore",
                "company": "startup",
                "location": "",
                "link": "https://linkedin.com/jobs/789"
            },
            "expected_min_score": 60,  # 40 + 20 (bangalore)
            "should_trigger_hunter": True
        },
        {
            "name": "Research Intern in Delhi",
            "internship": {
                "role": "research intern in delhi",
                "company": "research lab",
                "location": "",
                "link": "https://linkedin.com/jobs/101"
            },
            "expected_min_score": 60,  # 40 + 20 (delhi)
            "should_trigger_hunter": True
        },
        {
            "name": "AI Intern (no location)",
            "internship": {
                "role": "ai/ml intern",
                "company": "company",
                "location": "",
                "link": "https://linkedin.com/jobs/202"
            },
            "expected_min_score": 40,  # Only 40 (high_priority_role)
            "should_trigger_hunter": False
        },
        {
            "name": "AI Intern with location field",
            "internship": {
                "role": "ai intern",
                "company": "startup",
                "location": "Mumbai, India",  # Dedicated location field
                "link": "https://linkedin.com/jobs/303"
            },
            "expected_min_score": 60,  # 40 + 20 (location field)
            "should_trigger_hunter": True
        }
    ]
    
    print("\nTest Results:")
    print("-" * 70)
    
    all_passed = True
    hunter_threshold = 60
    
    for i, test in enumerate(test_cases, 1):
        result = pre_score(test["internship"])
        
        score = result.score
        breakdown = result.breakdown
        
        # Check if score meets expectation
        score_ok = score >= test["expected_min_score"]
        hunter_ok = (score >= hunter_threshold) == test["should_trigger_hunter"]
        
        status = "✓ PASS" if (score_ok and hunter_ok) else "✗ FAIL"
        
        print(f"\n{status} Test {i}: {test['name']}")
        print(f"   Role: '{test['internship']['role']}'")
        print(f"   Location field: '{test['internship']['location']}'")
        print(f"   Score: {score} (expected >= {test['expected_min_score']})")
        print(f"   Breakdown: {breakdown}")
        print(f"   Hunter triggered: {score >= hunter_threshold} (expected: {test['should_trigger_hunter']})")
        
        if not (score_ok and hunter_ok):
            all_passed = False
            if not score_ok:
                print(f"   ✗ Score too low: {score} < {test['expected_min_score']}")
            if not hunter_ok:
                print(f"   ✗ Hunter trigger mismatch")
    
    print("\n" + "=" * 70)
    if all_passed:
        print("✓ ALL TESTS PASSED")
        print(f"✓ Location extraction from role titles working correctly")
        print(f"✓ Leads now reach {hunter_threshold}+ score to trigger Hunter API")
    else:
        print("✗ SOME TESTS FAILED")
        print("✗ Location extraction needs debugging")
    print("=" * 70)
    
    return all_passed


if __name__ == "__main__":
    try:
        success = test_location_extraction()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n✗ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
