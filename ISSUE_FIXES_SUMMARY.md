# Pipeline Issues - Fixed

All 4 critical pipeline issues have been resolved.

## Issue 1: Pre-scoring giving every lead score of 40 ✅ FIXED

**Problem**: All internships getting pre_score = 40 regardless of role title. Keywords not matching correctly.

**Solution**: Rewrote `backend/pipeline/pre_scorer.py`
- Keywords loaded from `data/keywords.json`
- Case-insensitive matching (`.lower()` on both sides)
- Disqualify keywords checked first → return 0 immediately
- Correct point values:
  - high_priority role → +40 points
  - medium_priority role → +20 points
  - high_priority company → +20 points
  - location → +20 points
- Score breakdown logged per lead for debugging
- Added `breakdown` dict to `PreScoreResult` dataclass

## Issue 2: HackerNews URLs have placeholder IDs ✅ FIXED

**Problem**: HackerNews source URLs contained literal placeholder text instead of real thread IDs.

**Solution**: Updated `backend/data/job_source.json`
- "Who is Hiring" → thread ID: 42931219
- "Who Wants to be Hired" → thread ID: 42947535
- Final URLs: `https://news.ycombinator.com/item?id=<thread_id>`

## Issue 3: RemoteOK blocking the scraper ✅ FIXED

**Problem**: All RemoteOK URLs returning scrape_failed consistently.

**Solution**: Created RemoteOK-specific handling in `backend/scraper/scrape_router.py`
- 8-12 seconds random delay between RemoteOK requests
- Custom User-Agent header: `Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36`
- Max 2 retries with additional delay between attempts
- NO Firecrawl fallback for RemoteOK failures (saves credits)
- Updated `backend/scraper/http_fetcher.py` to accept `user_agent` parameter

**Files Modified**:
- `backend/scraper/http_fetcher.py` - Added `user_agent` parameter, `REMOTEOK_USER_AGENT` constant
- `backend/scraper/scrape_router.py` - Added `_is_remoteok_url()` and `_fetch_with_remoteok_handling()` functions

## Issue 4: Wellfound returns 403 on subsequent requests ✅ FIXED

**Problem**: First Wellfound URL succeeds, subsequent ones get blocked due to rapid sequential requests to same domain.

**Solution**: Created global domain-based rate limiter
- New file: `backend/scraper/domain_rate_limiter.py`
- Tracks last request timestamp per domain globally
- Enforces 6-8 second minimum gap between same-domain requests
- Thread-safe with Lock for concurrent access
- Applies to ALL sources (http and dynamic), not just Wellfound

**Files Modified**:
- `backend/scraper/domain_rate_limiter.py` - NEW FILE with global rate limiting logic
- `backend/scraper/http_fetcher.py` - Calls `wait_for_domain()` before each request
- `backend/scraper/dynamic_fetcher.py` - Calls `wait_for_domain()` before each request

## How It Works

### Domain Rate Limiting (Issue 4)
1. Before any HTTP/dynamic request, `wait_for_domain(url)` is called
2. Extracts domain from URL (e.g., "wellfound.com")
3. Checks last request timestamp for that domain
4. If < 6-8 seconds have passed, sleeps until gap is satisfied
5. Updates timestamp after waiting
6. Prevents 403 errors from rapid same-domain requests

### RemoteOK Handling (Issue 3)
1. `scrape_router.py` detects RemoteOK URLs
2. Uses custom User-Agent to appear as real browser
3. Applies 8-12 second delay (longer than normal 2-3s)
4. Retries up to 2 times with additional delays
5. Skips Firecrawl fallback to save credits
6. Logs as `scrape_failed` after max retries

## Testing Recommendations

1. **Pre-scoring**: Check logs for score breakdown per lead
2. **HackerNews**: Verify URLs resolve to correct threads
3. **RemoteOK**: Monitor scrape success rate, should improve significantly
4. **Wellfound**: First and subsequent requests should both succeed (no 403s)

## No Schema Changes

As requested, no database schema changes were made. Only scraper logic was modified.
