'use client'

import { cn } from '@/lib/utils'
import { FORMATS } from '@/lib/constants'
import type { FormatKey } from '@/lib/constants'
import type { ContentPack } from '@/lib/types'

interface FormatNavProps {
  active:      FormatKey
  content:     ContentPack | null
  onSelect:    (key: FormatKey) => void
  episode?:    { title: string; durationSeconds?: number; processingCompletedAt?: string }
}

export function FormatNav({ active, content, onSelect, episode }: FormatNavProps) {
  return (
    <aside className="flex flex-col gap-1" aria-label="Content formats">
      <p className="text-xs font-semibold text-secondary uppercase tracking-wide px-2 mb-1">
        Content formats
      </p>

      {FORMATS.map(({ key, label, icon }) => {
        const formatData = content?.[key as keyof ContentPack]
        const hasError   = formatData !== null && typeof formatData === 'object' &&
                           'error' in (formatData as unknown as Record<string, unknown>)
        const isReady    = formatData !== null && formatData !== undefined && !hasError
        const isActive   = active === key

        return (
          <button
            key={key}
            onClick={() => onSelect(key as FormatKey)}
            aria-current={isActive ? 'true' : undefined}
            className={cn(
              'flex items-center gap-3 px-3 py-2 rounded-lg text-sm text-left',
              'transition-all duration-150 cursor-pointer w-full',
              'border border-transparent',
              isActive
                ? 'bg-bg-elevated border-border-default text-primary border-l-2 border-l-amber'
                : 'text-secondary hover:text-primary hover:bg-bg-elevated',
            )}
          >
            <span className="shrink-0 size-4 flex items-center justify-center text-base leading-none" aria-hidden="true">
              {icon}
            </span>
            <span className="flex-1 truncate">{label}</span>
            {/* Status dot */}
            {content && (
              <span
                className={cn(
                  'size-1.5 rounded-full shrink-0',
                  isReady  && 'bg-success',
                  hasError && 'bg-error',
                  !isReady && !hasError && 'bg-tertiary',
                )}
                aria-label={isReady ? 'Ready' : hasError ? 'Error' : 'Unavailable'}
              />
            )}
          </button>
        )
      })}

      {/* Episode info */}
      {episode && (
        <>
          <div className="my-2 border-t border-border-subtle" />
          <div className="px-3 space-y-1">
            <p className="text-xs font-semibold text-secondary uppercase tracking-wide mb-1">
              Episode
            </p>
            <p className="text-xs text-primary leading-snug line-clamp-2">{episode.title}</p>
            {episode.durationSeconds != null && (
              <p className="text-xs font-mono text-tertiary">
                {Math.floor(episode.durationSeconds / 60)}m {episode.durationSeconds % 60}s
              </p>
            )}
          </div>
        </>
      )}
    </aside>
  )
}

FormatNav.displayName = 'FormatNav'
