# Design Document: Pipeline Scoring Enhancement

## Overview

This design enhances the LazyIntern pipeline's pre-scoring system to improve lead qualification accuracy through expanded keyword matching, job description analysis, and intelligent rescue mechanisms. The enhancement operates entirely through local regex and string operations without introducing additional API calls, maintaining the system's zero-cost constraint.

### Key Enhancements

1. **Expanded Daily Limits**: Increase SMS capacity from 15 to 50 messages per day
2. **Comprehensive Role Keywords**: Expand high-priority keywords to cover AI/ML, data science, robotics, backend/full-stack, systems, cloud/MLOps, mobile, and investment banking/quant roles
3. **JD-Based Keyword Scanning**: Three-tier keyword system that analyzes job descriptions for technical depth
4. **Generic Title Rescue**: Mechanism to upgrade generic-titled roles when JD demonstrates strong technical content
5. **Track Detection**: Classify leads as "tech" or "finance" based on keyword analysis
6. **Enhanced Disqualification**: Expanded filters with critical override rule for high-priority keywords
7. **Expanded Bonuses**: Additional company and location keywords
8. **Detailed Logging**: Full score breakdown for transparency and debugging

### Design Principles

- **Zero-Cost Operation**: All enhancements use local regex/string matching only
- **Backward Compatibility**: Existing scoring logic remains intact, new features are additive
- **Transparency**: Comprehensive logging shows exactly how scores are calculated
- **Maintainability**: Keywords stored in JSON configuration for easy updates
- **Performance**: Efficient regex patterns with word boundaries to prevent false matches

## Architecture

### Component Overview

The pre-scoring system consists of these components:

```
┌─────────────────────────────────────────────────────────────┐
│                     Pre-Scorer Module                        │
│                                                              │
│  ┌────────────────┐      ┌──────────────────┐             │
│  │  Keyword       │      │  Score           │             │
│  │  Loader        │─────▶│  Calculator      │             │
│  └────────────────┘      └──────────────────┘             │
│         │                         │                         │
│         │                         ▼                         │
│         │                ┌──────────────────┐             │
│         │                │  JD Scanner      │             │
│         │                │  (3-tier)        │             │
│         │                └──────────────────┘             │
│         │                         │                         │
│         │                         ▼                         │
│         │                ┌──────────────────┐             │
│         │                │  Track Detector  │             │
│         │                └──────────────────┘             │
│         │                         │                         │
│         │                         ▼                         │
│         │                ┌──────────────────┐             │
│         │                │  Rescue          │             │
│         │                │  Mechanism       │             │
│         │                └──────────────────┘             │
│         │                         │                         │
│         ▼                         ▼                         │
│  ┌────────────────────────────────────────┐               │
│  │     Disqualification Filter            │               │
│  │     (with override logic)              │               │
│  └────────────────────────────────────────┘               │
│                    │                                        │
│                    ▼                                        │
│         ┌──────────────────┐                               │
│         │  Score Result    │                               │
│         │  + Breakdown     │                               │
│         └──────────────────┘                               │
└─────────────────────────────────────────────────────────────┘
```

### Processing Flow

1. **Load Keywords**: Read keyword configuration from `keywords.json`
2. **Initial Scoring**: Apply title, company, and location bonuses
3. **JD Scanning**: Analyze job description for technical keywords (3 tiers)
4. **Track Detection**: Classify lead as tech or finance based on keywords
5. **Rescue Evaluation**: Check if generic titles should be upgraded based on JD strength
6. **Disqualification Check**: Apply filters with override logic for high-priority keywords
7. **Score Aggregation**: Combine all components with detailed breakdown
8. **Result Return**: Provide score, status, and breakdown for logging

### Integration Points

- **Keywords Configuration** (`backend/data/keywords.json`): Central keyword repository
- **Pre-Scorer Module** (`backend/pipeline/pre_scorer.py`): Core scoring logic
- **SMS Sender** (`backend/approval/twilio_sender.py`): Daily limit enforcement
- **Cycle Manager** (`backend/scheduler/cycle_manager.py`): Status logging
- **Dashboard API** (`backend/api/routes/dashboard.py`): Limit display

## Components and Interfaces

### 1. Keyword Loader

**Purpose**: Load and parse keyword configuration from JSON

**Interface**:
```python
def _load_keywords() -> dict[str, Any]:
    """Load keywords from keywords.json"""
    pass
```

**Responsibilities**:
- Read keywords.json file
- Parse JSON structure
- Return keyword dictionary
- Handle missing file gracefully

### 2. Score Calculator
