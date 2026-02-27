type Props = {
  repliedPositive: number;
  repliedNegative: number;
  repliedNeutral: number;
};

export function PerformancePanel({
  repliedPositive,
  repliedNegative,
  repliedNeutral,
}: Props) {
  const total = repliedPositive + repliedNegative + repliedNeutral;
  const positiveRate = total ? Math.round((repliedPositive / total) * 100) : 0;

  return (
    <section className="rounded-xl border border-zinc-200 bg-white p-4 dark:border-zinc-800 dark:bg-zinc-950">
      <h2 className="text-sm font-semibold text-zinc-900 dark:text-zinc-100">Performance</h2>
      <div className="mt-3 grid grid-cols-3 gap-3 text-sm">
        <div className="rounded-lg bg-zinc-50 p-3 dark:bg-zinc-900">
          <p className="text-zinc-500 dark:text-zinc-400">Positive</p>
          <p className="text-lg font-semibold">{repliedPositive}</p>
        </div>
        <div className="rounded-lg bg-zinc-50 p-3 dark:bg-zinc-900">
          <p className="text-zinc-500 dark:text-zinc-400">Neutral</p>
          <p className="text-lg font-semibold">{repliedNeutral}</p>
        </div>
        <div className="rounded-lg bg-zinc-50 p-3 dark:bg-zinc-900">
          <p className="text-zinc-500 dark:text-zinc-400">Negative</p>
          <p className="text-lg font-semibold">{repliedNegative}</p>
        </div>
      </div>
      <p className="mt-3 text-xs text-zinc-500 dark:text-zinc-400">
        Positive reply rate: {positiveRate}% ({total} classified replies)
      </p>
    </section>
  );
}

