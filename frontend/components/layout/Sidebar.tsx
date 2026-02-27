import type { ReactNode } from "react";

interface SidebarProps {
  children?: ReactNode;
}

export function Sidebar({ children }: SidebarProps) {
  return (
    <aside className="glass-panel w-64 shrink-0 p-4 flex flex-col gap-6">
      <div>
        <div className="flex items-center gap-2">
          <div className="h-8 w-8 rounded-xl bg-accent/20 border border-accent/70 flex items-center justify-center">
            <span className="text-accent text-lg font-semibold">L</span>
          </div>
          <div>
            <p className="font-semibold tracking-tight">LazyIntern</p>
            <p className="text-xs text-slate-400">Outreach Control Center</p>
          </div>
        </div>
      </div>

      <nav className="flex-1">
        <ul className="space-y-1 text-sm">
          {[
            "Overview",
            "Discovery",
            "Email Quality",
            "Outreach",
            "Performance",
            "Retries"
          ].map((item, idx) => (
            <li key={item}>
              <a
                href={`#${item.toLowerCase().replace(/\s+/g, "-")}`}
                className={
                  "flex items-center gap-2 px-3 py-2 rounded-xl text-slate-300 hover:text-white hover:bg-accentSoft/60 transition-colors" +
                  (idx === 0 ? " bg-accentSoft/80 text-white" : "")
                }
              >
                <span className="h-1.5 w-1.5 rounded-full bg-slate-500" />
                <span>{item}</span>
              </a>
            </li>
          ))}
        </ul>
      </nav>

      <div className="mt-auto text-xs text-slate-500">
        <p>Scheduler: 3x/day · 15 emails max</p>
        <p>All metrics pulled from Supabase backend.</p>
      </div>
      {children}
    </aside>
  );
}

