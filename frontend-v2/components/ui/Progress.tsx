import { cn } from '@/lib/utils'

export interface ProgressProps extends React.HTMLAttributes<HTMLDivElement> {
  /** 0–100 */
  value: number
  /** Height class, e.g. "h-1", "h-2". Defaults to "h-1.5". */
  trackHeight?: string
  /** Show a label above the bar (e.g. "3 / 4 episodes") */
  label?: string
  /** Show the percentage to the right */
  showPct?: boolean
  /** Animate the fill (useful for indeterminate progress). */
  indeterminate?: boolean
}

export function Progress({
  value,
  trackHeight = 'h-1.5',
  label,
  showPct = false,
  indeterminate = false,
  className,
  ...props
}: ProgressProps) {
  const clamped = Math.min(100, Math.max(0, value))

  return (
    <div className={cn('flex flex-col gap-1.5', className)} {...props}>
      {(label || showPct) && (
        <div className="flex items-center justify-between">
          {label && <span className="text-xs text-secondary">{label}</span>}
          {showPct && (
            <span className="text-xs font-mono text-tertiary">{clamped}%</span>
          )}
        </div>
      )}

      <div
        role="progressbar"
        aria-valuenow={indeterminate ? undefined : clamped}
        aria-valuemin={0}
        aria-valuemax={100}
        className={cn(
          'w-full rounded-full bg-bg-elevated overflow-hidden',
          trackHeight,
        )}
      >
        <div
          className={cn(
            'h-full rounded-full bg-amber transition-all duration-300 ease-out',
            indeterminate && 'animate-pulse-amber',
          )}
          style={{ width: indeterminate ? '40%' : `${clamped}%` }}
        />
      </div>
    </div>
  )
}

Progress.displayName = 'Progress'
