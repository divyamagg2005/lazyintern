from __future__ import annotations

from fastapi import FastAPI

from api.routes.health import router as health_router
from api.routes.twilio_webhook import router as twilio_router

app = FastAPI(title="LazyIntern API")

app.include_router(health_router)
app.include_router(twilio_router)

