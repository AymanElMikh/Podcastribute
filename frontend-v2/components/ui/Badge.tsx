import { cn } from '@/lib/utils'

type BadgeVariant = 'amber' | 'success' | 'error' | 'muted' | 'warm'

export interface BadgeProps {
  variant?: BadgeVariant
  dot?: boolean
}

export function Badge({
  variant = 'amber',
  dot = false,
  className,
  children,
  ...props
}: React.HTMLAttributes<HTMLSpanElement> & BadgeProps) {
  const variantStyles: Record<BadgeVariant, string> = {
    amber:   'bg-amber/10 text-amber border-amber/20',
    success: 'bg-success/10 text-success border-success/20',
    error:   'bg-error/10 text-error border-error/20',
    muted:   'bg-bg-elevated text-secondary border-border-subtle',
    warm:    'bg-warm/10 text-warm border-warm/20',
  }

  const dotColors: Record<BadgeVariant, string> = {
    amber:   'bg-amber',
    success: 'bg-success',
    error:   'bg-error',
    muted:   'bg-secondary',
    warm:    'bg-warm',
  }

  return (
    <span
      className={cn(
        'inline-flex items-center gap-1.5 px-2 py-0.5',
        'text-[11px] font-medium rounded-sm border',
        variantStyles[variant],
        className,
      )}
      {...props}
    >
      {dot && (
        <span
          aria-hidden="true"
          className={cn('size-1.5 rounded-full shrink-0', dotColors[variant])}
        />
      )}
      {children}
    </span>
  )
}

Badge.displayName = 'Badge'
