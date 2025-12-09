// frontendrag/pages/Analytics.tsx

import React, { useEffect, useState } from "react";
import { apiClient } from "../services/api";

interface OverviewMetrics {
  total_queries?: number;
  unique_documents?: number;
  avg_latency_ms?: number;
  total_tokens?: number;
}

interface RecentQuery {
  id?: string;
  query: string;
  answer_preview?: string;
  created_at?: string;
  latency_ms?: number;
  mode?: string;
}

interface UserAnalytics {
  recent_queries?: RecentQuery[];
  [key: string]: any;
}

// 🔹 Named export so `import { Analytics }` keeps working
export const Analytics: React.FC = () => {
  const [overview, setOverview] = useState<OverviewMetrics | null>(null);
  const [userStats, setUserStats] = useState<UserAnalytics | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const load = async () => {
      try {
        setLoading(true);
        setError(null);

        const [overviewRes, userRes] = await Promise.all([
          apiClient.get("/analytics/overview"),
          apiClient.get("/analytics/user"),
        ]);

        // axios usually returns { data: ... } – but handle both shapes safely
        setOverview((overviewRes as any).data ?? overviewRes);
        setUserStats((userRes as any).data ?? userRes);
      } catch (err: any) {
        console.error("Failed to load analytics:", err);
        setError(err?.message || "Failed to load analytics");
      } finally {
        setLoading(false);
      }
    };

    load();
  }, []);

  const recentQueries: RecentQuery[] =
    userStats?.recent_queries && Array.isArray(userStats.recent_queries)
      ? userStats.recent_queries
      : [];

  if (loading) {
    return (
      <div className="p-6 text-gray-700 dark:text-gray-100">
        Loading analytics…
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-6 text-red-600 dark:text-red-400">
        Analytics error: {error}
      </div>
    );
  }

  return (
    <div className="p-6 space-y-6 text-gray-900 dark:text-gray-100">
      <div>
        <h1 className="text-2xl font-semibold mb-1">Analytics</h1>
        <p className="text-sm text-gray-500 dark:text-gray-400">
          High-level stats about your RAG queries and document usage.
        </p>
      </div>

      {/* Overview cards */}
      <div className="grid gap-4 grid-cols-1 sm:grid-cols-2 lg:grid-cols-4">
        <div className="rounded-lg border border-gray-200 dark:border-gray-700 p-4 bg-white dark:bg-gray-900">
          <div className="text-xs uppercase text-gray-500 mb-1">
            Total Queries
          </div>
          <div className="text-2xl font-bold">
            {overview?.total_queries ?? 0}
          </div>
        </div>

        <div className="rounded-lg border border-gray-200 dark:border-gray-700 p-4 bg-white dark:bg-gray-900">
          <div className="text-xs uppercase text-gray-500 mb-1">
            Unique Documents
          </div>
          <div className="text-2xl font-bold">
            {overview?.unique_documents ?? 0}
          </div>
        </div>

        <div className="rounded-lg border border-gray-200 dark:border-gray-700 p-4 bg-white dark:bg-gray-900">
          <div className="text-xs uppercase text-gray-500 mb-1">
            Avg Latency (ms)
          </div>
          <div className="text-2xl font-bold">
            {overview?.avg_latency_ms
              ? overview.avg_latency_ms.toFixed(0)
              : "—"}
          </div>
        </div>

        <div className="rounded-lg border border-gray-200 dark:border-gray-700 p-4 bg-white dark:bg-gray-900">
          <div className="text-xs uppercase text-gray-500 mb-1">
            Tokens Used
          </div>
          <div className="text-2xl font-bold">
            {overview?.total_tokens ?? 0}
          </div>
        </div>
      </div>

      {/* Recent queries table */}
      <div className="rounded-lg border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900">
        <div className="px-4 py-3 border-b border-gray-200 dark:border-gray-700 flex items-center justify-between">
          <h2 className="font-semibold">Recent Queries</h2>
          <span className="text-xs text-gray-500">
            {recentQueries.length}{" "}
            {recentQueries.length === 1 ? "query" : "queries"}
          </span>
        </div>

        {recentQueries.length === 0 ? (
          <div className="p-4 text-sm text-gray-500">
            No analytics yet. Ask a question in the Chat tab and come back
            here.
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-full text-sm">
              <thead className="bg-gray-50 dark:bg-gray-800">
                <tr>
                  <th className="px-4 py-2 text-left font-medium text-gray-500">
                    Query
                  </th>
                  <th className="px-4 py-2 text-left font-medium text-gray-500">
                    Mode
                  </th>
                  <th className="px-4 py-2 text-left font-medium text-gray-500">
                    Latency (ms)
                  </th>
                  <th className="px-4 py-2 text-left font-medium text-gray-500">
                    Time
                  </th>
                </tr>
              </thead>
              <tbody>
                {recentQueries.map((q, idx) => (
                  <tr
                    key={q.id ?? idx}
                    className="border-t border-gray-100 dark:border-gray-800"
                  >
                    <td className="px-4 py-2 max-w-xs truncate">
                      {q.query || "(no query text)"}
                    </td>
                    <td className="px-4 py-2 text-gray-500">
                      {q.mode ?? "default"}
                    </td>
                    <td className="px-4 py-2 text-gray-500">
                      {q.latency_ms ? q.latency_ms.toFixed(0) : "—"}
                    </td>
                    <td className="px-4 py-2 text-gray-500">
                      {q.created_at
                        ? new Date(q.created_at).toLocaleString()
                        : "—"}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
};

// Optional default export – harmless, can keep it
export default Analytics;
