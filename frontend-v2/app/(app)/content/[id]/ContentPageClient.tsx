'use client'

import { useState } from 'react'
import Link from 'next/link'
import { useSearchParams } from 'next/navigation'
import { useEpisode } from '@/hooks/useEpisodes'
import { useContent } from '@/hooks/useContent'
import { ProcessingStream }  from '@/components/processing/ProcessingStream'
import { FormatNav }         from '@/components/content/FormatNav'
import { FormatNavMobile }   from '@/components/content/FormatNavMobile'
import { TwitterPreview }    from '@/components/content/TwitterPreview'
import { LinkedInPreview }   from '@/components/content/LinkedInPreview'
import { NewsletterPreview } from '@/components/content/NewsletterPreview'
import { VideoClipsList }    from '@/components/content/VideoClipsList'
import { BlogPreview }       from '@/components/content/BlogPreview'
import { YouTubePreview }    from '@/components/content/YouTubePreview'
import { QuoteCardPreview }  from '@/components/content/QuoteCardPreview'
import { EmailPreview }      from '@/components/content/EmailPreview'
import { PublishPanel }      from '@/components/publish/PublishPanel'
import { SkeletonCard }      from '@/components/ui/Skeleton'
import { Button }            from '@/components/ui/Button'
import type { FormatKey }    from '@/lib/constants'
import type { ContentPack }  from '@/lib/types'

interface ContentPageClientProps {
  episodeId: string
}

export function ContentPageClient({ episodeId }: ContentPageClientProps) {
  const { episode, isLoading: epLoading, error: epError } = useEpisode(episodeId)
  const { content, isLoading: contentLoading }            = useContent(
    episode?.status === 'ready' ? episodeId : null,
  )
  const searchParams = useSearchParams()
  const forceReady   = searchParams.get('view') === 'ready'

  const [activeFormat, setActiveFormat] = useState<FormatKey>('twitter')

  /* ── Loading ── */
  if (epLoading) {
    return (
      <div className="max-w-lg mx-auto space-y-3 mt-8">
        <SkeletonCard />
        <SkeletonCard />
      </div>
    )
  }

  /* ── Episode not found ── */
  if (epError || !episode) {
    return (
      <div className="flex flex-col items-center justify-center py-24 text-center">
        <p className="text-error text-sm mb-4">Episode not found or access denied.</p>
        <Button variant="secondary" size="sm" asChild>
          <Link href="/dashboard">Back to dashboard</Link>
        </Button>
      </div>
    )
  }

  /* ── Processing view ── */
  if (!forceReady && episode.status !== 'ready' && episode.status !== 'error') {
    return <ProcessingStream episodeId={episodeId} title={episode.title} />
  }

  /* ── Episode errored ── */
  if (episode.status === 'error') {
    return (
      <div className="flex flex-col items-center justify-center py-24 text-center">
        <div className="size-12 rounded-full bg-error/10 flex items-center justify-center mb-4">
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#EF4444" strokeWidth="1.5">
            <circle cx="12" cy="12" r="9" />
            <path d="M12 8v4M12 16h.01" strokeLinecap="round" />
          </svg>
        </div>
        <h2 className="text-lg font-semibold text-error mb-2">Processing failed</h2>
        <p className="text-sm text-secondary max-w-sm mb-6">
          {episode.errorMessage ?? 'An error occurred while processing your episode.'}
        </p>
        <Button asChild size="md">
          <Link href="/upload">Try again</Link>
        </Button>
      </div>
    )
  }

  /* ── Content review ── */
  return (
    <div className="flex flex-col h-[calc(100vh-3.5rem-1.5rem)] -mx-5 -mt-6">

      {/* Mobile format tab bar */}
      <div className="lg:hidden shrink-0">
        <FormatNavMobile
          active={activeFormat}
          content={content}
          onSelect={setActiveFormat}
        />
      </div>

      {/* Three-column row — fills remaining height */}
      <div className="flex flex-1 min-h-0">

        {/* Left: format nav (240px, desktop only) */}
        <div className="hidden lg:flex flex-col w-60 shrink-0 border-r border-border-subtle px-3 py-4 overflow-y-auto">
          <FormatNav
            active={activeFormat}
            content={content}
            onSelect={setActiveFormat}
            episode={{
              title:                 episode.title,
              durationSeconds:       episode.durationSeconds,
              processingCompletedAt: episode.processingCompletedAt,
            }}
          />
        </div>

        {/* Center: content area */}
        <div className="flex-1 overflow-y-auto px-4 lg:px-6 py-5 min-w-0">
          {contentLoading ? (
            <div className="space-y-3 max-w-xl">
              <SkeletonCard />
              <SkeletonCard />
              <SkeletonCard />
            </div>
          ) : content ? (
            <FormatRenderer format={activeFormat} content={content} />
          ) : (
            <p className="text-secondary text-sm">No content available for this episode.</p>
          )}
        </div>

        {/* Right: publish panel (288px, desktop only) */}
        <div className="hidden xl:flex flex-col w-72 shrink-0 border-l border-border-subtle px-4 py-5 overflow-y-auto">
          <PublishPanel episodeId={episodeId} content={content} />
        </div>

      </div>
    </div>
  )
}

/* ─── Route to correct preview component ─── */

function FormatRenderer({ format, content }: { format: FormatKey; content: ContentPack }) {
  const data = content[format as keyof ContentPack]

  if (!data) {
    return (
      <div className="flex items-center justify-center h-48 text-secondary text-sm">
        This format was not generated for this episode.
      </div>
    )
  }

  const dataAsRecord = data as unknown as Record<string, unknown>
  if (typeof data === 'object' && 'error' in dataAsRecord) {
    return (
      <div className="flex items-center justify-center h-48 text-error text-sm">
        Failed to generate this format: {String(dataAsRecord.error)}
      </div>
    )
  }

  switch (format) {
    case 'twitter':       return <TwitterPreview    content={content.twitter!}       />
    case 'linkedin':      return <LinkedInPreview   content={content.linkedin!}      />
    case 'newsletter':    return <NewsletterPreview content={content.newsletter!}    />
    case 'shortVideo':    return <VideoClipsList    content={content.shortVideo!}    />
    case 'blogPost':      return <BlogPreview       content={content.blogPost!}      />
    case 'youtube':       return <YouTubePreview    content={content.youtube!}       />
    case 'quoteCards':    return <QuoteCardPreview  content={content.quoteCards!}    />
    case 'emailSequence': return <EmailPreview      content={content.emailSequence!} />
    default:              return null
  }
}
