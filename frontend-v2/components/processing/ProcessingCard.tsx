'use client'

import Link from 'next/link'
import { cn, truncate, relativeTime } from '@/lib/utils'
import { Badge } from '@/components/ui/Badge'
import { useSSE } from '@/hooks/useSSE'
import { SSE_STEP_LABELS } from '@/lib/constants'
import type { Episode } from '@/lib/types'

/**
 * Compact episode card shown in the dashboard processing queue.
 * Connects its own SSE stream to show the live current step label.
 */
interface ProcessingCardProps {
  episode: Episode
}

export function ProcessingCard({ episode }: ProcessingCardProps) {
  const isActive = ['transcribing', 'detecting', 'generating'].includes(episode.status)
  const { events } = useSSE(isActive ? episode.id : null)

  // Latest meaningful step label from the stream
  const latestEvent = [...events].reverse().find(
    (e) => e.type !== 'error' && SSE_STEP_LABELS[e.type],
  )
  const stepLabel = latestEvent ? SSE_STEP_LABELS[latestEvent.type] : null

  return (
    <Link
      href={`/content/${episode.id}`}
      className={cn(
        'flex items-center gap-3 p-3 rounded-lg border',
        'bg-bg-surface border-border-subtle',
        'hover:border-border-default transition-all duration-150',
      )}
    >
      {/* Amber pulse dot */}
      <span className="size-2 rounded-full bg-amber animate-pulse-amber shrink-0" aria-hidden="true" />

      <div className="flex-1 min-w-0">
        <p className="text-sm text-primary truncate">{truncate(episode.title, 40)}</p>
        <p className="text-xs text-secondary mt-0.5">
          {stepLabel ?? 'Processing…'}
        </p>
      </div>

      <Badge variant="amber" className="shrink-0">Live</Badge>
    </Link>
  )
}

ProcessingCard.displayName = 'ProcessingCard'
