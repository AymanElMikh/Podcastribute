import { cn } from '@/lib/utils'

export interface SkeletonProps extends React.HTMLAttributes<HTMLDivElement> {
  /** Width, e.g. "w-32", "w-full" */
  width?: string
  /** Height, e.g. "h-4", "h-10" */
  height?: string
  /** Make it circular (for avatars). */
  circle?: boolean
}

export function Skeleton({ width, height, circle = false, className, ...props }: SkeletonProps) {
  return (
    <div
      aria-hidden="true"
      className={cn(
        'bg-bg-elevated animate-shimmer rounded-md',
        circle && 'rounded-full',
        width,
        height,
        className,
      )}
      {...props}
    />
  )
}

Skeleton.displayName = 'Skeleton'

/** Skeleton for a single text line. */
export function SkeletonLine({ className }: { className?: string }) {
  return <Skeleton height="h-4" className={cn('w-full', className)} />
}

/** Skeleton for a card with title + description lines. */
export function SkeletonCard({ className }: { className?: string }) {
  return (
    <div className={cn('bg-bg-surface border border-border-subtle rounded-lg p-5 space-y-3', className)}>
      <Skeleton height="h-5" width="w-2/5" />
      <Skeleton height="h-3" width="w-full" />
      <Skeleton height="h-3" width="w-3/4" />
    </div>
  )
}
