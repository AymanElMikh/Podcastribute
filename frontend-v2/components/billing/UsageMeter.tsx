import Link from 'next/link'
import { Progress } from '@/components/ui/Progress'
import { Badge } from '@/components/ui/Badge'
import { Skeleton } from '@/components/ui/Skeleton'
import { PLAN_LABELS } from '@/lib/constants'
import { useAuth } from '@/hooks/useAuth'
import type { Plan } from '@/lib/types'

export function UsageMeter() {
  const { user, isLoading } = useAuth(false)

  if (isLoading) {
    return (
      <div className="space-y-2">
        <Skeleton height="h-4" width="w-32" />
        <Skeleton height="h-1.5" width="w-full" />
      </div>
    )
  }

  if (!user) return null

  const limit      = user.planLimit
  const used       = user.episodesThisMonth
  const pct        = limit ? Math.min(100, Math.round((used / limit) * 100)) : 0
  const planLabel  = PLAN_LABELS[user.plan as Plan]
  const isUnlimited = limit === null
  const isAtLimit  = !isUnlimited && used >= (limit ?? 0)

  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between">
        <span className="text-xs text-secondary">
          {isUnlimited ? 'Unlimited episodes' : `${used} / ${limit} episodes`}
        </span>
        <Badge variant={isAtLimit ? 'error' : 'amber'}>{planLabel}</Badge>
      </div>

      {!isUnlimited && (
        <Progress
          value={pct}
          trackHeight="h-1"
        />
      )}

      {isAtLimit && (
        <p className="text-xs text-error">
          Limit reached.{' '}
          <Link href="/settings/billing" className="underline hover:text-amber transition-colors duration-150">
            Upgrade your plan
          </Link>
        </p>
      )}
    </div>
  )
}

UsageMeter.displayName = 'UsageMeter'
