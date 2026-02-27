from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from core.supabase_db import db


@dataclass
class DedupResult:
    is_duplicate: bool
    reason: str | None = None
    existing_id: str | None = None


def check_duplicate(internship: dict[str, Any]) -> DedupResult:
    """
    Phase 2 — Deduplication:
    - same job link seen before
    - same company + role exists
    - existing status already processed (anything other than discovered is treated as "seen")
    """
    link = internship.get("link")
    company = (internship.get("company") or "").strip()
    role = (internship.get("role") or "").strip()

    if link:
        res = (
            db.client.table("internships")
            .select("id,status")
            .eq("link", link)
            .limit(1)
            .execute()
        )
        if res.data:
            row = res.data[0]
            return DedupResult(True, reason="link_seen", existing_id=row["id"])

    if company and role:
        res = (
            db.client.table("internships")
            .select("id,status,company,role")
            .ilike("company", company)
            .ilike("role", role)
            .limit(1)
            .execute()
        )
        if res.data:
            row = res.data[0]
            return DedupResult(True, reason="company_role_seen", existing_id=row["id"])

    return DedupResult(False)

