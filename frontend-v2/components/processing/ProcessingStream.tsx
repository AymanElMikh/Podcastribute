'use client'

import { useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { cn } from '@/lib/utils'
import { Button } from '@/components/ui/Button'
import { useSSE } from '@/hooks/useSSE'
import { SSE_STEP_LABELS } from '@/lib/constants'

/* ─── Ordered pipeline steps ─── */

const PIPELINE_STEPS = [
  'upload_received',
  'transcription_start',
  'transcription_done',
  'moments_detected',
  'generating_content',
  'content_ready',
] as const

type StepKey = typeof PIPELINE_STEPS[number]

type StepState = 'done' | 'active' | 'pending'

function getStepState(
  stepKey: StepKey,
  arrivedTypes: Set<string>,
  sseStatus: 'idle' | 'connecting' | 'streaming' | 'done' | 'error',
): StepState {
  if (arrivedTypes.has(stepKey)) return 'done'

  // Find the last arrived step's index
  const lastDoneIndex = [...PIPELINE_STEPS]
    .map((k, i) => (arrivedTypes.has(k) ? i : -1))
    .filter((i) => i !== -1)
    .at(-1) ?? -1

  const thisIndex = PIPELINE_STEPS.indexOf(stepKey)

  if (sseStatus === 'connecting' && thisIndex === 0) return 'active'
  if (thisIndex === lastDoneIndex + 1 && sseStatus !== 'done') return 'active'

  return 'pending'
}

/* ─── Component ─── */

interface ProcessingStreamProps {
  episodeId: string
  title:     string
}

export function ProcessingStream({ episodeId, title }: ProcessingStreamProps) {
  const router = useRouter()
  const { events, status } = useSSE(episodeId)

  const arrivedTypes = new Set(events.map((e) => e.type))
  const isDone       = status === 'done'
  const isError      = status === 'error'

  // Auto-redirect on completion
  useEffect(() => {
    if (!isDone) return
    const t = setTimeout(() => router.push(`/content/${episodeId}?view=ready`), 1200)
    return () => clearTimeout(t)
  }, [isDone, episodeId, router])

  // Error event label
  const errorEvent = events.find((e) => e.type === 'error')
  const errorMsg   =
    (errorEvent?.data as { message?: string } | undefined)?.message ??
    'Something went wrong during processing.'

  return (
    <div className="max-w-lg mx-auto py-8 animate-fade-up">
      {/* Episode title */}
      <p className="text-sm text-secondary text-center mb-8 truncate">{title}</p>

      {/* Step list */}
      <ol className="space-y-1" aria-label="Processing steps">
        {PIPELINE_STEPS.map((key) => {
          const state = getStepState(key, arrivedTypes, status)
          const label = SSE_STEP_LABELS[key] ?? key

          return (
            <li
              key={key}
              className={cn(
                'flex items-center gap-3 px-4 py-2.5 rounded-lg transition-all duration-300',
                state === 'active' && 'bg-amber/5',
              )}
            >
              {/* Step indicator */}
              <span className="shrink-0 size-5 flex items-center justify-center">
                {state === 'done' && <CheckCircleIcon />}
                {state === 'active' && <SpinnerIcon />}
                {state === 'pending' && <PendingDot />}
              </span>

              {/* Label */}
              <span
                className={cn(
                  'text-sm transition-colors duration-300',
                  state === 'done'    && 'text-secondary line-through decoration-border-default',
                  state === 'active'  && 'text-primary font-medium',
                  state === 'pending' && 'text-tertiary',
                )}
              >
                {label}
              </span>
            </li>
          )
        })}
      </ol>

      {/* Complete state */}
      {isDone && (
        <div className="mt-8 flex flex-col items-center gap-4 animate-fade-up">
          <div className="size-12 rounded-full bg-success/10 flex items-center justify-center">
            <BigCheckIcon />
          </div>
          <p className="text-base font-semibold text-success">All content ready!</p>
          <p className="text-xs text-tertiary">Redirecting you now…</p>
        </div>
      )}

      {/* Error state */}
      {isError && (
        <div className="mt-8 flex flex-col items-center gap-4 animate-fade-up">
          <div className="size-12 rounded-full bg-error/10 flex items-center justify-center">
            <ErrorIcon />
          </div>
          <div className="text-center">
            <p className="text-base font-semibold text-error">Processing failed</p>
            <p className="text-xs text-secondary mt-1 max-w-xs">{errorMsg}</p>
          </div>
          <Button variant="secondary" size="sm" onClick={() => router.push('/upload')}>
            Try again
          </Button>
        </div>
      )}

      {/* Hint */}
      {!isDone && !isError && (
        <p className="text-center text-xs text-tertiary mt-8">
          Processing takes 2–5 minutes for a 1-hour episode
        </p>
      )}
    </div>
  )
}

ProcessingStream.displayName = 'ProcessingStream'

/* ─── Step icons ─── */

function CheckCircleIcon() {
  return (
    <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
      <circle cx="10" cy="10" r="9" stroke="#22C55E" strokeWidth="1.5" />
      <path d="M6.5 10l2.5 2.5 5-5" stroke="#22C55E" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  )
}

function SpinnerIcon() {
  return (
    <svg width="20" height="20" viewBox="0 0 20 20" fill="none" className="animate-spin-slow">
      <circle cx="10" cy="10" r="8" stroke="var(--border-default)" strokeWidth="2" />
      <path d="M10 2a8 8 0 0 1 8 8" stroke="var(--accent-amber)" strokeWidth="2" strokeLinecap="round" />
    </svg>
  )
}

function PendingDot() {
  return (
    <span className="size-2 rounded-full bg-border-default mx-auto block" aria-hidden="true" />
  )
}

function BigCheckIcon() {
  return (
    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#22C55E" strokeWidth="2">
      <path d="M5 13l4 4L19 7" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  )
}

function ErrorIcon() {
  return (
    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#EF4444" strokeWidth="1.5">
      <circle cx="12" cy="12" r="9" />
      <path d="M12 8v4M12 16h.01" strokeLinecap="round" />
    </svg>
  )
}
