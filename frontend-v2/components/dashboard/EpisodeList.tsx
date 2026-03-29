'use client'

import Link from 'next/link'
import { Button } from '@/components/ui/Button'
import { EpisodeCard, EpisodeCardSkeleton } from './EpisodeCard'
import { useEpisodes } from '@/hooks/useEpisodes'

export function EpisodeList() {
  const { episodes, isLoading, error } = useEpisodes()

  /* ── Loading state ── */
  if (isLoading) {
    return (
      <div className="space-y-2.5">
        {Array.from({ length: 3 }).map((_, i) => (
          <EpisodeCardSkeleton key={i} />
        ))}
      </div>
    )
  }

  /* ── Error state ── */
  if (error) {
    return (
      <div className="flex flex-col items-center justify-center py-16 text-center">
        <p className="text-error text-sm mb-3">Failed to load episodes</p>
        <Button variant="secondary" size="sm" onClick={() => window.location.reload()}>
          Try again
        </Button>
      </div>
    )
  }

  /* ── Empty state ── */
  if (episodes.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-20 text-center animate-fade-up">
        <div
          className="size-14 rounded-full bg-bg-elevated flex items-center justify-center mb-5"
          aria-hidden="true"
        >
          <MicIcon />
        </div>
        <h2 className="font-display text-2xl font-bold text-primary mb-2">
          No episodes yet
        </h2>
        <p className="text-sm text-secondary max-w-xs mb-6">
          Upload your first podcast episode and turn it into 8 content formats in minutes.
        </p>
        <Button asChild size="lg">
          <Link href="/upload">Upload your first episode</Link>
        </Button>
      </div>
    )
  }

  /* ── Episode list ── */
  return (
    <ul className="space-y-2.5" aria-label="Your episodes">
      {episodes.map((episode) => (
        <li key={episode.id}>
          <EpisodeCard episode={episode} />
        </li>
      ))}
    </ul>
  )
}

EpisodeList.displayName = 'EpisodeList'

function MicIcon() {
  return (
    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" className="text-tertiary">
      <rect x="9" y="2" width="6" height="12" rx="3" />
      <path d="M5 10a7 7 0 0 0 14 0" strokeLinecap="round" />
      <path d="M12 19v3M9 22h6" strokeLinecap="round" />
    </svg>
  )
}
