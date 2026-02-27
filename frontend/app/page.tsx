"use client";

import { useEffect, useState } from "react";
import { Sidebar } from "../components/layout/Sidebar";
import { TopBar } from "../components/layout/TopBar";
import { MetricCard } from "../components/dashboard/MetricCard";
import { ProgressBar } from "../components/dashboard/ProgressBar";
import { FunnelBar } from "../components/dashboard/FunnelBar";
import { fetchDashboardData } from "../lib/api";
import type { DashboardData } from "../lib/types";

export default function DashboardPage() {
  const [data, setData] = useState<DashboardData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        setLoading(true);
        const payload = await fetchDashboardData();
        if (!cancelled) {
          setData(payload);
        }
      } catch (err) {
        if (!cancelled) {
          setError(err instanceof Error ? err.message : "Unknown error");
        }
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    })();

    return () => {
      cancelled = true;
    };
  }, []);

  const lastUpdatedLabel = data
    ? new Date(data.lastUpdated).toLocaleString()
    : loading
    ? "Loading…"
    : "Failed to load";

  return (
    <div className="flex min-h-screen p-4 gap-4">
      <Sidebar>
        {/* Extra controls can be added here later */}
      </Sidebar>

      <main className="flex-1 flex flex-col gap-4 overflow-hidden">
        <TopBar lastUpdatedLabel={lastUpdatedLabel} />

        {loading && (
          <div className="flex-1 flex items-center justify-center text-slate-400 text-sm">
            Loading dashboard data from backend…
          </div>
        )}

        {error && !loading && (
          <div className="glass-panel p-4 text-sm text-rose-300 border-rose-500/40">
            <p className="font-semibold mb-1">Unable to reach backend</p>
            <p>{error}</p>
            <p className="mt-2 text-xs text-rose-200/80">
              Once your backend exposes a `GET /dashboard` endpoint and you set
              <code className="mx-1 rounded bg-slate-900 px-1 py-0.5 text-[11px]">
                NEXT_PUBLIC_API_BASE_URL
              </code>
              this view will populate automatically.
            </p>
          </div>
        )}

        {!loading && !error && data && (
          <div className="flex-1 flex flex-col gap-4 overflow-y-auto pb-6 scrollbar-thin">
            {/* Overview */}
            <section id="overview" className="grid grid-cols-1 md:grid-cols-4 gap-4">
              <MetricCard
                label="Internships discovered (today)"
                value={data.discovery.internshipsToday}
                hint="Fresh roles scraped across all tiers in the last 24h."
                accent="blue"
              />
              <MetricCard
                label="Emails sent (today)"
                value={`${data.outreach.emailsSentToday} / ${data.outreach.dailyEmailLimit}`}
                hint="Warmup-aware Gmail send cap with 45min spacing."
                accent="emerald"
              />
              <MetricCard
                label="Positive reply rate"
                value={`${data.performance.positiveReplyRate.toFixed(1)}%`}
                hint="Based on replies classified as positive in the last 30 days."
                accent="amber"
              />
              <MetricCard
                label="Active retries"
                value={data.retries.activeRetriesByPhase.reduce(
                  (sum, r) => sum + r.activeJobs,
                  0
                )}
                hint="Jobs currently in the retry queue across Groq, Hunter, Gmail, and Twilio."
                accent="rose"
              />
            </section>

            {/* Discovery */}
            <section
              id="discovery"
              className="glass-panel p-4 flex flex-col gap-4"
            >
              <header className="flex items-center justify-between">
                <div>
                  <h2 className="text-sm font-semibold tracking-tight">
                    Discovery Panel
                  </h2>
                  <p className="text-xs text-slate-400">
                    3-tier scraping engine health and Firecrawl budget.
                  </p>
                </div>
              </header>

              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <MetricCard
                  label="Internships (this week)"
                  value={data.discovery.internshipsThisWeek}
                  hint="Unique roles passing deduplication over the current week."
                />
                <MetricCard
                  label="Pre-score kill rate"
                  value={`${data.discovery.preScoreKillRate.toFixed(1)}%`}
                  hint="Low-signal roles stopped at Gate 1 before any API spend."
                  accent="amber"
                />
                <MetricCard
                  label="Firecrawl usage"
                  value={`${data.discovery.firecrawlUsed} / ${data.discovery.firecrawlLimit}`}
                  hint="High-cost fallback calls today across all domains."
                  accent="rose"
                />
              </div>

              <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-xs text-slate-300">
                <div>
                  <p className="mb-2 text-[11px] uppercase tracking-wide text-slate-400">
                    Scrapling Tier Success
                  </p>
                  <ul className="space-y-1">
                    <li>
                      Tier 1 (HTTP):{" "}
                      <span className="font-medium">
                        {data.discovery.tier1SuccessRate.toFixed(1)}%
                      </span>
                    </li>
                    <li>
                      Tier 2 (Dynamic):{" "}
                      <span className="font-medium">
                        {data.discovery.tier2SuccessRate.toFixed(1)}%
                      </span>
                    </li>
                    <li>
                      Tier 3 (Firecrawl):{" "}
                      <span className="font-medium">
                        {data.discovery.tier3SuccessRate.toFixed(1)}%
                      </span>
                    </li>
                  </ul>
                </div>

                <div className="md:col-span-2">
                  <ProgressBar
                    value={data.discovery.firecrawlUsed}
                    max={data.discovery.firecrawlLimit}
                    label="Firecrawl daily cap"
                  />
                </div>
              </div>
            </section>

            {/* Email quality */}
            <section id="email-quality" className="glass-panel p-4 flex flex-col gap-4">
              <header className="flex items-center justify-between">
                <div>
                  <h2 className="text-sm font-semibold tracking-tight">
                    Email Panel
                  </h2>
                  <p className="text-xs text-slate-400">
                    Source mix, Hunter credit shield, and validation failures.
                  </p>
                </div>
              </header>

              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <MetricCard
                  label="Regex vs Hunter"
                  value={
                    <div className="text-sm">
                      <span className="font-semibold">
                        {data.email.regexEmails}
                      </span>{" "}
                      regex ·{" "}
                      <span className="font-semibold">
                        {data.email.hunterEmails}
                      </span>{" "}
                      Hunter
                    </div>
                  }
                  hint="Regex is free; Hunter is guarded by pre-score + limits."
                  accent="blue"
                />
                <MetricCard
                  label="Hunter calls (today)"
                  value={`${data.email.hunterCallsToday} / ${data.email.hunterDailyLimit}`}
                  hint="One call per new domain only, with strict daily cap."
                  accent="emerald"
                />
                <MetricCard
                  label="Validation failures"
                  value={
                    <div className="text-xs space-y-0.5">
                      <p>MX: {data.email.validationFailuresMx}</p>
                      <p>Format: {data.email.validationFailuresFormat}</p>
                      <p>SMTP: {data.email.validationFailuresSmtp}</p>
                    </div>
                  }
                  hint="Emails killed at Gate 2 to protect sender reputation."
                  accent="rose"
                />
              </div>
            </section>

            {/* Outreach */}
            <section id="outreach" className="glass-panel p-4 flex flex-col gap-4">
              <header className="flex items-center justify-between">
                <div>
                  <h2 className="text-sm font-semibold tracking-tight">
                    Outreach Panel
                  </h2>
                  <p className="text-xs text-slate-400">
                    Groq drafts, approvals, Gmail warmup, and follow-ups.
                  </p>
                </div>
              </header>

              <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                <MetricCard
                  label="Groq drafts generated"
                  value={data.outreach.groqDraftsGenerated}
                  hint="Leads that made it through all three kill gates."
                />
                <MetricCard
                  label="Approval rate"
                  value={`${data.outreach.approvalRate.toFixed(1)}%`}
                  hint="YES + auto-approved over total drafts awaiting approval."
                  accent="emerald"
                />
                <MetricCard
                  label="Auto-approvals (2h timeout)"
                  value={data.outreach.autoApprovals}
                  hint="High-scoring drafts auto-routed to the email queue."
                  accent="amber"
                />
                <MetricCard
                  label="Pending follow-ups"
                  value={data.outreach.pendingFollowups}
                  hint="Day 5 follow-ups not yet sent and not cancelled by replies."
                  accent="blue"
                />
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <ProgressBar
                  value={data.outreach.emailsSentToday}
                  max={data.outreach.dailyEmailLimit}
                  label="Gmail warmup-aware daily limit"
                />
                <div className="space-y-1 text-xs text-slate-300">
                  <p className="text-[11px] uppercase tracking-wide text-slate-400">
                    Warmup Phase
                  </p>
                  <div className="flex items-center gap-2">
                    <div className="h-2 flex-1 rounded-full bg-slate-900/80 overflow-hidden">
                      <div
                        className="h-full rounded-full bg-gradient-to-r from-amber-400 via-amber-300 to-emerald-400"
                        style={{
                          width: `${Math.min(
                            100,
                            Math.round(data.outreach.warmupProgressPct)
                          )}%`
                        }}
                      />
                    </div>
                    <span className="text-[11px] text-slate-400">
                      {data.outreach.warmupProgressPct.toFixed(0)}%
                    </span>
                  </div>
                  <p className="text-[11px] text-slate-500">
                    {data.outreach.isWarmupPhase
                      ? "Gradually increasing daily send volume to avoid spam flags."
                      : "Warmup complete — running at full daily capacity."}
                  </p>
                </div>
              </div>
            </section>

            {/* Performance */}
            <section id="performance" className="glass-panel p-4 flex flex-col gap-4">
              <header className="flex items-center justify-between">
                <div>
                  <h2 className="text-sm font-semibold tracking-tight">
                    Performance Panel
                  </h2>
                  <p className="text-xs text-slate-400">
                    Funnel performance, reply rates, and scoring weight tuner.
                  </p>
                </div>
              </header>

              <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
                <div className="lg:col-span-2">
                  <FunnelBar stages={data.performance.funnel} />
                </div>
                <div className="space-y-2 text-xs text-slate-300">
                  <p className="text-[11px] uppercase tracking-wide text-slate-400">
                    Top company types
                  </p>
                  <ul className="space-y-1">
                    {data.performance.topCompanyTypes.map((c) => (
                      <li
                        key={c.type}
                        className="flex items-center justify-between"
                      >
                        <span>{c.type}</span>
                        <span className="text-emerald-300">
                          {c.replyRate.toFixed(1)}%
                        </span>
                      </li>
                    ))}
                  </ul>
                </div>
              </div>

              <div className="mt-2">
                <p className="text-[11px] uppercase tracking-wide text-slate-400 mb-2">
                  Scoring weights (from Supabase)
                </p>
                <div className="overflow-x-auto scrollbar-thin">
                  <table className="min-w-full text-xs text-left">
                    <thead className="text-slate-400 border-b border-slate-800">
                      <tr>
                        <th className="py-2 pr-4">Signal</th>
                        <th className="py-2 pr-4">Weight</th>
                        <th className="py-2">Description</th>
                      </tr>
                    </thead>
                    <tbody>
                      {data.scoringConfig.map((row) => (
                        <tr
                          key={row.key}
                          className="border-b border-slate-900/60 last:border-0"
                        >
                          <td className="py-2 pr-4 font-mono text-[11px] text-slate-300">
                            {row.key}
                          </td>
                          <td className="py-2 pr-4">
                            {row.weight.toFixed(2)}
                          </td>
                          <td className="py-2 text-slate-400">
                            {row.description}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
                <p className="mt-1 text-[11px] text-slate-500">
                  This table is read-only from the frontend. Hook it up to a
                  secure backend endpoint if you later want to edit weights from
                  the UI.
                </p>
              </div>
            </section>

            {/* Retry / reliability */}
            <section id="retries" className="glass-panel p-4 flex flex-col gap-4">
              <header className="flex items-center justify-between">
                <div>
                  <h2 className="text-sm font-semibold tracking-tight">
                    Retry Panel
                  </h2>
                  <p className="text-xs text-slate-400">
                    Exponential backoff jobs and max-retry failures that need
                    manual attention.
                  </p>
                </div>
              </header>

              <div className="grid grid-cols-1 md:grid-cols-4 gap-4 text-xs text-slate-300">
                {data.retries.activeRetriesByPhase.map((r) => (
                  <div key={r.phase} className="glass-panel p-3">
                    <p className="text-[11px] uppercase tracking-wide text-slate-400 mb-1">
                      {r.phase.toUpperCase()}
                    </p>
                    <p className="text-lg font-semibold">{r.activeJobs}</p>
                    <p className="text-[11px] text-slate-500">
                      Active jobs in retry queue for this phase.
                    </p>
                  </div>
                ))}
              </div>

              <div className="mt-2">
                <p className="text-[11px] uppercase tracking-wide text-slate-400 mb-2">
                  Max-retry failures
                </p>
                {data.retries.maxRetryFailures.length === 0 ? (
                  <p className="text-xs text-emerald-300">
                    No jobs have hit their retry ceiling. All external
                    integrations are healthy.
                  </p>
                ) : (
                  <div className="overflow-x-auto scrollbar-thin">
                    <table className="min-w-full text-xs text-left">
                      <thead className="text-slate-400 border-b border-slate-800">
                        <tr>
                          <th className="py-2 pr-4">Phase</th>
                          <th className="py-2 pr-4">Created</th>
                          <th className="py-2">Last error</th>
                        </tr>
                      </thead>
                      <tbody>
                        {data.retries.maxRetryFailures.map((job) => (
                          <tr
                            key={job.id}
                            className="border-b border-slate-900/60 last:border-0"
                          >
                            <td className="py-2 pr-4 font-mono text-[11px] text-slate-300">
                              {job.phase.toUpperCase()}
                            </td>
                            <td className="py-2 pr-4 text-slate-400">
                              {new Date(job.createdAt).toLocaleString()}
                            </td>
                            <td className="py-2 text-slate-400 max-w-xl">
                              <span className="inline-block truncate align-top">
                                {job.lastError}
                              </span>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}
              </div>
            </section>
          </div>
        )}
      </main>
    </div>
  );
}

