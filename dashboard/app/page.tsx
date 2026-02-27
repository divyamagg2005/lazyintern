import { DiscoveryPanel } from "@/components/DiscoveryPanel";
import { EmailPanel } from "@/components/EmailPanel";
import { FunnelChart } from "@/components/FunnelChart";
import { LogsPanel } from "@/components/LogsPanel";
import { OutreachPanel } from "@/components/OutreachPanel";
import { PerformancePanel } from "@/components/PerformancePanel";
import { RetryPanel } from "@/components/RetryPanel";
import { getDashboardData } from "@/lib/dashboard-data";

export const revalidate = 10;

export default async function Home() {
  const data = await getDashboardData();

  return (
    <div className="min-h-screen bg-zinc-50 px-4 py-6 text-zinc-900 dark:bg-black dark:text-zinc-100">
      <main className="mx-auto flex w-full max-w-7xl flex-col gap-4">
        <header className="rounded-xl border border-zinc-200 bg-white p-4 dark:border-zinc-800 dark:bg-zinc-950">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div>
              <h1 className="text-xl font-semibold">LazyIntern Dashboard</h1>
              <p className="text-sm text-zinc-500 dark:text-zinc-400">
                Discovery → scoring → personalization → approval → send → replies
              </p>
            </div>
            <span
              className={`rounded-full px-3 py-1 text-xs font-medium ${
                data.connected
                  ? "bg-emerald-100 text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-300"
                  : "bg-rose-100 text-rose-700 dark:bg-rose-900/30 dark:text-rose-300"
              }`}
            >
              {data.connected ? "Supabase Connected" : "Supabase Not Connected"}
            </span>
          </div>
          {!data.connected && (
            <p className="mt-3 text-xs text-rose-600 dark:text-rose-300">
              {data.connectionError}
            </p>
          )}
        </header>

        <section className="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-3">
          <DiscoveryPanel {...data.discovery} />
          <EmailPanel {...data.email} />
          <OutreachPanel {...data.outreach} />
          <PerformancePanel {...data.performance} />
          <RetryPanel {...data.retry} />
          <FunnelChart {...data.funnel} />
        </section>

        <LogsPanel logs={data.logs} />

        <p className="text-center text-xs text-zinc-500 dark:text-zinc-400">
          Auto-refresh every 10 seconds
        </p>
      </main>
    </div>
  );
}
