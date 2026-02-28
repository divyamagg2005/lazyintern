"use client";

import { useEffect, useState } from "react";
import { DiscoveryPanel } from "@/components/DiscoveryPanel";
import { EmailPanel } from "@/components/EmailPanel";
import { OutreachPanel } from "@/components/OutreachPanel";
import { PerformancePanel } from "@/components/PerformancePanel";

interface DashboardData {
  lastUpdated: string;
  discovery: any;
  email: any;
  outreach: any;
  performance: any;
  retries: any;
  scoringConfig: any;
}

export default function Home() {
  const [data, setData] = useState<DashboardData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchData = async () => {
    try {
      const response = await fetch("http://localhost:8000/dashboard");
      if (!response.ok) throw new Error("Failed to fetch dashboard data");
      const json = await response.json();
      setData(json);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unknown error");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 30000); // Refresh every 30 seconds
    return () => clearInterval(interval);
  }, []);

  if (loading) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-zinc-50 dark:bg-zinc-900">
        <div className="text-center">
          <div className="h-8 w-8 animate-spin rounded-full border-4 border-zinc-300 border-t-zinc-900 dark:border-zinc-700 dark:border-t-zinc-100 mx-auto mb-4"></div>
          <p className="text-sm text-zinc-600 dark:text-zinc-400">Loading dashboard...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-zinc-50 dark:bg-zinc-900">
        <div className="max-w-md rounded-xl border border-red-200 bg-red-50 p-6 dark:border-red-900 dark:bg-red-950">
          <h2 className="text-lg font-semibold text-red-900 dark:text-red-100">Connection Error</h2>
          <p className="mt-2 text-sm text-red-700 dark:text-red-300">{error}</p>
          <p className="mt-4 text-xs text-red-600 dark:text-red-400">
            Make sure the backend API is running on http://localhost:8000
          </p>
          <button
            onClick={fetchData}
            className="mt-4 rounded-lg bg-red-600 px-4 py-2 text-sm font-medium text-white hover:bg-red-700"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-zinc-50 dark:bg-zinc-900">
      <div className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-zinc-900 dark:text-zinc-100">
            LazyIntern Dashboard
          </h1>
          <p className="mt-2 text-sm text-zinc-600 dark:text-zinc-400">
            Real-time pipeline monitoring • Last updated:{" "}
            {data?.lastUpdated ? new Date(data.lastUpdated).toLocaleTimeString() : "—"}
          </p>
        </div>

        {/* Panels Grid */}
        <div className="grid gap-6 md:grid-cols-2">
          <DiscoveryPanel data={data?.discovery} />
          <EmailPanel data={data?.email} />
          <OutreachPanel data={data?.outreach} />
          <PerformancePanel data={data?.performance} />
        </div>
      </div>
    </div>
  );
}
