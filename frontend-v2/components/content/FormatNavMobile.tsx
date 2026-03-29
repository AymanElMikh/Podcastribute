'use client'

import { useRef } from 'react'
import { cn } from '@/lib/utils'
import { FORMATS } from '@/lib/constants'
import type { FormatKey } from '@/lib/constants'
import type { ContentPack } from '@/lib/types'

interface FormatNavMobileProps {
  active:   FormatKey
  content:  ContentPack | null
  onSelect: (key: FormatKey) => void
}

/**
 * Horizontally-scrollable format picker for mobile/tablet.
 * Shown instead of the sidebar FormatNav on small screens.
 */
export function FormatNavMobile({ active, content, onSelect }: FormatNavMobileProps) {
  const scrollRef = useRef<HTMLDivElement>(null)

  return (
    <div
      ref={scrollRef}
      role="tablist"
      aria-label="Content formats"
      className="flex items-center gap-2 overflow-x-auto scrollbar-none px-4 py-2 border-b border-border-subtle bg-bg-base"
    >
      {FORMATS.map(({ key, label, icon }) => {
        const formatData = content?.[key as keyof ContentPack]
        const hasError   = formatData !== null &&
                           typeof formatData === 'object' &&
                           'error' in (formatData as unknown as Record<string, unknown>)
        const isReady    = formatData != null && !hasError
        const isActive   = active === key

        return (
          <button
            key={key}
            role="tab"
            aria-selected={isActive}
            onClick={() => onSelect(key as FormatKey)}
            className={cn(
              'flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-medium whitespace-nowrap',
              'border transition-all duration-150 shrink-0 cursor-pointer',
              isActive
                ? 'bg-amber/10 border-amber text-amber'
                : 'bg-bg-elevated border-border-subtle text-secondary hover:text-primary hover:border-border-default',
            )}
          >
            <span className="text-sm leading-none" aria-hidden="true">{icon}</span>
            {label}
            {/* Status dot */}
            {content && (
              <span
                className={cn(
                  'size-1.5 rounded-full',
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
    </div>
  )
}

FormatNavMobile.displayName = 'FormatNavMobile'
