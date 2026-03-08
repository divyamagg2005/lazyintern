# Requirements Document

## Introduction

The LazyIntern pipeline currently uses Hunter.io as the sole email discovery method for finding company contact emails. When Hunter.io returns no results for a domain, the internship opportunity is marked as "no_email" and no further action is taken. This results in many missed opportunities where valid contact emails could be discovered through alternative methods.

This feature adds a fallback chain of three additional email discovery methods that execute sequentially only when the previous method returns no results. The fallback methods are: (1) pattern-based email guessing using common HR/recruiting email patterns, (2) Snov.io API domain search, and (3) website scraping of contact/about/careers pages using the existing Scrapling library.

## Glossary

- **Email_Discovery_System**: The component responsible for finding contact emails for company domains
- **Hunter_Client**: The existing module that calls Hunter.io API for email discovery
- **Pattern_Guesser**: New component that generates common email patterns for a domain
- **Snov_Client**: New component that calls Snov.io API for email discovery
- **Website_Scraper**: New component that scrapes company websites for email addresses
- **Fallback_Chain**: The sequential execution of email discovery methods where each method only executes if previous methods returned no results
- **Source**: Existing TEXT column in leads table that stores which method discovered the email (values: "hunter", "pattern_guess", "snov", "scraped")
- **Confidence**: Existing INTEGER column in leads table that stores reliability score (0-100) of discovered email
- **Domain**: Company website domain extracted from company name (e.g., "blitzenx.com")
- **Lead**: Database record in leads table containing internship_id, email, source, confidence, verified, mx_valid, smtp_valid, and other contact information
- **Cycle_Manager**: The pipeline orchestrator that processes internships through discovery phases
- **Company_Domains**: Existing table that caches email discovery results per domain with columns: domain, emails (JSONB), hunter_called, last_checked

## Requirements

### Requirement 1: Pattern-Based Email Guessing

**User Story:** As a pipeline operator, I want to generate common email patterns when Hunter.io returns no results, so that I can attempt to contact companies using standard HR/recruiting email addresses.

#### Acceptance Criteria

1. WHEN Hunter.io returns no email for a Domain, THE Pattern_Guesser SHALL generate all 5 candidate emails using patterns: hr@domain, careers@domain, internships@domain, hello@domain, info@domain
2. THE Pattern_Guesser SHALL generate candidates in the specified order without making any external API calls
3. THE Pattern_Guesser SHALL mark all generated candidates with source="pattern_guess" and confidence=50
4. THE Pattern_Guesser SHALL return ALL 5 generated candidate emails as a list
5. WHEN Pattern_Guesser returns candidates, THE Email_Discovery_System SHALL validate all candidates and select the best one based on validation results
6. THE Email_Discovery_System SHALL NOT execute subsequent fallback methods (Snov_Client, Website_Scraper) when Pattern_Guesser returns at least one validated candidate
7. THE Cycle_Manager SHALL log all patterns generated and which pattern was selected after validation

### Requirement 2: Snov.io API Integration

**User Story:** As a pipeline operator, I want to use Snov.io as a secondary email discovery service, so that I can find verified company emails when Hunter.io and pattern guessing fail.

#### Acceptance Criteria

1. WHEN Pattern_Guesser returns no results, THE Snov_Client SHALL authenticate with Snov.io using SNOV_CLIENT_ID and SNOV_CLIENT_SECRET environment variables
2. THE Snov_Client SHALL request an access token from Snov.io OAuth endpoint before making domain search calls
3. WHEN authentication succeeds, THE Snov_Client SHALL call the Snov.io Domain Search endpoint (https://api.snov.io/v2/domain-emails-with-info) with the Domain parameter
4. THE Snov_Client SHALL select the email with the highest confidence score from the returned results
5. THE Snov_Client SHALL mark the selected email with source="snov" and preserve the confidence score from Snov.io API response
6. WHEN Snov_Client returns an email, THE Email_Discovery_System SHALL NOT execute subsequent fallback methods
7. IF Snov.io authentication fails, THEN THE Snov_Client SHALL log the error and return no results
8. IF Snov.io API call fails, THEN THE Snov_Client SHALL log the error and return no results

### Requirement 3: Website Scraping Fallback

**User Story:** As a pipeline operator, I want to scrape company websites for contact emails, so that I can discover emails published on contact/about/careers pages when API methods fail.

#### Acceptance Criteria

1. WHEN Snov_Client returns no results, THE Website_Scraper SHALL attempt to scrape the following URLs in order: domain.com/contact, domain.com/about, domain.com/careers
2. THE Website_Scraper SHALL use the existing Scrapling library (Fetcher.get) to fetch page content
3. THE Website_Scraper SHALL extract email addresses from page HTML using regex pattern: [a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}
4. THE Website_Scraper SHALL stop scraping additional pages when an email is found on any page
5. THE Website_Scraper SHALL mark discovered emails with source="scraped" and confidence=70
6. THE Website_Scraper SHALL return the first valid email address found
7. IF scraping fails for a URL, THEN THE Website_Scraper SHALL log the error and continue to the next URL
8. IF all URLs fail to return emails, THEN THE Website_Scraper SHALL return no results

### Requirement 4: Fallback Chain Orchestration

**User Story:** As a pipeline operator, I want email discovery methods to execute sequentially with proper fallback logic, so that the system tries all available methods before marking an internship as "no_email".

#### Acceptance Criteria

1. THE Email_Discovery_System SHALL execute email discovery methods in this order: Hunter_Client, Pattern_Guesser, Snov_Client, Website_Scraper
2. WHEN any method returns a validated email, THE Email_Discovery_System SHALL immediately return that email and skip remaining methods
3. WHEN Pattern_Guesser returns candidates but none pass validation, THE Email_Discovery_System SHALL continue to Snov_Client
4. WHEN all methods return no results, THE Email_Discovery_System SHALL return no results and mark the internship status as "no_email"
5. THE Email_Discovery_System SHALL preserve the source field through the entire pipeline to the leads table
6. THE Cycle_Manager SHALL log an event for each fallback method attempted with the method name and result
7. THE Cycle_Manager SHALL log a final event indicating which method successfully found the email or that all methods failed

### Requirement 5: Lead Creation with Source Tracking

**User Story:** As a pipeline operator, I want to track which discovery method found each email, so that I can analyze the effectiveness of each method and prioritize future improvements.

#### Acceptance Criteria

1. WHEN a Lead is created, THE Cycle_Manager SHALL store the source value in the existing leads.source column
2. WHEN a Lead is created, THE Cycle_Manager SHALL store the confidence score in the existing leads.confidence column
3. THE Cycle_Manager SHALL log the source and confidence in the "email_found" event
4. WHERE source="pattern_guess", THE Cycle_Manager SHALL set verified=FALSE in the leads table to indicate the email is unverified
5. THE Cycle_Manager SHALL maintain backward compatibility with existing Hunter.io leads (source="hunter")
6. THE leads table SHALL use existing columns: source (TEXT), confidence (INTEGER), verified (BOOLEAN), mx_valid (BOOLEAN), smtp_valid (BOOLEAN)

### Requirement 6: Error Handling and Resilience

**User Story:** As a pipeline operator, I want the fallback chain to handle errors gracefully, so that a failure in one method doesn't prevent other methods from executing.

#### Acceptance Criteria

1. WHEN any fallback method raises an exception, THE Email_Discovery_System SHALL log the error with method name and error details
2. WHEN any fallback method raises an exception, THE Email_Discovery_System SHALL continue to the next fallback method
3. IF Snov.io environment variables are missing, THEN THE Snov_Client SHALL log a warning and return no results without raising an exception
4. IF Scrapling fetch times out, THEN THE Website_Scraper SHALL log the timeout and continue to the next URL
5. THE Email_Discovery_System SHALL NOT crash the pipeline when all fallback methods fail

### Requirement 7: Configuration and Environment Variables

**User Story:** As a system administrator, I want to configure Snov.io credentials via environment variables, so that I can securely manage API access without hardcoding credentials.

#### Acceptance Criteria

1. THE Snov_Client SHALL read SNOV_CLIENT_ID from environment variables
2. THE Snov_Client SHALL read SNOV_CLIENT_SECRET from environment variables
3. WHERE SNOV_CLIENT_ID or SNOV_CLIENT_SECRET are not set, THE Snov_Client SHALL skip Snov.io API calls and return no results
4. THE implementation SHALL add SNOV_CLIENT_ID and SNOV_CLIENT_SECRET to the .env.example file with placeholder values
5. THE implementation SHALL update both .env and .env.example files with the required Snov.io environment variables
6. THE .env.example file SHALL include comments explaining how to obtain Snov.io API credentials

### Requirement 8: Domain-Level Result Caching

**User Story:** As a pipeline operator, I want to cache email discovery results at the domain level, so that I can avoid redundant API calls for the same company domain.

#### Acceptance Criteria

1. WHEN any email discovery method successfully finds an email for a Domain, THE Email_Discovery_System SHALL update the company_domains.emails JSONB column with the discovered email and source
2. THE Email_Discovery_System SHALL update company_domains.last_checked timestamp when any discovery method is executed for a Domain
3. WHEN processing a new internship for an existing Domain, THE Email_Discovery_System SHALL check company_domains.emails before executing fallback methods
4. WHERE company_domains.emails contains a cached result, THE Email_Discovery_System SHALL use the cached email and skip all discovery methods
5. THE company_domains table SHALL use existing columns: domain (TEXT PRIMARY KEY), emails (JSONB), hunter_called (BOOLEAN), last_checked (TIMESTAMPTZ)
