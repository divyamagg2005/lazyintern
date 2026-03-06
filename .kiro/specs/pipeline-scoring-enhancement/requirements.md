# Requirements Document

## Introduction

This document specifies requirements for enhancing the LazyIntern pipeline's pre-scoring system. The enhancement includes expanded keyword lists for role matching, job description-based scanning, generic title rescue mechanisms, track detection for tech vs finance roles, enhanced disqualification filters, expanded company and location bonuses, and updated daily send limits. All enhancements must operate without additional API calls, using only local regex and string operations.

## Glossary

- **Pre_Scorer**: The component that evaluates job leads and assigns initial scores before full evaluation
- **Lead**: A job opportunity record containing fields like title, company, location, and job description
- **JD**: Job Description text field in a Lead
- **Track**: Classification of a Lead as either "tech" or "finance" based on keyword analysis
- **Rescue_Mechanism**: Logic that upgrades generic-titled Leads when their JD contains strong relevant keywords
- **Tier1_Keywords**: Highest-value technical keywords in JD scanning (frameworks, tools, specialized domains)
- **Tier2_Keywords**: Medium-value technical keywords in JD scanning (algorithms, tasks, infrastructure)
- **Tier3_Keywords**: Low-value supporting keywords in JD scanning (general practices, tools)
- **Finance_Track_Keywords**: Keywords that indicate finance-oriented roles
- **High_Priority_Keywords**: Role title keywords that receive +40 point bonus
- **Medium_Priority_Keywords**: Role title keywords that receive +20 point bonus
- **Disqualify_Keywords**: Role title keywords that result in -100 points (instant rejection)
- **Company_Bonus_Keywords**: Company name keywords that receive +20 point bonus
- **Location_Keywords**: Location keywords that receive +20 point bonus
- **SMS_Sender**: Component that sends SMS messages to approved leads
- **Cycle_Manager**: Component that orchestrates pipeline execution cycles and logging

## Requirements

### Requirement 1: Update Daily Send Limits

**User Story:** As a pipeline operator, I want increased SMS capacity, so that I can reach more candidates per day.

#### Acceptance Criteria

1. THE Pre_Scorer SHALL use a MAX_SMS_PER_DAY constant value of 50
2. THE Pre_Scorer SHALL use a MAX_EMAILS_PER_DAY constant value of 50
3. WHEN checking SMS send limits, THE SMS_Sender SHALL compare against a threshold of 50
4. WHEN logging daily status, THE Cycle_Manager SHALL display format "📧 {n}/50 emails | 📱 {n}/50 SMS"

### Requirement 2: Expand High Priority Role Keywords

**User Story:** As a pipeline operator, I want comprehensive role keyword matching, so that I can identify all relevant technical and finance opportunities.

#### Acceptance Criteria

1. THE Pre_Scorer SHALL award +40 points WHEN a Lead title matches any High_Priority_Keywords
2. THE Pre_Scorer SHALL use case-insensitive matching with word boundaries for High_Priority_Keywords
3. THE Pre_Scorer SHALL include AI/ML keywords in High_Priority_Keywords (ai, machine learning, deep learning, neural networks, nlp, llm, computer vision, generative ai, reinforcement