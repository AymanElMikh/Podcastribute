'use client'

import { useState } from 'react'
import { cn } from '@/lib/utils'
import { ContentEditor, EditableText } from './ContentEditor'
import { CopyButton } from './CopyButton'
import type { QuoteCardsContent } from '@/lib/types'

interface QuoteCardPreviewProps { content: QuoteCardsContent }

export function QuoteCardPreview({ content: initial }: QuoteCardPreviewProps) {
  const [content, setContent] = useState(initial)
  const isDirty = JSON.stringify(content) !== JSON.stringify(initial)

  const updateQuote = (i: number, patch: Partial<typeof content.quotes[0]>) =>
    setContent((c) => ({
      ...c,
      quotes: c.quotes.map((q, j) => j === i ? { ...q, ...patch } : q),
    }))

  return (
    <ContentEditor
      formatName="Quote Cards"
      isDirty={isDirty}
      onReset={() => setContent(initial)}
    >
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 max-w-2xl">
        {content.quotes.map((quote, i) => (
          <div key={i} className="space-y-2">
            {/* Visual card */}
            <div className="p-5 rounded-xl bg-bg-elevated border border-border-default aspect-square flex flex-col justify-between">
              <div className="text-amber text-3xl font-display leading-none" aria-hidden="true">❝</div>
              <div className="flex-1 flex items-center py-3">
                <EditableText
                  value={quote.text}
                  onChange={(v) => updateQuote(i, { text: v })}
                  multiline
                  className="text-sm font-medium text-primary leading-relaxed text-center w-full"
                />
              </div>
              <EditableText
                value={quote.attribution}
                onChange={(v) => updateQuote(i, { attribution: v })}
                className="text-xs text-secondary italic text-center"
              />
            </div>

            {/* Caption */}
            <div className="flex items-start gap-2">
              <div className="flex-1">
                <p className="text-[10px] uppercase tracking-wide text-tertiary mb-1">Caption</p>
                <EditableText
                  value={quote.caption}
                  onChange={(v) => updateQuote(i, { caption: v })}
                  multiline
                  className="text-xs text-secondary"
                />
              </div>
              <CopyButton
                text={`${quote.text}\n\n${quote.attribution}\n\n${quote.caption}`}
                size="xs"
                className="mt-4 shrink-0"
              />
            </div>
          </div>
        ))}
      </div>
    </ContentEditor>
  )
}

QuoteCardPreview.displayName = 'QuoteCardPreview'
