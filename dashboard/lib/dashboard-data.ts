import { createSupabaseServerClient } from "@/lib/supabase";

type CountMap = Record<string, number>;

export type DashboardData = {
  connected: boolean;
  connectionError?: string;
  discovery: {
    internshipsToday: number;
    internshipsWeek: number;
    scrapeFailuresToday: number;
    preScoreKillsToday: number;
    firecrawlUsedToday: number;
  };
  email: {
    regexFound: number;
    hunterFound: number;
    leadsVerified: number;
    validationFailsToday: number;
    hunterCallsToday: number;
  };
  outreach: {
    draftsGeneratedToday: number;
    approvalsToday: number;
    autoApprovalsToday: number;
    sentToday: number;
    dailyLimit: number;
    followupsPending: number;
  };
  performance: {
    repliedPositive: number;
    repliedNegative: number;
    repliedNeutral: number;
  };
  retry: {
    activeByPhase: CountMap;
    maxRetryFailures: number;
  };
  funnel: {
    discovered: number;
    preScored: number;
    emailFound: number;
    emailValid: number;
    fullScored: number;
    draftGenerated: number;
    approved: number;
    sent: number;
    replied: number;
  };
  logs: Array<{
    id: string;
    event: string;
    created_at: string;
    internship_id: string | null;
    metadata: unknown;
  }>;
};

const TODAY = new Date().toISOString().slice(0, 10);

type EventRow = {
  id: string;
  event: string;
  created_at: string;
  internship_id: string | null;
  metadata: unknown;
};

type UsageRow = {
  pre_score_kills: number | null;
  firecrawl_calls: number | null;
  validation_fails: number | null;
  hunter_calls: number | null;
  auto_approvals: number | null;
  daily_limit: number | null;
};

type LeadRow = { verified: boolean | null };
type DraftRow = { sent_at: string | null };
type RetryRow = {
  phase: string | null;
  attempts: number | null;
  max_attempts: number | null;
};

function startsWithToday(iso: string | null | undefined): boolean {
  return typeof iso === "string" && iso.startsWith(TODAY);
}

function countBy<T>(rows: T[], selector: (row: T) => string): CountMap {
  return rows.reduce<CountMap>((acc, row) => {
    const key = selector(row);
    acc[key] = (acc[key] ?? 0) + 1;
    return acc;
  }, {});
}

export async function getDashboardData(): Promise<DashboardData> {
  const supabase = createSupabaseServerClient();
  if (!supabase) {
    return {
      connected: false,
      connectionError:
        "Supabase env vars missing. Set SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY in dashboard runtime.",
      discovery: {
        internshipsToday: 0,
        internshipsWeek: 0,
        scrapeFailuresToday: 0,
        preScoreKillsToday: 0,
        firecrawlUsedToday: 0,
      },
      email: {
        regexFound: 0,
        hunterFound: 0,
        leadsVerified: 0,
        validationFailsToday: 0,
        hunterCallsToday: 0,
      },
      outreach: {
        draftsGeneratedToday: 0,
        approvalsToday: 0,
        autoApprovalsToday: 0,
        sentToday: 0,
        dailyLimit: 0,
        followupsPending: 0,
      },
      performance: {
        repliedPositive: 0,
        repliedNegative: 0,
        repliedNeutral: 0,
      },
      retry: {
        activeByPhase: {},
        maxRetryFailures: 0,
      },
      funnel: {
        discovered: 0,
        preScored: 0,
        emailFound: 0,
        emailValid: 0,
        fullScored: 0,
        draftGenerated: 0,
        approved: 0,
        sent: 0,
        replied: 0,
      },
      logs: [],
    };
  }

  const [eventsRes, usageRes, leadsRes, draftsRes, retryRes, followupsRes] =
    await Promise.all([
      supabase
        .from("pipeline_events")
        .select("id,event,created_at,internship_id,metadata")
        .order("created_at", { ascending: false })
        .limit(300),
      supabase
        .from("daily_usage_stats")
        .select("*")
        .eq("date", TODAY)
        .maybeSingle(),
      supabase
        .from("leads")
        .select("id,source,verified,created_at")
        .order("created_at", { ascending: false })
        .limit(300),
      supabase
        .from("email_drafts")
        .select("id,status,created_at,sent_at")
        .order("created_at", { ascending: false })
        .limit(300),
      supabase
        .from("retry_queue")
        .select("id,phase,attempts,max_attempts,resolved")
        .eq("resolved", false),
      supabase
        .from("followup_queue")
        .select("id,sent")
        .eq("sent", false),
    ]);

  if (eventsRes.error) {
    return {
      connected: false,
      connectionError: eventsRes.error.message,
      discovery: {
        internshipsToday: 0,
        internshipsWeek: 0,
        scrapeFailuresToday: 0,
        preScoreKillsToday: 0,
        firecrawlUsedToday: 0,
      },
      email: {
        regexFound: 0,
        hunterFound: 0,
        leadsVerified: 0,
        validationFailsToday: 0,
        hunterCallsToday: 0,
      },
      outreach: {
        draftsGeneratedToday: 0,
        approvalsToday: 0,
        autoApprovalsToday: 0,
        sentToday: 0,
        dailyLimit: 0,
        followupsPending: 0,
      },
      performance: { repliedPositive: 0, repliedNegative: 0, repliedNeutral: 0 },
      retry: { activeByPhase: {}, maxRetryFailures: 0 },
      funnel: {
        discovered: 0,
        preScored: 0,
        emailFound: 0,
        emailValid: 0,
        fullScored: 0,
        draftGenerated: 0,
        approved: 0,
        sent: 0,
        replied: 0,
      },
      logs: [],
    };
  }

  const events = (eventsRes.data ?? []) as EventRow[];
  const logs = events.slice(0, 80);
  const eventsToday = events.filter((e) => startsWithToday(e.created_at));
  const usage = usageRes.data as UsageRow | null;
  const leads = (leadsRes.data ?? []) as LeadRow[];
  const drafts = (draftsRes.data ?? []) as DraftRow[];
  const retries = (retryRes.data ?? []) as RetryRow[];
  const followups = followupsRes.data ?? [];
  const eventCount = countBy(events, (e) => e.event);
  const eventCountToday = countBy(eventsToday, (e) => e.event);
  const retryByPhase = countBy(retries, (r) => r.phase ?? "unknown");

  const repliedPositive = eventCount["replied_positive"] ?? 0;
  const repliedNegative = eventCount["replied_negative"] ?? 0;
  const repliedNeutral = eventCount["replied_neutral"] ?? 0;

  const maxRetryFailures = retries.filter(
    (r) => (r.attempts ?? 0) >= (r.max_attempts ?? 3),
  ).length;

  const sentToday = drafts.filter((d) => startsWithToday(d.sent_at)).length;
  const approvalsToday =
    (eventCountToday.approved ?? 0) + (eventCountToday.auto_approved ?? 0);

  return {
    connected: true,
    discovery: {
      internshipsToday: eventCountToday.discovered ?? 0,
      internshipsWeek: eventCount.discovered ?? 0,
      scrapeFailuresToday: eventCountToday.scrape_failed ?? 0,
      preScoreKillsToday: usage?.pre_score_kills ?? 0,
      firecrawlUsedToday: usage?.firecrawl_calls ?? 0,
    },
    email: {
      regexFound: eventCount.email_found_regex ?? 0,
      hunterFound: eventCount.email_found_hunter ?? 0,
      leadsVerified: leads.filter((l) => l.verified).length,
      validationFailsToday: usage?.validation_fails ?? 0,
      hunterCallsToday: usage?.hunter_calls ?? 0,
    },
    outreach: {
      draftsGeneratedToday: eventCountToday.draft_generated ?? 0,
      approvalsToday,
      autoApprovalsToday: usage?.auto_approvals ?? 0,
      sentToday,
      dailyLimit: usage?.daily_limit ?? 0,
      followupsPending: followups.length,
    },
    performance: {
      repliedPositive,
      repliedNegative,
      repliedNeutral,
    },
    retry: {
      activeByPhase: retryByPhase,
      maxRetryFailures,
    },
    funnel: {
      discovered: eventCount.discovered ?? 0,
      preScored: eventCount.pre_scored ?? 0,
      emailFound:
        (eventCount.email_found_regex ?? 0) + (eventCount.email_found_hunter ?? 0),
      emailValid: eventCount.email_valid ?? 0,
      fullScored: eventCount.full_scored ?? 0,
      draftGenerated: eventCount.draft_generated ?? 0,
      approved:
        (eventCount.approved ?? 0) + (eventCount.auto_approved ?? 0),
      sent: eventCount.sent ?? 0,
      replied: repliedPositive + repliedNegative + repliedNeutral,
    },
    logs,
  };
}

