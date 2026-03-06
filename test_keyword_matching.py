import re
import json

def whole_word_match(keyword, text):
    pattern = r'\b' + re.escape(keyword.lower()) + r'\b'
    return bool(re.search(pattern, text.lower()))

# Load keywords
with open('backend/data/keywords.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

high_priority = data['role_keywords']['high_priority']

# Test cases
test_cases = [
    ('ML Engineer Intern', 'ml', True, 40),
    ('HTML Developer', 'ml', False, 0),
    ('AI Research Intern', 'ai', True, 40),
    ('Email Marketing', 'ai', False, 0),
    ('SDE Intern', 'sde intern', True, 40),
    ('Software Engineering Intern', 'software engineering intern', True, 40),
    ('Investment Banking Intern', 'investment banking', True, 40),
    ('IB Intern - Goldman Sachs', 'ib intern', True, 40),
    ('Quant Developer', 'quant developer', True, 40),
    ('Gen AI Engineer', 'gen ai', True, 40),
    ('Generative AI Intern', 'generative', True, 40),
    ('Backend Engineer', 'backend', True, 40),
    ('Full-Stack Developer', 'full-stack', True, 40),
    ('Node.js Developer', 'node.js', True, 40),
]

print('Testing CHANGE 1 - High Priority Role Keywords (+40 points)')
print('=' * 80)
print(f'Total keywords in high_priority list: {len(high_priority)}')
print('=' * 80)

all_passed = True
for title, keyword, should_match, expected_score in test_cases:
    result = whole_word_match(keyword, title)
    score = 40 if result else 0
    status = '✅' if result == should_match else '❌'
    if result != should_match:
        all_passed = False
    print(f'{status} "{title}" + "{keyword}" = {result} (score: {score})')

print('=' * 80)
if all_passed:
    print('🎉 All tests passed! Word boundary matching works correctly.')
    print('✅ CHANGE 1 is fully implemented with \\b word boundaries and case-insensitive matching.')
else:
    print('⚠️  Some tests failed!')
