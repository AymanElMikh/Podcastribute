'use client'

import { useState } from 'react'
import { cn } from '@/lib/utils'
import { ContentEditor, EditableText } from './ContentEditor'
import { CopyButton } from './CopyButton'
import { Badge } from '@/components/ui/Badge'
import type { ShortVideoContent } from '@/lib/types'

const PLATFORM_LABELS = { tiktok: 'TikTok', reels: 'Reels', shorts: 'Shorts' }

interface VideoClipsListProps { content: ShortVideoContent }

export function VideoClipsList({ content: initial }: VideoClipsListProps) {
  const [content, setContent] = useState(initial)
  const isDirty = JSON.stringify(content) !== JSON.stringify(initial)

  const updateClip = (i: number, patch: Partial<typeof content.clips[0]>) =>
    setContent((c) => ({
      ...c,
      clips: c.clips.map((clip, j) => j === i ? { ...clip, ...patch } : clip),
    }))

  return (
    <ContentEditor
      formatName="Short Video"
      isDirty={isDirty}
      onReset={() => setContent(initial)}
    >
      <div className="space-y-4 max-w-xl">
        {content.clips.map((clip, i) => (
          <div
            key={i}
            className="p-4 rounded-lg bg-bg-surface border border-border-subtle space-y-3"
          >
            {/* Header row */}
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Badge variant="muted" className="font-mono text-[10px]">
                  {clip.startTime} — {clip.endTime}
                </Badge>
                <Badge variant="amber">
                  {PLATFORM_LABELS[clip.platform] ?? clip.platform}
                </Badge>
              </div>
              <CopyButton
                text={`${clip.startTime} — ${clip.endTime}`}
                label="Copy timestamps"
                size="xs"
              />
            </div>

            {/* Hook */}
            <div>
              <p className="text-[10px] uppercase tracking-wide text-tertiary mb-1">Hook (first 3s)</p>
              <EditableText
                value={clip.hook}
                onChange={(v) => updateClip(i, { hook: v })}
                className="text-sm font-medium text-primary"
              />
            </div>

            {/* Script note */}
            <div>
              <p className="text-[10px] uppercase tracking-wide text-tertiary mb-1">Screen text / script note</p>
              <EditableText
                value={clip.scriptNote}
                onChange={(v) => updateClip(i, { scriptNote: v })}
                className="text-sm italic text-secondary"
              />
            </div>
          </div>
        ))}
      </div>
    </ContentEditor>
  )
}

VideoClipsList.displayName = 'VideoClipsList'
