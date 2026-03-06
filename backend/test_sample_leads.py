"""
Test scoring with realistic sample leads to verify all enhancements work correctly.
"""

from pipeline.pre_scorer import pre_score


def print_score_breakdown(internship, result):
    """Pretty print scoring breakdown."""
    print(f"\n{'='*80}")
    print(f"Role: {internship['role']}")
    print(f"Company: {internship['company']}")
    print(f"Location: {internship['location']}")
    print(f"{'='*80}")
    print(f"Total Score: {result.score}")
    print(f"Status: {result.status}")
    print(f"\nBreakdown:")
    for key, value in sorted(result.breakdown.items()):
        if isinstance(value, (int, float)):
            print(f"  {key:30s}: +{value}")
        else:
            print(f"  {key:30s}: {value}")
    print(f"{'='*80}\n")


def test_sample_leads():
    """Test with realistic sample leads."""
    
    print("\n" + "="*80)
    print("🧪 TESTING SAMPLE LEADS")
    print("="*80)
    
    # Sample 1: High-quality AI/ML role with strong JD
    sample1 = {
        "role": "Machine Learning Research Intern",
        "company": "OpenAI Research Lab",
        "location": "Remote, India",
        "description": """
        Join our AI research team working on large language models and transformers.
        You'll use PyTorch and TensorFlow to train foundation models on GPUs with CUDA.
        Experience with neural networks, deep learning, and model optimization required.
        Work on classification, regression, and NLP tasks using HuggingFace transformers.
        Collaborate using Git, agile methodologies, and CI/CD pipelines.
        """,
        "link": "https://openai.com/careers/ml-intern"
    }
    
    result1 = pre_score(sample1)
    print_score_breakdown(sample1, result1)
    assert result1.score >= 100, f"Expected high score for quality ML role, got {result1.score}"
    
    # Sample 2: Generic title with strong JD (should be rescued)
    sample2 = {
        "role": "Software Engineering Intern",
        "company": "YC Startup",
        "location": "Bangalore",
        "description": """
        Build scalable backend systems using Python, FastAPI, and PostgreSQL.
        Deploy on AWS with Docker and Kubernetes. Work with React frontend.
        Experience with microservices, REST APIs, and database design.
        Use Git for version control and participate in code reviews.
        """,
        "link": "https://ycstartup.com/careers"
    }
    
    result2 = pre_score(sample2)
    print_score_breakdown(sample2, result2)
    assert result2.breakdown.get("generic_title_rescued", 0) == 40, "Should rescue generic title with strong JD"
    
    # Sample 3: Finance/quant role
    sample3 = {
        "role": "Quantitative Trading Intern",
        "company": "Hedge Fund",
        "location": "Mumbai",
        "description": """
        Work on algorithmic trading systems and portfolio optimization.
        Build models for derivatives pricing and risk management.
        Use Python for financial modeling and quantitative analysis.
        Experience with statistical modeling and data analysis required.
        """,
        "link": "https://hedgefund.com/careers"
    }
    
    result3 = pre_score(sample3)
    print_score_breakdown(sample3, result3)
    assert result3.breakdown.get("track") == "finance", "Should detect finance track"
    
    # Sample 4: High-priority role with disqualify keyword (should override)
    sample4 = {
        "role": "AI Sales Engineer",
        "company": "Tech Company",
        "location": "Delhi",
        "description": """
        Help customers understand our AI platform and machine learning solutions.
        Technical pre-sales role requiring deep learning and NLP knowledge.
        """,
        "link": "https://techcompany.com/careers"
    }
    
    result4 = pre_score(sample4)
    print_score_breakdown(sample4, result4)
    assert result4.status != "disqualified", "Should not disqualify high-priority role"
    assert result4.breakdown.get("disqualify_overridden") == True, "Should show override"
    
    # Sample 5: Non-India location (should disqualify)
    sample5 = {
        "role": "Software Engineer",
        "company": "US Company",
        "location": "New York, USA",
        "description": "Build software in our NYC office",
        "link": "https://uscompany.com/careers"
    }
    
    result5 = pre_score(sample5)
    print_score_breakdown(sample5, result5)
    assert result5.status == "disqualified", "Should disqualify non-India location"
    
    # Sample 6: Global city with remote (should NOT disqualify)
    sample6 = {
        "role": "Backend Engineer",
        "company": "Global Startup",
        "location": "Seattle, USA (Remote)",
        "description": "Build distributed systems with Python and Kubernetes",
        "link": "https://globalstartup.com/careers"
    }
    
    result6 = pre_score(sample6)
    print_score_breakdown(sample6, result6)
    assert result6.status != "disqualified", "Should not disqualify remote-friendly location"
    assert result6.breakdown.get("location_match", 0) == 20, "Should have Seattle location bonus"
    
    # Sample 7: Generic title with weak JD (should NOT be rescued)
    sample7 = {
        "role": "Intern",
        "company": "Small Company",
        "location": "Pune",
        "description": "General internship opportunity. Learn and grow with us.",
        "link": "https://smallcompany.com/careers"
    }
    
    result7 = pre_score(sample7)
    print_score_breakdown(sample7, result7)
    assert result7.breakdown.get("generic_title_rescued", 0) == 0, "Should NOT rescue weak JD"
    
    print("\n" + "="*80)
    print("✅ ALL SAMPLE LEAD TESTS PASSED")
    print("="*80 + "\n")


if __name__ == "__main__":
    test_sample_leads()
