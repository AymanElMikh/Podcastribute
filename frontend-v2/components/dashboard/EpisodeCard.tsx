'use client'

import Link from 'next/link'
import { cn, formatDuration, relativeTime, truncate } from '@/lib/utils'
import { Badge } from '@/components/ui/Badge'
import { STATUS_LABELS } from '@/lib/constants'
import type { Episode, EpisodeStatus } from '@/lib/types'

/* ─── Status badge variant mapping ─── */

const STATUS_BADGE: Record<EpisodeStatus, 'amber' | 'success' | 'error' | 'muted'> = {
  queued:       'muted',
  transcribing: 'amber',
  detecting:    'amber',
  generating:   'amber',
  ready:        'success',
  error:        'error',
}

const SOURCE_LABELS = {
  upload:  'Upload',
  youtube: 'YouTube',
  rss:     'RSS',
} as const

/* ─── Component ─── */

interface EpisodeCardProps {
  episode: Episode
}

export function EpisodeCard({ episode }: EpisodeCardProps) {
  const isProcessing = ['queued', 'transcribing', 'detecting', 'generating'].includes(episode.status)
  const isReady      = episode.status === 'ready'
  const isError      = episode.status === 'error'

  const cardContent = (
    <div
      className={cn(
        'group flex items-start gap-4 px-4 py-3.5',
        'bg-bg-surface border border-border-subtle rounded-lg',
        'transition-all duration-150',
        isReady && 'hover:border-border-default hover:-translate-y-0.5 cursor-pointer',
        isError && 'border-error/20',
      )}
    >
      {/* Source type indicator — left stripe */}
      <div
        className={cn(
          'mt-0.5 size-8 rounded-md flex items-center justify-center shrink-0 text-xs font-semibold',
          isReady      && 'bg-success/10 text-success',
          isProcessing && 'bg-amber/10 text-amber',
          isError      && 'bg-error/10 text-error',
          episode.status === 'queued' && 'bg-bg-elevated text-tertiary',
        )}
        aria-hidden="true"
      >
        {SOURCE_LABELS[episode.sourceType][0]}
      </div>

      {/* Main content */}
      <div className="flex-1 min-w-0">
        <div className="flex items-start justify-between gap-2">
          {/* Title */}
          <p className="text-sm font-medium text-primary leading-snug">
            {truncate(episode.title, 60)}
          </p>

          {/* Status badge */}
          <Badge variant={STATUS_BADGE[episode.status]} dot className="shrink-0">
            {STATUS_LABELS[episode.status]}
          </Badge>
        </div>

        {/* Meta row */}
        <div className="flex items-center gap-3 mt-1.5">
          {/* Source type */}
          <span className="text-xs text-tertiary">{SOURCE_LABELS[episode.sourceType]}</span>

          {/* Duration */}
          {episode.durationSeconds != null && (
            <>
              <span className="text-tertiary" aria-hidden="true">·</span>
              <span className="text-xs font-mono text-tertiary">
                {formatDuration(episode.durationSeconds)}
              </span>
            </>
          )}

          {/* Time */}
          <span className="text-tertiary" aria-hidden="true">·</span>
          <span className="text-xs text-tertiary">{relativeTime(episode.createdAt)}</span>
        </div>

        {/* Processing animation */}
        {isProcessing && (
          <div className="flex items-center gap-1.5 mt-2" aria-label="Processing">
            {[0, 150, 300].map((delay) => (
              <span
                key={delay}
                className="size-1 rounded-full bg-amber animate-pulse-amber"
                style={{ animationDelay: `${delay}ms` }}
                aria-hidden="true"
              />
            ))}
            <span className="text-xs text-amber ml-1">{STATUS_LABELS[episode.status]}…</span>
          </div>
        )}

        {/* Error message */}
        {isError && episode.errorMessage && (
          <p className="text-xs text-error mt-1.5 truncate">{episode.errorMessage}</p>
        )}
      </div>

      {/* Arrow — only on ready episodes */}
      {isReady && (
        <span
          className="mt-1 text-secondary group-hover:text-amber transition-colors duration-150 shrink-0"
          aria-hidden="true"
        >
          <ArrowIcon />
        </span>
      )}
    </div>
  )

  if (isReady) {
    return (
      <Link href={`/content/${episode.id}`} aria-label={`View content for ${episode.title}`}>
        {cardContent}
      </Link>
    )
  }

  return cardContent
}

EpisodeCard.displayName = 'EpisodeCard'

/* ─── Skeleton ─── */

export function EpisodeCardSkeleton() {
  return (
    <div className="flex items-start gap-4 px-4 py-3.5 bg-bg-surface border border-border-subtle rounded-lg">
      <div className="mt-0.5 size-8 rounded-md bg-bg-elevated animate-shimmer shrink-0" />
      <div className="flex-1 space-y-2 min-w-0">
        <div className="flex justify-between gap-2">
          <div className="h-4 w-2/5 rounded bg-bg-elevated animate-shimmer" />
          <div className="h-5 w-16 rounded bg-bg-elevated animate-shimmer shrink-0" />
        </div>
        <div className="h-3 w-1/3 rounded bg-bg-elevated animate-shimmer" />
      </div>
    </div>
  )
}

/* ─── Icons ─── */

function ArrowIcon() {
  return (
    <svg width="14" height="14" viewBox="0 0 14 14" fill="none" stroke="currentColor" strokeWidth="1.5">
      <path d="M3 7h8M7 3l4 4-4 4" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  )
}
