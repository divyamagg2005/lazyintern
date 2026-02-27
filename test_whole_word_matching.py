"""
Test script to verify whole-word matching prevents false positives.
Run this to confirm keywords like 'pr' don't match 'product', 'prior', 'research'.
"""

import re


def whole_word_match(keyword: str, text: str) -> bool:
    """
    Check if keyword matches as a whole word in text (case-insensitive).
    """
    pattern = r'\b' + re.escape(keyword.lower()) + r'\b'
    return bool(re.search(pattern, text.lower()))


def test_whole_word_matching():
    print("=" * 60)
    print("Testing Whole-Word Keyword Matching")
    print("=" * 60)
    
    # Test cases that should PASS (match found)
    pass_cases = [
        ("ml", "ml engineer", True),
        ("ai", "ai research intern", True),
        ("research", "research scientist", True),
        ("pr", "pr manager", True),  # Legitimate PR role
        ("data", "data scientist", True),
        ("remote", "remote work", True),
    ]
    
    # Test cases that should FAIL (no match - false positives prevented)
    fail_cases = [
        ("pr", "product manager", False),  # 'pr' should NOT match 'product'
        ("pr", "prior experience", False),  # 'pr' should NOT match 'prior'
        ("pr", "research intern", False),   # 'pr' should NOT match 'research'
        ("ml", "html developer", False),    # 'ml' should NOT match 'html'
        ("ai", "email marketing", False),   # 'ai' should NOT match 'email'
        ("data", "update analyst", False),  # 'data' should NOT match 'update'
    ]
    
    print("\n✓ EXPECTED MATCHES (should find keyword):")
    print("-" * 60)
    all_pass = True
    for keyword, text, expected in pass_cases:
        result = whole_word_match(keyword, text)
        status = "✓ PASS" if result == expected else "✗ FAIL"
        print(f"{status} | '{keyword}' in '{text}' -> {result}")
        if result != expected:
            all_pass = False
    
    print("\n✗ EXPECTED NO MATCHES (should NOT find keyword):")
    print("-" * 60)
    for keyword, text, expected in fail_cases:
        result = whole_word_match(keyword, text)
        status = "✓ PASS" if result == expected else "✗ FAIL"
        print(f"{status} | '{keyword}' in '{text}' -> {result}")
        if result != expected:
            all_pass = False
    
    print("\n" + "=" * 60)
    if all_pass:
        print("✓ ALL TESTS PASSED - Whole-word matching works correctly!")
    else:
        print("✗ SOME TESTS FAILED - Check implementation")
    print("=" * 60)


if __name__ == "__main__":
    test_whole_word_matching()
