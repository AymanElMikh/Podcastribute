'use client'

import Link from 'next/link'
import { Card } from '@/components/ui/Card'
import { Badge } from '@/components/ui/Badge'
import { Skeleton } from '@/components/ui/Skeleton'
import { UsageMeter } from '@/components/billing/UsageMeter'
import { useAuth } from '@/hooks/useAuth'
import { useEpisodes } from '@/hooks/useEpisodes'
import { STATUS_LABELS } from '@/lib/constants'
import type { EpisodeStatus } from '@/lib/types'

const STATUS_BADGE: Record<EpisodeStatus, 'amber' | 'success' | 'error' | 'muted'> = {
  queued:       'muted',
  transcribing: 'amber',
  detecting:    'amber',
  generating:   'amber',
  ready:        'success',
  error:        'error',
}

export function StatsPanel() {
  const { user, isLoading: authLoading } = useAuth(false)
  const { episodes, isLoading: epLoading } = useEpisodes()

  const isLoading = authLoading || epLoading

  const processing = episodes.filter(
    (e) => ['queued', 'transcribing', 'detecting', 'generating'].includes(e.status),
  )
  const recentReady = episodes
    .filter((e) => e.status === 'ready')
    .slice(0, 3)

  const hasVoiceProfile = !!user?.voiceProfileId

  return (
    <aside className="space-y-4">
      {/* Monthly usage */}
      <Card>
        <p className="text-xs font-semibold text-secondary uppercase tracking-wide mb-3">
          This month
        </p>
        <UsageMeter />
      </Card>

      {/* Processing queue */}
      {(isLoading || processing.length > 0) && (
        <Card>
          <p className="text-xs font-semibold text-secondary uppercase tracking-wide mb-3">
            Processing
          </p>
          {isLoading ? (
            <div className="space-y-2">
              <Skeleton height="h-4" width="w-full" />
              <Skeleton height="h-4" width="w-3/4" />
            </div>
          ) : (
            <ul className="space-y-2">
              {processing.map((ep) => (
                <li key={ep.id} className="flex items-center justify-between gap-2">
                  <span className="text-xs text-primary truncate max-w-[140px]">{ep.title}</span>
                  <Badge variant={STATUS_BADGE[ep.status]} dot>
                    {STATUS_LABELS[ep.status]}
                  </Badge>
                </li>
              ))}
            </ul>
          )}
        </Card>
      )}

      {/* Recent ready episodes */}
      {(isLoading || recentReady.length > 0) && (
        <Card>
          <p className="text-xs font-semibold text-secondary uppercase tracking-wide mb-3">
            Recent content
          </p>
          {isLoading ? (
            <div className="space-y-2">
              <Skeleton height="h-4" width="w-full" />
              <Skeleton height="h-4" width="w-2/3" />
            </div>
          ) : (
            <ul className="space-y-2">
              {recentReady.map((ep) => (
                <li key={ep.id}>
                  <Link
                    href={`/content/${ep.id}`}
                    className="text-xs text-secondary hover:text-primary transition-colors duration-150 truncate block"
                  >
                    → {ep.title}
                  </Link>
                </li>
              ))}
            </ul>
          )}
        </Card>
      )}

      {/* Voice profile status */}
      <Card>
        <p className="text-xs font-semibold text-secondary uppercase tracking-wide mb-3">
          Voice profile
        </p>
        {isLoading ? (
          <Skeleton height="h-4" width="w-28" />
        ) : hasVoiceProfile ? (
          <div className="flex items-center justify-between">
            <Badge variant="success" dot>Calibrated</Badge>
            <Link
              href="/settings/voice"
              className="text-xs text-secondary hover:text-primary transition-colors duration-150"
            >
              Update →
            </Link>
          </div>
        ) : (
          <div className="space-y-2">
            <Badge variant="muted" dot>Not calibrated</Badge>
            <p className="text-xs text-tertiary">
              Calibrate your voice for more personalised content.
            </p>
            <Link
              href="/settings/voice"
              className="text-xs text-amber hover:text-gold transition-colors duration-150"
            >
              Set up voice profile →
            </Link>
          </div>
        )}
      </Card>
    </aside>
  )
}

StatsPanel.displayName = 'StatsPanel'
