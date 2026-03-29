'use client'

import { useRef, useState, useCallback } from 'react'
import { useRouter } from 'next/navigation'
import { cn } from '@/lib/utils'
import { Button } from '@/components/ui/Button'
import { Progress } from '@/components/ui/Progress'
import { useUpload } from '@/hooks/useUpload'
import { ACCEPTED_AUDIO_TYPES, MAX_UPLOAD_MB } from '@/lib/constants'

export function UploadZone() {
  const router                    = useRouter()
  const inputRef                  = useRef<HTMLInputElement>(null)
  const [isDragging, setDragging] = useState(false)
  const { upload, progress, status, error, reset } = useUpload()

  /* ── Drag handlers ── */
  const onDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault()          // required to allow drop
    e.stopPropagation()
    setDragging(true)
  }, [])

  const onDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    setDragging(false)
  }, [])

  const onDrop = useCallback(
    async (e: React.DragEvent) => {
      e.preventDefault()        // prevent browser from opening the file
      e.stopPropagation()
      setDragging(false)

      const file = e.dataTransfer.files[0]
      if (!file) return

      const id = await upload(file)
      if (id) router.push(`/content/${id}`)
    },
    [upload, router],
  )

  /* ── Click to browse ── */
  const onFileChange = useCallback(
    async (e: React.ChangeEvent<HTMLInputElement>) => {
      const file = e.target.files?.[0]
      if (!file) return

      const id = await upload(file)
      if (id) router.push(`/content/${id}`)

      // Reset input so the same file can be re-selected
      e.target.value = ''
    },
    [upload, router],
  )

  const isUploading = status === 'uploading' || status === 'validating'
  const isDone      = status === 'done'
  const isError     = status === 'error'
  const isIdle      = status === 'idle'

  return (
    <div className="space-y-4">
      {/* Drop zone */}
      <div
        role="button"
        tabIndex={0}
        aria-label="Upload audio file — click or drag and drop"
        onClick={() => !isUploading && inputRef.current?.click()}
        onKeyDown={(e) => e.key === 'Enter' && !isUploading && inputRef.current?.click()}
        onDragOver={onDragOver}
        onDragLeave={onDragLeave}
        onDrop={onDrop}
        className={cn(
          'relative flex flex-col items-center justify-center',
          'h-56 rounded-xl border-2 border-dashed',
          'transition-all duration-200 select-none',
          isIdle && !isDragging &&
            'border-border-default hover:border-amber hover:bg-amber/5 cursor-pointer',
          isDragging  && 'border-amber bg-amber/10 scale-[1.01]',
          isUploading && 'border-border-subtle bg-bg-elevated cursor-default',
          isDone      && 'border-success/40 bg-success/5 cursor-default',
          isError     && 'border-error/40 bg-error/5 cursor-pointer',
        )}
      >
        {/* Hidden file input */}
        <input
          ref={inputRef}
          type="file"
          accept={ACCEPTED_AUDIO_TYPES.join(',')}
          onChange={onFileChange}
          className="sr-only"
          aria-hidden="true"
          tabIndex={-1}
        />

        {/* Idle / dragging state */}
        {(isIdle || isDragging) && (
          <div className="flex flex-col items-center gap-3 pointer-events-none">
            <div className={cn(
              'size-12 rounded-full flex items-center justify-center',
              isDragging ? 'bg-amber/20' : 'bg-bg-elevated',
            )}>
              <WaveformIcon className={cn('size-6', isDragging ? 'text-amber' : 'text-tertiary')} />
            </div>
            <div className="text-center">
              <p className={cn('text-sm font-medium', isDragging ? 'text-amber' : 'text-primary')}>
                {isDragging ? 'Drop it here' : 'Drop your episode here'}
              </p>
              <p className="text-xs text-tertiary mt-1">
                MP3, MP4, WAV, M4A · up to {MAX_UPLOAD_MB} MB
              </p>
            </div>
            {!isDragging && (
              <Button variant="secondary" size="sm" className="pointer-events-none">
                Browse files
              </Button>
            )}
          </div>
        )}

        {/* Uploading state */}
        {isUploading && (
          <div className="flex flex-col items-center gap-4 w-full px-8 pointer-events-none">
            <div className="size-12 rounded-full bg-amber/10 flex items-center justify-center">
              <UploadingIcon className="size-6 text-amber animate-pulse-amber" />
            </div>
            <div className="w-full space-y-2">
              <Progress value={progress} showPct trackHeight="h-1.5" />
              <p className="text-xs text-center text-secondary">
                {status === 'validating' ? 'Validating file…' : 'Uploading…'}
              </p>
            </div>
          </div>
        )}

        {/* Done state */}
        {isDone && (
          <div className="flex flex-col items-center gap-3 pointer-events-none">
            <div className="size-12 rounded-full bg-success/10 flex items-center justify-center">
              <CheckIcon className="size-6 text-success" />
            </div>
            <p className="text-sm font-medium text-success">Upload complete!</p>
            <p className="text-xs text-secondary">Redirecting to processing view…</p>
          </div>
        )}

        {/* Error state */}
        {isError && (
          <div className="flex flex-col items-center gap-3 px-6 text-center">
            <div className="size-12 rounded-full bg-error/10 flex items-center justify-center">
              <ErrorIcon className="size-6 text-error" />
            </div>
            <div>
              <p className="text-sm font-medium text-error">Upload failed</p>
              {error && <p className="text-xs text-secondary mt-1">{error}</p>}
            </div>
            <Button variant="secondary" size="sm" onClick={(e) => { e.stopPropagation(); reset() }}>
              Try again
            </Button>
          </div>
        )}
      </div>
    </div>
  )
}

UploadZone.displayName = 'UploadZone'

/* ─── Icons ─── */

function WaveformIcon({ className }: { className?: string }) {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" className={className}>
      <path d="M2 12h2M6 8v8M10 5v14M14 9v6M18 7v10M22 12h-2" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  )
}

function UploadingIcon({ className }: { className?: string }) {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" className={className}>
      <path d="M12 16V8M9 11l3-3 3 3" strokeLinecap="round" strokeLinejoin="round" />
      <path d="M3 16.5A3.5 3.5 0 0 0 6.5 20h11A3.5 3.5 0 0 0 21 16.5" strokeLinecap="round" />
    </svg>
  )
}

function CheckIcon({ className }: { className?: string }) {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className={className}>
      <path d="M5 13l4 4L19 7" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  )
}

function ErrorIcon({ className }: { className?: string }) {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" className={className}>
      <circle cx="12" cy="12" r="9" />
      <path d="M12 8v4M12 16h.01" strokeLinecap="round" />
    </svg>
  )
}
