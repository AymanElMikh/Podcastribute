"use client";

import { useEffect, useState, useRef } from "react";
import { useRouter } from "next/navigation";
import { API_BASE } from "@/lib/api";
import { getToken } from "@/lib/auth";

interface ProgressEvent {
  type: string;
  label: string;
  data: Record<string, unknown>;
  timestamp: string;
}

interface Step {
  type: string;
  label: string;
  done: boolean;
}

const STEPS: { type: string; label: string }[] = [
  { type: "upload_received", label: "Episode received" },
  { type: "transcription_start", label: "Transcribing audio" },
  { type: "transcription_done", label: "Transcription complete" },
  { type: "moments_detected", label: "Detecting key moments" },
  { type: "generating_content", label: "Generating content" },
  { type: "content_ready", label: "Content ready!" },
];

interface Props {
  episodeId: string;
}

export default function ProcessingProgress({ episodeId }: Props) {
  const router = useRouter();
  const [steps, setSteps] = useState<Step[]>(
    STEPS.map((s) => ({ ...s, done: false }))
  );
  const [currentLabel, setCurrentLabel] = useState("Starting...");
  const [error, setError] = useState<string | null>(null);
  const esRef = useRef<EventSource | null>(null);

  useEffect(() => {
    const token = getToken();
    if (!token) return;

    // EventSource doesn't support custom headers; pass token as query param
    const url = `${API_BASE}/v1/stream/${episodeId}?token=${token}`;
    const es = new EventSource(url);
    esRef.current = es;

    es.onmessage = (e) => {
      try {
        const event: ProgressEvent = JSON.parse(e.data);
        setCurrentLabel(event.label);

        setSteps((prev) =>
          prev.map((s) =>
            s.type === event.type ? { ...s, done: true } : s
          )
        );

        if (event.type === "content_ready") {
          es.close();
          setTimeout(() => {
            router.push(`/content/${episodeId}`);
          }, 800);
        }

        if (event.type === "error") {
          const msg =
            (event.data?.message as string) ?? "Processing failed";
          setError(msg);
          es.close();
        }
      } catch {
        // ignore malformed events
      }
    };

    es.onerror = () => {
      setError("Connection lost. Processing may still be running.");
      es.close();
    };

    return () => {
      es.close();
    };
  }, [episodeId, router]);

  if (error) {
    return (
      <div className="rounded-lg border border-red-200 bg-red-50 p-6">
        <p className="font-medium text-red-700">Processing failed</p>
        <p className="mt-1 text-sm text-red-600">{error}</p>
      </div>
    );
  }

  return (
    <div className="rounded-lg border border-gray-200 bg-white p-8 shadow-sm">
      <h2 className="mb-6 text-lg font-semibold text-gray-900">
        Processing your episode…
      </h2>

      <div className="mb-6 space-y-3">
        {steps.map((step, i) => (
          <div key={step.type} className="flex items-center gap-3">
            {/* Step indicator */}
            <div
              className={`flex h-7 w-7 shrink-0 items-center justify-center rounded-full text-sm font-medium transition-all ${
                step.done
                  ? "bg-green-500 text-white"
                  : "bg-gray-100 text-gray-400"
              }`}
            >
              {step.done ? (
                <svg className="h-4 w-4" viewBox="0 0 20 20" fill="currentColor">
                  <path
                    fillRule="evenodd"
                    d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z"
                    clipRule="evenodd"
                  />
                </svg>
              ) : (
                <span>{i + 1}</span>
              )}
            </div>
            <span
              className={`text-sm ${
                step.done ? "font-medium text-gray-900" : "text-gray-400"
              }`}
            >
              {step.label}
            </span>
          </div>
        ))}
      </div>

      {/* Current status */}
      <div className="flex items-center gap-2 text-sm text-gray-500">
        <div className="h-2 w-2 animate-pulse rounded-full bg-blue-500" />
        {currentLabel}
      </div>
    </div>
  );
}
