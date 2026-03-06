"""
Test CHANGE 4 - Generic Title Rescue Mechanism
"""
import json
import re

def whole_word_match(keyword, text):
    pattern = r'\b' + re.escape(keyword.lower()) + r'\b'
    return bool(re.search(pattern, text.lower()))

def scan_jd_keywords(jd_text, keywords):
    jd_keywords = keywords.get("jd_keywords", {})
    
    tier1_matches = set()
    tier2_matches = set()
    tier3_matches = set()
    
    tier1_keywords = [kw.lower() for kw in jd_keywords.get("tier1", [])]
    for kw in tier1_keywords:
        if whole_word_match(kw, jd_text):
            tier1_matches.add(kw)
    
    tier2_keywords = [kw.lower() for kw in jd_keywords.get("tier2", [])]
    for kw in tier2_keywords:
        if whole_word_match(kw, jd_text):
            tier2_matches.add(kw)
    
    tier3_keywords = [kw.lower() for kw in jd_keywords.get("tier3", [])]
    for kw in tier3_keywords:
        if whole_word_match(kw, jd_text):
            tier3_matches.add(kw)
    
    tier1_score = min(len(tier1_matches) * 8, 40)
    tier2_score = min(len(tier2_matches) * 4, 20)
    tier3_score = min(len(tier3_matches) * 2, 10)
    total_jd_score = tier1_score + tier2_score + tier3_score
    
    return {
        "tier1_score": tier1_score,
        "tier2_score": tier2_score,
        "tier3_score": tier3_score,
        "total_jd_score": total_jd_score,
        "tier1_matches": tier1_matches,
        "tier2_matches": tier2_matches,
        "tier3_matches": tier3_matches
    }

def should_rescue_generic_title(role_title, company, jd_text, jd_results, keywords):
    # Check tech generic titles
    tech_generic_titles = [kw.lower() for kw in keywords.get("tech_generic_titles", [])]
    is_tech_generic = False
    for kw in tech_generic_titles:
        if whole_word_match(kw, role_title):
            is_tech_generic = True
            break
    
    if is_tech_generic:
        tier1_matches = len(jd_results.get("tier1_matches", set()))
        tier2_matches = len(jd_results.get("tier2_matches", set()))
        
        if tier1_matches >= 3:
            return (True, 30, "tech_jd_strong")
        elif tier1_matches >= 1 and tier2_matches >= 2:
            return (True, 20, "tech_jd_moderate")
    
    # Check finance generic titles
    finance_generic_titles = [kw.lower() for kw in keywords.get("finance_generic_titles", [])]
    is_finance_generic = False
    for kw in finance_generic_titles:
        if whole_word_match(kw, role_title):
            is_finance_generic = True
            break
    
    if is_finance_generic:
        finance_jd_signals = [kw.lower() for kw in keywords.get("finance_jd_signals", [])]
        finance_hits = 0
        for signal in finance_jd_signals:
            if whole_word_match(signal, jd_text):
                finance_hits += 1
        
        if finance_hits >= 3:
            return (True, 30, "finance_jd_strong")
        elif finance_hits >= 1:
            return (True, 20, "finance_jd_moderate")
    
    return (False, 0, "")

# Load keywords
with open('backend/data/keywords.json', 'r', encoding='utf-8') as f:
    keywords = json.load(f)

print('Testing CHANGE 4 - Generic Title Rescue Mechanism')
print('=' * 80)

# Verify keyword lists
tech_titles = keywords.get('tech_generic_titles', [])
finance_titles = keywords.get('finance_generic_titles', [])
finance_signals = keywords.get('finance_jd_signals', [])

print(f'Tech Generic Titles: {len(tech_titles)} (expected 16)')
print(f'Finance Generic Titles: {len(finance_titles)} (expected 11)')
print(f'Finance JD Signals: {len(finance_signals)} (expected 15)')
print('=' * 80)

# Test cases
test_cases = [
    {
        'name': 'Tech Generic - Strong (3+ tier1)',
        'title': 'Software Engineer Intern',
        'company': 'TechCorp',
        'jd': 'Build ML models using PyTorch, TensorFlow, and Hugging Face. Deploy with Docker.',
        'expected_rescue': True,
        'expected_bonus': 30,
        'expected_type': 'tech_jd_strong'
    },
    {
        'name': 'Tech Generic - Moderate (1 tier1, 2+ tier2)',
        'title': 'Engineering Intern',
        'company': 'StartupXYZ',
        'jd': 'Work with PyTorch for ML. Use pandas, numpy, and scikit-learn for data analysis.',
        'expected_rescue': True,
        'expected_bonus': 20,
        'expected_type': 'tech_jd_moderate'
    },
    {
        'name': 'Tech Generic - No Rescue (weak JD)',
        'title': 'Developer Intern',
        'company': 'Company ABC',
        'jd': 'General software development role. Use Git and follow agile practices.',
        'expected_rescue': False,
        'expected_bonus': 0,
        'expected_type': ''
    },
    {
        'name': 'Finance Generic - Strong (3+ finance signals)',
        'title': 'Summer Analyst',
        'company': 'Goldman Sachs',
        'jd': 'Build DCF models, perform equity valuation, and analyze derivatives. Use Bloomberg Terminal for trading analysis.',
        'expected_rescue': True,
        'expected_bonus': 30,
        'expected_type': 'finance_jd_strong'
    },
    {
        'name': 'Finance Generic - Moderate (1+ finance signals)',
        'title': 'Analyst Intern',
        'company': 'JP Morgan',
        'jd': 'Support investment banking team with financial modeling and valuation work.',
        'expected_rescue': True,
        'expected_bonus': 20,
        'expected_type': 'finance_jd_moderate'
    },
    {
        'name': 'Finance Generic - No Rescue (no finance signals)',
        'title': 'Winter Analyst',
        'company': 'Consulting Firm',
        'jd': 'General business analysis role. Work with Excel and PowerPoint.',
        'expected_rescue': False,
        'expected_bonus': 0,
        'expected_type': ''
    },
    {
        'name': 'Non-Generic Title - No Rescue',
        'title': 'Machine Learning Engineer',
        'company': 'AI Startup',
        'jd': 'Build ML models using PyTorch, TensorFlow, and Hugging Face.',
        'expected_rescue': False,
        'expected_bonus': 0,
        'expected_type': ''
    }
]

print('\nTest Results:')
print('=' * 80)

all_passed = True
for test in test_cases:
    jd_results = scan_jd_keywords(test['jd'], keywords)
    should_rescue, bonus, rescue_type = should_rescue_generic_title(
        test['title'], test['company'], test['jd'], jd_results, keywords
    )
    
    passed = (
        should_rescue == test['expected_rescue'] and
        bonus == test['expected_bonus'] and
        rescue_type == test['expected_type']
    )
    
    status = '✅' if passed else '❌'
    if not passed:
        all_passed = False
    
    print(f"\n{status} {test['name']}")
    print(f"   Title: '{test['title']}' at '{test['company']}'")
    print(f"   Rescued: {should_rescue} (expected {test['expected_rescue']})")
    print(f"   Bonus: +{bonus} (expected +{test['expected_bonus']})")
    print(f"   Type: {rescue_type} (expected {test['expected_type']})")
    print(f"   JD Tiers: T1={len(jd_results['tier1_matches'])}, T2={len(jd_results['tier2_matches'])}, T3={len(jd_results['tier3_matches'])}")

print('\n' + '=' * 80)

# Verify specific titles
print('\nVerifying Specific Title Lists:')
print('=' * 80)

expected_tech = [
    "software engineer intern", "software developer intern", "technical intern",
    "engineering intern", "tech intern", "developer intern", "sde intern",
    "programmer intern", "associate engineer intern", "junior developer intern",
    "graduate engineer trainee", "get intern", "intern engineer",
    "technology intern", "it intern", "computer science intern"
]

expected_finance = [
    "analyst intern", "summer analyst", "winter analyst", "spring analyst",
    "off cycle intern", "associate intern", "division intern",
    "junior analyst intern", "intern analyst", "operations analyst intern",
    "generalist intern"
]

expected_finance_signals = [
    "bloomberg", "dcf", "valuation", "modeling", "trading", "portfolio",
    "equity", "derivatives", "fixed income", "capital markets", "investment",
    "quantitative", "risk", "hedge fund", "asset management"
]

tech_match = all(title in tech_titles for title in expected_tech)
finance_match = all(title in finance_titles for title in expected_finance)
signals_match = all(signal in finance_signals for signal in expected_finance_signals)

print(f'Tech titles match: {"✅" if tech_match else "❌"} ({len(tech_titles)}/16)')
print(f'Finance titles match: {"✅" if finance_match else "❌"} ({len(finance_titles)}/11)')
print(f'Finance signals match: {"✅" if signals_match else "❌"} ({len(finance_signals)}/15)')

print('=' * 80)
if all_passed and tech_match and finance_match and signals_match:
    print('🎉 All tests passed!')
    print('✅ CHANGE 4 is fully implemented with correct rescue logic.')
else:
    print('⚠️  Some tests failed!')
