"""
Test script to verify disqualification override logic in pre_scorer.

Tests that high-priority role keywords take precedence over disqualification keywords,
preventing false negatives for roles like "AI Sales Engineer" or "ML Technical Support".
"""

import sys
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_path))

from pipeline.pre_scorer import pre_score


def test_override_logic():
    """Test that high-priority keywords override disqualification."""
    
    print("Testing disqualification override logic...\n")
    
    # Test Case 1: "AI Sales Engineer" - should NOT be disqualified
    # "sales engineer" is in disqualify list, but "ai" is high-priority
    test_case_1 = {
        "role": "AI Sales Engineer",
        "company": "Tech Corp",
        "location": "Bangalore",
        "description": "Work on AI solutions for enterprise clients",
        "link": "https://example.com/job1"
    }
    
    result_1 = pre_score(test_case_1)
    print(f"Test Case 1: AI Sales Engineer")
    print(f"  Score: {result_1.score}")
    print(f"  Status: {result_1.status}")
    print(f"  Breakdown: {result_1.breakdown}")
    print(f"  Override applied: {'disqualify_overridden' in result_1.breakdown}")
    
    assert result_1.score > 0, "AI Sales Engineer should NOT be disqualified"
    assert result_1.status != "disqualified", "Status should not be disqualified"
    assert "high_priority_role" in result_1.breakdown, "Should have high_priority_role match"
    print("  ✓ PASSED: High-priority keyword overrode disqualification\n")
    
    # Test Case 2: "ML Technical Support" - should NOT be disqualified
    # "technical support" is in disqualify list, but "ml" is high-priority
    test_case_2 = {
        "role": "ML Technical Support Engineer",
        "company": "AI Startup",
        "location": "Mumbai",
        "description": "Support ML infrastructure and models",
        "link": "https://example.com/job2"
    }
    
    result_2 = pre_score(test_case_2)
    print(f"Test Case 2: ML Technical Support Engineer")
    print(f"  Score: {result_2.score}")
    print(f"  Status: {result_2.status}")
    print(f"  Breakdown: {result_2.breakdown}")
    print(f"  Override applied: {'disqualify_overridden' in result_2.breakdown}")
    
    assert result_2.score > 0, "ML Technical Support should NOT be disqualified"
    assert result_2.status != "disqualified", "Status should not be disqualified"
    assert "high_priority_role" in result_2.breakdown, "Should have high_priority_role match"
    print("  ✓ PASSED: High-priority keyword overrode disqualification\n")
    
    # Test Case 3: "Sales Engineer" (no high-priority keyword) - SHOULD be disqualified
    test_case_3 = {
        "role": "Sales Engineer",
        "company": "Generic Corp",
        "location": "Delhi",
        "description": "Sell products to clients",
        "link": "https://example.com/job3"
    }
    
    result_3 = pre_score(test_case_3)
    print(f"Test Case 3: Sales Engineer (no high-priority keyword)")
    print(f"  Score: {result_3.score}")
    print(f"  Status: {result_3.status}")
    print(f"  Breakdown: {result_3.breakdown}")
    
    assert result_3.score == 0, "Plain Sales Engineer should be disqualified"
    assert result_3.status == "disqualified", "Status should be disqualified"
    assert "disqualify" in result_3.breakdown, "Should have disqualify in breakdown"
    print("  ✓ PASSED: Disqualification applied correctly without high-priority keyword\n")
    
    # Test Case 4: "Data Entry Clerk" - SHOULD be disqualified
    test_case_4 = {
        "role": "Data Entry Clerk",
        "company": "Office Corp",
        "location": "Pune",
        "description": "Enter data into systems",
        "link": "https://example.com/job4"
    }
    
    result_4 = pre_score(test_case_4)
    print(f"Test Case 4: Data Entry Clerk")
    print(f"  Score: {result_4.score}")
    print(f"  Status: {result_4.status}")
    print(f"  Breakdown: {result_4.breakdown}")
    
    assert result_4.score == 0, "Data Entry should be disqualified"
    assert result_4.status == "disqualified", "Status should be disqualified"
    print("  ✓ PASSED: New disqualify keyword working correctly\n")
    
    print("=" * 60)
    print("All tests passed! Override logic working correctly.")
    print("=" * 60)


if __name__ == "__main__":
    test_override_logic()
