from __future__ import annotations

POSITIVE_SIGNALS = [
    "interested",
    "let's connect",
    "can you send",
    "interview",
    "would love",
    "tell me more",
]

NEGATIVE_SIGNALS = [
    "not hiring",
    "no openings",
    "unsubscribe",
    "not interested",
    "remove me",
]


def classify(email_body: str) -> str:
    body_lower = email_body.lower()
    if any(s in body_lower for s in POSITIVE_SIGNALS):
        return "positive"
    if any(s in body_lower for s in NEGATIVE_SIGNALS):
        return "negative"
    return "neutral"

