type Props = {
  activeByPhase: Record<string, number>;
  maxRetryFailures: number;
};

export function RetryPanel({ activeByPhase, maxRetryFailures }: Props) {
  const phases = Object.entries(activeByPhase).sort((a, b) => b[1] - a[1]);

  return (
    <section className="rounded-xl border border-zinc-200 bg-white p-4 dark:border-zinc-800 dark:bg-zinc-950">
      <h2 className="text-sm font-semibold text-zinc-900 dark:text-zinc-100">Retry Queue</h2>
      <div className="mt-3 space-y-2 text-sm">
        {phases.length === 0 ? (
          <p className="text-zinc-500 dark:text-zinc-400">No active retries.</p>
        ) : (
          phases.map(([phase, count]) => (
            <div
              key={phase}
              className="flex items-center justify-between rounded bg-zinc-50 px-3 py-2 dark:bg-zinc-900"
            >
              <span className="capitalize">{phase}</span>
              <span className="font-semibold">{count}</span>
            </div>
          ))
        )}
      </div>
      <p className="mt-3 text-xs text-zinc-500 dark:text-zinc-400">
        Max-retry failures needing manual action: {maxRetryFailures}
      </p>
    </section>
  );
}

