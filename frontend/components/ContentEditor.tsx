"use client";

import { useState, useEffect } from "react";
import {
  ContentPack,
  TwitterContent,
  LinkedInContent,
  NewsletterContent,
  ShortVideoContent,
  BlogPostContent,
  YouTubeContent,
  QuoteCardsContent,
  EmailSequenceContent,
} from "@/lib/api";
import { FormatKey } from "./FormatNav";

interface Props {
  format: FormatKey;
  pack: ContentPack;
  edits: Partial<ContentPack>;
  onEdit: (format: FormatKey, value: unknown) => void;
}

function CharCount({
  text,
  max,
}: {
  text: string;
  max: number;
}) {
  const len = text.length;
  const over = len > max;
  return (
    <span className={`text-xs ${over ? "text-red-500 font-medium" : "text-gray-400"}`}>
      {len}/{max}
    </span>
  );
}

function WordCount({ text }: { text: string }) {
  const count = text.trim() ? text.trim().split(/\s+/).length : 0;
  return <span className="text-xs text-gray-400">{count} words</span>;
}

// ---------------------------------------------------------------------------
// Twitter
// ---------------------------------------------------------------------------

function TwitterEditor({ data, onEdit }: { data: TwitterContent; onEdit: (v: TwitterContent) => void }) {
  return (
    <div className="space-y-4">
      <div>
        <h3 className="mb-2 text-sm font-semibold text-gray-700">Thread ({data.main_thread.length} tweets)</h3>
        <div className="space-y-2">
          {data.main_thread.map((tweet, i) => (
            <div key={i} className="rounded-lg border border-gray-200 p-3">
              <textarea
                className="w-full resize-none text-sm text-gray-800 outline-none"
                rows={3}
                value={tweet}
                onChange={(e) => {
                  const updated = [...data.main_thread];
                  updated[i] = e.target.value;
                  onEdit({ ...data, main_thread: updated });
                }}
              />
              <div className="flex justify-end">
                <CharCount text={tweet} max={280} />
              </div>
            </div>
          ))}
        </div>
      </div>

      <div>
        <h3 className="mb-2 text-sm font-semibold text-gray-700">Standalone hooks</h3>
        <div className="space-y-2">
          {data.standalone_hooks.map((hook, i) => (
            <div key={i} className="rounded-lg border border-gray-200 p-3">
              <textarea
                className="w-full resize-none text-sm text-gray-800 outline-none"
                rows={2}
                value={hook}
                onChange={(e) => {
                  const updated = [...data.standalone_hooks];
                  updated[i] = e.target.value;
                  onEdit({ ...data, standalone_hooks: updated });
                }}
              />
              <div className="flex justify-end">
                <CharCount text={hook} max={280} />
              </div>
            </div>
          ))}
        </div>
      </div>

      <div>
        <h3 className="mb-2 text-sm font-semibold text-gray-700">Listen tweet</h3>
        <div className="rounded-lg border border-gray-200 p-3">
          <textarea
            className="w-full resize-none text-sm text-gray-800 outline-none"
            rows={2}
            value={data.listen_tweet}
            onChange={(e) => onEdit({ ...data, listen_tweet: e.target.value })}
          />
          <div className="flex justify-end">
            <CharCount text={data.listen_tweet} max={280} />
          </div>
        </div>
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// LinkedIn
// ---------------------------------------------------------------------------

function LinkedInEditor({ data, onEdit }: { data: LinkedInContent; onEdit: (v: LinkedInContent) => void }) {
  return (
    <div className="space-y-4">
      <div>
        <div className="mb-1 flex items-center justify-between">
          <h3 className="text-sm font-semibold text-gray-700">Post</h3>
          <WordCount text={data.post} />
        </div>
        <textarea
          className="w-full rounded-lg border border-gray-200 p-3 text-sm text-gray-800 outline-none focus:border-blue-400"
          rows={8}
          value={data.post}
          onChange={(e) => onEdit({ ...data, post: e.target.value })}
        />
      </div>

      <div>
        <h3 className="mb-2 text-sm font-semibold text-gray-700">Carousel outline (7 slides)</h3>
        <div className="space-y-2">
          {data.carousel_outline.map((slide, i) => (
            <div key={i} className="flex items-center gap-2">
              <span className="w-6 shrink-0 text-center text-xs text-gray-400">{i + 1}</span>
              <input
                className="flex-1 rounded-lg border border-gray-200 px-3 py-2 text-sm outline-none focus:border-blue-400"
                value={slide}
                onChange={(e) => {
                  const updated = [...data.carousel_outline];
                  updated[i] = e.target.value;
                  onEdit({ ...data, carousel_outline: updated });
                }}
              />
            </div>
          ))}
        </div>
      </div>

      <div>
        <h3 className="mb-2 text-sm font-semibold text-gray-700">Alternative hooks</h3>
        <div className="space-y-2">
          {data.post_hooks.map((hook, i) => (
            <input
              key={i}
              className="w-full rounded-lg border border-gray-200 px-3 py-2 text-sm outline-none focus:border-blue-400"
              value={hook}
              onChange={(e) => {
                const updated = [...data.post_hooks];
                updated[i] = e.target.value;
                onEdit({ ...data, post_hooks: updated });
              }}
            />
          ))}
        </div>
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Newsletter
// ---------------------------------------------------------------------------

function NewsletterEditor({ data, onEdit }: { data: NewsletterContent; onEdit: (v: NewsletterContent) => void }) {
  return (
    <div className="space-y-4">
      <div>
        <h3 className="mb-1 text-sm font-semibold text-gray-700">Section title</h3>
        <input
          className="w-full rounded-lg border border-gray-200 px-3 py-2 text-sm outline-none focus:border-blue-400"
          value={data.section_title}
          onChange={(e) => onEdit({ ...data, section_title: e.target.value })}
        />
      </div>

      <div>
        <div className="mb-1 flex items-center justify-between">
          <h3 className="text-sm font-semibold text-gray-700">Body</h3>
          <WordCount text={data.section_body} />
        </div>
        <textarea
          className="w-full rounded-lg border border-gray-200 p-3 text-sm text-gray-800 outline-none focus:border-blue-400"
          rows={10}
          value={data.section_body}
          onChange={(e) => onEdit({ ...data, section_body: e.target.value })}
        />
      </div>

      <div>
        <h3 className="mb-2 text-sm font-semibold text-gray-700">Subject lines</h3>
        <div className="space-y-2">
          {data.subject_lines.map((line, i) => (
            <input
              key={i}
              className="w-full rounded-lg border border-gray-200 px-3 py-2 text-sm outline-none focus:border-blue-400"
              value={line}
              onChange={(e) => {
                const updated = [...data.subject_lines];
                updated[i] = e.target.value;
                onEdit({ ...data, subject_lines: updated });
              }}
            />
          ))}
        </div>
      </div>

      <div>
        <h3 className="mb-1 text-sm font-semibold text-gray-700">Preview text</h3>
        <input
          className="w-full rounded-lg border border-gray-200 px-3 py-2 text-sm outline-none focus:border-blue-400"
          value={data.preview_text}
          onChange={(e) => onEdit({ ...data, preview_text: e.target.value })}
        />
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Short Video
// ---------------------------------------------------------------------------

function ShortVideoEditor({ data, onEdit }: { data: ShortVideoContent; onEdit: (v: ShortVideoContent) => void }) {
  return (
    <div className="space-y-4">
      {data.clips.map((clip, i) => (
        <div key={i} className="rounded-lg border border-gray-200 p-4">
          <div className="mb-3 flex items-center gap-2">
            <span className="rounded-full bg-blue-100 px-2 py-0.5 text-xs font-medium text-blue-700">
              {clip.platform}
            </span>
            <span className="text-xs text-gray-500">
              {clip.start_time} → {clip.end_time}
            </span>
          </div>

          <div className="space-y-2">
            <div>
              <label className="mb-1 block text-xs font-medium text-gray-500">Hook (first 3 seconds)</label>
              <input
                className="w-full rounded border border-gray-200 px-3 py-1.5 text-sm outline-none focus:border-blue-400"
                value={clip.hook}
                onChange={(e) => {
                  const updated = [...data.clips];
                  updated[i] = { ...clip, hook: e.target.value };
                  onEdit({ ...data, clips: updated });
                }}
              />
            </div>
            <div>
              <label className="mb-1 block text-xs font-medium text-gray-500">Screen note for editor</label>
              <input
                className="w-full rounded border border-gray-200 px-3 py-1.5 text-sm outline-none focus:border-blue-400"
                value={clip.script_note}
                onChange={(e) => {
                  const updated = [...data.clips];
                  updated[i] = { ...clip, script_note: e.target.value };
                  onEdit({ ...data, clips: updated });
                }}
              />
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Blog Post
// ---------------------------------------------------------------------------

function BlogPostEditor({ data, onEdit }: { data: BlogPostContent; onEdit: (v: BlogPostContent) => void }) {
  return (
    <div className="space-y-4">
      <div>
        <h3 className="mb-1 text-sm font-semibold text-gray-700">Title (H1)</h3>
        <input
          className="w-full rounded-lg border border-gray-200 px-3 py-2 text-sm font-semibold outline-none focus:border-blue-400"
          value={data.title}
          onChange={(e) => onEdit({ ...data, title: e.target.value })}
        />
      </div>

      <div>
        <div className="mb-1 flex items-center justify-between">
          <h3 className="text-sm font-semibold text-gray-700">Meta description</h3>
          <CharCount text={data.meta_description} max={155} />
        </div>
        <input
          className="w-full rounded-lg border border-gray-200 px-3 py-2 text-sm outline-none focus:border-blue-400"
          value={data.meta_description}
          onChange={(e) => onEdit({ ...data, meta_description: e.target.value })}
        />
      </div>

      <div>
        <div className="mb-1 flex items-center justify-between">
          <h3 className="text-sm font-semibold text-gray-700">Body (markdown)</h3>
          <WordCount text={data.body} />
        </div>
        <textarea
          className="w-full rounded-lg border border-gray-200 p-3 font-mono text-sm text-gray-800 outline-none focus:border-blue-400"
          rows={16}
          value={data.body}
          onChange={(e) => onEdit({ ...data, body: e.target.value })}
        />
      </div>

      <div>
        <h3 className="mb-2 text-sm font-semibold text-gray-700">Target keywords</h3>
        <div className="flex flex-wrap gap-2">
          {data.target_keywords.map((kw, i) => (
            <span key={i} className="rounded-full bg-gray-100 px-3 py-1 text-xs text-gray-600">
              {kw}
            </span>
          ))}
        </div>
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// YouTube Description
// ---------------------------------------------------------------------------

function YouTubeEditor({ data, onEdit }: { data: YouTubeContent; onEdit: (v: YouTubeContent) => void }) {
  return (
    <div className="space-y-4">
      <div>
        <div className="mb-1 flex items-center justify-between">
          <h3 className="text-sm font-semibold text-gray-700">Description</h3>
          <WordCount text={data.description} />
        </div>
        <textarea
          className="w-full rounded-lg border border-gray-200 p-3 text-sm text-gray-800 outline-none focus:border-blue-400"
          rows={8}
          value={data.description}
          onChange={(e) => onEdit({ ...data, description: e.target.value })}
        />
      </div>

      <div>
        <h3 className="mb-2 text-sm font-semibold text-gray-700">Chapters</h3>
        <div className="space-y-2">
          {data.chapters.map((ch, i) => (
            <div key={i} className="flex items-center gap-2">
              <input
                className="w-20 rounded border border-gray-200 px-2 py-1.5 text-sm font-mono outline-none"
                value={ch.time}
                onChange={(e) => {
                  const updated = [...data.chapters];
                  updated[i] = { ...ch, time: e.target.value };
                  onEdit({ ...data, chapters: updated });
                }}
              />
              <input
                className="flex-1 rounded border border-gray-200 px-2 py-1.5 text-sm outline-none"
                value={ch.title}
                onChange={(e) => {
                  const updated = [...data.chapters];
                  updated[i] = { ...ch, title: e.target.value };
                  onEdit({ ...data, chapters: updated });
                }}
              />
            </div>
          ))}
        </div>
      </div>

      <div>
        <h3 className="mb-2 text-sm font-semibold text-gray-700">Tags</h3>
        <div className="flex flex-wrap gap-2">
          {data.tags.map((tag, i) => (
            <span key={i} className="rounded-full bg-gray-100 px-3 py-1 text-xs text-gray-600">
              {tag}
            </span>
          ))}
        </div>
      </div>

      <div>
        <h3 className="mb-1 text-sm font-semibold text-gray-700">End screen script</h3>
        <textarea
          className="w-full rounded-lg border border-gray-200 p-3 text-sm text-gray-800 outline-none focus:border-blue-400"
          rows={4}
          value={data.end_screen_script}
          onChange={(e) => onEdit({ ...data, end_screen_script: e.target.value })}
        />
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Quote Cards
// ---------------------------------------------------------------------------

function QuoteCardsEditor({ data, onEdit }: { data: QuoteCardsContent; onEdit: (v: QuoteCardsContent) => void }) {
  return (
    <div className="space-y-4">
      {data.quotes.map((quote, i) => (
        <div key={i} className="rounded-lg border border-gray-200 p-4">
          <div className="space-y-3">
            <div>
              <div className="mb-1 flex items-center justify-between">
                <label className="text-xs font-medium text-gray-500">Quote text</label>
                <CharCount text={quote.text} max={140} />
              </div>
              <textarea
                className="w-full resize-none rounded border border-gray-200 p-2 text-sm outline-none focus:border-blue-400"
                rows={2}
                value={quote.text}
                onChange={(e) => {
                  const updated = [...data.quotes];
                  updated[i] = { ...quote, text: e.target.value };
                  onEdit({ ...data, quotes: updated });
                }}
              />
            </div>
            <div>
              <label className="mb-1 block text-xs font-medium text-gray-500">Attribution</label>
              <input
                className="w-full rounded border border-gray-200 px-2 py-1.5 text-sm outline-none"
                value={quote.attribution}
                onChange={(e) => {
                  const updated = [...data.quotes];
                  updated[i] = { ...quote, attribution: e.target.value };
                  onEdit({ ...data, quotes: updated });
                }}
              />
            </div>
            <div>
              <label className="mb-1 block text-xs font-medium text-gray-500">Caption</label>
              <input
                className="w-full rounded border border-gray-200 px-2 py-1.5 text-sm outline-none"
                value={quote.caption}
                onChange={(e) => {
                  const updated = [...data.quotes];
                  updated[i] = { ...quote, caption: e.target.value };
                  onEdit({ ...data, quotes: updated });
                }}
              />
            </div>
            <div className="text-xs text-gray-400">
              Design: {quote.background_suggestion}
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Email Sequence
// ---------------------------------------------------------------------------

const PURPOSE_LABELS: Record<string, string> = {
  announce: "Day 0 — Announcement",
  insight: "Day 2 — Best insight",
  cta: "Day 5 — Call to action",
};

function EmailSequenceEditor({ data, onEdit }: { data: EmailSequenceContent; onEdit: (v: EmailSequenceContent) => void }) {
  return (
    <div className="space-y-4">
      {data.emails.map((email, i) => (
        <div key={i} className="rounded-lg border border-gray-200 p-4">
          <div className="mb-3 text-xs font-semibold uppercase tracking-wide text-blue-600">
            {PURPOSE_LABELS[email.purpose] ?? `Email ${i + 1}`}
          </div>
          <div className="space-y-3">
            <div>
              <label className="mb-1 block text-xs font-medium text-gray-500">Subject</label>
              <input
                className="w-full rounded border border-gray-200 px-2 py-1.5 text-sm outline-none focus:border-blue-400"
                value={email.subject}
                onChange={(e) => {
                  const updated = [...data.emails];
                  updated[i] = { ...email, subject: e.target.value };
                  onEdit({ ...data, emails: updated });
                }}
              />
            </div>
            <div>
              <label className="mb-1 block text-xs font-medium text-gray-500">Preview text</label>
              <input
                className="w-full rounded border border-gray-200 px-2 py-1.5 text-sm outline-none focus:border-blue-400"
                value={email.preview_text}
                onChange={(e) => {
                  const updated = [...data.emails];
                  updated[i] = { ...email, preview_text: e.target.value };
                  onEdit({ ...data, emails: updated });
                }}
              />
            </div>
            <div>
              <div className="mb-1 flex items-center justify-between">
                <label className="text-xs font-medium text-gray-500">Body</label>
                <WordCount text={email.body} />
              </div>
              <textarea
                className="w-full rounded border border-gray-200 p-2 text-sm outline-none focus:border-blue-400"
                rows={6}
                value={email.body}
                onChange={(e) => {
                  const updated = [...data.emails];
                  updated[i] = { ...email, body: e.target.value };
                  onEdit({ ...data, emails: updated });
                }}
              />
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Main ContentEditor dispatcher
// ---------------------------------------------------------------------------

export default function ContentEditor({ format, pack, edits, onEdit }: Props) {
  const raw = pack[format] as Record<string, unknown> | undefined;

  if (!raw) {
    return (
      <div className="rounded-lg border border-gray-100 bg-gray-50 p-8 text-center text-sm text-gray-400">
        No content for this format yet.
      </div>
    );
  }

  if (raw.error) {
    return (
      <div className="rounded-lg border border-red-100 bg-red-50 p-6">
        <p className="font-medium text-red-700">Generation failed</p>
        <p className="mt-1 text-sm text-red-600">{String(raw.error)}</p>
      </div>
    );
  }

  // Merge original data with any local edits
  const rawDict = raw as unknown as Record<string, unknown>;
  const editDict = (edits[format] as unknown as Record<string, unknown>) ?? {};
  const current = { ...rawDict, ...editDict };

  const handleEdit = (value: unknown) => onEdit(format, value);

  const resetButton = Object.keys(edits[format] ?? {}).length > 0 && (
    <button
      onClick={() => onEdit(format, null)}
      className="mb-4 text-xs text-gray-400 underline hover:text-gray-600"
    >
      Reset to original
    </button>
  );

  return (
    <div>
      {resetButton}
      {format === "twitter" && (
        <TwitterEditor
          data={current as unknown as TwitterContent}
          onEdit={handleEdit}
        />
      )}
      {format === "linkedin" && (
        <LinkedInEditor
          data={current as unknown as LinkedInContent}
          onEdit={handleEdit}
        />
      )}
      {format === "newsletter" && (
        <NewsletterEditor
          data={current as unknown as NewsletterContent}
          onEdit={handleEdit}
        />
      )}
      {format === "short_video" && (
        <ShortVideoEditor
          data={current as unknown as ShortVideoContent}
          onEdit={handleEdit}
        />
      )}
      {format === "blog_post" && (
        <BlogPostEditor
          data={current as unknown as BlogPostContent}
          onEdit={handleEdit}
        />
      )}
      {format === "youtube" && (
        <YouTubeEditor
          data={current as unknown as YouTubeContent}
          onEdit={handleEdit}
        />
      )}
      {format === "quote_cards" && (
        <QuoteCardsEditor
          data={current as unknown as QuoteCardsContent}
          onEdit={handleEdit}
        />
      )}
      {format === "email_sequence" && (
        <EmailSequenceEditor
          data={current as unknown as EmailSequenceContent}
          onEdit={handleEdit}
        />
      )}
    </div>
  );
}
