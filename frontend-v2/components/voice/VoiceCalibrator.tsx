'use client'

import { useState } from 'react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { toast } from 'sonner'
import { cn } from '@/lib/utils'
import { Button } from '@/components/ui/Button'
import { VoiceProfileCard } from './VoiceProfileCard'
import { calibrateVoice, calibrateVoiceFromTranscripts, refineVoice } from '@/lib/api'
import { APIError } from '@/lib/types'
import type { VoiceProfile } from '@/lib/types'

type Method = 'posts' | 'episodes' | null
type Step   = 'choose' | 'input' | 'result'

/* ─── Social posts schema ─── */

const postsSchema = z.object({
  post1: z.string().min(20, 'Post must be at least 20 characters'),
  post2: z.string().min(20, 'Post must be at least 20 characters'),
  post3: z.string().min(20, 'Post must be at least 20 characters'),
  post4: z.string().optional(),
  post5: z.string().optional(),
})
type PostsForm = z.infer<typeof postsSchema>

/* ─── Refinement schema ─── */

const refineSchema = z.object({
  feedback: z.string().min(10, 'Please describe what to change'),
})
type RefineForm = z.infer<typeof refineSchema>

/* ─── Component ─── */

interface VoiceCalibratorProps {
  existing?: VoiceProfile | null
  onSaved?:  (profile: VoiceProfile) => void
}

export function VoiceCalibrator({ existing, onSaved }: VoiceCalibratorProps) {
  const [step,    setStep]    = useState<Step>(existing ? 'result' : 'choose')
  const [method,  setMethod]  = useState<Method>(null)
  const [profile, setProfile] = useState<VoiceProfile | null>(existing ?? null)
  const [loading, setLoading] = useState(false)

  /* ─── Posts form ─── */
  const postsForm = useForm<PostsForm>({ resolver: zodResolver(postsSchema) })
  const refineForm = useForm<RefineForm>({ resolver: zodResolver(refineSchema) })

  const onSubmitPosts = async (values: PostsForm) => {
    setLoading(true)
    try {
      const posts = [values.post1, values.post2, values.post3, values.post4, values.post5]
        .filter((p): p is string => !!p && p.length > 0)
      const result = await calibrateVoice(posts)
      setProfile(result)
      setStep('result')
      onSaved?.(result)
      toast.success('Voice profile calibrated!')
    } catch (err) {
      const msg = err instanceof APIError ? err.message : 'Calibration failed'
      toast.error('Calibration failed', { description: msg })
    } finally {
      setLoading(false)
    }
  }

  const onRefine = async (values: RefineForm) => {
    setLoading(true)
    try {
      const result = await refineVoice(values.feedback)
      setProfile(result)
      onSaved?.(result)
      toast.success('Voice profile updated!')
      refineForm.reset()
    } catch (err) {
      const msg = err instanceof APIError ? err.message : 'Refinement failed'
      toast.error('Refinement failed', { description: msg })
    } finally {
      setLoading(false)
    }
  }

  /* ─── STEP: Choose method ─── */
  if (step === 'choose') {
    return (
      <div className="space-y-4 animate-fade-up">
        <p className="text-sm text-secondary">
          How would you like to calibrate your voice profile?
        </p>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          {/* Social posts option */}
          <button
            onClick={() => { setMethod('posts'); setStep('input') }}
            className={cn(
              'flex flex-col gap-3 p-5 rounded-xl border text-left',
              'bg-bg-surface border-border-default',
              'hover:border-amber hover:bg-amber/5',
              'transition-all duration-150 cursor-pointer',
            )}
          >
            <div className="size-10 rounded-lg bg-amber/10 flex items-center justify-center text-amber text-lg">
              ✍
            </div>
            <div>
              <p className="text-sm font-semibold text-primary">Use social posts</p>
              <p className="text-xs text-secondary mt-1">
                Paste 3–5 existing posts or tweets. Fastest option — done in 30 seconds.
              </p>
            </div>
            <Badge className="self-start">Fastest</Badge>
          </button>

          {/* Past episodes option */}
          <button
            onClick={() => { setMethod('episodes'); setStep('input') }}
            className={cn(
              'flex flex-col gap-3 p-5 rounded-xl border text-left',
              'bg-bg-surface border-border-default',
              'hover:border-amber hover:bg-amber/5',
              'transition-all duration-150 cursor-pointer',
            )}
          >
            <div className="size-10 rounded-lg bg-bg-elevated flex items-center justify-center text-secondary text-lg">
              🎙
            </div>
            <div>
              <p className="text-sm font-semibold text-primary">Use past episodes</p>
              <p className="text-xs text-secondary mt-1">
                Upload 2–3 old episode transcripts for the most accurate profile.
              </p>
            </div>
            <Badge variant="muted" className="self-start">Most accurate</Badge>
          </button>
        </div>

        {existing && (
          <Button variant="ghost" size="sm" onClick={() => setStep('result')}>
            ← Back to current profile
          </Button>
        )}
      </div>
    )
  }

  /* ─── STEP: Input ─── */
  if (step === 'input' && method === 'posts') {
    return (
      <form
        onSubmit={postsForm.handleSubmit(onSubmitPosts)}
        noValidate
        className="space-y-4 animate-fade-up"
      >
        <div className="flex items-center justify-between">
          <p className="text-sm text-secondary">
            Paste 3–5 posts that represent how you write online.
          </p>
          <Button variant="ghost" size="sm" type="button" onClick={() => setStep('choose')}>
            ← Back
          </Button>
        </div>

        {([
          { name: 'post1' as const, label: 'Post 1', required: true  },
          { name: 'post2' as const, label: 'Post 2', required: true  },
          { name: 'post3' as const, label: 'Post 3', required: true  },
          { name: 'post4' as const, label: 'Post 4', required: false },
          { name: 'post5' as const, label: 'Post 5', required: false },
        ]).map(({ name, label, required }) => (
          <div key={name} className="space-y-1.5">
            <label className="text-xs font-medium text-secondary uppercase tracking-wide flex items-center gap-1.5">
              {label}
              {!required && <span className="text-tertiary normal-case font-normal">(optional)</span>}
            </label>
            <textarea
              {...postsForm.register(name)}
              rows={3}
              placeholder="Paste a tweet, LinkedIn post, or any text that sounds like you…"
              className={cn(
                'w-full px-3 py-2.5 rounded-lg text-sm text-primary',
                'bg-bg-elevated border border-border-subtle',
                'placeholder:text-tertiary resize-none',
                'focus:outline-none focus:border-amber transition-colors duration-150',
                postsForm.formState.errors[name] && 'border-error',
              )}
            />
            {postsForm.formState.errors[name] && (
              <p className="text-xs text-error">{postsForm.formState.errors[name]?.message}</p>
            )}
          </div>
        ))}

        <Button type="submit" fullWidth size="lg" loading={loading}>
          Analyze my voice
        </Button>
      </form>
    )
  }

  if (step === 'input' && method === 'episodes') {
    return (
      <div className="space-y-4 animate-fade-up">
        <div className="flex items-center justify-between">
          <p className="text-sm text-secondary">
            Paste transcripts from 2–3 past episodes.
          </p>
          <Button variant="ghost" size="sm" onClick={() => setStep('choose')}>← Back</Button>
        </div>
        <TranscriptInput
          onSubmit={async (transcripts) => {
            setLoading(true)
            try {
              const result = await calibrateVoiceFromTranscripts(transcripts)
              setProfile(result)
              setStep('result')
              onSaved?.(result)
              toast.success('Voice profile calibrated!')
            } catch (err) {
              const msg = err instanceof APIError ? err.message : 'Calibration failed'
              toast.error('Calibration failed', { description: msg })
            } finally {
              setLoading(false)
            }
          }}
          loading={loading}
        />
      </div>
    )
  }

  /* ─── STEP: Result ─── */
  if (step === 'result' && profile) {
    return (
      <div className="space-y-5 animate-fade-up">
        <div className="flex items-center justify-between">
          <p className="text-sm font-medium text-primary">Your voice profile</p>
          <Button variant="secondary" size="sm" onClick={() => setStep('choose')}>
            Recalibrate
          </Button>
        </div>

        <VoiceProfileCard profile={profile} />

        {/* Refinement */}
        <div className="pt-2 border-t border-border-subtle">
          <p className="text-xs font-semibold text-secondary uppercase tracking-wide mb-3">
            Refine your profile
          </p>
          <form onSubmit={refineForm.handleSubmit(onRefine)} noValidate className="space-y-3">
            <textarea
              {...refineForm.register('feedback')}
              rows={2}
              placeholder='e.g. "I never use corporate buzzwords" or "Make it more casual and direct"'
              className={cn(
                'w-full px-3 py-2.5 rounded-lg text-sm text-primary',
                'bg-bg-elevated border border-border-subtle',
                'placeholder:text-tertiary resize-none',
                'focus:outline-none focus:border-amber transition-colors duration-150',
              )}
            />
            {refineForm.formState.errors.feedback && (
              <p className="text-xs text-error">{refineForm.formState.errors.feedback.message}</p>
            )}
            <Button type="submit" variant="secondary" size="sm" loading={loading}>
              Update voice
            </Button>
          </form>
        </div>
      </div>
    )
  }

  return null
}

VoiceCalibrator.displayName = 'VoiceCalibrator'

/* ─── Badge import fix ─── */
import { Badge } from '@/components/ui/Badge'

/* ─── Transcript input sub-component ─── */

function TranscriptInput({
  onSubmit,
  loading,
}: {
  onSubmit: (transcripts: string[]) => void
  loading:  boolean
}) {
  const [texts, setTexts] = useState(['', '', ''])

  const updateText = (i: number, v: string) =>
    setTexts((prev) => prev.map((t, j) => (j === i ? v : t)))

  const filled = texts.filter((t) => t.trim().length > 100)

  return (
    <div className="space-y-3">
      {texts.map((text, i) => (
        <div key={i} className="space-y-1.5">
          <label className="text-xs font-medium text-secondary uppercase tracking-wide flex items-center gap-1.5">
            Transcript {i + 1}
            {i > 1 && <span className="text-tertiary normal-case font-normal">(optional)</span>}
          </label>
          <textarea
            value={text}
            onChange={(e) => updateText(i, e.target.value)}
            rows={4}
            placeholder="Paste transcript text here (at least 100 characters)…"
            className={cn(
              'w-full px-3 py-2.5 rounded-lg text-sm text-primary',
              'bg-bg-elevated border border-border-subtle',
              'placeholder:text-tertiary resize-none',
              'focus:outline-none focus:border-amber transition-colors duration-150',
            )}
          />
        </div>
      ))}
      <Button
        fullWidth
        size="lg"
        loading={loading}
        disabled={filled.length < 1}
        onClick={() => onSubmit(texts.filter((t) => t.trim().length > 0))}
      >
        Analyze my voice
      </Button>
    </div>
  )
}
