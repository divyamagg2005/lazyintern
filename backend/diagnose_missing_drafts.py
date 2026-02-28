"""Simple diagnostic for missing drafts."""

from core.supabase_db import db

def diagnose():
    # Get all leads
    leads_result = db.client.table("leads").select("*").execute()
    all_leads = leads_result.data or []
    
    print(f"\n{'='*70}")
    print(f"LEADS ANALYSIS")
    print(f"{'='*70}")
    print(f"Total leads: {len(all_leads)}\n")
    
    # Get all drafts
    drafts_result = db.client.table("email_drafts").select("lead_id").execute()
    existing_draft_lead_ids = set(draft["lead_id"] for draft in (drafts_result.data or []))
    
    print(f"Total drafts: {len(existing_draft_lead_ids)}\n")
    
    # Analyze each lead
    print(f"{'='*70}")
    print(f"LEAD DETAILS:")
    print(f"{'='*70}\n")
    
    for idx, lead in enumerate(all_leads, 1):
        lead_id = lead["id"]
        email = lead.get("email", "")
        verified = lead.get("verified", False)
        mx_valid = lead.get("mx_valid", False)
        smtp_valid = lead.get("smtp_valid", False)
        has_draft = lead_id in existing_draft_lead_ids
        
        # Get internship info
        internship_id = lead.get("internship_id")
        internship_result = db.client.table("internships").select("company, role, full_score").eq("id", internship_id).limit(1).execute()
        
        if internship_result.data:
            internship = internship_result.data[0]
            company = internship.get("company", "Unknown")[:30]
            role = internship.get("role", "Unknown")[:40]
            score = internship.get("full_score", 0)
        else:
            company = "Unknown"
            role = "Unknown"
            score = 0
        
        status = "✓ HAS DRAFT" if has_draft else "✗ NO DRAFT"
        eligible = "✓" if (verified and mx_valid) else "✗"
        
        print(f"{idx}. {status} | Eligible: {eligible}")
        print(f"   Email: {email}")
        print(f"   Company: {company}")
        print(f"   Role: {role}")
        print(f"   Score: {score}")
        print(f"   Verified: {verified} | MX Valid: {mx_valid} | SMTP Valid: {smtp_valid}")
        
        if not has_draft and verified and mx_valid:
            print(f"   >>> MISSING DRAFT - Should be backfilled!")
        elif not has_draft and not verified:
            print(f"   >>> No draft (not verified)")
        elif not has_draft and not mx_valid:
            print(f"   >>> No draft (MX invalid)")
        
        print()
    
    # Summary
    verified_leads = [l for l in all_leads if l.get("verified") == True]
    mx_valid_leads = [l for l in verified_leads if l.get("mx_valid") == True]
    missing_drafts = [l for l in mx_valid_leads if l["id"] not in existing_draft_lead_ids]
    
    print(f"{'='*70}")
    print(f"SUMMARY:")
    print(f"{'='*70}")
    print(f"Total leads: {len(all_leads)}")
    print(f"Verified leads: {len(verified_leads)}")
    print(f"Verified + MX valid: {len(mx_valid_leads)}")
    print(f"Drafts created: {len(existing_draft_lead_ids)}")
    print(f"MISSING DRAFTS: {len(missing_drafts)}")
    print(f"{'='*70}\n")
    
    if missing_drafts:
        print("Run 'python backfill_drafts.py' to create missing drafts.")

if __name__ == "__main__":
    diagnose()
