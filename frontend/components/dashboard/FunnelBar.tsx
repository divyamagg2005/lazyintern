interface FunnelStage {
  label: string;
  count: number;
}

interface FunnelBarProps {
  stages: FunnelStage[];
}

export function FunnelBar({ stages }: FunnelBarProps) {
  const max = stages.reduce((acc, s) => Math.max(acc, s.count), 0) || 1;

  return (
    <div className="space-y-2">
      {stages.map((stage, idx) => {
        const pct = Math.max(6, Math.round((stage.count / max) * 100));
        const opacity = 1 - idx * 0.08;
        return (
          <div key={stage.label} className="space-y-1">
            <div className="flex justify-between text-[11px] text-slate-400">
              <span>{stage.label}</span>
              <span>{stage.count}</span>
            </div>
            <div className="h-2 rounded-full bg-slate-900/80 overflow-hidden">
              <div
                className="h-full rounded-full bg-gradient-to-r from-sky-400 via-sky-500 to-emerald-400"
                style={{ width: `${pct}%`, opacity }}
              />
            </div>
          </div>
        );
      })}
    </div>
  );
}

