# Design Document: Email Discovery Fallback Chain

## Overview

This feature extends the LazyIntern pipeline's email discovery capabilities by implementing a fallback chain of three additional methods that execute sequentially when Hunter.io returns no results. The fallback methods are: (1) pattern-based email guessing, (2) Snov.io API integration, and (3) website scraping.

The design maintains backward compatibility with the existing Hunter.io implementation while adding resilient fallback logic that maximizes email discovery success rates. All discovered emails are validated using the existing email_validator.py module and cached at the domain level in the company_domains table.

### Key Design Principles

- Sequential execution: Each method only executes if previous methods returned no validated results
- Fail-safe: Errors in one method don't prevent subsequent methods from executing
- Source tracking: Every discovered email is tagged with its discovery method
- Domain-level caching: Results are cached to avoid redundant API calls
- Validation-first: All discovered emails must pass MX and SMTP validation before being used

## Architecture

### Module Structure

```
backend/pipeline/
├── hunter_client.py          # Existing Hunter.io integration
├── pattern_guesser.py        # NEW: Pattern-based email generation
├── snov_client.py            # NEW: Snov.io API integration
├── website_scraper.py        # NEW: Website scraping for emails
├── email_discovery.py        # NEW: Fallback chain orchestrator
└── email_validator.py        # Existing validation logic
```

### Data Flow

```
cycle_manager.py
    ↓
email_discovery.py (orchestrator)
    ↓
1. Check company_domains cache
    ↓ (cache miss)
2. Hunter.io (existing)
    ↓ (no results)
3. Pattern Guesser
    ↓ (validation fails or no results)
4. Snov.io API
    ↓ (no results)
5. Website Scraper
    ↓
email_validator.py (validate all candidates)
    ↓
Update company_domains cache
    ↓
Return best validated email or None
```

## Components and Interfaces

### 1. EmailDiscoveryResult (Data Class)

```python
@dataclass
class EmailDiscoveryResult:
    email: str
    source: str  # "hunter", "pattern_guess", "snov", "scraped"
    confidence: int  # 0-100
    recruiter_name: str | None = None
```

### 2. Pattern Guesser Module (pattern_guesser.py)

**Purpose**: Generate common HR/recruiting email patterns for a domain.

**Function Signature**:
```python
def generate_pattern_candidates(domain: str) -> list[EmailDiscoveryResult]:
    """
    Generate 5 common email patterns for the domain.
    
    Args:
        domain: Company domain (e.g., "blitzenx.com")
    
    Returns:
        List of 5 EmailDiscoveryResult objects with source="pattern_guess"
        and confidence=50, in order: hr@, careers@, internships@, hello@, info@
    """
```

**Implementation Notes**:
- No external API calls
- Always returns exactly 5 candidates
- Order matters: hr@ is tried first, info@ is tried last
- All candidates have confidence=50 (medium confidence)

### 3. Snov.io Client Module (snov_client.py)

**Purpose**: Integrate with Snov.io API for email discovery.

**Function Signatures**:
```python
def _get_snov_access_token() -> str | None:
    """
    Authenticate with Snov.io OAuth endpoint.
    
    Returns:
        Access token string or None if authentication fails
    
    Environment Variables:
        SNOV_CLIENT_ID: Snov.io OAuth client ID
        SNOV_CLIENT_SECRET: Snov.io OAuth client secret
    """

def search_snov_domain(domain: str) -> EmailDiscoveryResult | None:
    """
    Search Snov.io for emails associated with a domain.
    
    Args:
        domain: Company domain (e.g., "blitzenx.com")
    
    Returns:
        EmailDiscoveryResult with highest confidence email or None
    
    API Endpoint:
        POST https://api.snov.io/v2/domain-emails-with-info
    """
```

**Implementation Notes**:
- OAuth authentication required before each domain search
- Select email with highest confidence score from results
- Preserve Snov.io confidence score in result
- Return None if environment variables are missing (graceful degradation)
- Log all errors without raising exceptions

### 4. Website Scraper Module (website_scraper.py)

**Purpose**: Scrape company websites for contact emails.

**Function Signature**:
```python
def scrape_domain_for_email(domain: str) -> EmailDiscoveryResult | None:
    """
    Scrape company website pages for email addresses.
    
    Args:
        domain: Company domain (e.g., "blitzenx.com")
    
    Returns:
        EmailDiscoveryResult with first valid email found or None
    
    Pages Scraped (in order):
        1. https://{domain}/contact
        2. https://{domain}/about
        3. https://{domain}/careers
    """
```

**Implementation Notes**:
- Use Scrapling's Fetcher.get() for HTTP requests
- Extract emails using regex: `[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}`
- Stop scraping after first email found
- Set confidence=70 for all scraped emails
- Continue to next URL if current URL fails
- Return None if all URLs fail

### 5. Email Discovery Orchestrator (email_discovery.py)

**Purpose**: Coordinate the fallback chain and manage domain-level caching.

**Function Signature**:
```python
def discover_email_with_fallback(
    domain: str,
    company_name: str
) -> EmailDiscoveryResult | None:
    """
    Execute email discovery fallback chain with domain-level caching.
    
    Args:
        domain: Company domain (e.g., "blitzenx.com")
        company_name: Company name for logging
    
    Returns:
        EmailDiscoveryResult with validated email or None
    
    Execution Order:
        1. Check company_domains cache
        2. Hunter.io (via hunter_client.search_domain_for_email)
        3. Pattern Guesser (validate all 5 candidates, select best)
        4. Snov.io API
        5. Website Scraper
    
    Caching:
        - Cache hit: Return cached email immediately
        - Cache miss: Execute fallback chain, cache result
        - Update company_domains.last_checked on every call
    """
```

**Implementation Notes**:
- Check cache first using company_domains.emails JSONB column
- For pattern guessing: validate all 5 candidates, select first valid one
- Stop execution immediately when any method returns a validated email
- Continue to next method if current method returns no results or validation fails
- Update cache with discovered email and source
- Log each method attempted and its result
- Handle all exceptions gracefully without crashing pipeline

### 6. Integration with cycle_manager.py

**Current Hunter.io Call** (line ~113):
```python
hunter = search_domain_for_email(domain)
```

**New Fallback Chain Call**:
```python
from pipeline.email_discovery import discover_email_with_fallback

# Replace hunter_client call with fallback chain orchestrator
result = discover_email_with_fallback(domain, company_name)
```

**Changes Required**:
- Replace direct hunter_client.search_domain_for_email() call with discover_email_with_fallback()
- Update logging to include source field
- Preserve existing lead creation logic
- Maintain backward compatibility with Hunter.io results

## Data Models

### company_domains Table (Existing)

```sql
CREATE TABLE company_domains (
  domain TEXT PRIMARY KEY,
  emails JSONB,              -- Stores discovered emails with source
  hunter_called BOOLEAN DEFAULT FALSE,
  last_checked TIMESTAMPTZ,
  reply_history JSONB,
  firecrawl_calls_this_week INTEGER DEFAULT 0,
  week_start DATE
);
```

**emails JSONB Structure**:
```json
[
  {
    "email": "hr@blitzenx.com",
    "source": "pattern_guess",
    "confidence": 50
  }
]
```

### leads Table (Existing)

```sql
CREATE TABLE leads (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  internship_id UUID REFERENCES internships(id) ON DELETE CASCADE,
  recruiter_name TEXT,
  email TEXT NOT NULL,
  source TEXT,               -- "hunter", "pattern_guess", "snov", "scraped"
  confidence INTEGER,        -- 0-100
  verified BOOLEAN DEFAULT FALSE,
  mx_valid BOOLEAN,
  smtp_valid BOOLEAN,
  created_at TIMESTAMPTZ DEFAULT NOW()
);
```

**Source Values**:
- `"hunter"`: Discovered via Hunter.io API
- `"pattern_guess"`: Generated using common email patterns
- `"snov"`: Discovered via Snov.io API
- `"scraped"`: Extracted from company website


## Correctness Properties

A property is a characteristic or behavior that should hold true across all valid executions of a system—essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.

### Property Reflection

After analyzing all acceptance criteria, I identified several areas of redundancy:

1. Properties 1.1-1.4 all test aspects of pattern generation that can be combined into a single comprehensive property
2. Properties 2.1, 2.2, 2.3 test the authentication and API call sequence that can be combined
3. Properties 4.1, 4.2, 4.6 test the fallback chain execution order and short-circuit behavior that overlap
4. Properties 5.1, 5.2, 5.3 test database persistence that can be combined
5. Properties 6.1, 6.2 test error handling resilience that can be combined
6. Properties 8.1, 8.2 test cache updates that can be combined

The following properties represent the unique, non-redundant validation requirements:

### Property 1: Pattern Generation Completeness

For any valid domain string, the pattern guesser shall generate exactly 5 email candidates in the order [hr@, careers@, internships@, hello@, info@], where each candidate has source="pattern_guess" and confidence=50.

**Validates: Requirements 1.1, 1.2, 1.3, 1.4**

### Property 2: Pattern Validation and Selection

For any list of pattern candidates with varying validation results, the email discovery system shall validate all candidates and return the first one that passes validation, or None if all fail validation.

**Validates: Requirements 1.5**

### Property 3: Fallback Chain Short-Circuit

For any email discovery attempt, when any method (Hunter, Pattern, Snov, Scraper) returns a validated email, all subsequent methods in the chain shall not be executed.

**Validates: Requirements 1.6, 2.6, 4.2**

### Property 4: Snov.io Authentication and Search Sequence

For any domain search via Snov.io, the client shall first authenticate using environment variables SNOV_CLIENT_ID and SNOV_CLIENT_SECRET, then call the domain search endpoint with the domain parameter, and return the email with the highest confidence score marked with source="snov".

**Validates: Requirements 2.1, 2.2, 2.3, 2.4, 2.5**

### Property 5: Snov.io Error Handling

For any Snov.io authentication or API call failure, the client shall log the error and return None without raising an exception.

**Validates: Requirements 2.7, 2.8**

### Property 6: Website Scraping Order and Early Exit

For any domain, the website scraper shall attempt to scrape URLs in the order [/contact, /about, /careers], and shall stop scraping additional pages when an email is found on any page.

**Validates: Requirements 3.1, 3.4**

### Property 7: Email Extraction from HTML

For any HTML content containing email addresses, the website scraper shall extract emails matching the regex pattern `[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}` and return the first valid email with source="scraped" and confidence=70.

**Validates: Requirements 3.3, 3.5, 3.6**

### Property 8: Scraping Resilience

For any list of URLs to scrape, if scraping fails for one URL, the scraper shall log the error and continue to the next URL, returning None only if all URLs fail.

**Validates: Requirements 3.7, 3.8**

### Property 9: Fallback Chain Execution Order

For any email discovery attempt, the system shall execute methods in the order [Hunter, Pattern Guesser, Snov, Website Scraper], where each method only executes if all previous methods returned no validated results.

**Validates: Requirements 4.1, 4.3**

### Property 10: Complete Failure Handling

For any email discovery attempt where all methods return no results, the system shall return None and mark the internship status as "no_email" without raising an exception.

**Validates: Requirements 4.4, 6.5**

### Property 11: Source Preservation Through Pipeline

For any discovered email with a source value, the source shall be preserved through the entire pipeline and stored in the leads.source column in the database.

**Validates: Requirements 4.5, 5.1**

### Property 12: Lead Metadata Persistence

For any lead created, the system shall store the confidence score in leads.confidence, log the source and confidence in the "email_found" event, and set verified=FALSE when source="pattern_guess".

**Validates: Requirements 5.2, 5.3, 5.4**

### Property 13: Hunter.io Backward Compatibility

For any email discovered via Hunter.io, the system shall create a lead with source="hunter" and preserve all existing Hunter.io functionality.

**Validates: Requirements 5.5**

### Property 14: Fallback Method Error Resilience

For any fallback method that raises an exception, the system shall log the error with method name and error details, then continue to the next fallback method without crashing the pipeline.

**Validates: Requirements 6.1, 6.2**

### Property 15: Snov.io Graceful Degradation

For any Snov.io client call when environment variables SNOV_CLIENT_ID or SNOV_CLIENT_SECRET are missing, the client shall log a warning and return None without raising an exception.

**Validates: Requirements 6.3, 7.3**

### Property 16: Scraping Timeout Handling

For any Scrapling fetch that times out, the website scraper shall log the timeout and continue to the next URL without raising an exception.

**Validates: Requirements 6.4**

### Property 17: Domain-Level Cache Update

For any email discovery method that successfully finds an email for a domain, the system shall update company_domains.emails with the discovered email and source, and update company_domains.last_checked with the current timestamp.

**Validates: Requirements 8.1, 8.2**

### Property 18: Cache-First Discovery

For any email discovery attempt for a domain, the system shall check company_domains.emails before executing any fallback methods, and if a cached result exists, shall return the cached email without calling any discovery methods.

**Validates: Requirements 8.3, 8.4**

### Property 19: Logging Completeness

For any email discovery attempt, the system shall log an event for each fallback method attempted with the method name and result, and shall log a final event indicating which method succeeded or that all methods failed.

**Validates: Requirements 4.6, 4.7**

## Error Handling

### Error Categories and Responses

1. **API Authentication Failures** (Snov.io)
   - Log warning with error details
   - Return None to trigger next fallback method
   - Never raise exception

2. **API Call Failures** (Hunter.io, Snov.io)
   - Log error with domain and error details
   - Add to retry queue for later retry
   - Return None to trigger next fallback method
   - Send error notification via Twilio

3. **Network Timeouts** (Website Scraping)
   - Log timeout with URL
   - Continue to next URL in scraping list
   - Return None if all URLs timeout

4. **Validation Failures** (Email Validator)
   - Log validation failure reason (format, disposable, MX, SMTP)
   - For pattern guessing: try next pattern
   - For other methods: trigger next fallback method
   - Update internship status to "email_invalid" if all methods fail validation

5. **Missing Configuration** (Environment Variables)
   - Log warning about missing SNOV_CLIENT_ID or SNOV_CLIENT_SECRET
   - Skip Snov.io method gracefully
   - Continue to next fallback method

6. **Database Errors** (Cache Read/Write)
   - Log error with domain and operation
   - Continue with discovery (don't let cache failures block discovery)
   - Retry cache write after successful discovery

### Error Logging Format

All errors shall be logged with the following structure:
```python
logger.error(
    f"[{method_name}] Error for domain {domain}: {error_message}",
    extra={
        "domain": domain,
        "method": method_name,
        "error_type": error.__class__.__name__,
        "internship_id": internship_id
    }
)
```

### Retry Strategy

- **Hunter.io failures**: Add to retry_queue with 15-minute delay
- **Snov.io failures**: Add to retry_queue with 15-minute delay
- **Scraping failures**: No retry (fallback to next URL or method)
- **Validation failures**: No retry (try next method)

## Testing Strategy

### Dual Testing Approach

This feature requires both unit tests and property-based tests to ensure comprehensive coverage:

- **Unit tests**: Verify specific examples, edge cases, and error conditions
- **Property tests**: Verify universal properties across all inputs

Both testing approaches are complementary and necessary. Unit tests catch concrete bugs in specific scenarios, while property tests verify general correctness across a wide range of inputs.

### Property-Based Testing Configuration

**Library**: Use `hypothesis` for Python property-based testing

**Configuration**:
- Minimum 100 iterations per property test (due to randomization)
- Each property test must reference its design document property
- Tag format: `# Feature: email-discovery-fallback-chain, Property {number}: {property_text}`

**Example Property Test Structure**:
```python
from hypothesis import given, strategies as st

@given(domain=st.text(min_size=3, max_size=50).filter(lambda x: '.' in x))
def test_property_1_pattern_generation_completeness(domain):
    """
    Feature: email-discovery-fallback-chain
    Property 1: Pattern Generation Completeness
    
    For any valid domain string, the pattern guesser shall generate
    exactly 5 email candidates in the specified order with correct metadata.
    """
    candidates = generate_pattern_candidates(domain)
    
    assert len(candidates) == 5
    assert [c.email.split('@')[0] for c in candidates] == ['hr', 'careers', 'internships', 'hello', 'info']
    assert all(c.source == "pattern_guess" for c in candidates)
    assert all(c.confidence == 50 for c in candidates)
    assert all(c.email.endswith(f"@{domain}") for c in candidates)
```

### Unit Testing Focus Areas

1. **Pattern Generation**
   - Test with common domains (google.com, microsoft.com)
   - Test with edge case domains (single-letter.io, very-long-domain-name.com)
   - Test with international domains (.co.uk, .com.au)

2. **Snov.io Integration**
   - Mock OAuth authentication success/failure
   - Mock domain search API responses
   - Test confidence score selection logic
   - Test missing environment variables

3. **Website Scraping**
   - Test email extraction from sample HTML
   - Test with pages containing no emails
   - Test with pages containing multiple emails
   - Test with malformed HTML
   - Test timeout handling

4. **Fallback Chain Orchestration**
   - Test cache hit scenario (no methods called)
   - Test Hunter.io success (no fallback methods called)
   - Test Hunter.io failure → Pattern success
   - Test Hunter + Pattern failure → Snov success
   - Test all methods failure → return None
   - Test validation failure → continue to next method

5. **Error Handling**
   - Test exception in each method doesn't crash pipeline
   - Test missing Snov.io credentials
   - Test network timeout in scraping
   - Test database cache read/write failures

6. **Integration with cycle_manager.py**
   - Test lead creation with each source type
   - Test source preservation in database
   - Test logging events for each method
   - Test backward compatibility with Hunter.io

### Test Data Generators

For property-based tests, use these Hypothesis strategies:

```python
# Domain strategy
domains = st.text(
    alphabet=st.characters(whitelist_categories=('Ll', 'Nd'), whitelist_characters='-'),
    min_size=3,
    max_size=50
).filter(lambda x: '.' in x and not x.startswith('-') and not x.endswith('-'))

# Email strategy
emails = st.emails()

# Confidence score strategy
confidence_scores = st.integers(min_value=0, max_value=100)

# Source strategy
sources = st.sampled_from(['hunter', 'pattern_guess', 'snov', 'scraped'])

# HTML with emails strategy
html_with_emails = st.text(min_size=100, max_size=1000).map(
    lambda text: f'<html><body>{text} contact@example.com {text}</body></html>'
)
```

### Coverage Goals

- **Line coverage**: Minimum 85%
- **Branch coverage**: Minimum 80%
- **Property test iterations**: Minimum 100 per property
- **Unit test count**: Minimum 50 tests across all modules

### Test Execution

```bash
# Run all tests
pytest backend/tests/test_email_discovery/

# Run property tests only
pytest backend/tests/test_email_discovery/ -m property

# Run unit tests only
pytest backend/tests/test_email_discovery/ -m unit

# Run with coverage
pytest backend/tests/test_email_discovery/ --cov=backend/pipeline --cov-report=html
```

## Implementation Notes

### Dependencies

Add to requirements.txt:
```
hypothesis>=6.100.0  # Property-based testing
```

Snov.io API credentials are required (add to .env):
```
SNOV_CLIENT_ID=your_client_id_here
SNOV_CLIENT_SECRET=your_client_secret_here
```

### Performance Considerations

1. **Cache First**: Always check company_domains cache before executing any discovery methods
2. **Short-Circuit**: Stop execution immediately when any method returns a validated email
3. **Parallel Validation**: For pattern guessing, validate all 5 candidates in parallel (future optimization)
4. **Timeout Configuration**: Set reasonable timeouts for all HTTP requests (20 seconds for Snov.io, 10 seconds for scraping)
5. **Rate Limiting**: Respect existing Hunter.io daily limits (15 calls/day)

### Security Considerations

1. **Environment Variables**: Never hardcode Snov.io credentials
2. **Input Validation**: Validate domain format before making API calls
3. **Error Messages**: Don't expose sensitive information in error logs
4. **HTTPS Only**: All API calls must use HTTPS
5. **Robots.txt**: Respect robots.txt when scraping websites (use existing _robots_allowed check)

### Monitoring and Observability

1. **Metrics to Track**:
   - Success rate per discovery method
   - Average execution time per method
   - Cache hit rate
   - Validation failure rate per method
   - Daily API usage per service

2. **Logging Events**:
   - `email_discovery_cache_hit`: Cache returned result
   - `email_discovery_cache_miss`: Cache empty, starting fallback chain
   - `email_discovery_hunter_success`: Hunter.io found email
   - `email_discovery_hunter_failure`: Hunter.io returned no results
   - `email_discovery_pattern_generated`: Pattern candidates generated
   - `email_discovery_pattern_success`: Pattern candidate validated
   - `email_discovery_pattern_failure`: All patterns failed validation
   - `email_discovery_snov_success`: Snov.io found email
   - `email_discovery_snov_failure`: Snov.io returned no results
   - `email_discovery_scraper_success`: Scraper found email
   - `email_discovery_scraper_failure`: Scraper returned no results
   - `email_discovery_complete_failure`: All methods failed
   - `email_discovery_error`: Exception in any method

3. **Dashboard Queries**:
```sql
-- Success rate by source
SELECT source, COUNT(*) as count
FROM leads
WHERE created_at > NOW() - INTERVAL '7 days'
GROUP BY source
ORDER BY count DESC;

-- Cache hit rate
SELECT 
  COUNT(*) FILTER (WHERE event = 'email_discovery_cache_hit') as cache_hits,
  COUNT(*) FILTER (WHERE event = 'email_discovery_cache_miss') as cache_misses,
  ROUND(100.0 * COUNT(*) FILTER (WHERE event = 'email_discovery_cache_hit') / 
    NULLIF(COUNT(*), 0), 2) as hit_rate_percent
FROM pipeline_events
WHERE created_at > NOW() - INTERVAL '7 days'
  AND event IN ('email_discovery_cache_hit', 'email_discovery_cache_miss');
```

### Migration Plan

1. **Phase 1**: Implement new modules (pattern_guesser.py, snov_client.py, website_scraper.py, email_discovery.py)
2. **Phase 2**: Write comprehensive tests (unit + property tests)
3. **Phase 3**: Update cycle_manager.py to use new email_discovery.py orchestrator
4. **Phase 4**: Deploy to staging and monitor for 48 hours
5. **Phase 5**: Deploy to production with feature flag (can rollback to Hunter-only if needed)
6. **Phase 6**: Monitor metrics and optimize based on success rates

### Rollback Strategy

If issues arise in production:
1. Set feature flag `USE_FALLBACK_CHAIN=false` in environment
2. Revert cycle_manager.py to use hunter_client.search_domain_for_email() directly
3. Investigate issues in staging
4. Fix and redeploy

### Future Enhancements

1. **Parallel Validation**: Validate pattern candidates in parallel using asyncio
2. **Machine Learning**: Train model to predict which pattern is most likely to be valid
3. **Additional Scrapers**: Add LinkedIn company page scraping
4. **Smart Caching**: Cache validation results separately from discovery results
5. **A/B Testing**: Compare success rates of different pattern orders
6. **Cost Optimization**: Track cost per successful email discovery by method
