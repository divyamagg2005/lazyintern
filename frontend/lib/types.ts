export interface DiscoveryMetrics {
  internshipsToday: number;
  internshipsThisWeek: number;
  tier1SuccessRate: number;
  tier2SuccessRate: number;
  tier3SuccessRate: number;
  preScoreKillRate: number;
  firecrawlUsed: number;
  firecrawlLimit: number;
}

export interface EmailMetrics {
  regexEmails: number;
  hunterEmails: number;
  hunterCallsToday: number;
  hunterDailyLimit: number;
  validationFailuresMx: number;
  validationFailuresFormat: number;
  validationFailuresSmtp: number;
}

export interface OutreachMetrics {
  groqDraftsGenerated: number;
  approvalRate: number;
  autoApprovals: number;
  emailsSentToday: number;
  dailyEmailLimit: number;
  isWarmupPhase: boolean;
  warmupProgressPct: number;
  pendingFollowups: number;
}

export interface FunnelStageMetric {
  label: string;
  count: number;
}

export interface CompanyTypePerformance {
  type: string;
  replyRate: number;
}

export interface PerformanceMetrics {
  replyRate: number;
  positiveReplyRate: number;
  funnel: FunnelStageMetric[];
  topCompanyTypes: CompanyTypePerformance[];
}

export type RetryPhase = "groq" | "twilio" | "gmail" | "hunter";

export interface RetrySummary {
  phase: RetryPhase;
  activeJobs: number;
}

export interface MaxRetryFailure {
  id: string;
  phase: RetryPhase;
  lastError: string;
  createdAt: string;
}

export interface RetryMetrics {
  activeRetriesByPhase: RetrySummary[];
  maxRetryFailures: MaxRetryFailure[];
}

export interface ScoringWeight {
  key: string;
  weight: number;
  description?: string;
}

export interface DashboardData {
  lastUpdated: string;
  discovery: DiscoveryMetrics;
  email: EmailMetrics;
  outreach: OutreachMetrics;
  performance: PerformanceMetrics;
  retries: RetryMetrics;
  scoringConfig: ScoringWeight[];
}

