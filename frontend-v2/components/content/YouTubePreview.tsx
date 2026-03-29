'use client'

import { useState } from 'react'
import { ContentEditor, EditableText } from './ContentEditor'
import { CopyButton } from './CopyButton'
import { Badge } from '@/components/ui/Badge'
import type { YouTubeContent } from '@/lib/types'

interface YouTubePreviewProps { content: YouTubeContent }

export function YouTubePreview({ content: initial }: YouTubePreviewProps) {
  const [content, setContent] = useState(initial)
  const isDirty = JSON.stringify(content) !== JSON.stringify(initial)

  return (
    <ContentEditor
      formatName="YouTube"
      isDirty={isDirty}
      onReset={() => setContent(initial)}
    >
      <div className="space-y-6 max-w-xl">
        {/* Description */}
        <section>
          <div className="flex items-center justify-between mb-3">
            <div>
              <p className="text-xs font-semibold text-secondary uppercase tracking-wide">Description</p>
              <p className="text-[10px] text-tertiary mt-0.5">First 150 chars are shown in search</p>
            </div>
            <CopyButton text={content.description} />
          </div>
          <div className="p-4 rounded-lg bg-bg-surface border border-border-subtle">
            <EditableText
              value={content.description}
              onChange={(v) => setContent((c) => ({ ...c, description: v }))}
              multiline
              className="text-sm leading-relaxed"
            />
          </div>
        </section>

        {/* Chapters */}
        <section>
          <p className="text-xs font-semibold text-secondary uppercase tracking-wide mb-3">
            Chapters
          </p>
          <ol className="space-y-1.5">
            {content.chapters.map((ch, i) => (
              <li key={i} className="flex items-center gap-3 p-2.5 rounded-md bg-bg-surface border border-border-subtle">
                <Badge variant="muted" className="font-mono text-[10px] shrink-0">{ch.time}</Badge>
                <EditableText
                  value={ch.title}
                  onChange={(v) => setContent((c) => ({
                    ...c,
                    chapters: c.chapters.map((c2, j) => j === i ? { ...c2, title: v } : c2),
                  }))}
                  className="text-sm flex-1"
                />
              </li>
            ))}
          </ol>
          <div className="mt-2 flex justify-end">
            <CopyButton
              text={content.chapters.map((c) => `${c.time} ${c.title}`).join('\n')}
              label="Copy chapters"
            />
          </div>
        </section>

        {/* Tags */}
        <section>
          <p className="text-xs font-semibold text-secondary uppercase tracking-wide mb-3">
            Tags <span className="text-tertiary normal-case font-normal">({content.tags.length} tags)</span>
          </p>
          <div className="flex flex-wrap gap-1.5">
            {content.tags.map((tag, i) => (
              <Badge key={i} variant="muted">{tag}</Badge>
            ))}
          </div>
          <div className="mt-2 flex justify-end">
            <CopyButton text={content.tags.join(', ')} label="Copy tags" />
          </div>
        </section>

        {/* End screen script */}
        <section>
          <p className="text-xs font-semibold text-secondary uppercase tracking-wide mb-2">
            End screen script <span className="text-tertiary normal-case font-normal">(last 20 seconds)</span>
          </p>
          <div className="p-3 rounded-lg bg-bg-surface border border-border-subtle">
            <EditableText
              value={content.endScreenScript}
              onChange={(v) => setContent((c) => ({ ...c, endScreenScript: v }))}
              multiline
              className="text-sm italic text-secondary"
            />
          </div>
        </section>
      </div>
    </ContentEditor>
  )
}

YouTubePreview.displayName = 'YouTubePreview'
