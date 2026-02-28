interface DiscoveryData {
  internshipsToday: number;
  internshipsThisWeek: number;
  tier1SuccessRate: number;
  tier2SuccessRate: number;
  tier3SuccessRate: number;
  preScoreKillRate: number;
  firecrawlUsed: number;
  firecrawlLimit: number;
}

export function DiscoveryPanel({ data }: { data?: DiscoveryData }) {
  if (!data) {
    return (
      <section className="rounded-xl border border-zinc-200 bg-white p-6 dark:border-zinc-800 dark:bg-zinc-950">
        <h2 className="text-lg font-semibold text-zinc-900 dark:text-zinc-100">
          🔍 Discovery
        </h2>
        <p className="mt-2 text-sm text-zinc-500">Loading...</p>
      </section>
    );
  }

  return (
    <section className="rounded-xl border border-zinc-200 bg-white p-6 dark:border-zinc-800 dark:bg-zinc-950">
      <h2 className="text-lg font-semibold text-zinc-900 dark:text-zinc-100">
        🔍 Discovery
      </h2>
      
      {/* Main Stats */}
      <div className="mt-4 grid grid-cols-2 gap-4">
        <div>
          <p className="text-2xl font-bold text-zinc-900 dark:text-zinc-100">
            {data.internshipsToday}
          </p>
          <p className="text-xs text-zinc-600 dark:text-zinc-400">Internships Today</p>
        </div>
        <div>
          <p className="text-2xl font-bold text-zinc-900 dark:text-zinc-100">
            {data.internshipsThisWeek}
          </p>
          <p className="text-xs text-zinc-600 dark:text-zinc-400">This Week</p>
        </div>
      </div>

      {/* Scrape Tier Success Rates */}
      <div className="mt-6">
        <p className="text-sm font-medium text-zinc-700 dark:text-zinc-300">
          Scrape Tier Success
        </p>
        <div className="mt-2 space-y-2">
          <div className="flex items-center justify-between">
            <span className="text-xs text-zinc-600 dark:text-zinc-400">Tier 1 (HTTP)</span>
            <span className="text-sm font-medium text-green-600 dark:text-green-400">
              {data.tier1SuccessRate}%
            </span>
          </div>
          <div className="flex items-center justify-between">
            <span className="text-xs text-zinc-600 dark:text-zinc-400">Tier 2 (Dynamic)</span>
            <span className="text-sm font-medium text-yellow-600 dark:text-yellow-400">
              {data.tier2SuccessRate}%
            </span>
          </div>
          <div className="flex items-center justify-between">
            <span className="text-xs text-zinc-600 dark:text-zinc-400">Tier 3 (Firecrawl)</span>
            <span className="text-sm font-medium text-orange-600 dark:text-orange-400">
              {data.tier3SuccessRate}%
            </span>
          </div>
        </div>
      </div>

      {/* Kill Rate & Firecrawl */}
      <div className="mt-6 grid grid-cols-2 gap-4">
        <div className="rounded-lg bg-red-50 p-3 dark:bg-red-950/20">
          <p className="text-lg font-bold text-red-700 dark:text-red-400">
            {data.preScoreKillRate.toFixed(1)}%
          </p>
          <p className="text-xs text-red-600 dark:text-red-500">Pre-score Kill Rate</p>
        </div>
        <div className="rounded-lg bg-blue-50 p-3 dark:bg-blue-950/20">
          <p className="text-lg font-bold text-blue-700 dark:text-blue-400">
            {data.firecrawlUsed}/{data.firecrawlLimit}
          </p>
          <p className="text-xs text-blue-600 dark:text-blue-500">Firecrawl Used</p>
        </div>
      </div>
    </section>
  );
}

