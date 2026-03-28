"use client";

import { useEffect, useState, use } from "react";
import { content, episodes, ContentPack, Episode } from "@/lib/api";
import ProcessingProgress from "@/components/ProcessingProgress";
import FormatNav, { FormatKey, FORMAT_LABELS } from "@/components/FormatNav";
import ContentEditor from "@/components/ContentEditor";
import PublishQueue from "@/components/PublishQueue";

const IN_PROGRESS_STATUSES = new Set([
  "queued",
  "transcribing",
  "detecting",
  "generating",
]);

interface Props {
  params: Promise<{ id: string }>;
}

export default function ContentPage({ params }: Props) {
  const { id } = use(params);
  const [episode, setEpisode] = useState<Episode | null>(null);
  const [pack, setPack] = useState<ContentPack | null>(null);
  const [activeFormat, setActiveFormat] = useState<FormatKey>("twitter");
  const [edits, setEdits] = useState<Partial<ContentPack>>({});
  const [approvedFormats, setApprovedFormats] = useState<Set<FormatKey>>(new Set());
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    episodes.get(id).then((ep) => {
      setEpisode(ep);
      setLoading(false);

      if (ep.status === "ready") {
        content.get(id).then(setPack).catch(() => null);
      }
    }).catch(() => setLoading(false));
  }, [id]);

  const handleEdit = (format: FormatKey, value: unknown) => {
    setEdits((prev) => {
      if (value === null) {
        const next = { ...prev };
        delete next[format];
        return next;
      }
      return { ...prev, [format]: value as ContentPack[typeof format] };
    });
  };

  const handleApproveAll = () => {
    if (!pack) return;
    const formats = Object.keys(pack) as FormatKey[];
    setApprovedFormats(new Set(formats));
  };

  if (loading) {
    return (
      <div className="flex min-h-[60vh] items-center justify-center text-gray-400">
        Loading…
      </div>
    );
  }

  if (!episode) {
    return (
      <div className="flex min-h-[60vh] items-center justify-center text-gray-400">
        Episode not found.
      </div>
    );
  }

  // Show processing view
  if (IN_PROGRESS_STATUSES.has(episode.status)) {
    return (
      <div className="mx-auto max-w-xl px-4 py-12">
        <h1 className="mb-6 text-xl font-semibold text-gray-900">
          {episode.title}
        </h1>
        <ProcessingProgress episodeId={id} />
      </div>
    );
  }

  if (episode.status === "error") {
    return (
      <div className="mx-auto max-w-xl px-4 py-12">
        <div className="rounded-lg border border-red-200 bg-red-50 p-6">
          <p className="font-medium text-red-700">Processing failed</p>
          {episode.error_message && (
            <p className="mt-1 text-sm text-red-600">{episode.error_message}</p>
          )}
        </div>
      </div>
    );
  }

  if (!pack) {
    return (
      <div className="flex min-h-[60vh] items-center justify-center text-gray-400">
        Loading content…
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-6xl px-4 py-6">
      {/* Top bar */}
      <div className="mb-6 flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold text-gray-900">{episode.title}</h1>
          <p className="text-sm text-gray-400">
            {approvedFormats.size} of {Object.keys(pack).length} formats approved
          </p>
        </div>
      </div>

      <div className="grid grid-cols-[220px_1fr_240px] gap-6">
        {/* Left: format nav */}
        <aside className="rounded-lg border border-gray-200 bg-white p-3">
          <FormatNav
            pack={pack}
            active={activeFormat}
            onSelect={setActiveFormat}
            approvedFormats={approvedFormats}
            onApproveAll={handleApproveAll}
          />
        </aside>

        {/* Center: editor */}
        <section className="rounded-lg border border-gray-200 bg-white p-6">
          <div className="mb-4 flex items-center justify-between">
            <h2 className="font-semibold text-gray-900">
              {FORMAT_LABELS[activeFormat]}
            </h2>
            {!approvedFormats.has(activeFormat) ? (
              <button
                onClick={() =>
                  setApprovedFormats((prev) => new Set([...prev, activeFormat]))
                }
                className="rounded-lg border border-green-200 px-3 py-1 text-xs font-medium text-green-700 hover:bg-green-50"
              >
                Mark as approved
              </button>
            ) : (
              <span className="text-xs font-medium text-green-600">✓ Approved</span>
            )}
          </div>
          <ContentEditor
            format={activeFormat}
            pack={pack}
            edits={edits}
            onEdit={handleEdit}
          />
        </section>

        {/* Right: episode info + publish */}
        <aside className="space-y-4">
          <div className="rounded-lg border border-gray-200 bg-white p-4">
            <h3 className="mb-2 text-sm font-semibold text-gray-700">Episode</h3>
            <p className="text-sm text-gray-600">{episode.title}</p>
            <p className="mt-1 text-xs capitalize text-gray-400">
              {episode.source_type}
            </p>
          </div>

          <PublishQueue
            episodeId={id}
            format={activeFormat}
            pack={pack}
            edits={edits}
          />
        </aside>
      </div>
    </div>
  );
}
