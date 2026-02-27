type Props = {
  regexFound: number;
  hunterFound: number;
  leadsVerified: number;
  validationFailsToday: number;
  hunterCallsToday: number;
};

export function EmailPanel({
  regexFound,
  hunterFound,
  leadsVerified,
  validationFailsToday,
  hunterCallsToday,
}: Props) {
  return (
    <section className="rounded-xl border border-zinc-200 bg-white p-4 dark:border-zinc-800 dark:bg-zinc-950">
      <h2 className="text-sm font-semibold text-zinc-900 dark:text-zinc-100">Email</h2>
      <div className="mt-3 grid grid-cols-2 gap-3 text-sm">
        <div className="rounded-lg bg-zinc-50 p-3 dark:bg-zinc-900">
          <p className="text-zinc-500 dark:text-zinc-400">Regex Found</p>
          <p className="text-lg font-semibold">{regexFound}</p>
        </div>
        <div className="rounded-lg bg-zinc-50 p-3 dark:bg-zinc-900">
          <p className="text-zinc-500 dark:text-zinc-400">Hunter Found</p>
          <p className="text-lg font-semibold">{hunterFound}</p>
        </div>
        <div className="rounded-lg bg-zinc-50 p-3 dark:bg-zinc-900">
          <p className="text-zinc-500 dark:text-zinc-400">Verified Leads</p>
          <p className="text-lg font-semibold">{leadsVerified}</p>
        </div>
        <div className="rounded-lg bg-zinc-50 p-3 dark:bg-zinc-900">
          <p className="text-zinc-500 dark:text-zinc-400">Validation Fails Today</p>
          <p className="text-lg font-semibold">{validationFailsToday}</p>
        </div>
      </div>
      <p className="mt-3 text-xs text-zinc-500 dark:text-zinc-400">
        Hunter calls today: {hunterCallsToday}
      </p>
    </section>
  );
}

