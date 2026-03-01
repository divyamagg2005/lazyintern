"""
Test script for email-level deduplication functionality.

This script tests:
1. Internship-level deduplication (existing behavior)
2. Email-level deduplication (new behavior)
3. Domain-level check for Hunter optimization
"""

from core.supabase_db import db
from core.logger import logger
import uuid

def test_email_deduplication():
    """Test email-level deduplication logic."""
    
    print("\n" + "="*70)
    print("TESTING EMAIL-LEVEL DEDUPLICATION")
    print("="*70 + "\n")
    
    test_email = "test.recruiter@testcompany.com"
    
    # Create test internships first (required for foreign key constraint)
    print("SETUP: Creating test internships...")
    internship_1_data = {
        "company": "Test Company 1",
        "role": "Test Role 1",
        "link": f"https://test.com/job/{uuid.uuid4()}",
        "description": "Test description 1",
        "status": "discovered"
    }
    internship_2_data = {
        "company": "Test Company 2",
        "role": "Test Role 2",
        "link": f"https://test.com/job/{uuid.uuid4()}",
        "description": "Test description 2",
        "status": "discovered"
    }
    internship_3_data = {
        "company": "Test Company 3",
        "role": "Test Role 3",
        "link": f"https://test.com/job/{uuid.uuid4()}",
        "description": "Test description 3",
        "status": "discovered"
    }
    internship_4_data = {
        "company": "Test Company 4",
        "role": "Test Role 4",
        "link": f"https://test.com/job/{uuid.uuid4()}",
        "description": "Test description 4",
        "status": "discovered"
    }
    
    int_1 = db.client.table("internships").insert(internship_1_data).execute().data[0]
    int_2 = db.client.table("internships").insert(internship_2_data).execute().data[0]
    int_3 = db.client.table("internships").insert(internship_3_data).execute().data[0]
    int_4 = db.client.table("internships").insert(internship_4_data).execute().data[0]
    
    internship_1 = int_1["id"]
    internship_2 = int_2["id"]
    internship_3 = int_3["id"]
    internship_4 = int_4["id"]
    
    print(f"✓ Test internships created")
    print(f"Test email: {test_email}")
    print(f"Internship 1: {internship_1}")
    print(f"Internship 2: {internship_2}\n")
    
    # TEST 1: Insert first lead
    print("TEST 1: Insert first lead for internship 1")
    lead_1 = db.insert_lead({
        "internship_id": internship_1,
        "email": test_email,
        "recruiter_name": "Test Recruiter",
        "source": "test",
        "confidence": 95
    })
    
    if lead_1:
        print(f"✓ Lead 1 inserted successfully: {lead_1['id']}")
    else:
        print("✗ Lead 1 insertion failed (unexpected)")
        return
    
    # TEST 2: Try to insert duplicate for same internship (should fail)
    print("\nTEST 2: Try to insert duplicate for same internship")
    lead_1_dup = db.insert_lead({
        "internship_id": internship_1,
        "email": test_email,
        "recruiter_name": "Test Recruiter",
        "source": "test",
        "confidence": 95
    })
    
    if not lead_1_dup:
        print("✓ Duplicate internship correctly blocked")
    else:
        print("✗ Duplicate internship NOT blocked (unexpected)")
    
    # TEST 3: Insert draft with 'generated' status (not sent yet)
    print("\nTEST 3: Create draft with 'generated' status (not sent)")
    draft_1 = db.insert_email_draft({
        "lead_id": lead_1["id"],
        "subject": "Test Subject",
        "body": "Test Body",
        "status": "generated"
    })
    print(f"✓ Draft created with status: {draft_1['status']}")
    
    # TEST 4: Try to insert same email for different internship (should succeed - not sent yet)
    print("\nTEST 4: Try same email for different internship (draft not sent)")
    lead_2 = db.insert_lead({
        "internship_id": internship_2,
        "email": test_email,
        "recruiter_name": "Test Recruiter",
        "source": "test",
        "confidence": 95
    })
    
    if lead_2:
        print(f"✓ Lead 2 inserted (allowed - email not sent yet): {lead_2['id']}")
    else:
        print("✗ Lead 2 blocked (unexpected - email wasn't sent)")
    
    # TEST 5: Update draft to 'sent' status
    print("\nTEST 5: Update draft to 'sent' status")
    db.update_email_draft(draft_1["id"], {"status": "sent"})
    print("✓ Draft status updated to 'sent'")
    
    # TEST 6: Try to insert same email for another internship (should fail - already sent)
    print("\nTEST 6: Try same email for new internship (after sent)")
    lead_3 = db.insert_lead({
        "internship_id": internship_3,
        "email": test_email,
        "recruiter_name": "Test Recruiter",
        "source": "test",
        "confidence": 95
    })
    
    if not lead_3:
        print("✓ Email-level deduplication working! (blocked after sent)")
    else:
        print("✗ Email-level deduplication NOT working (unexpected)")
    
    # TEST 7: Test domain check
    print("\nTEST 7: Test domain-level check")
    domain_contacted = db.check_domain_already_contacted("testcompany.com")
    
    if domain_contacted:
        print("✓ Domain check working! (testcompany.com marked as contacted)")
    else:
        print("✗ Domain check NOT working (unexpected)")
    
    # TEST 8: Test different email from same domain
    print("\nTEST 8: Test different email from same domain")
    different_email = "another.person@testcompany.com"
    lead_4 = db.insert_lead({
        "internship_id": internship_4,
        "email": different_email,
        "recruiter_name": "Another Person",
        "source": "test",
        "confidence": 95
    })
    
    if lead_4:
        print(f"✓ Different email from same domain allowed: {lead_4['id']}")
        print("  (Note: Domain check is for Hunter optimization, not blocking)")
    else:
        print("✗ Different email blocked (unexpected)")
    
    # CLEANUP
    print("\n" + "="*70)
    print("CLEANUP: Deleting test data")
    print("="*70)
    
    try:
        # Delete drafts first (foreign key constraint)
        db.client.table("email_drafts").delete().eq("lead_id", lead_1["id"]).execute()
        if lead_2:
            db.client.table("email_drafts").delete().eq("lead_id", lead_2["id"]).execute()
        if lead_4:
            db.client.table("email_drafts").delete().eq("lead_id", lead_4["id"]).execute()
        
        # Delete leads
        db.client.table("leads").delete().eq("id", lead_1["id"]).execute()
        if lead_2:
            db.client.table("leads").delete().eq("id", lead_2["id"]).execute()
        if lead_4:
            db.client.table("leads").delete().eq("id", lead_4["id"]).execute()
        
        # Delete internships
        db.client.table("internships").delete().eq("id", internship_1).execute()
        db.client.table("internships").delete().eq("id", internship_2).execute()
        db.client.table("internships").delete().eq("id", internship_3).execute()
        db.client.table("internships").delete().eq("id", internship_4).execute()
        
        print("✓ Test data cleaned up successfully")
    except Exception as e:
        print(f"✗ Cleanup failed: {e}")
    
    print("\n" + "="*70)
    print("TEST COMPLETE")
    print("="*70 + "\n")


if __name__ == "__main__":
    test_email_deduplication()
