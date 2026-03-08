"""
Property-based tests for pattern_guesser.py module.

Feature: email-discovery-fallback-chain
"""

from hypothesis import given, strategies as st, settings
import sys
import os

# Add backend directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from pipeline.pattern_guesser import generate_pattern_candidates


# Domain strategy: valid domain strings with at least one dot
# Build domains as "name.tld" format to avoid excessive filtering
domains = st.builds(
    lambda name, tld: f"{name}.{tld}",
    name=st.text(
        alphabet=st.characters(whitelist_categories=('Ll', 'Nd'), whitelist_characters='-'),
        min_size=1,
        max_size=30
    ).filter(lambda x: x and not x.startswith('-') and not x.endswith('-')),
    tld=st.text(
        alphabet=st.characters(whitelist_categories=('Ll',)),
        min_size=2,
        max_size=10
    )
)


@settings(max_examples=100)
@given(domain=domains)
def test_property_1_pattern_generation_completeness(domain):
    """
    Feature: email-discovery-fallback-chain
    Property 1: Pattern Generation Completeness
    
    **Validates: Requirements 1.1, 1.2, 1.3, 1.4**
    
    For any valid domain string, the pattern guesser shall generate
    exactly 5 email candidates in the order [hr@, careers@, internships@, 
    hello@, info@], where each candidate has source="pattern_guess" and 
    confidence=50.
    """
    # Generate pattern candidates
    candidates = generate_pattern_candidates(domain)
    
    # Verify exactly 5 candidates generated
    assert len(candidates) == 5, f"Expected 5 candidates, got {len(candidates)}"
    
    # Verify correct order of patterns
    expected_patterns = ['hr', 'careers', 'internships', 'hello', 'info']
    actual_patterns = [c.email.split('@')[0] for c in candidates]
    assert actual_patterns == expected_patterns, \
        f"Expected patterns {expected_patterns}, got {actual_patterns}"
    
    # Verify all candidates have correct source
    assert all(c.source == "pattern_guess" for c in candidates), \
        "All candidates should have source='pattern_guess'"
    
    # Verify all candidates have correct confidence
    assert all(c.confidence == 50 for c in candidates), \
        "All candidates should have confidence=50"
    
    # Verify all emails end with the correct domain
    assert all(c.email.endswith(f"@{domain}") for c in candidates), \
        f"All emails should end with @{domain}"
    
    # Verify recruiter_name is None for all candidates
    assert all(c.recruiter_name is None for c in candidates), \
        "All candidates should have recruiter_name=None"


if __name__ == "__main__":
    # Run the property test
    test_property_1_pattern_generation_completeness()
    print("✓ Property test passed: Pattern Generation Completeness")

