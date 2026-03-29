import { cn } from '@/lib/utils'

export interface PageHeaderProps {
  title:        string
  description?: string
  /** Slot for right-side actions (buttons, etc.) */
  actions?:     React.ReactNode
  className?:   string
}

/**
 * Per-page top header — sits below the global <Header /> inside the main content area.
 * Used on every app page for consistent title + action layout.
 */
export function PageHeader({ title, description, actions, className }: PageHeaderProps) {
  return (
    <div
      className={cn(
        'flex items-start justify-between gap-4 mb-6',
        className,
      )}
    >
      <div>
        <h1 className="text-2xl font-bold text-primary font-display">{title}</h1>
        {description && (
          <p className="text-sm text-secondary mt-1">{description}</p>
        )}
      </div>

      {actions && (
        <div className="flex items-center gap-2 shrink-0">{actions}</div>
      )}
    </div>
  )
}

PageHeader.displayName = 'PageHeader'
