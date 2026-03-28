"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { episodes, billing, Episode, UsageInfo } from "@/lib/api";
import { isLoggedIn } from "@/lib/auth";

const STATUS_COLORS: Record<string, string> = {
  queued: "bg-gray-100 text-gray-600",
  transcribing: "bg-blue-100 text-blue-700",
  detecting: "bg-purple-100 text-purple-700",
  generating: "bg-yellow-100 text-yellow-700",
  ready: "bg-green-100 text-green-700",
  error: "bg-red-100 text-red-700",
};

function formatDuration(seconds: number | null): string {
  if (!seconds) return "—";
  const m = Math.floor(seconds / 60);
  const s = seconds % 60;
  return `${m}:${s.toString().padStart(2, "0")}`;
}

export default function DashboardPage() {
  const router = useRouter();
  const [episodeList, setEpisodeList] = useState<Episode[]>([]);
  const [usage, setUsage] = useState<UsageInfo | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!isLoggedIn()) {
      router.replace("/");
      return;
    }

    Promise.all([
      episodes.list().catch(() => ({ items: [], total: 0 })),
      billing.usage().catch(() => null),
    ]).then(([eps, usageData]) => {
      setEpisodeList(eps.items);
      setUsage(usageData);
      setLoading(false);
    });
  }, [router]);

  if (loading) {
    return (
      <div className="flex min-h-[60vh] items-center justify-center text-gray-400">
        Loading…
      </div>
    );
  }

  const usagePercent =
    usage && usage.limit
      ? Math.min((usage.episodes_this_month / usage.limit) * 100, 100)
      : 0;

  return (
    <div className="mx-auto max-w-5xl px-4 py-8">
      {/* Header */}
      <div className="mb-8 flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-900">Your episodes</h1>
        <Link
          href="/upload"
          className="rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white transition hover:bg-blue-700"
        >
          + New episode
        </Link>
      </div>

      {/* Usage meter */}
      {usage && (
        <div className="mb-6 rounded-lg border border-gray-200 bg-white p-4">
          <div className="mb-2 flex items-center justify-between">
            <span className="text-sm text-gray-600">
              {usage.episodes_this_month} /{" "}
              {usage.limit ?? "∞"} episodes this month
            </span>
            <span className="capitalize text-sm font-medium text-gray-700">
              {usage.plan} plan
            </span>
          </div>
          {usage.limit && (
            <div className="h-2 w-full overflow-hidden rounded-full bg-gray-100">
              <div
                className={`h-2 rounded-full transition-all ${
                  usagePercent >= 100 ? "bg-red-500" : "bg-blue-500"
                }`}
                style={{ width: `${usagePercent}%` }}
              />
            </div>
          )}
          {usage.plan === "free" || usage.plan === "starter" ? (
            <div className="mt-2 text-right">
              <Link
                href="/pricing"
                className="text-xs text-blue-600 hover:underline"
              >
                Upgrade for more →
              </Link>
            </div>
          ) : null}
        </div>
      )}

      {/* Episode list */}
      {episodeList.length === 0 ? (
        <div className="rounded-lg border-2 border-dashed border-gray-200 py-16 text-center">
          <p className="text-gray-400">No episodes yet.</p>
          <Link
            href="/upload"
            className="mt-3 inline-block text-sm font-medium text-blue-600 hover:underline"
          >
            Upload your first episode →
          </Link>
        </div>
      ) : (
        <div className="space-y-3">
          {episodeList.map((ep) => (
            <div
              key={ep.id}
              className="flex items-center gap-4 rounded-lg border border-gray-200 bg-white p-4"
            >
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2">
                  <span className="truncate font-medium text-gray-900">
                    {ep.title}
                  </span>
                  <span
                    className={`shrink-0 rounded-full px-2 py-0.5 text-xs font-medium capitalize ${
                      STATUS_COLORS[ep.status] ?? "bg-gray-100 text-gray-600"
                    }`}
                  >
                    {ep.status}
                  </span>
                </div>
                <div className="mt-1 flex items-center gap-3 text-xs text-gray-400">
                  <span className="capitalize">{ep.source_type}</span>
                  <span>{formatDuration(ep.duration_seconds)}</span>
                  <span>{new Date(ep.created_at).toLocaleDateString()}</span>
                </div>
              </div>

              <div className="flex shrink-0 items-center gap-2">
                {ep.status === "ready" && (
                  <Link
                    href={`/content/${ep.id}`}
                    className="rounded-lg bg-blue-50 px-3 py-1.5 text-sm font-medium text-blue-700 hover:bg-blue-100"
                  >
                    View content
                  </Link>
                )}
                {(ep.status === "queued" ||
                  ep.status === "transcribing" ||
                  ep.status === "detecting" ||
                  ep.status === "generating") && (
                  <Link
                    href={`/content/${ep.id}`}
                    className="rounded-lg bg-gray-50 px-3 py-1.5 text-sm text-gray-500 hover:bg-gray-100"
                  >
                    View progress
                  </Link>
                )}
                {ep.status === "error" && (
                  <span className="text-xs text-red-500">{ep.error_message}</span>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
