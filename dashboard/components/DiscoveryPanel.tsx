type Props = {
  internshipsToday: number;
  internshipsWeek: number;
  scrapeFailuresToday: number;
  preScoreKillsToday: number;
  firecrawlUsedToday: number;
};

export function DiscoveryPanel({
  internshipsToday,
  internshipsWeek,
  scrapeFailuresToday,
  preScoreKillsToday,
  firecrawlUsedToday,
}: Props) {
  return (
    <section className="rounded-xl border border-zinc-200 bg-white p-4 dark:border-zinc-800 dark:bg-zinc-950">
      <h2 className="text-sm font-semibold text-zinc-900 dark:text-zinc-100">Discovery</h2>
      <div className="mt-3 grid grid-cols-2 gap-3 text-sm">
        <div className="rounded-lg bg-zinc-50 p-3 dark:bg-zinc-900">
          <p className="text-zinc-500 dark:text-zinc-400">Found Today</p>
          <p className="text-lg font-semibold">{internshipsToday}</p>
        </div>
        <div className="rounded-lg bg-zinc-50 p-3 dark:bg-zinc-900">
          <p className="text-zinc-500 dark:text-zinc-400">Found (Loaded Window)</p>
          <p className="text-lg font-semibold">{internshipsWeek}</p>
        </div>
        <div className="rounded-lg bg-zinc-50 p-3 dark:bg-zinc-900">
          <p className="text-zinc-500 dark:text-zinc-400">Scrape Fails Today</p>
          <p className="text-lg font-semibold">{scrapeFailuresToday}</p>
        </div>
        <div className="rounded-lg bg-zinc-50 p-3 dark:bg-zinc-900">
          <p className="text-zinc-500 dark:text-zinc-400">Pre-score Kills Today</p>
          <p className="text-lg font-semibold">{preScoreKillsToday}</p>
        </div>
      </div>
      <p className="mt-3 text-xs text-zinc-500 dark:text-zinc-400">
        Firecrawl calls used today: {firecrawlUsedToday}
      </p>
    </section>
  );
}

