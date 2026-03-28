"use client";

import { ContentPack } from "@/lib/api";

export type FormatKey =
  | "twitter"
  | "linkedin"
  | "newsletter"
  | "short_video"
  | "blog_post"
  | "youtube"
  | "quote_cards"
  | "email_sequence";

const FORMAT_LABELS: Record<FormatKey, string> = {
  twitter: "Twitter / X",
  linkedin: "LinkedIn",
  newsletter: "Newsletter",
  short_video: "Short Video",
  blog_post: "Blog Post",
  youtube: "YouTube",
  quote_cards: "Quote Cards",
  email_sequence: "Email Sequence",
};

const FORMAT_ICONS: Record<FormatKey, string> = {
  twitter: "𝕏",
  linkedin: "in",
  newsletter: "✉",
  short_video: "▶",
  blog_post: "📝",
  youtube: "▷",
  quote_cards: "❝",
  email_sequence: "📧",
};

interface Props {
  pack: ContentPack;
  active: FormatKey;
  onSelect: (format: FormatKey) => void;
  approvedFormats: Set<FormatKey>;
  onApproveAll: () => void;
}

export default function FormatNav({
  pack,
  active,
  onSelect,
  approvedFormats,
  onApproveAll,
}: Props) {
  const formats = Object.keys(FORMAT_LABELS) as FormatKey[];

  return (
    <nav className="flex flex-col gap-1">
      {formats.map((fmt) => {
        const content = pack[fmt] as Record<string, unknown> | undefined;
        const hasError = content?.error;
        const isApproved = approvedFormats.has(fmt);

        return (
          <button
            key={fmt}
            onClick={() => onSelect(fmt)}
            className={`flex w-full items-center gap-3 rounded-lg px-3 py-2.5 text-left text-sm transition-colors ${
              active === fmt
                ? "bg-blue-50 font-medium text-blue-700"
                : "text-gray-600 hover:bg-gray-50"
            }`}
          >
            <span className="w-6 shrink-0 text-center font-mono text-xs">
              {FORMAT_ICONS[fmt]}
            </span>
            <span className="flex-1">{FORMAT_LABELS[fmt]}</span>
            {hasError ? (
              <span className="rounded-full bg-red-100 px-2 py-0.5 text-xs text-red-600">
                error
              </span>
            ) : isApproved ? (
              <span className="rounded-full bg-green-100 px-2 py-0.5 text-xs text-green-600">
                ✓
              </span>
            ) : (
              <span className="rounded-full bg-gray-100 px-2 py-0.5 text-xs text-gray-500">
                ready
              </span>
            )}
          </button>
        );
      })}

      <div className="mt-4 border-t border-gray-100 pt-4">
        <button
          onClick={onApproveAll}
          className="w-full rounded-lg bg-green-600 px-3 py-2 text-sm font-medium text-white transition-colors hover:bg-green-700"
        >
          Approve all formats
        </button>
      </div>
    </nav>
  );
}

export { FORMAT_LABELS };
