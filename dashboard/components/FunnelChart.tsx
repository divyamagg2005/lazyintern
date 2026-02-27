type Props = {
  discovered: number;
  preScored: number;
  emailFound: number;
  emailValid: number;
  fullScored: number;
  draftGenerated: number;
  approved: number;
  sent: number;
  replied: number;
};

export function FunnelChart({
  discovered,
  preScored,
  emailFound,
  emailValid,
  fullScored,
  draftGenerated,
  approved,
  sent,
  replied,
}: Props) {
  const rows = [
    ["Discovered", discovered],
    ["Pre-scored", preScored],
    ["Email Found", emailFound],
    ["Email Valid", emailValid],
    ["Full Scored", fullScored],
    ["Draft Generated", draftGenerated],
    ["Approved", approved],
    ["Sent", sent],
    ["Replied", replied],
  ] as const;
  const max = Math.max(1, ...rows.map(([, count]) => count));

  return (
    <section className="rounded-xl border border-zinc-200 bg-white p-4 dark:border-zinc-800 dark:bg-zinc-950">
      <h2 className="text-sm font-semibold text-zinc-900 dark:text-zinc-100">Funnel</h2>
      <div className="mt-4 space-y-2">
        {rows.map(([label, count]) => (
          <div key={label} className="grid grid-cols-[120px_1fr_48px] items-center gap-3 text-sm">
            <span className="text-zinc-600 dark:text-zinc-300">{label}</span>
            <div className="h-2 rounded bg-zinc-200 dark:bg-zinc-800">
              <div
                className="h-2 rounded bg-zinc-900 dark:bg-zinc-200"
                style={{ width: `${Math.max(4, (count / max) * 100)}%` }}
              />
            </div>
            <span className="text-right font-medium">{count}</span>
          </div>
        ))}
      </div>
    </section>
  );
}

