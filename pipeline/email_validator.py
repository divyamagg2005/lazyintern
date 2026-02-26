from __future__ import annotations

import time
import re
from dataclasses import dataclass
from pathlib import Path

import httpx
import dns.resolver

from core.config import settings

RFC_REGEX = re.compile(
    r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
)

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DISPOSABLE_PATH = PROJECT_ROOT / "data" / "disposable_domains.txt"
DISPOSABLE_LIST_URL = "https://raw.githubusercontent.com/disposable-email-domains/disposable-email-domains/refs/heads/main/disposable_email_blocklist.conf"


@dataclass
class ValidationResult:
    valid: bool
    reason: str | None = None
    mx_valid: bool = False
    smtp_valid: bool = False


def refresh_disposable_list_if_stale(*, max_age_days: int = 7) -> bool:
    """
    Refresh disposable domain blocklist if file is missing/old.

    Returns True if we downloaded a fresh copy, else False.
    """
    try:
        if DISPOSABLE_PATH.exists():
            age_days = (time.time() - DISPOSABLE_PATH.stat().st_mtime) / 86400.0
            if age_days <= max_age_days:
                return False
        else:
            DISPOSABLE_PATH.parent.mkdir(parents=True, exist_ok=True)

        resp = httpx.get(DISPOSABLE_LIST_URL, timeout=20.0, follow_redirects=True)
        resp.raise_for_status()

        tmp = DISPOSABLE_PATH.with_suffix(".tmp")
        tmp.write_text(resp.text, encoding="utf-8")
        tmp.replace(DISPOSABLE_PATH)
        return True
    except Exception:
        # Never fail validation because refresh failed.
        return False


def _load_disposable() -> set[str]:
    refresh_disposable_list_if_stale()
    if not DISPOSABLE_PATH.exists():
        return set()
    lines = DISPOSABLE_PATH.read_text(encoding="utf-8").splitlines()
    return {ln.strip().lower() for ln in lines if ln.strip() and not ln.strip().startswith("#")}


def validate_email(email: str, confidence: int) -> ValidationResult:
    """
    Returns ValidationResult with MX check and optional SMTP ping.
    """
    if not RFC_REGEX.match(email):
        return ValidationResult(valid=False, reason="format_invalid")

    domain = email.split("@", 1)[1].lower()
    disposable = _load_disposable()
    if domain in disposable:
        return ValidationResult(valid=False, reason="disposable_domain")

    # MX check
    try:
        records = dns.resolver.resolve(domain, "MX")
        mx_valid = bool(records)
    except Exception:
        return ValidationResult(valid=False, reason="mx_failure", mx_valid=False)

    if not settings.enable_smtp_ping or confidence >= 90:
        return ValidationResult(valid=True, reason=None, mx_valid=mx_valid, smtp_valid=False)

    # Optional SMTP handshake would go here; skipped in initial version.
    return ValidationResult(valid=True, reason=None, mx_valid=mx_valid, smtp_valid=False)

