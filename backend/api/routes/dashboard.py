from __future__ import annotations

from datetime import date, timedelta
from typing import Any

from fastapi import APIRouter
from fastapi.responses import JSONResponse

from core.supabase_db import db, today_utc
from core.logger import logger

router = APIRouter(prefix="/dashboard")


def _calculate_tier_success_rate(tier: str) -> float:
    """
    Calculate scraping tier success rate from pipeline events.
    Success = discovered event with tier metadata.
    Failure = scrape_failed event with tier metadata.
    """
    week_start = today_utc() - timedelta(days=7)
    
    # Count successes
    success_count = (
        db.client.table("pipeline_events")
        .select("id", count="exact")
        .eq("event", "discovered")
        .contains("metadata", {"tier": tier})
        .gte("created_at", str(week_start))
        .execute()
    )
    
    # Count failures
    failure_count = (
        db.client.table("pipeline_events")
        .select("id", count="exact")
        .eq("event", "scrape_failed")
        .contains("metadata", {"tier": tier})
        .gte("created_at", str(week_start))
        .execute()
    )
    
    successes = success_count.count or 0
    failures = failure_count.count or 0
    total = successes + failures
    
    if total == 0:
        return 0.0
    
    return round((successes / total) * 100, 1)


def _get_discovery_metrics() -> dict[str, Any]:
    """Calculate discovery panel metrics."""
    today = today_utc()
    week_start = today - timedelta(days=today.weekday())
    
    # Internships discovered today
    today_count = db.client.table("internships").select("id", count="exact").gte("created_at", str(today)).execute()
    internships_today = today_count.count or 0
    
    # Internships this week
    week_count = db.client.table("internships").select("id", count="exact").gte("created_at", str(week_start)).execute()
    internships_week = week_count.count or 0
    
    # Pre-score kill rate
    usage = db.get_or_create_daily_usage(today)
    total_discovered = internships_today or 1
    pre_score_kill_rate = (usage.pre_score_kills / total_discovered) * 100 if total_discovered > 0 else 0
    
    # Tier success rates from pipeline events
    tier1_success = _calculate_tier_success_rate("tier1_success")
    tier2_success = _calculate_tier_success_rate("tier2_success")
    tier3_success = _calculate_tier_success_rate("tier3_success")
    
    return {
        "internshipsToday": internships_today,
        "internshipsThisWeek": internships_week,
        "tier1SuccessRate": tier1_success,
        "tier2SuccessRate": tier2_success,
        "tier3SuccessRate": tier3_success,
        "preScoreKillRate": round(pre_score_kill_rate, 1),
        "firecrawlUsed": usage.firecrawl_calls,
        "firecrawlLimit": 10
    }


def _get_email_metrics() -> dict[str, Any]:
    """Calculate email panel metrics."""
    today = today_utc()
    
    # Count emails by source
    regex_count = db.client.table("leads").select("id", count="exact").eq("source", "regex").execute()
    hunter_count = db.client.table("leads").select("id", count="exact").eq("source", "hunter").execute()
    
    usage = db.get_or_create_daily_usage(today)
    
    # Validation failures breakdown (from events)
    mx_fails = db.client.table("pipeline_events").select("id", count="exact").eq("event", "email_invalid").contains("metadata", {"reason": "mx_failure"}).execute()
    format_fails = db.client.table("pipeline_events").select("id", count="exact").eq("event", "email_invalid").contains("metadata", {"reason": "format_invalid"}).execute()
    smtp_fails = db.client.table("pipeline_events").select("id", count="exact").eq("event", "email_invalid").contains("metadata", {"reason": "smtp_failure"}).execute()
    
    return {
        "regexEmails": regex_count.count or 0,
        "hunterEmails": hunter_count.count or 0,
        "hunterCallsToday": usage.hunter_calls,
        "hunterDailyLimit": 15,
        "validationFailuresMx": mx_fails.count or 0,
        "validationFailuresFormat": format_fails.count or 0,
        "validationFailuresSmtp": smtp_fails.count or 0
    }


def _get_outreach_metrics() -> dict[str, Any]:
    """Calculate outreach panel metrics."""
    today = today_utc()
    usage = db.get_or_create_daily_usage(today)
    
    # Groq drafts generated
    drafts_count = db.client.table("email_drafts").select("id", count="exact").execute()
    groq_drafts = drafts_count.count or 0
    
    # Approval rate
    approved_count = db.client.table("email_drafts").select("id", count="exact").in_("status", ["approved", "auto_approved"]).execute()
    total_drafts = groq_drafts or 1
    approval_rate = (approved_count.count or 0) / total_drafts * 100 if total_drafts > 0 else 0
    
    # Pending follow-ups
    followups_count = db.client.table("followup_queue").select("id", count="exact").eq("sent", False).execute()
    
    # Warmup progress (assume 11-day warmup to reach 15 emails/day)
    warmup_progress = min(100, (usage.daily_limit / 15) * 100)
    is_warmup = usage.daily_limit < 15
    
    return {
        "groqDraftsGenerated": groq_drafts,
        "approvalRate": round(approval_rate, 1),
        "autoApprovals": usage.auto_approvals,
        "emailsSentToday": usage.emails_sent,
        "dailyEmailLimit": usage.daily_limit or 15,
        "isWarmupPhase": is_warmup,
        "warmupProgressPct": round(warmup_progress, 1),
        "pendingFollowups": followups_count.count or 0
    }


def _get_performance_metrics() -> dict[str, Any]:
    """Calculate performance panel metrics."""
    # Reply rates (from company_domains.reply_history)
    domains = db.client.table("company_domains").select("reply_history").execute()
    
    total_positive = 0
    total_negative = 0
    total_neutral = 0
    
    for domain in (domains.data or []):
        history = domain.get("reply_history") or {}
        total_positive += history.get("positive", 0)
        total_negative += history.get("negative", 0)
        total_neutral += history.get("neutral", 0)
    
    total_replies = total_positive + total_negative + total_neutral
    reply_rate = (total_replies / 100) * 100 if total_replies > 0 else 0  # Placeholder denominator
    positive_reply_rate = (total_positive / total_replies) * 100 if total_replies > 0 else 0
    
    # Funnel stages
    discovered = db.client.table("internships").select("id", count="exact").execute().count or 0
    pre_scored = db.client.table("internships").select("id", count="exact").is_not("pre_score", "null").execute().count or 0
    email_found = db.client.table("leads").select("id", count="exact").execute().count or 0
    validated = db.client.table("leads").select("id", count="exact").eq("verified", True).execute().count or 0
    full_scored = db.client.table("internships").select("id", count="exact").is_not("full_score", "null").execute().count or 0
    drafted = db.client.table("email_drafts").select("id", count="exact").execute().count or 0
    approved = db.client.table("email_drafts").select("id", count="exact").in_("status", ["approved", "auto_approved", "sent"]).execute().count or 0
    sent = db.client.table("email_drafts").select("id", count="exact").eq("status", "sent").execute().count or 0
    replied = total_replies
    
    funnel = [
        {"label": "Discovered", "count": discovered},
        {"label": "Pre-scored", "count": pre_scored},
        {"label": "Email found", "count": email_found},
        {"label": "Validated", "count": validated},
        {"label": "Full-scored", "count": full_scored},
        {"label": "Drafted", "count": drafted},
        {"label": "Approved", "count": approved},
        {"label": "Sent", "count": sent},
        {"label": "Replied", "count": replied}
    ]
    
    # Top company types (placeholder)
    top_companies = [
        {"type": "AI Startup", "replyRate": 14.2},
        {"type": "YC Company", "replyRate": 11.8},
        {"type": "Research Lab", "replyRate": 9.3}
    ]
    
    return {
        "replyRate": round(reply_rate, 1),
        "positiveReplyRate": round(positive_reply_rate, 1),
        "funnel": funnel,
        "topCompanyTypes": top_companies
    }


def _get_retry_metrics() -> dict[str, Any]:
    """Calculate retry panel metrics."""
    # Active retries by phase
    retries = db.client.table("retry_queue").select("phase").eq("resolved", False).execute()
    
    phase_counts: dict[str, int] = {"groq": 0, "twilio": 0, "gmail": 0, "hunter": 0}
    for retry in (retries.data or []):
        phase = retry.get("phase", "")
        if phase in phase_counts:
            phase_counts[phase] += 1
    
    active_by_phase = [
        {"phase": phase, "activeJobs": count}
        for phase, count in phase_counts.items()
    ]
    
    # Max retry failures
    max_failures = db.client.table("retry_queue").select("*").eq("resolved", False).gte("attempts", 3).execute()
    
    failures = [
        {
            "id": f["id"],
            "phase": f["phase"],
            "lastError": f.get("last_error", "Unknown error"),
            "createdAt": f.get("created_at", "")
        }
        for f in (max_failures.data or [])
    ]
    
    return {
        "activeRetriesByPhase": active_by_phase,
        "maxRetryFailures": failures
    }


def _get_scoring_config() -> list[dict[str, Any]]:
    """Get scoring weights from database."""
    weights = db.client.table("scoring_config").select("*").execute()
    
    return [
        {
            "key": w["key"],
            "weight": float(w["weight"]),
            "description": w.get("description", "")
        }
        for w in (weights.data or [])
    ]


@router.get("")
async def get_dashboard_data() -> JSONResponse:
    """
    Main dashboard endpoint.
    Returns all metrics for the frontend dashboard.
    """
    try:
        data = {
            "lastUpdated": today_utc().isoformat(),
            "discovery": _get_discovery_metrics(),
            "email": _get_email_metrics(),
            "outreach": _get_outreach_metrics(),
            "performance": _get_performance_metrics(),
            "retries": _get_retry_metrics(),
            "scoringConfig": _get_scoring_config()
        }
        
        logger.info("Dashboard data generated successfully")
        return JSONResponse(content=data)
        
    except Exception as e:
        logger.error(f"Dashboard data generation failed: {e}")
        return JSONResponse(
            status_code=500,
            content={"error": "Failed to generate dashboard data", "detail": str(e)}
        )
