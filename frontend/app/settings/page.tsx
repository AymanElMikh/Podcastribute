"use client";

import { useEffect, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { voice, billing, VoiceProfile, UsageInfo, ApiError } from "@/lib/api";
import { isLoggedIn } from "@/lib/auth";
import { Suspense } from "react";

function SettingsContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const upgraded = searchParams.get("upgraded");

  const [profile, setProfile] = useState<VoiceProfile | null>(null);
  const [usage, setUsage] = useState<UsageInfo | null>(null);
  const [loading, setLoading] = useState(true);

  // Voice refinement
  const [feedback, setFeedback] = useState("");
  const [refineLoading, setRefineLoading] = useState(false);
  const [refineSuccess, setRefineSuccess] = useState(false);

  // Billing
  const [billingLoading, setBillingLoading] = useState(false);

  useEffect(() => {
    if (!isLoggedIn()) {
      router.replace("/");
      return;
    }

    Promise.all([
      voice.get().catch(() => null),
      billing.usage().catch(() => null),
    ]).then(([v, u]) => {
      setProfile(v);
      setUsage(u);
      setLoading(false);
    });
  }, [router]);

  const handleRefine = async () => {
    if (!feedback.trim()) return;
    setRefineLoading(true);
    try {
      const updated = await voice.refine(feedback.trim());
      setProfile(updated);
      setFeedback("");
      setRefineSuccess(true);
      setTimeout(() => setRefineSuccess(false), 2000);
    } catch {
      // ignore
    } finally {
      setRefineLoading(false);
    }
  };

  const handlePortal = async () => {
    setBillingLoading(true);
    try {
      const { url } = await billing.portal();
      window.location.href = url;
    } catch (err) {
      alert(err instanceof ApiError ? err.message : "Could not open billing portal");
    } finally {
      setBillingLoading(false);
    }
  };

  const handleUpgrade = async (plan: "starter" | "creator" | "studio") => {
    setBillingLoading(true);
    try {
      const { url } = await billing.checkout(plan);
      window.location.href = url;
    } catch (err) {
      alert(err instanceof ApiError ? err.message : "Could not start checkout");
    } finally {
      setBillingLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex min-h-[60vh] items-center justify-center text-gray-400">
        Loading…
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-2xl px-4 py-8">
      <h1 className="mb-6 text-2xl font-bold text-gray-900">Settings</h1>

      {upgraded && (
        <div className="mb-6 rounded-lg bg-green-50 px-4 py-3 text-sm font-medium text-green-700">
          🎉 Plan upgraded successfully!
        </div>
      )}

      {/* Voice profile */}
      <section className="mb-6 rounded-xl border border-gray-200 bg-white p-6">
        <h2 className="mb-4 text-base font-semibold text-gray-900">
          Voice profile
        </h2>

        {profile ? (
          <div className="mb-4 space-y-2 text-sm text-gray-600">
            <div>
              <span className="font-medium">Tone:</span>{" "}
              {profile.tone_adjectives?.join(", ") || "—"}
            </div>
            <div>
              <span className="font-medium">Style:</span>{" "}
              {profile.sentence_style || "—"}
            </div>
            <div>
              <span className="font-medium">Humor:</span>{" "}
              {profile.humor_level || "—"}
            </div>
            <div>
              <span className="font-medium">Words to avoid:</span>{" "}
              {profile.words_to_avoid?.join(", ") || "none"}
            </div>
          </div>
        ) : (
          <p className="mb-4 text-sm text-gray-400">
            No voice profile yet.{" "}
            <a href="/onboarding" className="text-blue-600 hover:underline">
              Set one up →
            </a>
          </p>
        )}

        <div>
          <label className="mb-1 block text-sm font-medium text-gray-700">
            Refine your voice
          </label>
          <textarea
            className="w-full rounded-lg border border-gray-200 p-3 text-sm outline-none focus:border-blue-400"
            rows={3}
            placeholder='e.g. "I never use buzzwords like synergy" or "make it more casual"'
            value={feedback}
            onChange={(e) => setFeedback(e.target.value)}
          />
          <button
            onClick={handleRefine}
            disabled={refineLoading || !feedback.trim()}
            className="mt-2 rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white transition hover:bg-blue-700 disabled:opacity-50"
          >
            {refineLoading ? "Updating…" : refineSuccess ? "✓ Updated!" : "Update voice"}
          </button>
        </div>
      </section>

      {/* Plan & billing */}
      <section className="rounded-xl border border-gray-200 bg-white p-6">
        <h2 className="mb-4 text-base font-semibold text-gray-900">Plan & billing</h2>

        {usage && (
          <div className="mb-4 rounded-lg bg-gray-50 p-4 text-sm">
            <div className="flex items-center justify-between">
              <span className="font-medium capitalize text-gray-800">
                {usage.plan} plan
              </span>
              <span className="text-gray-500">
                {usage.episodes_this_month} / {usage.limit ?? "∞"} episodes used
              </span>
            </div>
          </div>
        )}

        <div className="flex gap-3">
          {usage?.plan !== "studio" && (
            <button
              onClick={() => {
                const next =
                  usage?.plan === "free"
                    ? "starter"
                    : usage?.plan === "starter"
                    ? "creator"
                    : "studio";
                handleUpgrade(next as "starter" | "creator" | "studio");
              }}
              disabled={billingLoading}
              className="rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white transition hover:bg-blue-700 disabled:opacity-50"
            >
              Upgrade plan
            </button>
          )}
          {usage?.plan !== "free" && (
            <button
              onClick={handlePortal}
              disabled={billingLoading}
              className="rounded-lg border border-gray-200 px-4 py-2 text-sm font-medium text-gray-600 transition hover:bg-gray-50 disabled:opacity-50"
            >
              Manage subscription
            </button>
          )}
        </div>
      </section>
    </div>
  );
}

export default function SettingsPage() {
  return (
    <Suspense fallback={<div className="flex min-h-[60vh] items-center justify-center text-gray-400">Loading…</div>}>
      <SettingsContent />
    </Suspense>
  );
}
