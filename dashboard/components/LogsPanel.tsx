type LogItem = {
  id: string;
  event: string;
  created_at: string;
  internship_id: string | null;
  metadata: unknown;
};

type Props = {
  logs: LogItem[];
};

function formatTs(iso: string): string {
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) {
    return iso;
  }
  return d.toLocaleString();
}

export function LogsPanel({ logs }: Props) {
  return (
    <section className="rounded-xl border border-zinc-200 bg-white p-4 dark:border-zinc-800 dark:bg-zinc-950">
      <div className="flex items-center justify-between">
        <h2 className="text-sm font-semibold text-zinc-900 dark:text-zinc-100">Pipeline Logs</h2>
        <span className="text-xs text-zinc-500 dark:text-zinc-400">Latest {logs.length}</span>
      </div>
      <div className="mt-3 max-h-[420px] overflow-auto rounded-lg border border-zinc-200 dark:border-zinc-800">
        <table className="w-full border-collapse text-left text-xs">
          <thead className="sticky top-0 bg-zinc-100 dark:bg-zinc-900">
            <tr>
              <th className="px-3 py-2">Time</th>
              <th className="px-3 py-2">Event</th>
              <th className="px-3 py-2">Internship</th>
              <th className="px-3 py-2">Metadata</th>
            </tr>
          </thead>
          <tbody>
            {logs.length === 0 ? (
              <tr>
                <td className="px-3 py-3 text-zinc-500 dark:text-zinc-400" colSpan={4}>
                  No logs yet.
                </td>
              </tr>
            ) : (
              logs.map((log) => (
                <tr key={log.id} className="border-t border-zinc-200 dark:border-zinc-800">
                  <td className="px-3 py-2 whitespace-nowrap">{formatTs(log.created_at)}</td>
                  <td className="px-3 py-2 font-medium">{log.event}</td>
                  <td className="px-3 py-2 font-mono text-[11px]">
                    {log.internship_id ? log.internship_id.slice(0, 8) : "-"}
                  </td>
                  <td className="px-3 py-2">
                    <code className="line-clamp-2 block text-[11px] text-zinc-600 dark:text-zinc-300">
                      {JSON.stringify(log.metadata)}
                    </code>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </section>
  );
}

