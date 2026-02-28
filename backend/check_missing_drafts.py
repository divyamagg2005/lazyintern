"""Check which leads are missing drafts and why."""

from core.supabase_db import db
from core.logger import logger

def check_missing_drafts():
    """Check which verified leads don't have drafts."""
    
    logger.info("=" * 70)
    logger.info("Checking for leads without drafts")
    logger.info("=" * 70)
    
    # Get all leads
    leads_result = (
        db.client.table("leads")
        .select("*")
        .execute()
    )
    
    all_leads = leads_result.data or []
    logger.info(f"\nTotal leads in database: {len(all_leads)}")
    
    # Count by verification status
    verified_leads = [l for l in all_leads if l.get("verified") == True]
    unverified_leads = [l for l in all_leads if l.get("verified") != True]
    
    logger.info(f"  - Verified leads: {len(verified_leads)}")
    logger.info(f"  - Unverified leads: {len(unverified_leads)}")
    
    # Count by mx_valid status
    mx_valid_leads = [l for l in verified_leads if l.get("mx_valid") == True]
    mx_invalid_leads = [l for l in verified_leads if l.get("mx_valid") != True]
    
    logger.info(f"\nVerified leads breakdown:")
    logger.info(f"  - MX valid: {len(mx_valid_leads)}")
    logger.info(f"  - MX invalid: {len(mx_invalid_leads)}")
    
    # Get all drafts
    drafts_result = (
        db.client.table("email_drafts")
        .select("lead_id")
        .execute()
    )
    
    existing_draft_lead_ids = set(
        draft["lead_id"] for draft in (drafts_result.data or [])
    )
    
    logger.info(f"\nTotal drafts in database: {len(existing_draft_lead_ids)}")
    
    # Find leads that should have drafts but don't
    eligible_leads = [l for l in all_leads if l.get("verified") == True and l.get("mx_valid") == True]
    leads_without_drafts = [
        lead for lead in eligible_leads
        if lead["id"] not in existing_draft_lead_ids
    ]
    
    logger.info(f"\nEligible leads (verified + mx_valid): {len(eligible_leads)}")
    logger.info(f"Leads WITHOUT drafts: {len(leads_without_drafts)}")
    
    if leads_without_drafts:
        logger.info("\n" + "=" * 70)
        logger.info("MISSING DRAFTS - Details:")
        logger.info("=" * 70)
        
        for idx, lead in enumerate(leads_without_drafts, 1):
            internship_id = lead.get("internship_id")
            email = lead.get("email")
            
            # Get internship details
            internship_result = (
                db.client.table("internships")
                .select("*")
                .eq("id", internship_id)
                .limit(1)
                .execute()
            )
            
            if internship_result.data:
                internship = internship_result.data[0]
                company = internship.get("company", "Unknown")
                role = internship.get("role", "Unknown")
                full_score = internship.get("full_score", 0)
                status = internship.get("status", "unknown")
                
                logger.info(f"\n{idx}. Lead ID: {lead['id']}")
                logger.info(f"   Email: {email}")
                logger.info(f"   Company: {company}")
                logger.info(f"   Role: {role}")
                logger.info(f"   Full Score: {full_score}")
                logger.info(f"   Internship Status: {status}")
                logger.info(f"   Verified: {lead.get('verified')}")
                logger.info(f"   MX Valid: {lead.get('mx_valid')}")
                logger.info(f"   SMTP Valid: {lead.get('smtp_valid')}")
            else:
                logger.info(f"\n{idx}. Lead ID: {lead['id']}")
                logger.info(f"   Email: {email}")
                logger.info(f"   ERROR: Internship not found (ID: {internship_id})")
    else:
        logger.info("\n✓ All eligible leads have drafts!")
    
    # Check for leads that are verified but not mx_valid
    if mx_invalid_leads:
        logger.info("\n" + "=" * 70)
        logger.info("VERIFIED but MX INVALID leads (won't get drafts):")
        logger.info("=" * 70)
        for idx, lead in enumerate(mx_invalid_leads, 1):
            logger.info(f"{idx}. {lead.get('email')} - verified={lead.get('verified')}, mx_valid={lead.get('mx_valid')}")
    
    # Check for unverified leads
    if unverified_leads:
        logger.info("\n" + "=" * 70)
        logger.info("UNVERIFIED leads (won't get drafts):")
        logger.info("=" * 70)
        for idx, lead in enumerate(unverified_leads[:10], 1):  # Show first 10
            logger.info(f"{idx}. {lead.get('email')} - verified={lead.get('verified')}, mx_valid={lead.get('mx_valid')}")
        if len(unverified_leads) > 10:
            logger.info(f"... and {len(unverified_leads) - 10} more")
    
    logger.info("\n" + "=" * 70)
    logger.info("Summary:")
    logger.info("=" * 70)
    logger.info(f"Total leads: {len(all_leads)}")
    logger.info(f"Eligible for drafts (verified + mx_valid): {len(eligible_leads)}")
    logger.info(f"Drafts created: {len(existing_draft_lead_ids)}")
    logger.info(f"Missing drafts: {len(leads_without_drafts)}")
    logger.info("=" * 70)


if __name__ == "__main__":
    check_missing_drafts()
