"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { auth, voice, ApiError } from "@/lib/api";
import { setToken } from "@/lib/auth";

type Step = "auth" | "voice" | "done";
type VoiceMethod = "posts" | "skip";

export default function OnboardingPage() {
  const router = useRouter();
  const [step, setStep] = useState<Step>("auth");
  const [isLogin, setIsLogin] = useState(false);

  // Auth state
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [authError, setAuthError] = useState<string | null>(null);
  const [authLoading, setAuthLoading] = useState(false);

  // Voice state
  const [voiceMethod, setVoiceMethod] = useState<VoiceMethod>("posts");
  const [posts, setPosts] = useState("");
  const [voiceLoading, setVoiceLoading] = useState(false);
  const [voiceError, setVoiceError] = useState<string | null>(null);

  const handleAuth = async () => {
    setAuthError(null);
    setAuthLoading(true);
    try {
      const res = isLogin
        ? await auth.login(email, password)
        : await auth.register(email, password);
      setToken(res.access_token);
      setStep("voice");
    } catch (err) {
      setAuthError(
        err instanceof ApiError ? err.message : "Authentication failed"
      );
    } finally {
      setAuthLoading(false);
    }
  };

  const handleVoice = async () => {
    setVoiceError(null);
    setVoiceLoading(true);
    try {
      if (voiceMethod === "posts") {
        const postList = posts
          .split("\n\n")
          .map((p) => p.trim())
          .filter(Boolean);
        if (postList.length < 2) {
          setVoiceError("Please paste at least 2 social posts (separated by blank lines)");
          setVoiceLoading(false);
          return;
        }
        await voice.calibrateFromPosts(postList);
      }
      setStep("done");
      setTimeout(() => router.push("/upload"), 1200);
    } catch (err) {
      setVoiceError(
        err instanceof ApiError ? err.message : "Voice calibration failed"
      );
    } finally {
      setVoiceLoading(false);
    }
  };

  return (
    <div className="flex min-h-screen flex-col items-center justify-center px-4 py-12">
      {/* Step indicator */}
      <div className="mb-8 flex items-center gap-2">
        {(["auth", "voice", "done"] as Step[]).map((s, i) => (
          <div key={s} className="flex items-center gap-2">
            <div
              className={`flex h-8 w-8 items-center justify-center rounded-full text-sm font-medium transition-all ${
                step === s
                  ? "bg-blue-600 text-white"
                  : ["auth", "voice", "done"].indexOf(step) > i
                  ? "bg-green-500 text-white"
                  : "bg-gray-200 text-gray-500"
              }`}
            >
              {["auth", "voice", "done"].indexOf(step) > i ? "✓" : i + 1}
            </div>
            {i < 2 && <div className="h-px w-8 bg-gray-200" />}
          </div>
        ))}
      </div>

      <div className="w-full max-w-md rounded-xl border border-gray-200 bg-white p-8 shadow-sm">
        {/* Step 1: Auth */}
        {step === "auth" && (
          <>
            <h1 className="mb-1 text-2xl font-bold text-gray-900">
              {isLogin ? "Sign in" : "Create your account"}
            </h1>
            <p className="mb-6 text-sm text-gray-500">
              {isLogin
                ? "Welcome back."
                : "Start with 1 free episode — no credit card needed."}
            </p>

            <div className="space-y-3">
              <input
                type="email"
                placeholder="you@example.com"
                className="w-full rounded-lg border border-gray-200 px-3 py-2.5 text-sm outline-none focus:border-blue-400"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && handleAuth()}
              />
              <input
                type="password"
                placeholder="Password"
                className="w-full rounded-lg border border-gray-200 px-3 py-2.5 text-sm outline-none focus:border-blue-400"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && handleAuth()}
              />
            </div>

            {authError && (
              <p className="mt-3 text-sm text-red-500">{authError}</p>
            )}

            <button
              onClick={handleAuth}
              disabled={authLoading}
              className="mt-4 w-full rounded-lg bg-blue-600 py-2.5 text-sm font-semibold text-white transition hover:bg-blue-700 disabled:opacity-60"
            >
              {authLoading
                ? "Please wait…"
                : isLogin
                ? "Sign in"
                : "Create account"}
            </button>

            <p className="mt-4 text-center text-sm text-gray-400">
              {isLogin ? "New here?" : "Already have an account?"}{" "}
              <button
                onClick={() => setIsLogin(!isLogin)}
                className="text-blue-600 hover:underline"
              >
                {isLogin ? "Create account" : "Sign in"}
              </button>
            </p>
          </>
        )}

        {/* Step 2: Voice calibration */}
        {step === "voice" && (
          <>
            <h1 className="mb-1 text-2xl font-bold text-gray-900">
              Set up your voice
            </h1>
            <p className="mb-6 text-sm text-gray-500">
              Paste examples of how you write so your content sounds like you —
              not generic AI.
            </p>

            <div className="mb-4 flex gap-2">
              <button
                onClick={() => setVoiceMethod("posts")}
                className={`flex-1 rounded-lg border py-2 text-sm font-medium transition ${
                  voiceMethod === "posts"
                    ? "border-blue-300 bg-blue-50 text-blue-700"
                    : "border-gray-200 text-gray-500 hover:bg-gray-50"
                }`}
              >
                Paste social posts
              </button>
              <button
                onClick={() => setVoiceMethod("skip")}
                className={`flex-1 rounded-lg border py-2 text-sm font-medium transition ${
                  voiceMethod === "skip"
                    ? "border-blue-300 bg-blue-50 text-blue-700"
                    : "border-gray-200 text-gray-500 hover:bg-gray-50"
                }`}
              >
                Skip for now
              </button>
            </div>

            {voiceMethod === "posts" && (
              <div>
                <label className="mb-1 block text-xs font-medium text-gray-500">
                  Paste 3-5 tweets or posts (one per paragraph, blank line between)
                </label>
                <textarea
                  className="w-full rounded-lg border border-gray-200 p-3 text-sm outline-none focus:border-blue-400"
                  rows={8}
                  placeholder={"Your best tweet here...\n\nAnother great post...\n\nA third example..."}
                  value={posts}
                  onChange={(e) => setPosts(e.target.value)}
                />
              </div>
            )}

            {voiceMethod === "skip" && (
              <p className="rounded-lg bg-gray-50 px-4 py-3 text-sm text-gray-500">
                We'll use a balanced default voice. You can calibrate later in
                Settings.
              </p>
            )}

            {voiceError && (
              <p className="mt-3 text-sm text-red-500">{voiceError}</p>
            )}

            <button
              onClick={handleVoice}
              disabled={voiceLoading}
              className="mt-4 w-full rounded-lg bg-blue-600 py-2.5 text-sm font-semibold text-white transition hover:bg-blue-700 disabled:opacity-60"
            >
              {voiceLoading
                ? "Analyzing…"
                : voiceMethod === "skip"
                ? "Continue with default voice"
                : "Analyze my voice"}
            </button>
          </>
        )}

        {/* Step 3: Done */}
        {step === "done" && (
          <div className="text-center">
            <div className="mx-auto mb-4 flex h-14 w-14 items-center justify-center rounded-full bg-green-100 text-2xl">
              ✓
            </div>
            <h1 className="mb-2 text-2xl font-bold text-gray-900">
              You're all set!
            </h1>
            <p className="text-sm text-gray-500">
              Redirecting to upload your first episode…
            </p>
          </div>
        )}
      </div>
    </div>
  );
}
