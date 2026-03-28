"use client";

import { useState } from "react";
import { publish, ContentPack } from "@/lib/api";
import { FormatKey } from "./FormatNav";

const PLATFORM_CONFIG: Partial<
  Record<FormatKey, { label: string; icon: string; color: string }>
> = {
  twitter: { label: "Twitter / X", icon: "𝕏", color: "bg-black" },
  linkedin: { label: "LinkedIn", icon: "in", color: "bg-blue-700" },
  newsletter: { label: "Newsletter", icon: "✉", color: "bg-purple-600" },
  youtube: { label: "YouTube", icon: "▷", color: "bg-red-600" },
};

interface Props {
  episodeId: string;
  format: FormatKey;
  pack: ContentPack;
  edits: Partial<ContentPack>;
}

type PublishStatus = "idle" | "publishing" | "success" | "error";

export default function PublishQueue({ episodeId, format, pack, edits }: Props) {
  const [status, setStatus] = useState<PublishStatus>("idle");
  const [message, setMessage] = useState("");

  const platform = PLATFORM_CONFIG[format];

  const effectiveContent = {
    ...pack,
    ...(edits[format] ? { [format]: edits[format] } : {}),
  };

  const handleCopy = async () => {
    const raw = effectiveContent[format] as Record<string, unknown> | undefined;
    if (!raw) return;

    let text = "";
    if (format === "twitter") {
      const t = raw as { main_thread?: string[] };
      text = (t.main_thread ?? []).join("\n\n---\n\n");
    } else if (format === "blog_post") {
      const b = raw as { body?: string };
      text = b.body ?? "";
    } else {
      text = JSON.stringify(raw, null, 2);
    }

    await navigator.clipboard.writeText(text);
    setMessage("Copied!");
    setStatus("success");
    setTimeout(() => {
      setStatus("idle");
      setMessage("");
    }, 2000);
  };

  const handlePublish = async () => {
    setStatus("publishing");
    setMessage("");
    try {
      await publish.send(episodeId, [format], effectiveContent as Record<string, unknown>);
      setStatus("success");
      setMessage(`Published to ${platform?.label ?? format}!`);
    } catch (err) {
      setStatus("error");
      setMessage(err instanceof Error ? err.message : "Publish failed");
    }
  };

  return (
    <div className="rounded-lg border border-gray-200 bg-white p-4">
      <h3 className="mb-3 text-sm font-semibold text-gray-700">Publish</h3>

      <div className="space-y-2">
        {/* Copy to clipboard — always available */}
        <button
          onClick={handleCopy}
          className="flex w-full items-center gap-2 rounded-lg border border-gray-200 px-3 py-2 text-sm text-gray-600 transition hover:bg-gray-50"
        >
          <span>📋</span>
          <span>Copy to clipboard</span>
        </button>

        {/* Direct publish (only for supported platforms) */}
        {platform && (
          <button
            onClick={handlePublish}
            disabled={status === "publishing"}
            className={`flex w-full items-center gap-2 rounded-lg px-3 py-2 text-sm text-white transition ${platform.color} disabled:opacity-60 hover:opacity-90`}
          >
            <span>{platform.icon}</span>
            <span>
              {status === "publishing" ? "Publishing…" : `Publish to ${platform.label}`}
            </span>
          </button>
        )}
      </div>

      {/* Feedback */}
      {message && (
        <p
          className={`mt-2 text-xs ${
            status === "error" ? "text-red-500" : "text-green-600"
          }`}
        >
          {message}
        </p>
      )}
    </div>
  );
}
