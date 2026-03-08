# Implementation Plan: Email Discovery Fallback Chain

## Overview

This implementation adds a resilient email discovery system with a sequential fallback chain: Hunter.io → Pattern Guesser → Snov.io → Website Scraper. Each method executes only if previous methods return no validated results. The system includes domain-level caching, comprehensive error handling, and dual testing strategy (unit tests + property-based tests using hypothesis).

## Tasks

- [x] 1. Set up environment configuration and dependencies
  - Add hypothesis>=6.100.0 to requirements.txt for property-based testing
  - Add SNOV_CLIENT_ID and SNOV_CLIENT_SECRET to .env with placeholder values
  - Add SNOV_CLIENT_ID and SNOV_CLIENT_SECRET to .env.example with comments explaining how to obtain credentials
  - _Requirements: 7.1, 7.2, 7.4, 7.5, 7.6_

- [x] 2. Implement pattern_guesser.py module
  - [x] 2.1 Create EmailDiscoveryResult dataclass and generate_pattern_candidates function
    - Create backend/pipeline/pattern_guesser.py
    - Define EmailDiscoveryResult dataclass with fields: email, source, confidence, recruiter_name
    - Implement generate_pattern_candidates(domain: str) that returns exactly 5 candidates in order: hr@, careers@, internships@, hello@, info@
    - Set source="pattern_guess" and confidence=50 for all candidates
    - _Requirements: 1.1, 1.2, 1.3, 1.4_
  
  - [x] 2.2 Write property test for pattern generation completeness
    - **Property 1: Pattern Generation Completeness**
    - **Validates: Requirements 1.1, 1.2, 1.3, 1.4**
    - Create backend/tests/test_email_discovery/test_pattern_guesser.py
    - Use hypothesis @given decorator with domain strategy
    - Verify exactly 5 candidates generated in correct order with correct metadata
    - Run minimum 100 iterations
  
  - [x] 2.3 Write unit tests for pattern_guesser.py
    - Test with common domains (google.com, microsoft.com)
    - Test with edge case domains (single-letter.io, very-long-domain-name.com)
    - Test with international domains (.co.uk, .com.au)
    - _Requirements: 1.1, 1.2, 1.3, 1.4_

- [x] 3. Implement snov_client.py module
  - [x] 3.1 Create Snov.io authentication and domain search functions
    - Create backend/pipeline/snov_client.py
    - Implement _get_snov_access_token() that reads SNOV_CLIENT_ID and SNOV_CLIENT_SECRET from environment
    - Authenticate with Snov.io OAuth endpoint and return access token or None
    - Implement search_snov_domain(domain: str) that calls POST https://api.snov.io/v2/domain-emails-with-info
    - Select email with highest confidence score from results
    - Return EmailDiscoveryResult with source="snov" or None
    - Handle missing environment variables gracefully (log warning, return None)
    - Log all errors without raising exceptions
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 2.7, 2.8, 6.3, 7.1, 7.2, 7.3_
  
  - [x] 3.2 Write property test for Snov.io authentication and search sequence
    - **Property 4: Snov.io Authentication and Search Sequence**
    - **Validates: Requirements 2.1, 2.2, 2.3, 2.4, 2.5**
    - Create backend/tests/test_email_discovery/test_snov_client.py
    - Mock OAuth endpoint and domain search endpoint
    - Verify authentication happens before search
    - Verify highest confidence email is selected
  
  - [x] 3.3 Write property test for Snov.io error handling
    - **Property 5: Snov.io Error Handling**
    - **Validates: Requirements 2.7, 2.8**
    - Test authentication failures return None without exception
    - Test API call failures return None without exception
  
  - [x] 3.4 Write property test for Snov.io graceful degradation
    - **Property 15: Snov.io Graceful Degradation**
    - **Validates: Requirements 6.3, 7.3**
    - Test missing SNOV_CLIENT_ID returns None with warning log
    - Test missing SNOV_CLIENT_SECRET returns None with warning log
  
  - [x] 3.5 Write unit tests for snov_client.py
    - Mock OAuth authentication success/failure scenarios
    - Mock domain search API responses with varying confidence scores
    - Test confidence score selection logic
    - Test missing environment variables
    - Test network errors and timeouts
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 2.7, 2.8, 6.3_

- [x] 4. Implement website_scraper.py module
  - [x] 4.1 Create website scraping function with email extraction
    - Create backend/pipeline/website_scraper.py
    - Implement scrape_domain_for_email(domain: str) that scrapes URLs in order: /contact, /about, /careers
    - Use Scrapling's Fetcher.get() for HTTP requests
    - Extract emails using regex: [a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}
    - Stop scraping after first email found
    - Return EmailDiscoveryResult with source="scraped" and confidence=70 or None
    - Continue to next URL if current URL fails
    - Log errors without raising exceptions
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 3.7, 3.8, 6.4_
  
  - [x] 4.2 Write property test for website scraping order and early exit
    - **Property 6: Website Scraping Order and Early Exit**
    - **Validates: Requirements 3.1, 3.4**
    - Mock Scrapling Fetcher.get() to track URL order
    - Verify URLs scraped in correct order
    - Verify scraping stops after first email found
  
  - [x] 4.3 Write property test for email extraction from HTML
    - **Property 7: Email Extraction from HTML**
    - **Validates: Requirements 3.3, 3.5, 3.6**
    - Use hypothesis to generate HTML with embedded emails
    - Verify regex extracts emails correctly
    - Verify first email is returned with correct metadata
  
  - [x] 4.4 Write property test for scraping resilience
    - **Property 8: Scraping Resilience**
    - **Validates: Requirements 3.7, 3.8**
    - Mock failures for individual URLs
    - Verify scraper continues to next URL on failure
    - Verify None returned only if all URLs fail
  
  - [x] 4.5 Write property test for scraping timeout handling
    - **Property 16: Scraping Timeout Handling**
    - **Validates: Requirements 6.4**
    - Mock Scrapling timeout exceptions
    - Verify timeout logged and next URL attempted
  
  - [x] 4.6 Write unit tests for website_scraper.py
    - Test email extraction from sample HTML pages
    - Test pages containing no emails
    - Test pages containing multiple emails (verify first is selected)
    - Test malformed HTML handling
    - Test timeout handling with mocked Scrapling
    - Test URL failure scenarios
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 3.7, 3.8_

- [x] 5. Checkpoint - Ensure all module tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 6. Implement email_discovery.py orchestrator
  - [x] 6.1 Create fallback chain orchestrator with caching
    - Create backend/pipeline/email_discovery.py
    - Import hunter_client.search_domain_for_email, pattern_guesser, snov_client, website_scraper, email_validator
    - Implement discover_email_with_fallback(domain: str, company_name: str) function
    - Check company_domains.emails cache first, return cached result if exists
    - Execute fallback chain: Hunter → Pattern → Snov → Scraper
    - For pattern guessing: validate all 5 candidates, select first valid one
    - Stop execution when any method returns validated email
    - Update company_domains.emails and last_checked after successful discovery
    - Log each method attempted and result
    - Handle all exceptions gracefully without crashing
    - Return EmailDiscoveryResult or None
    - _Requirements: 1.5, 1.6, 2.6, 4.1, 4.2, 4.3, 4.4, 4.5, 4.6, 4.7, 6.1, 6.2, 6.5, 8.1, 8.2, 8.3, 8.4_
  
  - [x] 6.2 Write property test for pattern validation and selection
    - **Property 2: Pattern Validation and Selection**
    - **Validates: Requirements 1.5**
    - Mock email_validator with varying validation results
    - Verify all candidates validated
    - Verify first valid candidate selected
  
  - [x] 6.3 Write property test for fallback chain short-circuit
    - **Property 3: Fallback Chain Short-Circuit**
    - **Validates: Requirements 1.6, 2.6, 4.2**
    - Mock each discovery method
    - Verify subsequent methods not called when earlier method succeeds
  
  - [x] 6.4 Write property test for fallback chain execution order
    - **Property 9: Fallback Chain Execution Order**
    - **Validates: Requirements 4.1, 4.3**
    - Mock all discovery methods to track execution order
    - Verify methods execute in correct sequence
    - Verify each method only executes if previous returned no results
  
  - [x] 6.5 Write property test for complete failure handling
    - **Property 10: Complete Failure Handling**
    - **Validates: Requirements 4.4, 6.5**
    - Mock all methods to return no results
    - Verify None returned without exception
  
  - [x] 6.6 Write property test for fallback method error resilience
    - **Property 14: Fallback Method Error Resilience**
    - **Validates: Requirements 6.1, 6.2**
    - Mock exceptions in each fallback method
    - Verify error logged and next method executed
    - Verify pipeline doesn't crash
  
  - [x] 6.7 Write property test for domain-level cache update
    - **Property 17: Domain-Level Cache Update**
    - **Validates: Requirements 8.1, 8.2**
    - Mock successful discovery from each method
    - Verify company_domains.emails updated with email and source
    - Verify company_domains.last_checked updated
  
  - [x] 6.8 Write property test for cache-first discovery
    - **Property 18: Cache-First Discovery**
    - **Validates: Requirements 8.3, 8.4**
    - Mock company_domains.emails with cached result
    - Verify cached email returned immediately
    - Verify no discovery methods called
  
  - [x] 6.9 Write unit tests for email_discovery.py
    - Test cache hit scenario (no methods called)
    - Test Hunter.io success (no fallback methods called)
    - Test Hunter.io failure → Pattern success
    - Test Hunter + Pattern failure → Snov success
    - Test Hunter + Pattern + Snov failure → Scraper success
    - Test all methods failure → return None
    - Test validation failure → continue to next method
    - Test exception in each method doesn't crash pipeline
    - Test database cache read/write failures
    - _Requirements: 4.1, 4.2, 4.3, 4.4, 6.1, 6.2, 8.1, 8.2, 8.3, 8.4_

- [x] 7. Integrate with cycle_manager.py
  - [x] 7.1 Replace Hunter.io call with fallback chain orchestrator
    - Import discover_email_with_fallback from pipeline.email_discovery
    - Replace search_domain_for_email(domain) call with discover_email_with_fallback(domain, company_name) in backend/scheduler/cycle_manager.py (around line 113)
    - Update result handling to use EmailDiscoveryResult dataclass
    - Preserve existing lead creation logic
    - Update logging to include source field in "email_found" event
    - Set verified=FALSE when source="pattern_guess"
    - Maintain backward compatibility with Hunter.io results
    - _Requirements: 4.5, 4.6, 4.7, 5.1, 5.2, 5.3, 5.4, 5.5_
  
  - [x] 7.2 Write property test for source preservation through pipeline
    - **Property 11: Source Preservation Through Pipeline**
    - **Validates: Requirements 4.5, 5.1**
    - Mock discover_email_with_fallback with different sources
    - Verify source preserved in leads.source column
  
  - [x] 7.3 Write property test for lead metadata persistence
    - **Property 12: Lead Metadata Persistence**
    - **Validates: Requirements 5.2, 5.3, 5.4**
    - Mock lead creation with different sources and confidence scores
    - Verify confidence stored in leads.confidence
    - Verify source and confidence logged in "email_found" event
    - Verify verified=FALSE when source="pattern_guess"
  
  - [x] 7.4 Write property test for Hunter.io backward compatibility
    - **Property 13: Hunter.io Backward Compatibility**
    - **Validates: Requirements 5.5**
    - Mock Hunter.io success
    - Verify lead created with source="hunter"
    - Verify existing Hunter.io functionality preserved
  
  - [x] 7.5 Write property test for logging completeness
    - **Property 19: Logging Completeness**
    - **Validates: Requirements 4.6, 4.7**
    - Mock all discovery methods
    - Verify event logged for each method attempted
    - Verify final event indicates success method or complete failure

- [x] 8. Integration testing
  - [x] 8.1 Write integration test for complete fallback chain
    - Create backend/tests/test_email_discovery/test_integration.py
    - Test end-to-end flow from cycle_manager through all fallback methods
    - Mock external APIs (Hunter.io, Snov.io, Scrapling)
    - Verify lead created with correct source and confidence
    - Verify cache updated correctly
    - Verify logging events generated
    - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5, 5.1, 5.2, 5.3, 8.1, 8.2_
  
  - [x] 8.2 Write integration test for error scenarios
    - Test all methods failing gracefully
    - Test partial failures (some methods succeed, some fail)
    - Test missing Snov.io credentials
    - Test network timeouts
    - Test database errors
    - Verify pipeline continues running
    - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5_

- [x] 9. Final checkpoint - Ensure all tests pass
  - Run pytest backend/tests/test_email_discovery/ with coverage
  - Verify minimum 85% line coverage and 80% branch coverage
  - Ensure all property tests run minimum 100 iterations
  - Ensure all tests pass, ask the user if questions arise.

- [x] 10. Update documentation
  - Add inline code comments explaining fallback chain logic
  - Document EmailDiscoveryResult dataclass fields
  - Document environment variable requirements in code comments
  - Add docstrings to all public functions with Args, Returns, and Examples sections
  - _Requirements: 7.4, 7.5, 7.6_

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- Each task references specific requirements for traceability
- Property tests validate universal correctness properties using hypothesis library
- Unit tests validate specific examples and edge cases
- Integration tests verify end-to-end flows
- The fallback chain executes sequentially: Hunter → Pattern → Snov → Scraper
- Domain-level caching prevents redundant API calls
- All errors are handled gracefully without crashing the pipeline
- Source tracking enables analysis of discovery method effectiveness
