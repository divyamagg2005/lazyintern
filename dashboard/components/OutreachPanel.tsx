type Props = {
  draftsGeneratedToday: number;
  approvalsToday: number;
  autoApprovalsToday: number;
  sentToday: number;
  dailyLimit: number;
  followupsPending: number;
};

export function OutreachPanel({
  draftsGeneratedToday,
  approvalsToday,
  autoApprovalsToday,
  sentToday,
  dailyLimit,
  followupsPending,
}: Props) {
  return (
    <section className="rounded-xl border border-zinc-200 bg-white p-4 dark:border-zinc-800 dark:bg-zinc-950">
      <h2 className="text-sm font-semibold text-zinc-900 dark:text-zinc-100">Outreach</h2>
      <div className="mt-3 grid grid-cols-2 gap-3 text-sm">
        <div className="rounded-lg bg-zinc-50 p-3 dark:bg-zinc-900">
          <p className="text-zinc-500 dark:text-zinc-400">Drafts Today</p>
          <p className="text-lg font-semibold">{draftsGeneratedToday}</p>
        </div>
        <div className="rounded-lg bg-zinc-50 p-3 dark:bg-zinc-900">
          <p className="text-zinc-500 dark:text-zinc-400">Approvals Today</p>
          <p className="text-lg font-semibold">{approvalsToday}</p>
        </div>
        <div className="rounded-lg bg-zinc-50 p-3 dark:bg-zinc-900">
          <p className="text-zinc-500 dark:text-zinc-400">Auto-Approvals Today</p>
          <p className="text-lg font-semibold">{autoApprovalsToday}</p>
        </div>
        <div className="rounded-lg bg-zinc-50 p-3 dark:bg-zinc-900">
          <p className="text-zinc-500 dark:text-zinc-400">Sent Today</p>
          <p className="text-lg font-semibold">
            {sentToday} / {dailyLimit}
          </p>
        </div>
      </div>
      <p className="mt-3 text-xs text-zinc-500 dark:text-zinc-400">
        Pending follow-ups: {followupsPending}
      </p>
    </section>
  );
}

