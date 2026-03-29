import { cn } from '@/lib/utils'
import type { PublishStatus } from '@/lib/types'

interface PlatformBadgeProps {
  platform: string
  status?:  PublishStatus | null
}

const PLATFORM_META: Record<string, { label: string; color: string }> = {
  twitter:   { label: 'Twitter / X', color: 'text-[#1d9bf0]' },
  linkedin:  { label: 'LinkedIn',    color: 'text-[#0a66c2]' },
  newsletter:{ label: 'Newsletter',  color: 'text-amber'     },
  buffer:    { label: 'Buffer',      color: 'text-[#168eea]' },
}

export function PlatformBadge({ platform, status }: PlatformBadgeProps) {
  const meta = PLATFORM_META[platform] ?? { label: platform, color: 'text-secondary' }

  return (
    <div className="flex items-center gap-2">
      <span className={cn('text-xs font-medium', meta.color)}>{meta.label}</span>
      {status === 'sent' && (
        <span className="text-[10px] text-success font-medium">✓ Sent</span>
      )}
      {status === 'failed' && (
        <span className="text-[10px] text-error font-medium">✗ Failed</span>
      )}
      {status === 'scheduled' && (
        <span className="text-[10px] text-amber font-medium">⏰ Scheduled</span>
      )}
    </div>
  )
}

PlatformBadge.displayName = 'PlatformBadge'
