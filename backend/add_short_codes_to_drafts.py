"""Add short codes to existing drafts that don't have them."""

import hashlib
from core.supabase_db import db
from core.logger import logger

def generate_short_code(draft_id: str) -> str:
    """Generate a 6-character short code from draft ID."""
    return hashlib.md5(draft_id.encode()).hexdigest()[:6].upper()

def add_short_codes():
    """Add short codes to all drafts that don't have them."""
    
    # Get all drafts
    result = db.client.table("email_drafts").select("*").execute()
    drafts = result.data or []
    
    print(f"Found {len(drafts)} drafts")
    
    updated = 0
    for draft in drafts:
        draft_id = draft["id"]
        metadata = draft.get("metadata") or {}
        
        if not metadata.get("short_code"):
            short_code = generate_short_code(draft_id)
            metadata["short_code"] = short_code
            
            db.client.table("email_drafts").update(
                {"metadata": metadata}
            ).eq("id", draft_id).execute()
            
            print(f"Added short code {short_code} to draft {draft_id}")
            updated += 1
    
    print(f"\nUpdated {updated} drafts with short codes")

if __name__ == "__main__":
    add_short_codes()
