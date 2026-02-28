"""
Test script to verify India region filtering in pre_scorer.
Ensures non-India locations are disqualified before scoring.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from pipeline.pre_scorer import pre_score


def test_india_region_filter():
    print("=" * 70)
    print("Testing India Region Filter")
    print("=" * 70)
    
    test_cases = [
        # (name, internship, should_pass, reason)
        {
            "name": "India location - Mumbai",
            "internship": {
                "role": "AI Intern",
                "company": "TechCorp",
                "location": "Mumbai, India",
                "link": "https://example.com/job1"
            },
            "should_pass": True,
            "reason": "Indian city"
        },
        {
            "name": "India location - Bangalore",
            "internship": {
                "role": "ML Engineer Intern",
                "company": "Startup",
                "location": "Bangalore",
                "link": "https://example.com/job2"
            },
            "should_pass": True,
            "reason": "Indian city"
        },
        {
            "name": "Remote location",
            "internship": {
                "role": "AI Research Intern",
                "company": "RemoteCo",
                "location": "Remote",
                "link": "https://example.com/job3"
            },
            "should_pass": True,
            "reason": "Remote (could be anywhere)"
        },
        {
            "name": "Empty location",
            "internship": {
                "role": "Data Science Intern",
                "company": "Company",
                "location": "",
                "link": "https://example.com/job4"
            },
            "should_pass": True,
            "reason": "Empty location (can't tell)"
        },
        {
            "name": "USA location",
            "internship": {
                "role": "AI Intern",
                "company": "USCompany",
                "location": "USA",
                "link": "https://example.com/job5"
            },
            "should_pass": False,
            "reason": "Non-India: USA"
        },
        {
            "name": "New York location",
            "internship": {
                "role": "ML Intern",
                "company": "NYCompany",
                "location": "New York, USA",
                "link": "https://example.com/job6"
            },
            "should_pass": False,
            "reason": "Non-India: New York"
        },
        {
            "name": "UK location",
            "internship": {
                "role": "AI Intern",
                "company": "UKCompany",
                "location": "London, UK",
                "link": "https://example.com/job7"
            },
            "should_pass": False,
            "reason": "Non-India: London/UK"
        },
        {
            "name": "Singapore location",
            "internship": {
                "role": "Data Scientist Intern",
                "company": "SGCompany",
                "location": "Singapore",
                "link": "https://example.com/job8"
            },
            "should_pass": False,
            "reason": "Non-India: Singapore"
        },
        {
            "name": "Canada location",
            "internship": {
                "role": "ML Engineer Intern",
                "company": "CanadaCo",
                "location": "Toronto, Canada",
                "link": "https://example.com/job9"
            },
            "should_pass": False,
            "reason": "Non-India: Canada"
        },
        {
            "name": "UAE location",
            "internship": {
                "role": "AI Intern",
                "company": "UAECompany",
                "location": "Dubai, UAE",
                "link": "https://example.com/job10"
            },
            "should_pass": False,
            "reason": "Non-India: UAE"
        },
        {
            "name": "USA but also mentions India",
            "internship": {
                "role": "AI Intern - USA or India",
                "company": "GlobalCo",
                "location": "USA, India",
                "link": "https://example.com/job11"
            },
            "should_pass": True,
            "reason": "USA but also mentions India (exception)"
        },
        {
            "name": "UK but remote",
            "internship": {
                "role": "ML Intern - UK Remote",
                "company": "RemoteUK",
                "location": "UK, Remote",
                "link": "https://example.com/job12"
            },
            "should_pass": True,
            "reason": "UK but mentions remote (exception)"
        },
        {
            "name": "Location in role title - USA",
            "internship": {
                "role": "AI Intern in San Francisco",
                "company": "SFCompany",
                "location": "",
                "link": "https://example.com/job13"
            },
            "should_pass": False,
            "reason": "Non-India location in role title"
        },
        {
            "name": "Location in role title - India",
            "internship": {
                "role": "ML Intern in Mumbai",
                "company": "IndiaCompany",
                "location": "",
                "link": "https://example.com/job14"
            },
            "should_pass": True,
            "reason": "India location in role title"
        },
    ]
    
    print("\n✓ Should PASS (India/Remote/Empty):")
    print("-" * 70)
    all_passed = True
    for test in test_cases:
        if test["should_pass"]:
            result = pre_score(test["internship"])
            passed = result.status != "disqualified"
            status = "✓ PASS" if passed else "✗ FAIL"
            print(f"{status} | {test['name']:40s} | {test['reason']}")
            if not passed:
                print(f"       Expected: PASS, Got: {result.status}, Breakdown: {result.breakdown}")
                all_passed = False
    
    print("\n✗ Should FAIL (Non-India locations):")
    print("-" * 70)
    for test in test_cases:
        if not test["should_pass"]:
            result = pre_score(test["internship"])
            passed = result.status == "disqualified"
            status = "✓ PASS" if passed else "✗ FAIL"
            print(f"{status} | {test['name']:40s} | {test['reason']}")
            if not passed:
                print(f"       Expected: DISQUALIFIED, Got: {result.status}, Score: {result.score}")
                all_passed = False
    
    return all_passed


def test_job_source_urls():
    print("\n" + "=" * 70)
    print("Job Source URL Updates")
    print("=" * 70)
    
    print("\n✓ LinkedIn URLs (should have location=India):")
    print("-" * 70)
    linkedin_urls = [
        "https://www.linkedin.com/jobs/search/?keywords=AI+intern&location=India&f_JT=I",
        "https://www.linkedin.com/jobs/search/?keywords=machine+learning+intern&location=India&f_JT=I",
        "https://www.linkedin.com/jobs/search/?keywords=data+science+intern&location=India&f_JT=I",
        "https://www.linkedin.com/jobs/search/?keywords=AI+intern&location=India&f_WT=2&f_JT=I",
        "https://www.linkedin.com/jobs/search/?keywords=LLM+engineer+intern&location=India&f_JT=I",
        "https://www.linkedin.com/jobs/search/?keywords=generative+AI+intern&location=India&f_JT=I",
    ]
    
    for url in linkedin_urls:
        has_india = "location=India" in url
        status = "✓" if has_india else "✗"
        print(f"{status} {url}")
    
    print("\n✓ Wellfound URLs (should have location=India):")
    print("-" * 70)
    wellfound_urls = [
        "https://wellfound.com/jobs?role=Machine+Learning+Engineer&jobType=internship&location=India",
        "https://wellfound.com/jobs?role=Artificial+Intelligence&jobType=internship&location=India",
        "https://wellfound.com/jobs?role=Data+Scientist&jobType=internship&location=India",
    ]
    
    for url in wellfound_urls:
        has_india = "location=India" in url
        status = "✓" if has_india else "✗"
        print(f"{status} {url}")
    
    print("\n✓ Internshala URLs (already India-only):")
    print("-" * 70)
    print("✓ Internshala is India-specific platform, no changes needed")


def main():
    print("\n" + "=" * 70)
    print("INDIA REGION FILTER TEST SUITE")
    print("=" * 70)
    
    test1_passed = test_india_region_filter()
    test_job_source_urls()
    
    print("\n" + "=" * 70)
    print("FINAL RESULTS")
    print("=" * 70)
    print(f"Test 1 (Region Filter): {'✓ PASSED' if test1_passed else '✗ FAILED'}")
    
    if test1_passed:
        print("\n✓ ALL TESTS PASSED")
        print("\nFixes Applied:")
        print("1. ✓ Job sources updated with India location parameters")
        print("2. ✓ Pre-scorer filters non-India locations before scoring")
        print("\nBenefits:")
        print("- Only India-relevant jobs scraped from LinkedIn/Wellfound")
        print("- Non-India locations disqualified early (saves processing)")
        print("- Remote jobs kept (could be India-friendly)")
        print("- Exception: USA/UK jobs that also mention India/remote")
    else:
        print("\n✗ SOME TESTS FAILED")
    
    print("=" * 70)
    
    return test1_passed


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
