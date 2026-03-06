# Implementation Plan: Pipeline Scoring Enhancement

## Overview

This plan implements enhancements to the LazyIntern pipeline's pre-scoring system. All changes are local regex/string operations with zero new API calls. The main file to modify is `backend/pipeline/pre_scorer.py`, with keyword updates in `backend/data/keywords.json`. The pre_score() function signature remains unchanged for backward compatibility.

## Tasks

- [x] 1. Update daily send limit constants
  - Update MAX_SMS_PER_DAY from 15 to 50 in pre_scorer.py
  - Update MAX_EMAILS_PER_DAY from 15 to 50 in pre_scorer.py
  - Update SMS_Sender limit checks in backend/approval/twilio_sender.py
  - Update Cycle_Manager logging format to show "📧 {n}/50 emails | 📱 {n}/50 SMS" in backend/scheduler/cycle_manager.py
  - Update Dashboard API to display new limits in backend/api/routes/dashboard.py
  - _Requirements: 1.1, 1.2, 1.3, 1.4_

- [x] 2. Expand high priority role keywords in keywords.json
  - [x] 2.1 Add AI/ML keywords to high_priority list
    - Add: ai, machine learning, deep learning, neural networks, nlp, llm, computer vision, generative ai, reinforcement learning, ml engineer, ai engineer, research scientist, applied scientist
    - _Requirements: 2.3_
  
  - [x] 2.2 Add data science keywords to high_priority list
    - Add: data science, data scientist, quantitative researcher, analytics, statistical modeling
    - _Requirements: 2.4_
  
  - [x] 2.3 Add robotics keywords to high_priority list
    - Add: robotics, autonomous systems, perception, planning, control systems, slam, sensor fusion
    - _Requirements: 2.5_
  
  - [x] 2.4 Add backend/full-stack keywords to high_priority list
    - Add: backend engineer, backend developer, full stack engineer, full stack developer, software engineer, platform engineer, systems engineer
    - _Requirements: 2.6_
  
  - [x] 2.5 Add systems programming keywords to high_priority list
    - Add: systems programming, distributed systems, infrastructure engineer, performance engineering, low-level programming
    - _Requirements: 2.7_
  
  - [x] 2.6 Add cloud/MLOps keywords to high_priority list
    - Add: mlops, ml infrastructure, cloud engineer, devops engineer, site reliability engineer, sre, platform engineering
    - _Requirements: 2.8_
  
  - [x] 2.7 Add mobile development keywords to high_priority list
    - Add: mobile engineer, ios developer, android developer, react native, flutter, mobile development
    - _Requirements: 2.9_
  
  - [x] 2.8 Add investment banking/quant keywords to high_priority list
    - Add: investment banking, quantitative trading, algorithmic trading, quant developer, trading systems, financial engineering
    - _Requirements: 2.10_
  
  - [x] 2.9 Add finance role keywords to high_priority list
    - Add: financial analyst, risk analyst, portfolio management, derivatives, fixed income, equity research
    - _Requirements: 2.11_

- [x] 3. Implement JD-based keyword scanning with 3-tier system
  - [x] 3.1 Add JD keyword tiers to keywords.json
    - Create "jd_keywords" section with tier1, tier2, tier3 arrays
    - Tier 1 (frameworks/tools): pytorch, tensorflow, react, kubernetes, aws, docker, etc.
    - Tier 2 (algorithms/tasks): optimization, classification, regression, api design, etc.
    - Tier 3 (general practices): agile, git, testing, documentation, etc.
    - _Requirements: 3.1, 3.2, 3.3, 3.4_
  
  - [x] 3.2 Implement scan_jd_keywords() function in pre_scorer.py
    - Accept jd_text and keywords dict as parameters
    - Use whole_word_match() for each tier
    - Track unique matches per tier (avoid double-counting)
    - Apply tier-specific caps: Tier 1 (+8 each, max +40), Tier 2 (+4 each, max +20), Tier 3 (+2 each, max +10)
    - Return dict with tier1_score, tier2_score, tier3_score, total_jd_score
    - _Requirements: 3.5, 3.6, 3.7, 3.8, 3.9_
  
  - [x] 3.3 Integrate JD scanning into pre_score() function
    - Call scan_jd_keywords() after initial title/company/location scoring
    - Add JD scores to breakdown dict (jd_tier1, jd_tier2, jd_tier3)
    - Add JD scores to total score
    - _Requirements: 3.10_

- [x] 4. Implement track detection system
  - [x] 4.1 Add finance_track_keywords to keywords.json
    - Add keywords: trading, investment, portfolio, derivatives, equity, fixed income, risk management, financial modeling, quantitative finance, hedge fund, asset management
    - _Requirements: 4.1_
  
  - [x] 4.2 Implement detect_track() function in pre_scorer.py
    - Accept role_title, jd_text, and keywords dict as parameters
    - Check for finance_track_keywords in title and JD
    - Return "finance" if 2+ finance keywords found, else "tech"
    - _Requirements: 4.2, 4.3_
  
  - [x] 4.3 Integrate track detection into pre_score() function
    - Call detect_track() after JD scanning
    - Store track in breakdown dict for logging
    - _Requirements: 4.4_

- [x] 5. Implement generic title rescue mechanism
  - [x] 5.1 Add generic_titles list to keywords.json
    - Add: intern, internship, trainee, apprentice, associate, junior, entry level, graduate, fresher
    - _Requirements: 5.1_
  
  - [x] 5.2 Implement should_rescue_generic_title() function in pre_scorer.py
    - Accept role_title, track, jd_score, and keywords dict as parameters
    - Check if title matches generic_titles using whole_word_match()
    - For tech track: rescue if jd_score >= 30
    - For finance track: rescue if jd_score >= 20
    - Return boolean indicating rescue decision
    - _Requirements: 5.2, 5.3, 5.4_
  
  - [x] 5.3 Integrate rescue mechanism into pre_score() function
    - Call should_rescue_generic_title() after track detection
    - If rescued, add +40 points and set breakdown["generic_title_rescued"] = 40
    - Log rescue decision with track and JD score
    - _Requirements: 5.5, 5.6_

- [x] 6. Enhance disqualification filters with override logic
  - [x] 6.1 Expand disqualify keywords in keywords.json
    - Add: sales engineer, business development, account manager, customer success manager, technical support, help desk, data entry, administrative, clerical, receptionist, office manager
    - _Requirements: 6.1_
  
  - [x] 6.2 Implement critical override rule in pre_score() function
    - Move disqualification check to AFTER high_priority_role matching
    - If high_priority_role matched (breakdown contains "high_priority_role"), skip disqualification
    - Log override decision when it occurs
    - _Requirements: 6.2, 6.3, 6.4_

- [x] 7. Expand company bonus keywords
  - [x] 7.1 Add new company keywords to keywords.json high_priority list
    - Add: unicorn, decacorn, forbes cloud 100, fast company, inc 5000, techstars, 500 startups, sequoia, andreessen horowitz, a16z, accel, benchmark, greylock
    - _Requirements: 7.1_

- [x] 8. Expand location keywords
  - [x] 8.1 Add new India cities to preferred_cities_india in keywords.json
    - Add: Kolkata, Ahmedabad, Jaipur, Chandigarh, Kochi, Indore, Coimbatore, Thiruvananthapuram
    - _Requirements: 8.1_
  
  - [x] 8.2 Add new global cities to preferred_cities_global in keywords.json
    - Add: Seattle, Boston, Austin, Paris, Tel Aviv, Dubai, Hong Kong, Tokyo, Sydney, Melbourne
    - _Requirements: 8.2_

- [x] 9. Update logging format with full breakdown
  - [x] 9.1 Enhance pre_score() logging output
    - Include all breakdown components in log message
    - Show: title score, company score, location score, JD scores (tier1/2/3), track, rescue status, disqualification status
    - Format: "Pre-score: {total} | Title: +{n} | Company: +{n} | Location: +{n} | JD: +{n} (T1:{n}, T2:{n}, T3:{n}) | Track: {track} | Rescued: {yes/no} | Role: '{title}'"
    - _Requirements: 9.1, 9.2_

- [x] 10. Checkpoint - Verify all changes and run tests
  - Ensure all tests pass, verify scoring logic with sample leads
  - Test edge cases: generic titles with strong JDs, high-priority roles with disqualify keywords, non-India locations
  - Verify backward compatibility: pre_score() signature unchanged, existing leads score correctly
  - Ask the user if questions arise

## Notes

- All tasks modify existing files; no new files created except tasks.md
- Keywords.json changes are additive; existing keywords remain
- Pre_scorer.py maintains backward compatibility with unchanged function signature
- All new functions use existing whole_word_match() helper for consistency
- Zero new API calls; all operations are local regex/string matching
- Testing tasks are integrated as checkpoint verification steps
