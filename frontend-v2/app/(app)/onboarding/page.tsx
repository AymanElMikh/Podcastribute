'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import { cn } from '@/lib/utils'
import { Button } from '@/components/ui/Button'
import { VoiceCalibrator } from '@/components/voice/VoiceCalibrator'
import type { VoiceProfile } from '@/lib/types'

type Step = 1 | 2 | 3

const STEPS = [
  { n: 1, label: 'Voice profile' },
  { n: 2, label: 'First upload'  },
  { n: 3, label: 'Review'        },
] as const

export default function OnboardingPage() {
  const router  = useRouter()
  const [step, setStep]         = useState<Step>(1)
  const [profile, setProfile]   = useState<VoiceProfile | null>(null)
  const [skipped, setSkipped]   = useState(false)

  return (
    <div className="max-w-xl mx-auto">
      {/* Step indicator */}
      <div className="flex items-center gap-2 mb-8">
        {STEPS.map(({ n, label }) => (
          <div key={n} className="flex items-center gap-2 flex-1">
            <div className={cn(
              'size-7 rounded-full flex items-center justify-center text-xs font-bold shrink-0',
              step >= n
                ? 'bg-amber text-black'
                : 'bg-bg-elevated text-tertiary border border-border-subtle',
            )}>
              {step > n ? '✓' : n}
            </div>
            <span className={cn(
              'text-xs hidden sm:block truncate',
              step >= n ? 'text-primary' : 'text-tertiary',
            )}>
              {label}
            </span>
            {n < 3 && <div className="flex-1 h-px bg-border-subtle" />}
          </div>
        ))}
      </div>

      {/* Step 1: Voice calibration */}
      {step === 1 && (
        <div className="space-y-6">
          <div>
            <h1 className="text-2xl font-bold text-primary font-display">Welcome to PodcastAI</h1>
            <p className="text-sm text-secondary mt-1">
              First, let&apos;s calibrate the AI to write in your voice. This takes 30 seconds.
            </p>
          </div>

          <VoiceCalibrator
            onSaved={(p) => { setProfile(p); setStep(2) }}
          />

          <div className="text-center">
            <button
              onClick={() => { setSkipped(true); setStep(2) }}
              className="text-xs text-tertiary hover:text-secondary transition-colors duration-150 cursor-pointer"
            >
              Skip for now — I&apos;ll calibrate later
            </button>
          </div>
        </div>
      )}

      {/* Step 2: Upload first episode */}
      {step === 2 && (
        <div className="space-y-6 animate-fade-up">
          <div>
            <h1 className="text-2xl font-bold text-primary font-display">
              {skipped ? 'Upload your first episode' : 'Now upload your first episode'}
            </h1>
            <p className="text-sm text-secondary mt-1">
              {profile
                ? 'Your voice profile is ready. Upload an episode to see it in action.'
                : 'Upload an episode to get 8 content formats in minutes.'}
            </p>
          </div>

          <div className="flex flex-col gap-3">
            <Button size="lg" fullWidth asChild>
              <a href="/upload">Upload an episode →</a>
            </Button>
            <Button variant="ghost" size="sm" onClick={() => router.push('/dashboard')}>
              Skip — go to dashboard
            </Button>
          </div>
        </div>
      )}
    </div>
  )
}
