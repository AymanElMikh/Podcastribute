'use client'

import { useState } from 'react'
import { cn } from '@/lib/utils'
import { ContentEditor, EditableText } from './ContentEditor'
import { CopyButton } from './CopyButton'
import type { NewsletterContent } from '@/lib/types'

interface NewsletterPreviewProps { content: NewsletterContent }

export function NewsletterPreview({ content: initial }: NewsletterPreviewProps) {
  const [content,        setContent]        = useState(initial)
  const [selectedSubject, setSelectedSubject] = useState(0)
  const isDirty = JSON.stringify(content) !== JSON.stringify(initial)

  return (
    <ContentEditor
      formatName="Newsletter"
      isDirty={isDirty}
      onReset={() => setContent(initial)}
    >
      <div className="space-y-6 max-w-xl">
        {/* Subject lines */}
        <section>
          <p className="text-xs font-semibold text-secondary uppercase tracking-wide mb-3">
            Subject lines <span className="text-tertiary normal-case font-normal">(pick one)</span>
          </p>
          <div className="space-y-1.5" role="radiogroup" aria-label="Subject line options">
            {content.subjectLines.map((subject, i) => (
              <label
                key={i}
                className={cn(
                  'flex items-start gap-3 p-3 rounded-lg border cursor-pointer',
                  'transition-all duration-150',
                  selectedSubject === i
                    ? 'border-amber bg-amber/5'
                    : 'border-border-subtle bg-bg-surface hover:border-border-default',
                )}
              >
                <input
                  type="radio"
                  name="subject"
                  checked={selectedSubject === i}
                  onChange={() => setSelectedSubject(i)}
                  className="mt-0.5 accent-amber shrink-0"
                />
                <div className="flex-1">
                  <EditableText
                    value={subject}
                    onChange={(v) => setContent((c) => ({
                      ...c, subjectLines: c.subjectLines.map((s, j) => j === i ? v : s),
                    }))}
                    className="text-sm"
                  />
                </div>
                <CopyButton text={subject} size="xs" className="shrink-0" />
              </label>
            ))}
          </div>
        </section>

        {/* Preview text */}
        <section>
          <p className="text-xs font-semibold text-secondary uppercase tracking-wide mb-2">
            Preview text
          </p>
          <div className="p-3 rounded-lg bg-bg-surface border border-border-subtle">
            <EditableText
              value={content.previewText}
              onChange={(v) => setContent((c) => ({ ...c, previewText: v }))}
              className="text-sm italic text-secondary"
            />
          </div>
        </section>

        {/* Body */}
        <section>
          <div className="flex items-center justify-between mb-3">
            <p className="text-xs font-semibold text-secondary uppercase tracking-wide">Section body</p>
            <CopyButton text={content.sectionBody} />
          </div>
          {/* Email preview styling */}
          <div className="p-5 rounded-lg bg-bg-surface border border-border-subtle">
            <div className="mb-3 pb-3 border-b border-border-subtle">
              <p className="text-xs text-tertiary">Subject:</p>
              <p className="text-sm font-medium text-primary">
                {content.subjectLines[selectedSubject]}
              </p>
              <p className="text-xs italic text-secondary mt-0.5">{content.previewText}</p>
            </div>
            <div className="mb-3">
              <EditableText
                value={content.sectionTitle}
                onChange={(v) => setContent((c) => ({ ...c, sectionTitle: v }))}
                className="text-base font-semibold text-primary font-display"
              />
            </div>
            <EditableText
              value={content.sectionBody}
              onChange={(v) => setContent((c) => ({ ...c, sectionBody: v }))}
              multiline
              className="text-sm leading-relaxed text-secondary"
            />
          </div>
        </section>
      </div>
    </ContentEditor>
  )
}

NewsletterPreview.displayName = 'NewsletterPreview'
