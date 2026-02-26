from __future__ import annotations

from core.supabase_db import db


def update_on_reply(domain: str, lead_id: str, reply_type: str) -> None:
    res = (
        db.client.table("company_domains")
        .select("*")
        .eq("domain", domain)
        .limit(1)
        .execute()
    )
    if res.data:
        record = res.data[0]
        history = record.get("reply_history") or {"positive": 0, "negative": 0, "neutral": 0}
    else:
        record = {"domain": domain}
        history = {"positive": 0, "negative": 0, "neutral": 0}

    history[reply_type] = int(history.get(reply_type) or 0) + 1

    db.client.table("company_domains").upsert(
        {
            "domain": domain,
            "reply_history": history,
        },
        on_conflict="domain",
    ).execute()

    if reply_type == "positive":
        db.client.table("followup_queue").update(
            {"sent": True}
        ).eq("lead_id", lead_id).eq("sent", False).execute()

