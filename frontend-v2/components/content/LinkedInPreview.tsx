'use client'

import { useState } from 'react'
import { ContentEditor, EditableText } from './ContentEditor'
import { CopyButton } from './CopyButton'
import type { LinkedInContent } from '@/lib/types'

interface LinkedInPreviewProps { content: LinkedInContent }

export function LinkedInPreview({ content: initial }: LinkedInPreviewProps) {
  const [content, setContent] = useState(initial)
  const isDirty = JSON.stringify(content) !== JSON.stringify(initial)

  return (
    <ContentEditor
      formatName="LinkedIn"
      isDirty={isDirty}
      onReset={() => setContent(initial)}
    >
      <div className="space-y-6 max-w-xl">
        {/* Post */}
        <section>
          <div className="flex items-center justify-between mb-3">
            <p className="text-xs font-semibold text-secondary uppercase tracking-wide">Post</p>
            <CopyButton text={content.post} />
          </div>
          <div className="p-4 rounded-lg bg-bg-surface border border-border-subtle">
            <EditableText
              value={content.post}
              onChange={(v) => setContent((c) => ({ ...c, post: v }))}
              multiline
              className="text-sm leading-relaxed"
            />
          </div>
        </section>

        {/* Alternative hooks */}
        <section>
          <p className="text-xs font-semibold text-secondary uppercase tracking-wide mb-3">
            Alternative opening lines
          </p>
          <div className="space-y-2">
            {content.postHooks.map((hook, i) => (
              <div key={i} className="flex items-start gap-2 p-3 rounded-lg bg-bg-surface border border-border-subtle">
                <span className="text-xs font-mono text-tertiary mt-0.5 shrink-0">{i + 1}</span>
                <div className="flex-1">
                  <EditableText
                    value={hook}
                    onChange={(v) => setContent((c) => ({
                      ...c, postHooks: c.postHooks.map((h, j) => j === i ? v : h),
                    }))}
                    multiline
                  />
                </div>
                <CopyButton text={hook} size="xs" className="shrink-0 mt-0.5" />
              </div>
            ))}
          </div>
        </section>

        {/* Carousel outline */}
        <section>
          <p className="text-xs font-semibold text-secondary uppercase tracking-wide mb-3">
            Carousel outline <span className="text-tertiary normal-case font-normal">(slide titles for Canva)</span>
          </p>
          <ol className="space-y-1.5">
            {content.carouselOutline.map((slide, i) => (
              <li key={i} className="flex items-center gap-3 p-2.5 rounded-md bg-bg-elevated border border-border-subtle">
                <span className="size-6 rounded flex items-center justify-center text-xs font-mono text-tertiary bg-bg-surface shrink-0">
                  {i + 1}
                </span>
                <EditableText
                  value={slide}
                  onChange={(v) => setContent((c) => ({
                    ...c, carouselOutline: c.carouselOutline.map((s, j) => j === i ? v : s),
                  }))}
                  className="text-sm flex-1"
                />
              </li>
            ))}
          </ol>
        </section>
      </div>
    </ContentEditor>
  )
}

LinkedInPreview.displayName = 'LinkedInPreview'
