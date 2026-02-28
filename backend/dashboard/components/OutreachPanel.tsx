interface OutreachData {
  groqDraftsGenerated: number;
  approvalRate: number;
  autoApprovals: number;
  emailsSentToday: number;
  dailyEmailLimit: number;
  isWarmupPhase: boolean;
  warmupProgressPct: number;
  pendingFollowups: number;
  smsSentToday: number;
  smsDailyLimit: number;
}

export function OutreachPanel({ data }: { data?: OutreachData }) {
  if (!data) {
    return (
      <section className="rounded-xl border border-zinc-200 bg-white p-6 dark:border-zinc-800 dark:bg-zinc-950">
        <h2 className="text-lg font-semibold text-zinc-900 dark:text-zinc-100">
          🚀 Outreach
        </h2>
        <p className="mt-2 text-sm text-zinc-500">Loading...</p>
      </section>
    );
  }

  return (
    <section className="rounded-xl border border-zinc-200 bg-white p-6 dark:border-zinc-800 dark:bg-zinc-950">
      <h2 className="text-lg font-semibold text-zinc-900 dark:text-zinc-100">
        🚀 Outreach
      </h2>
      
      {/* Drafts & Approval */}
      <div className="mt-4 grid grid-cols-2 gap-4">
        <div>
          <p className="text-2xl font-bold text-zinc-900 dark:text-zinc-100">
            {data.groqDraftsGenerated}
          </p>
          <p className="text-xs text-zinc-600 dark:text-zinc-400">Groq Drafts</p>
        </div>
        <div>
          <p className="text-2xl font-bold text-green-600 dark:text-green-400">
            {data.approvalRate.toFixed(0)}%
          </p>
          <p className="text-xs text-zinc-600 dark:text-zinc-400">Approval Rate</p>
        </div>
      </div>

      {/* Auto Approvals */}
      <div className="mt-4 rounded-lg bg-purple-50 p-3 dark:bg-purple-950/20">
        <div className="flex items-center justify-between">
          <span className="text-sm text-purple-900 dark:text-purple-100">
            Auto-Approvals (2h timeout)
          </span>
          <span className="text-lg font-bold text-purple-700 dark:text-purple-400">
            {data.autoApprovals}
          </span>
        </div>
        <p className="mt-1 text-xs text-purple-600 dark:text-purple-500">
          All drafts auto-approve after 2 hours
        </p>
      </div>

      {/* Email Sending */}
      <div className="mt-6">
        <div className="flex items-center justify-between">
          <span className="text-sm font-medium text-zinc-700 dark:text-zinc-300">
            Emails Sent Today
          </span>
          <span className="text-xl font-bold text-zinc-900 dark:text-zinc-100">
            {data.emailsSentToday}/{data.dailyEmailLimit}
          </span>
        </div>
        <div className="mt-2 h-3 w-full overflow-hidden rounded-full bg-zinc-200 dark:bg-zinc-800">
          <div
            className={`h-full ${
              data.emailsSentToday >= data.dailyEmailLimit
                ? "bg-red-500"
                : "bg-green-500"
            }`}
            style={{ width: `${(data.emailsSentToday / data.dailyEmailLimit) * 100}%` }}
          />
        </div>
        {data.isWarmupPhase && (
          <p className="mt-2 text-xs text-yellow-600 dark:text-yellow-500">
            ⚠️ Warmup Phase: {data.warmupProgressPct.toFixed(0)}% complete
          </p>
        )}
      </div>

      {/* SMS Sending */}
      <div className="mt-4">
        <div className="flex items-center justify-between">
          <span className="text-sm font-medium text-zinc-700 dark:text-zinc-300">
            SMS Sent Today
          </span>
          <span className="text-xl font-bold text-zinc-900 dark:text-zinc-100">
            {data.smsSentToday}/{data.smsDailyLimit}
          </span>
        </div>
        <div className="mt-2 h-3 w-full overflow-hidden rounded-full bg-zinc-200 dark:bg-zinc-800">
          <div
            className={`h-full ${
              data.smsSentToday >= data.smsDailyLimit
                ? "bg-red-500"
                : "bg-blue-500"
            }`}
            style={{ width: `${(data.smsSentToday / data.smsDailyLimit) * 100}%` }}
          />
        </div>
      </div>

      {/* Follow-ups */}
      <div className="mt-6 rounded-lg bg-orange-50 p-3 dark:bg-orange-950/20">
        <div className="flex items-center justify-between">
          <span className="text-sm text-orange-900 dark:text-orange-100">
            Pending Follow-ups
          </span>
          <span className="text-lg font-bold text-orange-700 dark:text-orange-400">
            {data.pendingFollowups}
          </span>
        </div>
        <p className="mt-1 text-xs text-orange-600 dark:text-orange-500">
          Scheduled for 3-5 days after initial send
        </p>
      </div>
    </section>
  );
}

