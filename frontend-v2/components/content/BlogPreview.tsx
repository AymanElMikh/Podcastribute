'use client'

import { useState } from 'react'
import { ContentEditor, EditableText } from './ContentEditor'
import { CopyButton } from './CopyButton'
import { Badge } from '@/components/ui/Badge'
import type { BlogContent } from '@/lib/types'

interface BlogPreviewProps { content: BlogContent }

export function BlogPreview({ content: initial }: BlogPreviewProps) {
  const [content, setContent] = useState(initial)
  const isDirty = JSON.stringify(content) !== JSON.stringify(initial)

  const wordCount = content.body.trim().split(/\s+/).filter(Boolean).length

  return (
    <ContentEditor
      formatName="Blog Post"
      isDirty={isDirty}
      onReset={() => setContent(initial)}
    >
      <div className="space-y-6">
        {/* SEO meta */}
        <section className="p-4 rounded-lg bg-bg-elevated border border-border-subtle space-y-3">
          <p className="text-xs font-semibold text-secondary uppercase tracking-wide">SEO metadata</p>
          <div>
            <p className="text-[10px] text-tertiary uppercase tracking-wide mb-1">Title (H1)</p>
            <EditableText
              value={content.title}
              onChange={(v) => setContent((c) => ({ ...c, title: v }))}
              className="text-sm font-semibold text-primary"
            />
          </div>
          <div>
            <p className="text-[10px] text-tertiary uppercase tracking-wide mb-1">
              Meta description <span className="normal-case">(155 chars)</span>
            </p>
            <EditableText
              value={content.metaDescription}
              onChange={(v) => setContent((c) => ({ ...c, metaDescription: v }))}
              multiline
              charLimit={155}
              className="text-sm text-secondary"
            />
          </div>
          <div>
            <p className="text-[10px] text-tertiary uppercase tracking-wide mb-1.5">Target keywords</p>
            <div className="flex flex-wrap gap-1.5">
              {content.targetKeywords.map((kw, i) => (
                <Badge key={i} variant="muted">{kw}</Badge>
              ))}
            </div>
          </div>
        </section>

        {/* Outline */}
        <section>
          <p className="text-xs font-semibold text-secondary uppercase tracking-wide mb-3">Outline</p>
          <ol className="space-y-1.5">
            {content.outline.map((heading, i) => (
              <li key={i} className="flex items-center gap-2.5 p-2 rounded-md bg-bg-surface border border-border-subtle">
                <span className="text-xs font-mono text-tertiary shrink-0">H{i + 2}</span>
                <EditableText
                  value={heading}
                  onChange={(v) => setContent((c) => ({
                    ...c, outline: c.outline.map((h, j) => j === i ? v : h),
                  }))}
                  className="text-sm flex-1"
                />
              </li>
            ))}
          </ol>
        </section>

        {/* Body */}
        <section>
          <div className="flex items-center justify-between mb-3">
            <div className="flex items-center gap-2">
              <p className="text-xs font-semibold text-secondary uppercase tracking-wide">Article body</p>
              <span className="text-xs font-mono text-tertiary">{wordCount} words</span>
            </div>
            <CopyButton text={content.body} />
          </div>
          <div className="p-5 rounded-lg bg-bg-surface border border-border-subtle max-w-2xl">
            <h1 className="font-display text-2xl font-bold text-primary mb-4">{content.title}</h1>
            <EditableText
              value={content.body}
              onChange={(v) => setContent((c) => ({ ...c, body: v }))}
              multiline
              className="text-sm leading-relaxed text-secondary"
            />
          </div>
        </section>
      </div>
    </ContentEditor>
  )
}

BlogPreview.displayName = 'BlogPreview'
