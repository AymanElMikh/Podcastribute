import { cn } from '@/lib/utils'
import { Badge } from '@/components/ui/Badge'
import { Card } from '@/components/ui/Card'
import type { VoiceProfile } from '@/lib/types'

interface VoiceProfileCardProps {
  profile:   VoiceProfile
  className?: string
}

const FIELD_LABELS: Record<string, string> = {
  vocabularyLevel: 'Vocabulary',
  sentenceStyle:   'Sentence style',
  humorLevel:      'Humor',
  twitterStyle:    'Twitter style',
  linkedinStyle:   'LinkedIn style',
  defaultCtaStyle: 'CTA style',
}

export function VoiceProfileCard({ profile, className }: VoiceProfileCardProps) {
  return (
    <Card className={cn('space-y-5', className)}>
      {/* Scalar fields */}
      <div className="grid grid-cols-2 gap-3">
        {Object.entries(FIELD_LABELS).map(([key, label]) => {
          const value = profile[key as keyof VoiceProfile]
          if (!value || typeof value !== 'string') return null
          return (
            <div key={key}>
              <p className="text-[10px] uppercase tracking-wide text-tertiary mb-0.5">{label}</p>
              <p className="text-sm text-primary capitalize">{value.replace(/_/g, ' ')}</p>
            </div>
          )
        })}
      </div>

      {/* Tone adjectives */}
      {profile.toneAdjectives?.length > 0 && (
        <div>
          <p className="text-[10px] uppercase tracking-wide text-tertiary mb-2">Tone</p>
          <div className="flex flex-wrap gap-1.5">
            {profile.toneAdjectives.map((adj, i) => (
              <Badge key={i} variant="amber">{adj}</Badge>
            ))}
          </div>
        </div>
      )}

      {/* Signature phrases */}
      {profile.signaturePhrases?.length > 0 && (
        <div>
          <p className="text-[10px] uppercase tracking-wide text-tertiary mb-2">Signature phrases</p>
          <div className="flex flex-wrap gap-1.5">
            {profile.signaturePhrases.map((p, i) => (
              <Badge key={i} variant="muted">&ldquo;{p}&rdquo;</Badge>
            ))}
          </div>
        </div>
      )}

      {/* Words to avoid */}
      {profile.wordsToAvoid?.length > 0 && (
        <div>
          <p className="text-[10px] uppercase tracking-wide text-tertiary mb-2">Words to avoid</p>
          <div className="flex flex-wrap gap-1.5">
            {profile.wordsToAvoid.map((w, i) => (
              <Badge key={i} variant="error">{w}</Badge>
            ))}
          </div>
        </div>
      )}
    </Card>
  )
}

VoiceProfileCard.displayName = 'VoiceProfileCard'
