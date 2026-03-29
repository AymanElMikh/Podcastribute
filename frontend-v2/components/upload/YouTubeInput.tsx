'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { toast } from 'sonner'
import { cn } from '@/lib/utils'
import { Input } from '@/components/ui/Input'
import { Button } from '@/components/ui/Button'
import { ingestYouTube } from '@/lib/api'
import { APIError } from '@/lib/types'

/* ─── Validation ─── */

const YOUTUBE_RE = /^(https?:\/\/)?(www\.)?(youtube\.com\/watch\?v=|youtu\.be\/)[\w-]{11}/

const schema = z.object({
  url: z
    .string()
    .min(1, 'Paste a YouTube URL')
    .refine((v) => YOUTUBE_RE.test(v), 'That doesn\'t look like a valid YouTube URL'),
})

type FormValues = z.infer<typeof schema>

export function YouTubeInput() {
  const router = useRouter()

  const {
    register,
    handleSubmit,
    watch,
    formState: { errors, isSubmitting },
  } = useForm<FormValues>({ resolver: zodResolver(schema) })

  const url     = watch('url') ?? ''
  const isValid = YOUTUBE_RE.test(url)

  /* Extract video ID for thumbnail preview */
  const videoId = (() => {
    const m = url.match(/(?:v=|youtu\.be\/)([\w-]{11})/)
    return m ? m[1] : null
  })()

  const onSubmit = async (values: FormValues) => {
    try {
      const { episode_id } = await ingestYouTube(values.url)
      router.push(`/content/${episode_id}`)
    } catch (err) {
      const msg = err instanceof APIError ? err.message : 'Failed to process YouTube URL'
      toast.error('YouTube ingestion failed', { description: msg })
    }
  }

  return (
    <form onSubmit={handleSubmit(onSubmit)} noValidate className="space-y-5">
      <div className="space-y-2">
        <Input
          label="YouTube URL"
          type="url"
          placeholder="https://youtube.com/watch?v=..."
          error={errors.url?.message}
          leftIcon={<YouTubeIcon />}
          {...register('url')}
        />
        <p className="text-xs text-tertiary">
          Paste the full URL of any YouTube podcast episode or video.
        </p>
      </div>

      {/* Video preview — shown when URL is valid */}
      {isValid && videoId && (
        <div
          className={cn(
            'flex items-center gap-3 p-3 rounded-lg',
            'bg-bg-elevated border border-border-subtle',
            'animate-fade-up',
          )}
        >
          {/* Thumbnail */}
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img
            src={`https://img.youtube.com/vi/${videoId}/mqdefault.jpg`}
            alt="Video thumbnail"
            className="w-20 h-14 rounded object-cover shrink-0 bg-bg-surface"
          />
          <div className="min-w-0">
            <p className="text-xs text-secondary">YouTube video detected</p>
            <p className="text-xs font-mono text-tertiary mt-0.5 truncate">
              ID: {videoId}
            </p>
          </div>
        </div>
      )}

      <Button
        type="submit"
        fullWidth
        size="lg"
        loading={isSubmitting}
        disabled={!isValid}
      >
        Process episode
      </Button>
    </form>
  )
}

YouTubeInput.displayName = 'YouTubeInput'

function YouTubeIcon() {
  return (
    <svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor">
      <path d="M23 7s-.3-2-1.2-2.8c-1.1-1.2-2.4-1.2-3-1.3C16.1 2.8 12 2.8 12 2.8s-4.1 0-6.8.2c-.6.1-1.9.1-3 1.3C1.3 5 1 7 1 7S.7 9.1.7 11.3v2c0 2.1.3 4.3.3 4.3s.3 2 1.2 2.8c1.1 1.2 2.6 1.1 3.3 1.2C7.4 21.9 12 22 12 22s4.1 0 6.8-.3c.6-.1 1.9-.1 3-1.3.9-.8 1.2-2.8 1.2-2.8s.3-2.1.3-4.3v-2C23.3 9.1 23 7 23 7zM9.7 15.5V8.4l8.1 3.6-8.1 3.5z" />
    </svg>
  )
}
