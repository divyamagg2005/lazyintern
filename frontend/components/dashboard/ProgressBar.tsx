interface ProgressBarProps {
  value: number;
  max: number;
  label?: string;
}

export function ProgressBar({ value, max, label }: ProgressBarProps) {
  const pct = max > 0 ? Math.min(100, Math.round((value / max) * 100)) : 0;

  return (
    <div className="space-y-1">
      {label && <p className="text-xs text-slate-400">{label}</p>}
      <div className="h-2 w-full rounded-full bg-slate-900/80 overflow-hidden">
        <div
          className="h-full rounded-full bg-gradient-to-r from-sky-400 via-emerald-400 to-emerald-500 transition-all"
          style={{ width: `${pct}%` }}
        />
      </div>
      <p className="text-[11px] text-slate-500">
        {value} / {max} ({pct}
        %)
      </p>
    </div>
  );
}

