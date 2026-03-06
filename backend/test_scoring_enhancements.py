"""
Comprehensive test suite for pipeline scoring enhancements.
Tests all new features including JD scanning, track detection, generic title rescue,
and disqualification override logic.
"""

from pipeline.pre_scorer import (
    pre_score,
    scan_jd_keywords,
    detect_track,
    should_rescue_generic_title,
    _load_keywords,
)


def test_daily_limits():
    """Verify daily send limits are set to 50."""
    from pipeline.pre_scorer import MAX_SMS_PER_DAY, MAX_EMAILS_PER_DAY
    
    assert MAX_SMS_PER_DAY == 50, f"Expected MAX_SMS_PER_DAY=50, got {MAX_SMS_PER_DAY}"
    assert MAX_EMAILS_PER_DAY == 50, f"Expected MAX_EMAILS_PER_DAY=50, got {MAX_EMAILS_PER_DAY}"
    print("✅ Daily limits correctly set to 50")


def test_high_priority_keywords():
    """Verify expanded high priority keywords are loaded."""
    keywords = _load_keywords()
    high_priority = [kw.lower() for kw in keywords.get("role_keywords", {}).get("high_priority", [])]
    
    # Check AI/ML keywords
    assert "ai" in high_priority
    assert "machine learning" in high_priority
    assert "deep learning" in high_priority
    
    # Check data science keywords
    assert "data scientist" in high_priority
    
    # Check robotics keywords
    assert "robotics" in high_priority
    
    # Check backend/full-stack keywords
    assert "backend engineer" in high_priority
    assert "full stack engineer" in high_priority
    
    # Check investment banking/quant keywords
    assert "investment banking" in high_priority
    assert "quantitative trading" in high_priority
    
    print(f"✅ High priority keywords expanded ({len(high_priority)} keywords)")


def test_jd_scanning_basic():
    """Test basic JD keyword scanning with 3-tier system."""
    keywords = _load_keywords()
    
    # JD with Tier 1 keywords (frameworks/tools)
    jd_text = "We're looking for someone with PyTorch and TensorFlow experience to build ML models using Kubernetes and Docker."
    result = scan_jd_keywords(jd_text, keywords)
    
    assert result["tier1_score"] > 0, "Should detect Tier 1 keywords"
    assert result["total_jd_score"] > 0, "Should have positive total JD score"
    print(f"✅ JD scanning basic test passed: {result}")


def test_jd_scanning_caps():
    """Test that JD scanning respects tier-specific caps."""
    keywords = _load_keywords()
    
    # JD with many Tier 1 keywords (should cap at +40)
    jd_text = """
    We need expertise in PyTorch, TensorFlow, Keras, JAX, scikit-learn, React, Angular, 
    Vue, Node.js, Express, Kubernetes, Docker, AWS, GCP, Azure, PostgreSQL, MongoDB, 
    Redis, Elasticsearch, Spark, Hadoop, Kafka, Airflow, MLflow.
    """
    result = scan_jd_keywords(jd_text, keywords)
    
    assert result["tier1_score"] <= 40, f"Tier 1 should cap at 40, got {result['tier1_score']}"
    print(f"✅ JD scanning caps test passed: Tier 1 capped at {result['tier1_score']}")


def test_track_detection_tech():
    """Test track detection for tech roles."""
    keywords = _load_keywords()
    
    role_title = "Machine Learning Engineer"
    jd_text = "Build ML models using PyTorch and TensorFlow"
    track = detect_track(role_title, jd_text, keywords)
    
    assert track == "tech", f"Expected 'tech' track, got '{track}'"
    print(f"✅ Track detection (tech) passed: {track}")


def test_track_detection_finance():
    """Test track detection for finance roles."""
    keywords = _load_keywords()
    
    role_title = "Quantitative Trading Analyst"
    jd_text = "Work on algorithmic trading systems, portfolio management, and derivatives pricing"
    track = detect_track(role_title, jd_text, keywords)
    
    assert track == "finance", f"Expected 'finance' track, got '{track}'"
    print(f"✅ Track detection (finance) passed: {track}")


def test_generic_title_rescue_tech():
    """Test generic title rescue for tech track with strong JD."""
    keywords = _load_keywords()
    
    role_title = "Software Engineering Intern"
    track = "tech"
    jd_score = 35  # Above tech threshold of 30
    
    should_rescue = should_rescue_generic_title(role_title, track, jd_score, keywords)
    assert should_rescue, "Should rescue generic tech title with JD score >= 30"
    print(f"✅ Generic title rescue (tech) passed: rescued with JD score {jd_score}")


def test_generic_title_rescue_finance():
    """Test generic title rescue for finance track with strong JD."""
    keywords = _load_keywords()
    
    role_title = "Finance Intern"
    track = "finance"
    jd_score = 25  # Above finance threshold of 20
    
    should_rescue = should_rescue_generic_title(role_title, track, jd_score, keywords)
    assert should_rescue, "Should rescue generic finance title with JD score >= 20"
    print(f"✅ Generic title rescue (finance) passed: rescued with JD score {jd_score}")


def test_generic_title_no_rescue():
    """Test that generic titles with weak JD are not rescued."""
    keywords = _load_keywords()
    
    role_title = "Intern"
    track = "tech"
    jd_score = 15  # Below tech threshold of 30
    
    should_rescue = should_rescue_generic_title(role_title, track, jd_score, keywords)
    assert not should_rescue, "Should NOT rescue generic title with low JD score"
    print(f"✅ Generic title no rescue passed: not rescued with JD score {jd_score}")


def test_edge_case_generic_title_strong_jd():
    """
    EDGE CASE: Generic title with strong JD should be rescued.
    Example: "Intern" role with detailed ML/AI job description.
    """
    internship = {
        "role": "Machine Learning Intern",
        "company": "AI Research Lab",
        "location": "Bangalore, India",
        "description": """
        We're seeking a talented intern to work on cutting-edge AI research.
        You'll use PyTorch and TensorFlow to build deep learning models for computer vision.
        Experience with transformers, CUDA, and model optimization is a plus.
        Work with our team on neural networks, classification, and regression tasks.
        """,
        "link": "https://example.com/job/123"
    }
    
    result = pre_score(internship)
    
    # Should have high score due to:
    # - High priority role match (+40)
    # - Strong JD score (multiple tier 1 keywords)
    # - Generic title rescue (+40)
    # - Location match (+20)
    
    assert result.score >= 80, f"Expected score >= 80 for rescued generic title, got {result.score}"
    assert result.breakdown.get("generic_title_rescued", 0) == 40, "Should have rescue bonus"
    print(f"✅ Edge case (generic title + strong JD) passed: score={result.score}, rescued={result.breakdown.get('generic_title_rescued', 0)}")


def test_edge_case_high_priority_with_disqualify():
    """
    EDGE CASE: High-priority role with disqualify keyword should NOT be disqualified.
    Example: "Sales Engineer" normally disqualifies, but "Machine Learning Sales Engineer" 
    should be rescued by high-priority "machine learning" keyword.
    """
    internship = {
        "role": "Machine Learning Sales Engineer",
        "company": "Tech Startup",
        "location": "Mumbai, India",
        "description": "Help customers understand our ML platform",
        "link": "https://example.com/job/456"
    }
    
    result = pre_score(internship)
    
    # Should NOT be disqualified because "machine learning" is high-priority
    assert result.status != "disqualified", f"Should not disqualify high-priority role, got status={result.status}"
    assert result.score > 0, f"Should have positive score, got {result.score}"
    assert result.breakdown.get("disqualify_overridden") == True, "Should show disqualification was overridden"
    print(f"✅ Edge case (high-priority + disqualify) passed: score={result.score}, override={result.breakdown.get('disqualify_overridden')}")


def test_edge_case_non_india_location():
    """
    EDGE CASE: Non-India location should be disqualified unless it mentions India or remote.
    """
    # Test 1: Pure non-India location (should disqualify)
    internship_usa = {
        "role": "Software Engineer",
        "company": "Tech Company",
        "location": "San Francisco, USA",
        "description": "Build amazing software",
        "link": "https://example.com/job/789"
    }
    
    result_usa = pre_score(internship_usa)
    assert result_usa.status == "disqualified", f"Should disqualify USA-only location, got status={result_usa.status}"
    print(f"✅ Edge case (non-India location) passed: USA location disqualified")
    
    # Test 2: Non-India location with remote (should NOT disqualify)
    internship_remote = {
        "role": "Software Engineer",
        "company": "Tech Company",
        "location": "San Francisco, USA (Remote OK)",
        "description": "Build amazing software",
        "link": "https://example.com/job/790"
    }
    
    result_remote = pre_score(internship_remote)
    assert result_remote.status != "disqualified", f"Should NOT disqualify remote-friendly location, got status={result_remote.status}"
    print(f"✅ Edge case (non-India + remote) passed: Remote location allowed")


def test_edge_case_global_city():
    """
    EDGE CASE: Global cities (Seattle, Boston, etc.) should receive location bonus.
    """
    internship = {
        "role": "AI Engineer",
        "company": "Tech Giant",
        "location": "Seattle, USA (Remote)",
        "description": "Work on AI systems",
        "link": "https://example.com/job/999"
    }
    
    result = pre_score(internship)
    
    # Should have location bonus for Seattle
    location_score = result.breakdown.get("location_match", 0) or result.breakdown.get("location_match_from_title", 0)
    assert location_score == 20, f"Should have location bonus for Seattle, got {location_score}"
    print(f"✅ Edge case (global city) passed: Seattle location bonus={location_score}")


def test_backward_compatibility():
    """
    Verify backward compatibility: pre_score() signature unchanged, 
    existing leads score correctly.
    """
    # Test with minimal internship (old format)
    internship = {
        "role": "Software Engineer",
        "company": "Startup",
        "location": "Bangalore",
        "link": "https://example.com/job"
    }
    
    result = pre_score(internship)
    
    # Should return PreScoreResult with score, status, breakdown
    assert hasattr(result, "score"), "Result should have 'score' attribute"
    assert hasattr(result, "status"), "Result should have 'status' attribute"
    assert hasattr(result, "breakdown"), "Result should have 'breakdown' attribute"
    assert isinstance(result.score, int), "Score should be integer"
    assert isinstance(result.status, str), "Status should be string"
    assert isinstance(result.breakdown, dict), "Breakdown should be dict"
    
    print(f"✅ Backward compatibility passed: score={result.score}, status={result.status}")


def test_comprehensive_scoring():
    """
    Test comprehensive scoring with all features combined.
    """
    internship = {
        "role": "AI Research Intern at YC Startup",
        "company": "Stealth AI Startup (YC W24)",
        "location": "Bangalore, India (Remote)",
        "description": """
        Join our AI research team to work on cutting-edge LLM technology.
        You'll use PyTorch, TensorFlow, and transformers to build foundation models.
        Experience with CUDA, model optimization, and neural networks required.
        Work on classification, regression, and deep learning projects.
        We use Kubernetes, Docker, AWS for ML infrastructure.
        Agile development with Git, testing, and CI/CD.
        """,
        "link": "https://example.com/job/comprehensive"
    }
    
    result = pre_score(internship)
    
    print(f"\n📊 Comprehensive Scoring Test Results:")
    print(f"   Total Score: {result.score}")
    print(f"   Status: {result.status}")
    print(f"   Breakdown:")
    for key, value in result.breakdown.items():
        print(f"      {key}: {value}")
    
    # Should have very high score due to:
    # - High priority role (AI Research) (+40)
    # - High priority company (YC) (+20)
    # - Location match (Bangalore + Remote) (+20)
    # - Strong JD score (many tier 1, 2, 3 keywords) (~50+)
    # - Generic title rescue (+40)
    
    assert result.score >= 100, f"Expected comprehensive score >= 100, got {result.score}"
    assert result.breakdown.get("high_priority_role", 0) == 40, "Should have high priority role bonus"
    assert result.breakdown.get("high_priority_company", 0) == 20, "Should have company bonus"
    assert result.breakdown.get("generic_title_rescued", 0) == 40, "Should have rescue bonus"
    
    print(f"✅ Comprehensive scoring passed: total score={result.score}")


def run_all_tests():
    """Run all test cases."""
    print("\n" + "=" * 80)
    print("🧪 RUNNING PIPELINE SCORING ENHANCEMENT TESTS")
    print("=" * 80 + "\n")
    
    tests = [
        ("Daily Limits", test_daily_limits),
        ("High Priority Keywords", test_high_priority_keywords),
        ("JD Scanning Basic", test_jd_scanning_basic),
        ("JD Scanning Caps", test_jd_scanning_caps),
        ("Track Detection (Tech)", test_track_detection_tech),
        ("Track Detection (Finance)", test_track_detection_finance),
        ("Generic Title Rescue (Tech)", test_generic_title_rescue_tech),
        ("Generic Title Rescue (Finance)", test_generic_title_rescue_finance),
        ("Generic Title No Rescue", test_generic_title_no_rescue),
        ("Edge Case: Generic Title + Strong JD", test_edge_case_generic_title_strong_jd),
        ("Edge Case: High Priority + Disqualify", test_edge_case_high_priority_with_disqualify),
        ("Edge Case: Non-India Location", test_edge_case_non_india_location),
        ("Edge Case: Global City", test_edge_case_global_city),
        ("Backward Compatibility", test_backward_compatibility),
        ("Comprehensive Scoring", test_comprehensive_scoring),
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        try:
            print(f"\n🔍 Testing: {test_name}")
            test_func()
            passed += 1
        except AssertionError as e:
            print(f"❌ FAILED: {test_name}")
            print(f"   Error: {e}")
            failed += 1
        except Exception as e:
            print(f"❌ ERROR: {test_name}")
            print(f"   Exception: {e}")
            failed += 1
    
    print("\n" + "=" * 80)
    print(f"📊 TEST RESULTS: {passed} passed, {failed} failed out of {len(tests)} tests")
    print("=" * 80 + "\n")
    
    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    exit(0 if success else 1)
