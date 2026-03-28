"use client";

import { useState, useRef, DragEvent } from "react";
import { useRouter } from "next/navigation";
import { episodes, ApiError } from "@/lib/api";

type TabKey = "file" | "youtube" | "rss";

export default function UploadPage() {
  const router = useRouter();
  const [tab, setTab] = useState<TabKey>("file");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [dragOver, setDragOver] = useState(false);

  // File upload state
  const [file, setFile] = useState<File | null>(null);
  const [title, setTitle] = useState("");
  const fileRef = useRef<HTMLInputElement>(null);

  // YouTube state
  const [ytUrl, setYtUrl] = useState("");

  // RSS state
  const [rssUrl, setRssUrl] = useState("");

  const handleDrop = (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setDragOver(false);
    const dropped = e.dataTransfer.files[0];
    if (dropped) {
      setFile(dropped);
      if (!title) setTitle(dropped.name.replace(/\.[^/.]+$/, ""));
    }
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const selected = e.target.files?.[0];
    if (selected) {
      setFile(selected);
      if (!title) setTitle(selected.name.replace(/\.[^/.]+$/, ""));
    }
  };

  const handleSubmit = async () => {
    setError(null);
    setSubmitting(true);
    try {
      let result: { episode_id: string };

      if (tab === "file") {
        if (!file) throw new Error("Please select a file");
        if (!title.trim()) throw new Error("Please enter a title");
        result = await episodes.upload(file, title.trim());
      } else if (tab === "youtube") {
        if (!ytUrl.trim()) throw new Error("Please enter a YouTube URL");
        result = await episodes.fromYouTube(ytUrl.trim());
      } else {
        if (!rssUrl.trim()) throw new Error("Please enter an RSS feed URL");
        result = await episodes.fromRSS(rssUrl.trim());
      }

      router.push(`/content/${result.episode_id}`);
    } catch (err) {
      setError(
        err instanceof ApiError
          ? err.message
          : err instanceof Error
          ? err.message
          : "Something went wrong"
      );
    } finally {
      setSubmitting(false);
    }
  };

  const tabs: { key: TabKey; label: string }[] = [
    { key: "file", label: "Upload file" },
    { key: "youtube", label: "YouTube URL" },
    { key: "rss", label: "RSS feed" },
  ];

  return (
    <div className="mx-auto max-w-2xl px-4 py-10">
      <h1 className="mb-6 text-2xl font-bold text-gray-900">New episode</h1>

      {/* Tabs */}
      <div className="mb-6 flex gap-1 rounded-lg border border-gray-200 bg-gray-50 p-1">
        {tabs.map((t) => (
          <button
            key={t.key}
            onClick={() => setTab(t.key)}
            className={`flex-1 rounded-md py-2 text-sm font-medium transition ${
              tab === t.key
                ? "bg-white text-gray-900 shadow-sm"
                : "text-gray-500 hover:text-gray-700"
            }`}
          >
            {t.label}
          </button>
        ))}
      </div>

      <div className="rounded-xl border border-gray-200 bg-white p-6 shadow-sm">
        {/* File upload */}
        {tab === "file" && (
          <div className="space-y-4">
            <div
              onClick={() => fileRef.current?.click()}
              onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
              onDragLeave={() => setDragOver(false)}
              onDrop={handleDrop}
              className={`flex cursor-pointer flex-col items-center justify-center rounded-lg border-2 border-dashed px-6 py-10 transition ${
                dragOver
                  ? "border-blue-400 bg-blue-50"
                  : "border-gray-200 hover:border-gray-300 hover:bg-gray-50"
              }`}
            >
              <svg
                className="mb-3 h-10 w-10 text-gray-300"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={1.5}
                  d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12"
                />
              </svg>
              {file ? (
                <p className="text-sm font-medium text-gray-700">{file.name}</p>
              ) : (
                <>
                  <p className="text-sm font-medium text-gray-600">
                    Drop your audio file here
                  </p>
                  <p className="mt-1 text-xs text-gray-400">
                    MP3, WAV, M4A — up to 500 MB
                  </p>
                </>
              )}
            </div>
            <input
              ref={fileRef}
              type="file"
              accept="audio/mpeg,audio/wav,audio/mp4,audio/x-m4a"
              className="hidden"
              onChange={handleFileChange}
            />

            <div>
              <label className="mb-1 block text-sm font-medium text-gray-700">
                Episode title
              </label>
              <input
                className="w-full rounded-lg border border-gray-200 px-3 py-2 text-sm outline-none focus:border-blue-400"
                placeholder="My Podcast — Ep. 42"
                value={title}
                onChange={(e) => setTitle(e.target.value)}
              />
            </div>
          </div>
        )}

        {/* YouTube URL */}
        {tab === "youtube" && (
          <div className="space-y-4">
            <p className="text-sm text-gray-500">
              Paste a YouTube video URL and we'll download the audio automatically.
            </p>
            <div>
              <label className="mb-1 block text-sm font-medium text-gray-700">
                YouTube URL
              </label>
              <input
                className="w-full rounded-lg border border-gray-200 px-3 py-2 text-sm outline-none focus:border-blue-400"
                placeholder="https://youtube.com/watch?v=..."
                value={ytUrl}
                onChange={(e) => setYtUrl(e.target.value)}
              />
            </div>
          </div>
        )}

        {/* RSS feed */}
        {tab === "rss" && (
          <div className="space-y-4">
            <p className="text-sm text-gray-500">
              Enter your podcast RSS feed URL to fetch the latest episode.
            </p>
            <div>
              <label className="mb-1 block text-sm font-medium text-gray-700">
                RSS feed URL
              </label>
              <input
                className="w-full rounded-lg border border-gray-200 px-3 py-2 text-sm outline-none focus:border-blue-400"
                placeholder="https://feeds.example.com/mypodcast.rss"
                value={rssUrl}
                onChange={(e) => setRssUrl(e.target.value)}
              />
            </div>
          </div>
        )}

        {error && (
          <p className="mt-4 rounded-lg bg-red-50 px-3 py-2 text-sm text-red-600">
            {error}
          </p>
        )}

        <button
          onClick={handleSubmit}
          disabled={submitting}
          className="mt-6 w-full rounded-lg bg-blue-600 py-2.5 text-sm font-semibold text-white transition hover:bg-blue-700 disabled:opacity-60"
        >
          {submitting ? "Submitting…" : "Process episode"}
        </button>
      </div>
    </div>
  );
}
