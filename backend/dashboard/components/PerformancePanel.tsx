interface PerformanceData {
  replyRate: number;
  positiveReplyRate: number;
  funnel: Array<{ label: string; count: number }>;
  topCompanyTypes: Array<{ type: string; replyRate: number }>;
}

export function PerformancePanel({ data }: { data?: PerformanceData }) {
  if (!data) {
    return (
      <section className="rounded-xl border border-zinc-200 bg-white p-6 dark:border-zinc-800 dark:bg-zinc-950 md:col-span-2">
        <h2 className="text-lg font-semibold text-zinc-900 dark:text-zinc-100">
          📊 Performance
        </h2>
        <p className="mt-2 text-sm text-zinc-500">Loading...</p>
      </section>
    );
  }

  const maxCount = Math.max(...data.funnel.map((stage) => stage.count), 1);

  return (
    <section className="rounded-xl border border-zinc-200 bg-white p-6 dark:border-zinc-800 dark:bg-zinc-950 md:col-span-2">
      <h2 className="text-lg font-semibold text-zinc-900 dark:text-zinc-100">
        📊 Performance
      </h2>
      
      <div className="mt-6 grid gap-6 md:grid-cols-2">
        {/* Reply Rates */}
        <div>
          <h3 className="text-sm font-medium text-zinc-700 dark:text-zinc-300">
            Reply Metrics
          </h3>
          <div className="mt-4 space-y-4">
            <div className="rounded-lg bg-green-50 p-4 dark:bg-green-950/20">
              <p className="text-3xl font-bold text-green-700 dark:text-green-400">
                {data.replyRate.toFixed(1)}%
              </p>
              <p className="text-sm text-green-600 dark:text-green-500">Overall Reply Rate</p>
            </div>
            <div className="rounded-lg bg-blue-50 p-4 dark:bg-blue-950/20">
              <p className="text-3xl font-bold text-blue-700 dark:text-blue-400">
                {data.positiveReplyRate.toFixed(1)}%
              </p>
              <p className="text-sm text-blue-600 dark:text-blue-500">Positive Reply Rate</p>
            </div>
          </div>

          {/* Top Company Types */}
          <div className="mt-6">
            <h3 className="text-sm font-medium text-zinc-700 dark:text-zinc-300">
              Top Company Types
            </h3>
            <div className="mt-3 space-y-2">
              {data.topCompanyTypes.map((company, idx) => (
                <div
                  key={idx}
                  className="flex items-center justify-between rounded-lg bg-zinc-50 p-2 dark:bg-zinc-900"
                >
                  <span className="text-sm text-zinc-700 dark:text-zinc-300">
                    {company.type}
                  </span>
                  <span className="text-sm font-medium text-zinc-900 dark:text-zinc-100">
                    {company.replyRate.toFixed(1)}%
                  </span>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Pipeline Funnel */}
        <div>
          <h3 className="text-sm font-medium text-zinc-700 dark:text-zinc-300">
            Pipeline Funnel
          </h3>
          <div className="mt-4 space-y-3">
            {data.funnel.map((stage, idx) => {
              const widthPercent = (stage.count / maxCount) * 100;
              const dropoffPercent =
                idx > 0
                  ? ((data.funnel[idx - 1].count - stage.count) /
                      data.funnel[idx - 1].count) *
                    100
                  : 0;

              return (
                <div key={idx}>
                  <div className="flex items-center justify-between text-xs">
                    <span className="text-zinc-600 dark:text-zinc-400">
                      {stage.label}
                    </span>
                    <div className="flex items-center gap-2">
                      <span className="font-medium text-zinc-900 dark:text-zinc-100">
                        {stage.count}
                      </span>
                      {idx > 0 && dropoffPercent > 0 && (
                        <span className="text-red-600 dark:text-red-400">
                          -{dropoffPercent.toFixed(0)}%
                        </span>
                      )}
                    </div>
                  </div>
                  <div className="mt-1 h-6 w-full overflow-hidden rounded-lg bg-zinc-200 dark:bg-zinc-800">
                    <div
                      className="h-full bg-gradient-to-r from-blue-500 to-purple-500 transition-all"
                      style={{ width: `${widthPercent}%` }}
                    />
                  </div>
                </div>
              );
            })}
          </div>

          {/* Conversion Rate */}
          <div className="mt-6 rounded-lg bg-purple-50 p-4 dark:bg-purple-950/20">
            <p className="text-sm text-purple-900 dark:text-purple-100">
              Overall Conversion
            </p>
            <p className="mt-1 text-2xl font-bold text-purple-700 dark:text-purple-400">
              {data.funnel.length > 0 && data.funnel[0].count > 0
                ? (
                    (data.funnel[data.funnel.length - 1].count /
                      data.funnel[0].count) *
                    100
                  ).toFixed(2)
                : "0.00"}
              %
            </p>
            <p className="mt-1 text-xs text-purple-600 dark:text-purple-500">
              Discovered → Replied
            </p>
          </div>
        </div>
      </div>
    </section>
  );
}

