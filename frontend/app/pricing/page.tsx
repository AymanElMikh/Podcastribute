"use client";

import { useState } from "react";
import Link from "next/link";
import { billing, ApiError } from "@/lib/api";
import { isLoggedIn } from "@/lib/auth";

const PLANS = [
  {
    key: "starter" as const,
    name: "Starter",
    price: "$49",
    description: "For podcasters just getting started",
    limit: "4 episodes / month",
    features: [
      "All 8 content formats",
      "Voice fingerprint",
      "Copy to clipboard",
      "Email support",
    ],
  },
  {
    key: "creator" as const,
    name: "Creator",
    price: "$149",
    description: "For consistent publishers",
    limit: "15 episodes / month",
    highlight: true,
    features: [
      "Everything in Starter",
      "Direct publish to Twitter & LinkedIn",
      "Newsletter integration (Beehiiv)",
      "Priority support",
    ],
  },
  {
    key: "studio" as const,
    name: "Studio",
    price: "$399",
    description: "For agencies and power users",
    limit: "Unlimited episodes",
    features: [
      "Everything in Creator",
      "Unlimited episodes",
      "Multiple podcast profiles",
      "Dedicated onboarding",
    ],
  },
];

export default function PricingPage() {
  const [loading, setLoading] = useState<string | null>(null);

  const handleCheckout = async (plan: "starter" | "creator" | "studio") => {
    if (!isLoggedIn()) {
      window.location.href = "/onboarding";
      return;
    }
    setLoading(plan);
    try {
      const { url } = await billing.checkout(plan);
      window.location.href = url;
    } catch (err) {
      alert(err instanceof ApiError ? err.message : "Could not start checkout");
    } finally {
      setLoading(null);
    }
  };

  return (
    <div className="mx-auto max-w-5xl px-4 py-16">
      <div className="mb-12 text-center">
        <h1 className="mb-3 text-4xl font-bold text-gray-900">
          Simple, honest pricing
        </h1>
        <p className="text-xl text-gray-500">
          Start with 1 free episode. No credit card required.
        </p>
      </div>

      <div className="grid grid-cols-1 gap-6 md:grid-cols-3">
        {PLANS.map((plan) => (
          <div
            key={plan.key}
            className={`relative rounded-2xl border p-6 ${
              plan.highlight
                ? "border-blue-500 bg-blue-600 text-white shadow-lg"
                : "border-gray-200 bg-white"
            }`}
          >
            {plan.highlight && (
              <div className="absolute -top-3 left-1/2 -translate-x-1/2 rounded-full bg-orange-400 px-3 py-0.5 text-xs font-bold text-white">
                Most popular
              </div>
            )}

            <div className="mb-4">
              <h2
                className={`text-lg font-bold ${plan.highlight ? "text-white" : "text-gray-900"}`}
              >
                {plan.name}
              </h2>
              <p
                className={`text-sm ${plan.highlight ? "text-blue-100" : "text-gray-500"}`}
              >
                {plan.description}
              </p>
            </div>

            <div className="mb-4">
              <span
                className={`text-4xl font-bold ${plan.highlight ? "text-white" : "text-gray-900"}`}
              >
                {plan.price}
              </span>
              <span
                className={`text-sm ${plan.highlight ? "text-blue-100" : "text-gray-500"}`}
              >
                /month
              </span>
            </div>

            <p
              className={`mb-4 text-sm font-medium ${plan.highlight ? "text-blue-100" : "text-blue-600"}`}
            >
              {plan.limit}
            </p>

            <ul className="mb-6 space-y-2">
              {plan.features.map((f) => (
                <li
                  key={f}
                  className={`flex items-start gap-2 text-sm ${plan.highlight ? "text-blue-50" : "text-gray-600"}`}
                >
                  <span className="mt-0.5 shrink-0">✓</span>
                  {f}
                </li>
              ))}
            </ul>

            <button
              onClick={() => handleCheckout(plan.key)}
              disabled={loading === plan.key}
              className={`w-full rounded-xl py-2.5 text-sm font-semibold transition disabled:opacity-60 ${
                plan.highlight
                  ? "bg-white text-blue-600 hover:bg-blue-50"
                  : "bg-blue-600 text-white hover:bg-blue-700"
              }`}
            >
              {loading === plan.key ? "Loading…" : `Start ${plan.name}`}
            </button>
          </div>
        ))}
      </div>

      <div className="mt-10 text-center">
        <p className="text-sm text-gray-400">
          Already have an account?{" "}
          <Link href="/dashboard" className="text-blue-600 hover:underline">
            Sign in →
          </Link>
        </p>
      </div>
    </div>
  );
}
