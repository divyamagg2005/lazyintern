from __future__ import annotations

import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
KEYWORDS_PATH = PROJECT_ROOT / "data" / "keywords.json"


def _load_keywords() -> dict:
    if KEYWORDS_PATH.exists():
        return json.loads(KEYWORDS_PATH.read_text(encoding="utf-8"))
    return {}


def classify(email_body: str) -> str:
    """
    Classify email reply as positive, negative, or neutral using keywords.
    Keywords loaded from data/keywords.json for easy tuning.
    """
    keywords = _load_keywords()
    reply_keywords = keywords.get("reply_classification", {})
    
    positive_signals = [s.lower() for s in reply_keywords.get("positive", [])]
    negative_signals = [s.lower() for s in reply_keywords.get("negative", [])]
    neutral_signals = [s.lower() for s in reply_keywords.get("neutral", [])]
    
    body_lower = email_body.lower()
    
    # Check positive first (most important)
    if any(s in body_lower for s in positive_signals):
        return "positive"
    
    # Then negative
    if any(s in body_lower for s in negative_signals):
        return "negative"
    
    # Then neutral (auto-replies, OOO)
    if any(s in body_lower for s in neutral_signals):
        return "neutral"
    
    # Default to neutral if no keywords match
    return "neutral"


