"use client";

import Link from "next/link";
import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { isLoggedIn } from "@/lib/auth";

export default function Home() {
  const router = useRouter();

  useEffect(() => {
    if (isLoggedIn()) {
      router.replace("/dashboard");
    }
  }, [router]);

  return (
    <div className="flex min-h-screen flex-col items-center justify-center px-4">
      <div className="max-w-2xl text-center">
        <h1 className="mb-4 text-5xl font-bold tracking-tight text-gray-900">
          Turn every episode into{" "}
          <span className="text-blue-600">8 pieces of content</span>
        </h1>
        <p className="mb-8 text-xl text-gray-500">
          Upload your podcast. Get Twitter threads, LinkedIn posts, newsletters,
          blog posts, YouTube descriptions, quote cards, and more — all in your
          voice.
        </p>
        <div className="flex items-center justify-center gap-4">
          <Link
            href="/onboarding"
            className="rounded-xl bg-blue-600 px-6 py-3 text-base font-semibold text-white shadow-sm transition hover:bg-blue-700"
          >
            Start for free
          </Link>
          <Link
            href="/pricing"
            className="rounded-xl border border-gray-200 bg-white px-6 py-3 text-base font-semibold text-gray-700 transition hover:bg-gray-50"
          >
            See pricing
          </Link>
        </div>
        <p className="mt-6 text-sm text-gray-400">
          Already have an account?{" "}
          <Link href="/login" className="text-blue-600 hover:underline">
            Sign in
          </Link>
        </p>
        <p className="mt-4 text-sm text-gray-400">
          1 free episode, no credit card required
        </p>
      </div>
    </div>
  );
}
