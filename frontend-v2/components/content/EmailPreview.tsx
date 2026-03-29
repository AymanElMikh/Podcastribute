'use client'

import { useState } from 'react'
import { cn } from '@/lib/utils'
import { ContentEditor, EditableText } from './ContentEditor'
import { CopyButton } from './CopyButton'
import { Badge } from '@/components/ui/Badge'
import type { EmailContent } from '@/lib/types'

const PURPOSE_LABELS = {
  announce: 'Announcement',
  insight:  'Best insight',
  cta:      'Call to action',
} as const

interface EmailPreviewProps { content: EmailContent }

export function EmailPreview({ content: initial }: EmailPreviewProps) {
  const [content, setContent] = useState(initial)
  const isDirty = JSON.stringify(content) !== JSON.stringify(initial)

  const updateEmail = (i: number, patch: Partial<typeof content.emails[0]>) =>
    setContent((c) => ({
      ...c,
      emails: c.emails.map((e, j) => j === i ? { ...e, ...patch } : e),
    }))

  return (
    <ContentEditor
      formatName="Email Sequence"
      isDirty={isDirty}
      onReset={() => setContent(initial)}
    >
      <div className="space-y-4 max-w-xl">
        {content.emails.map((email, i) => (
          <div
            key={i}
            className="rounded-lg bg-bg-surface border border-border-subtle overflow-hidden"
          >
            {/* Email header */}
            <div className="flex items-center justify-between px-4 py-2.5 bg-bg-elevated border-b border-border-subtle">
              <div className="flex items-center gap-2">
                <Badge variant="muted" className="font-mono">Day {email.sendDay}</Badge>
                <Badge variant="amber">
                  {PURPOSE_LABELS[email.purpose] ?? email.purpose}
                </Badge>
              </div>
              <CopyButton
                text={`Subject: ${email.subject}\n\n${email.body}`}
                size="xs"
              />
            </div>

            {/* Email meta */}
            <div className="px-4 py-3 border-b border-border-subtle space-y-2">
              <div className="flex items-baseline gap-2">
                <span className="text-xs text-tertiary shrink-0 w-14">Subject</span>
                <EditableText
                  value={email.subject}
                  onChange={(v) => updateEmail(i, { subject: v })}
                  className="text-sm font-medium text-primary flex-1"
                />
              </div>
              <div className="flex items-baseline gap-2">
                <span className="text-xs text-tertiary shrink-0 w-14">Preview</span>
                <EditableText
                  value={email.previewText}
                  onChange={(v) => updateEmail(i, { previewText: v })}
                  className="text-xs italic text-secondary flex-1"
                />
              </div>
            </div>

            {/* Email body */}
            <div className="px-4 py-3">
              <EditableText
                value={email.body}
                onChange={(v) => updateEmail(i, { body: v })}
                multiline
                className="text-sm leading-relaxed text-secondary"
              />
              <p className="text-[10px] font-mono text-tertiary mt-2">
                {email.body.trim().split(/\s+/).filter(Boolean).length} words
              </p>
            </div>
          </div>
        ))}
      </div>
    </ContentEditor>
  )
}

EmailPreview.displayName = 'EmailPreview'
