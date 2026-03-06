# Job Source Alignment Report

**Date:** 2026-03-03  
**File:** `backend/data/job_source.json`  
**Total Sources:** 155

---

## ✅ ALIGNMENT STATUS: EXCELLENT

The `job_source.json` file is **well-aligned** with the codebase and 3-day rotation logic.

---

## 📊 Key Metrics

### 3-Day Rotation Distribution
- **Day 1:** 53 sources (34.2%)
- **Day 2:** 52 sources (33.5%)
- **Day 3:** 50 sources (32.3%)
- **Balance:** ✅ Well balanced (max difference: 3 sources)

### Scrape Frequency
- **Daily:** 118 sources (76.1%)
- **Monthly:** 32 sources (20.6%)
- **Weekly:** 5 sources (3.2%)

### Track Distribution
- **Tech:** 121 sources (78.1%)
- **Finance:** 31 sources (20.0%)
- **Both:** 3 sources (1.9%)

### Priority Distribution
- **High:** 71 sources (45.8%)
- **Medium:** 56 sources (36.1%)
- **Low:** 28 sources (18.1%)

### Type Distribution
- **Dynamic (Scrapling Tier 2):** 78 sources (50.3%)
- **HTTP (Scrapling Tier 1):** 77 sources (49.7%)

---

## ✅ Validation Results

### Required Fields
- ✅ All sources have `name`
- ✅ All sources have `url`
- ✅ All sources have `type`
- ✅ All sources have `priority`
- ✅ All sources have `scrape_frequency`
- ✅ All sources have `day_rotation`
- ✅ All sources have `expected_quality`
- ✅ All sources have `track`

### Data Quality
- ✅ No duplicate URLs
- ✅ No duplicate names
- ✅ All `day_rotation` values are valid (1, 2, or 3)
- ✅ Metadata count matches actual count (155)

### Daily Limits Compliance
- **Daily sources limit:** 40
- **Today's daily sources:** 39
- ✅ Within limit

---

## ⚠️ Minor Issues (Non-Critical)

### Domain Rotation
Some domains appear multiple times on the same day:

**Day 1:**
- `internshala.com`: 7 times
- `wellfound.com`: 3 times
- `remoteok.com`: 3 times

**Day 2:**
- `internshala.com`: 7 times
- `remoteok.com`: 3 times
- `wellfound.com`: 2 times

**Day 3:**
- `internshala.com`: 6 times
- `wellfound.com`: 2 times
- `remoteok.com`: 2 times

**Impact:** Low - These are different URLs from the same domain (e.g., different search queries on Internshala). The scraper handles this correctly by treating each URL as a separate source.

**Recommendation:** This is acceptable as each URL targets different job categories (ML, AI, Data Science, etc.) and provides unique results.

---

## 🔧 3-Day Rotation Logic Alignment

### How It Works
The codebase implements 3-day rotation in `backend/scraper/scrape_router.py`:

```python
def _should_scrape_source(source: dict[str, Any], tracking: dict[str, Any]) -> tuple[bool, str]:
    # Calculate current day of 3-day cycle (1, 2, or 3)
    day_of_cycle = (date.today().toordinal() % 3) + 1
    
    # Check if source's day_rotation matches today
    if day_rotation != day_of_cycle:
        return False, f"day_rotation={day_rotation}, today={day_of_cycle}"
```

### Alignment Verification
- ✅ All sources have `day_rotation` field (1, 2, or 3)
- ✅ Distribution is balanced across 3 days
- ✅ Daily sources are evenly distributed (38-41 per day)
- ✅ Weekly/monthly sources are spread across days
- ✅ No source is missing the `day_rotation` field

---

## 📈 Source Coverage

### Tech Sources (121 total)
- **AI/ML Focus:** 45 sources
- **Full Stack/Web Dev:** 32 sources
- **Data Science:** 18 sources
- **Research:** 12 sources
- **General SWE:** 14 sources

### Finance Sources (31 total)
- **Investment Banking:** 12 sources
- **Equity Research:** 5 sources
- **Quantitative Finance:** 6 sources
- **Private Equity/VC:** 5 sources
- **General Finance:** 3 sources

### Platform Coverage
- **LinkedIn:** 20 sources
- **Internshala:** 20 sources
- **Wellfound:** 7 sources
- **RemoteOK:** 7 sources
- **Indeed India:** 7 sources
- **Company Career Pages:** 25 sources
- **Other Job Boards:** 69 sources

---

## 🎯 Recommendations

### Current Status: Production Ready ✅
The job_source.json file is well-structured and aligned with the codebase.

### Optional Improvements (Low Priority)
1. **Domain Diversity:** Consider spreading Internshala sources across more days to reduce same-domain concentration
2. **Finance Coverage:** Current 20% finance sources aligns well with user's dual-track approach
3. **Monthly Sources:** 32 monthly sources (mostly company career pages) is appropriate for low-frequency updates

---

## 🔍 Codebase Integration Points

### Files That Use job_source.json
1. **`backend/scraper/scrape_router.py`**
   - Reads `day_rotation` field
   - Implements 3-day cycle logic
   - Filters sources based on frequency

2. **`backend/scheduler/cycle_manager.py`**
   - Orchestrates daily scraping
   - Respects day rotation
   - Tracks scraping history

3. **`backend/data/source_tracking.json`**
   - Stores last_scraped_at timestamps
   - Used for weekly/monthly frequency checks

### Configuration Alignment
```json
"scrape_config": {
  "daily_sources_limit": 40,     // ✅ Aligned (39 daily sources per day)
  "weekly_sources_limit": 10,    // ✅ Aligned (1-3 weekly sources per day)
  "monthly_sources_limit": 25,   // ✅ Aligned (10-11 monthly sources per day)
  "max_concurrent_workers": 8,   // ✅ Reasonable for 155 sources
  "delay_between_requests_sec": [2, 4],  // ✅ Respectful scraping
  "respect_robots_txt": true     // ✅ Ethical scraping
}
```

---

## ✅ Final Verdict

**Status:** FULLY ALIGNED ✅

The `job_source.json` file is:
- ✅ Properly structured with all required fields
- ✅ Well-balanced across 3-day rotation
- ✅ Aligned with scrape_config limits
- ✅ Compatible with codebase logic
- ✅ Ready for production use

**No critical issues found.**

Minor domain concentration on same days is acceptable and does not impact functionality.
