'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { toast } from 'sonner'
import { cn, relativeTime } from '@/lib/utils'
import { Input } from '@/components/ui/Input'
import { Button } from '@/components/ui/Button'
import { Skeleton } from '@/components/ui/Skeleton'
import { ingestRSS } from '@/lib/api'
import { APIError } from '@/lib/types'

/* ─── Types ─── */

interface RSSEpisode {
  title:       string
  published:   string
  duration?:   string
  description: string
}

/* ─── Feed fetch schema ─── */

const feedSchema = z.object({
  feedUrl: z.string().url('Enter a valid RSS feed URL'),
})

type FeedValues = z.infer<typeof feedSchema>

/* ─── Component ─── */

export function RSSInput() {
  const router = useRouter()

  const [episodes,   setEpisodes]   = useState<RSSEpisode[]>([])
  const [selected,   setSelected]   = useState<number | null>(null)
  const [loading,    setLoading]    = useState(false)
  const [submitting, setSubmitting] = useState(false)
  const [feedUrl,    setFeedUrl]    = useState('')

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<FeedValues>({ resolver: zodResolver(feedSchema) })

  /* ── Step 1: load episodes from feed ── */
  const onLoadFeed = async (values: FeedValues) => {
    setLoading(true)
    setEpisodes([])
    setSelected(null)
    setFeedUrl(values.feedUrl)

    try {
      // We hit the proxy which calls FastAPI's RSS list endpoint
      const res = await fetch(`/api/proxy/v1/episodes/rss/list`, {
        method:  'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization:  `Bearer ${localStorage.getItem('token') ?? ''}`,
        },
        body: JSON.stringify({ feed_url: values.feedUrl, limit: 5 }),
      })

      if (!res.ok) {
        const data = await res.json().catch(() => ({})) as { detail?: string }
        throw new Error(data.detail ?? 'Failed to load feed')
      }

      const data = await res.json() as RSSEpisode[]
      setEpisodes(data)
    } catch (err) {
      toast.error('Could not load RSS feed', {
        description: err instanceof Error ? err.message : 'Check the URL and try again.',
      })
    } finally {
      setLoading(false)
    }
  }

  /* ── Step 2: ingest the selected episode ── */
  const onProcess = async () => {
    if (selected === null) return
    setSubmitting(true)

    try {
      const { episode_id } = await ingestRSS(feedUrl, selected)
      router.push(`/content/${episode_id}`)
    } catch (err) {
      const msg = err instanceof APIError ? err.message : 'Failed to process RSS episode'
      toast.error('RSS ingestion failed', { description: msg })
      setSubmitting(false)
    }
  }

  return (
    <div className="space-y-5">
      {/* Feed URL input */}
      <form onSubmit={handleSubmit(onLoadFeed)} noValidate className="flex gap-2">
        <div className="flex-1">
          <Input
            type="url"
            placeholder="https://feeds.example.com/podcast.rss"
            error={errors.feedUrl?.message}
            leftIcon={<RSSIcon />}
            {...register('feedUrl')}
          />
        </div>
        <Button type="submit" variant="secondary" size="md" loading={loading}>
          Load feed
        </Button>
      </form>

      {/* Loading skeletons */}
      {loading && (
        <div className="space-y-2">
          {Array.from({ length: 4 }).map((_, i) => (
            <div key={i} className="flex gap-3 p-3 rounded-lg bg-bg-elevated">
              <Skeleton height="h-4" width="w-4" circle />
              <div className="flex-1 space-y-1.5">
                <Skeleton height="h-3.5" width="w-3/4" />
                <Skeleton height="h-3" width="w-1/3" />
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Episode list */}
      {!loading && episodes.length > 0 && (
        <div className="space-y-2 animate-fade-up">
          <p className="text-xs text-secondary">
            Select an episode to process:
          </p>
          <ul role="listbox" aria-label="RSS episodes" className="space-y-1.5">
            {episodes.map((ep, i) => (
              <li key={i}>
                <button
                  role="option"
                  aria-selected={selected === i}
                  onClick={() => setSelected(i)}
                  className={cn(
                    'w-full text-left p-3 rounded-lg border transition-all duration-150 cursor-pointer',
                    selected === i
                      ? 'border-amber bg-amber/5'
                      : 'border-border-subtle bg-bg-elevated hover:border-border-default',
                  )}
                >
                  <div className="flex items-start gap-2.5">
                    {/* Selection indicator */}
                    <span
                      className={cn(
                        'mt-0.5 size-3.5 rounded-full border-2 shrink-0 transition-colors duration-150',
                        selected === i
                          ? 'border-amber bg-amber'
                          : 'border-border-strong',
                      )}
                      aria-hidden="true"
                    />
                    <div className="min-w-0">
                      <p className="text-sm text-primary font-medium leading-snug line-clamp-2">
                        {ep.title}
                      </p>
                      <div className="flex items-center gap-2 mt-1">
                        <span className="text-xs text-tertiary">
                          {relativeTime(ep.published)}
                        </span>
                        {ep.duration && (
                          <>
                            <span className="text-tertiary" aria-hidden="true">·</span>
                            <span className="text-xs font-mono text-tertiary">
                              {ep.duration}
                            </span>
                          </>
                        )}
                      </div>
                    </div>
                  </div>
                </button>
              </li>
            ))}
          </ul>

          <Button
            fullWidth
            size="lg"
            disabled={selected === null}
            loading={submitting}
            onClick={onProcess}
            className="mt-2"
          >
            Process this episode
          </Button>
        </div>
      )}
    </div>
  )
}

RSSInput.displayName = 'RSSInput'

function RSSIcon() {
  return (
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
      <path d="M4 11a9 9 0 0 1 9 9" strokeLinecap="round" />
      <path d="M4 4a16 16 0 0 1 16 16" strokeLinecap="round" />
      <circle cx="4" cy="20" r="1.5" fill="currentColor" stroke="none" />
    </svg>
  )
}
