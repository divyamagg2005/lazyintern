# Backfill Script Fixes - March 1, 2026

## Issues Found and Fixed

### 1. ❌ SQL Function Error (FIXED)
**Error**: `Could not find the function public.execute_sql(query) in the schema cache`

**Root Cause**: The backfill script was trying to use a raw SQL query via `db.client.rpc('execute_sql')`, but this function doesn't exist in Supabase.

**Fix**: Rewrote the query logic to use Supabase query builder:
- Query all verified leads: `db.client.table("leads").select("*").eq("verified", True).eq("mx_valid", True)`
- Query all existing drafts: `db.client.table("email_drafts").select("lead_id")`
- Filter in Python: `leads_without_drafts = [lead for lead in all_leads if lead["id"] not in existing_draft_lead_ids]`

**Files Modified**: `backend/backfill_drafts.py`

---

### 2. ❌ Groq API 400 Error (FIXED)
**Error**: `Client error '400 Bad Request' - The model 'llama-3.1-70b-versatile' has been decommissioned`

**Root Cause**: The Groq model `llama-3.1-70b-versatile` was deprecated and removed from Groq's API.

**Fix**: Updated to the new model `llama-3.3-70b-versatile`:
- Updated `backend/core/config.py`: Changed default model from `llama-3.1-70b-versatile` to `llama-3.3-70b-versatile`
- Updated `backend/.env`: Changed `GROQ_MODEL="llama-3.3-70b-versatile"`

**Verification**: Tested with `backend/test_groq_api.py` - API now returns 200 OK

**Files Modified**: 
- `backend/core/config.py`
- `backend/.env`

---

### 3. ❌ Twilio WhatsApp Error (FIXED)
**Error**: `Unable to create record: Twilio could not find a Channel with the specified From address`

**Root Cause**: The code was trying to send WhatsApp messages, but the Twilio account doesn't have WhatsApp configured (requires WhatsApp Business API setup).

**Fix**: Changed from WhatsApp to regular SMS:
- Removed `whatsapp:` prefix from phone numbers
- Simplified message format (no emojis, no markdown)
- Kept message under 160 chars for SMS compatibility
- Changed log message from "WhatsApp approval sent" to "SMS approval sent"

**Files Modified**: `backend/approval/twilio_sender.py`

---

## ✅ Backfill Script Status

**Current State**: ✅ Working correctly

The backfill script now:
1. Queries all verified leads without drafts using Supabase query builder
2. Generates Groq drafts using the new `llama-3.3-70b-versatile` model
3. Sends SMS approval messages via Twilio (not WhatsApp)
4. Adds 3 second delay between each SMS to avoid rate limiting

**How to Run**:
```bash
cd backend
python backfill_drafts.py
```

**Expected Behavior**:
- Checks if backfill is needed (verified leads without drafts)
- If needed, processes each lead one by one
- Logs progress: `[1/5] Processing: email@example.com at Company`
- Logs success: `[1/5] ✓ Backfill draft created for email@example.com at Company`
- Final summary: `Backfill complete: 5 success, 0 errors`

---

## 🔧 Additional Test Scripts Created

1. **test_groq_api.py** - Test Groq API with a simple request
2. **test_groq_models.py** - List all available Groq models

These can be used to verify Groq API configuration and model availability.

---

## 📝 Notes

- The backfill script will take time if there are many leads (3 seconds per lead)
- SMS messages are concise to fit within 160 character limit
- Groq API is now using the latest stable model (llama-3.3-70b-versatile)
- Regular SMS is more reliable than WhatsApp for approval workflow
