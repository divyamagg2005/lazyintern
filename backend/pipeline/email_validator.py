from __future__ import annotations

import time
import re
import smtplib
from dataclasses import dataclass
from pathlib import Path

import httpx
import dns.resolver

from core.config import settings
from core.logger import logger

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
        logger.info("Disposable domains list refreshed")
        return True
    except Exception as e:
        logger.warning(f"Failed to refresh disposable list: {e}")
        return False


def _load_disposable() -> set[str]:
    refresh_disposable_list_if_stale()
    if not DISPOSABLE_PATH.exists():
        return set()
    lines = DISPOSABLE_PATH.read_text(encoding="utf-8").splitlines()
    return {ln.strip().lower() for ln in lines if ln.strip() and not ln.strip().startswith("#")}


def _smtp_ping(email: str, mx_host: str) -> bool:
    """
    Perform SMTP handshake to verify email exists.
    Returns True if email is valid, False otherwise.
    """
    try:
        # Connect to MX server
        server = smtplib.SMTP(timeout=10)
        server.connect(mx_host)
        server.ehlo()
        
        # MAIL FROM (use a generic sender)
        server.mail("verify@lazyintern.com")
        
        # RCPT TO (this is where we check if email exists)
        code, message = server.rcpt(email)
        server.quit()
        
        # 250 = success, 251 = user not local (but will forward)
        if code in (250, 251):
            logger.info(f"SMTP ping success for {email}: {code}")
            return True
        else:
            logger.info(f"SMTP ping failed for {email}: {code} - {message}")
            return False
            
    except smtplib.SMTPServerDisconnected:
        logger.warning(f"SMTP server disconnected for {email}")
        return False
    except smtplib.SMTPResponseException as e:
        # 550 = mailbox not found, 553 = mailbox name not allowed
        if e.smtp_code in (550, 553):
            logger.info(f"SMTP ping: email not found {email}: {e.smtp_code}")
            return False
        # Temporary errors - assume valid to avoid false negatives
        logger.warning(f"SMTP temporary error for {email}: {e.smtp_code}")
        return True
    except Exception as e:
        logger.warning(f"SMTP ping error for {email}: {e}")
        # On error, assume valid to avoid false negatives
        return True


def validate_email(email: str, confidence: int) -> ValidationResult:
    """
    Returns ValidationResult with MX check and optional SMTP ping.
    """
    # Step 1: Format check
    if not RFC_REGEX.match(email):
        logger.info(f"Email format invalid: {email}")
        return ValidationResult(valid=False, reason="format_invalid")

    domain = email.split("@", 1)[1].lower()
    
    # Step 2: Disposable domain check
    disposable = _load_disposable()
    if domain in disposable:
        logger.info(f"Disposable domain detected: {domain}")
        return ValidationResult(valid=False, reason="disposable_domain")

    # Step 3: MX check
    try:
        records = dns.resolver.resolve(domain, "MX")
        mx_records = [str(r.exchange).rstrip('.') for r in records]
        mx_valid = bool(mx_records)
        
        if not mx_valid:
            logger.info(f"No MX records for domain: {domain}")
            return ValidationResult(valid=False, reason="mx_failure", mx_valid=False)
            
        logger.info(f"MX records found for {domain}: {mx_records[:2]}")
        
    except Exception as e:
        logger.warning(f"MX lookup failed for {domain}: {e}")
        return ValidationResult(valid=False, reason="mx_failure", mx_valid=False)

    # Step 4: SMTP ping (ALWAYS runs - compulsory)
    # Use first MX record
    mx_host = mx_records[0]
    smtp_valid = _smtp_ping(email, mx_host)
    
    if not smtp_valid:
        logger.info(f"SMTP ping failed for {email}")
        return ValidationResult(valid=False, reason="smtp_failure", mx_valid=True, smtp_valid=False)
    
    logger.info(f"Email validated successfully: {email}")
    return ValidationResult(valid=True, reason=None, mx_valid=mx_valid, smtp_valid=smtp_valid)

