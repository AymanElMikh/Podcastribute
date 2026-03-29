'use client'

import { useState } from 'react'
import { toast } from 'sonner'
import { cn } from '@/lib/utils'
import { Button } from '@/components/ui/Button'
import { PlatformBadge } from './PlatformBadge'
import { publishContent } from '@/lib/api'
import { APIError } from '@/lib/types'
import type { ContentPack, PublishStatus } from '@/lib/types'
import type { FormatKey } from '@/lib/constants'
import { FORMATS } from '@/lib/constants'
import { CopyButton } from '@/components/content/CopyButton'

/* ─── Platform config ─── */

const PLATFORMS = [
  { key: 'twitter',    label: 'Twitter / X',  formatKey: 'twitter'   as FormatKey },
  { key: 'linkedin',   label: 'LinkedIn',      formatKey: 'linkedin'  as FormatKey },
  { key: 'newsletter', label: 'Newsletter',    formatKey: 'newsletter'as FormatKey },
  { key: 'buffer',     label: 'Buffer (all)',  formatKey: null },
] as const

type PlatformKey = typeof PLATFORMS[number]['key']

/* ─── Component ─── */

interface PublishPanelProps {
  episodeId: string
  content:   ContentPack | null
}

export function PublishPanel({ episodeId, content }: PublishPanelProps) {
  const [selected,    setSelected]    = useState<Set<PlatformKey>>(new Set())
  const [schedule,    setSchedule]    = useState<'now' | 'later'>('now')
  const [scheduleAt,  setScheduleAt]  = useState('')
  const [submitting,  setSubmitting]  = useState(false)
  const [results,     setResults]     = useState<Record<string, PublishStatus>>({})

  const toggle = (key: PlatformKey) =>
    setSelected((prev) => {
      const next = new Set(prev)
      next.has(key) ? next.delete(key) : next.add(key)
      return next
    })

  const handlePublish = async () => {
    if (selected.size === 0) return
    setSubmitting(true)
    try {
      const result = await publishContent(
        episodeId,
        [...selected],
        {},
        schedule === 'later' && scheduleAt ? scheduleAt : undefined,
      )
      setResults(result)
      const successes = Object.values(result).filter((s) => s === 'sent' || s === 'scheduled').length
      toast.success(`Published to ${successes} platform${successes !== 1 ? 's' : ''}`)
    } catch (err) {
      const msg = err instanceof APIError ? err.message : 'Publish failed'
      toast.error('Publish failed', { description: msg })
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <aside className="flex flex-col gap-5" aria-label="Publish panel">
      {/* Publish section */}
      <div className="p-4 rounded-lg bg-bg-surface border border-border-subtle space-y-4">
        <p className="text-xs font-semibold text-secondary uppercase tracking-wide">Publish</p>

        {/* Platform toggles */}
        <div className="space-y-2">
          {PLATFORMS.map(({ key, label }) => {
            const isSelected = selected.has(key)
            const result     = results[key]

            return (
              <label
                key={key}
                className={cn(
                  'flex items-center gap-3 p-2.5 rounded-md border cursor-pointer',
                  'transition-all duration-150',
                  isSelected
                    ? 'border-amber/40 bg-amber/5'
                    : 'border-border-subtle hover:border-border-default',
                )}
              >
                <input
                  type="checkbox"
                  checked={isSelected}
                  onChange={() => toggle(key)}
                  className="accent-amber shrink-0"
                />
                <PlatformBadge platform={key} status={result ?? null} />
              </label>
            )
          })}
        </div>

        {/* Schedule toggle */}
        <div className="flex items-center gap-2">
          {(['now', 'later'] as const).map((opt) => (
            <button
              key={opt}
              onClick={() => setSchedule(opt)}
              className={cn(
                'flex-1 py-1.5 text-xs rounded-md border transition-all duration-150 cursor-pointer',
                schedule === opt
                  ? 'border-amber bg-amber/10 text-amber'
                  : 'border-border-subtle text-secondary hover:text-primary',
              )}
            >
              {opt === 'now' ? 'Publish now' : 'Schedule'}
            </button>
          ))}
        </div>

        {/* Date/time picker */}
        {schedule === 'later' && (
          <input
            type="datetime-local"
            value={scheduleAt}
            onChange={(e) => setScheduleAt(e.target.value)}
            className={cn(
              'w-full h-9 px-3 rounded-md text-sm',
              'bg-bg-elevated border border-border-subtle text-primary',
              'focus:outline-none focus:border-amber transition-colors duration-150',
            )}
          />
        )}

        <Button
          fullWidth
          size="md"
          loading={submitting}
          disabled={selected.size === 0}
          onClick={handlePublish}
        >
          {schedule === 'now' ? 'Publish selected' : 'Schedule selected'}
        </Button>
      </div>

      {/* Copy section */}
      <div className="p-4 rounded-lg bg-bg-surface border border-border-subtle space-y-3">
        <p className="text-xs font-semibold text-secondary uppercase tracking-wide">Copy to clipboard</p>

        <div className="space-y-1">
          {FORMATS.map(({ key, label }) => {
            const formatData = content?.[key as keyof ContentPack]
            if (!formatData) return null

            // Serialize the format content as plain text for copying
            const text = JSON.stringify(formatData, null, 2)

            return (
              <div
                key={key}
                className="flex items-center justify-between py-1.5 px-2 rounded-md hover:bg-bg-elevated transition-colors duration-150"
              >
                <span className="text-xs text-secondary">{label}</span>
                <CopyButton text={text} size="xs" label={label} />
              </div>
            )
          })}
        </div>
      </div>
    </aside>
  )
}

PublishPanel.displayName = 'PublishPanel'
