import type { ReactNode } from "react";

interface MetricCardProps {
  label: string;
  value: ReactNode;
  hint?: string;
  accent?: "blue" | "emerald" | "amber" | "rose";
}

const accentClasses: Record<NonNullable<MetricCardProps["accent"]>, string> = {
  blue: "from-sky-500/10 to-sky-500/0 border-sky-500/30",
  emerald: "from-emerald-500/10 to-emerald-500/0 border-emerald-500/30",
  amber: "from-amber-400/10 to-amber-400/0 border-amber-400/30",
  rose: "from-rose-500/10 to-rose-500/0 border-rose-500/30"
};

export function MetricCard({ label, value, hint, accent = "blue" }: MetricCardProps) {
  return (
    <div className="relative overflow-hidden glass-panel px-4 py-3">
      <div
        className={`pointer-events-none absolute inset-0 bg-gradient-to-br ${accentClasses[accent]}`}
      />
      <div className="relative flex flex-col gap-1">
        <p className="text-xs uppercase tracking-wide text-slate-400">{label}</p>
        <div className="text-lg font-semibold text-slate-50">{value}</div>
        {hint && <p className="text-[11px] text-slate-500">{hint}</p>}
      </div>
    </div>
  );
}

