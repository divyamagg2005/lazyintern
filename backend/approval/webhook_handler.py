from __future__ import annotations

from fastapi import HTTPException, Request
from twilio.request_validator import RequestValidator

from core.config import settings


async def validate_twilio_request(request: Request) -> None:
    """
    Shared validator for Twilio webhooks.
    Ensures the request really came from Twilio using the X-Twilio-Signature header.
    """
    if not settings.twilio_auth_token or not settings.public_base_url:
        raise HTTPException(
            status_code=500,
            detail="Twilio webhook not configured",
        )

    signature = request.headers.get("X-Twilio-Signature", "")
    url = f"{settings.public_base_url}{request.url.path}"
    params = await request.form()

    validator = RequestValidator(settings.twilio_auth_token)
    if not validator.validate(url, dict(params), signature):
        raise HTTPException(status_code=403, detail="Invalid Twilio signature")

