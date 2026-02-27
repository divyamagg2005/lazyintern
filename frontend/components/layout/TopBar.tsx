interface TopBarProps {
  lastUpdatedLabel?: string;
}

export function TopBar({ lastUpdatedLabel }: TopBarProps) {
  return (
    <header className="flex items-center justify-between gap-4 mb-6">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight flex items-center gap-2">
          Pipeline Health
          <span className="inline-flex items-center gap-1 rounded-full border border-emerald-500/40 bg-emerald-500/10 px-2 py-0.5 text-xs text-emerald-300">
            <span className="h-1.5 w-1.5 rounded-full bg-emerald-400 animate-pulse" />
            Live
          </span>
        </h1>
        <p className="text-sm text-slate-400">
          Monitor discovery, email quality, outreach, and feedback loops from a single view.
        </p>
      </div>

      <div className="flex items-center gap-3 text-xs text-slate-400">
        {lastUpdatedLabel && (
          <span className="px-2 py-1 rounded-full bg-slate-900/60 border border-slate-700/70">
            Last updated: {lastUpdatedLabel}
          </span>
        )}
      </div>
    </header>
  );
}

