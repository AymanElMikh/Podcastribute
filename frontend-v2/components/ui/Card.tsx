import { cn } from '@/lib/utils'

export interface CardProps extends React.HTMLAttributes<HTMLDivElement> {
  hoverable?: boolean
  padded?:    boolean
}

function Card({ hoverable = false, padded = true, className, children, ...props }: CardProps) {
  return (
    <div
      className={cn(
        'bg-bg-surface border border-border-subtle rounded-lg',
        'transition-all duration-150',
        hoverable && [
          'cursor-pointer',
          'hover:border-border-default',
          'hover:-translate-y-0.5',
        ],
        padded && 'p-5',
        className,
      )}
      {...props}
    >
      {children}
    </div>
  )
}

Card.displayName = 'Card'

function CardHeader({ className, children, ...props }: React.HTMLAttributes<HTMLDivElement>) {
  return (
    <div className={cn('mb-4', className)} {...props}>
      {children}
    </div>
  )
}
CardHeader.displayName = 'CardHeader'

function CardTitle({ className, children, ...props }: React.HTMLAttributes<HTMLHeadingElement>) {
  return (
    <h3 className={cn('text-lg font-semibold text-primary font-sans', className)} {...props}>
      {children}
    </h3>
  )
}
CardTitle.displayName = 'CardTitle'

function CardDescription({ className, children, ...props }: React.HTMLAttributes<HTMLParagraphElement>) {
  return (
    <p className={cn('text-sm text-secondary mt-1', className)} {...props}>
      {children}
    </p>
  )
}
CardDescription.displayName = 'CardDescription'

function CardFooter({ className, children, ...props }: React.HTMLAttributes<HTMLDivElement>) {
  return (
    <div className={cn('mt-4 pt-4 border-t border-border-subtle', className)} {...props}>
      {children}
    </div>
  )
}
CardFooter.displayName = 'CardFooter'

export { Card, CardHeader, CardTitle, CardDescription, CardFooter }
