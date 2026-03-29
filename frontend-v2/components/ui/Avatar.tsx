import { cn } from '@/lib/utils'

type AvatarSize = 'xs' | 'sm' | 'md' | 'lg' | 'xl'

export interface AvatarProps {
  /** Display name used to generate initials and accessible label. */
  name: string
  src?: string
  size?: AvatarSize
  className?: string
}

const sizeStyles: Record<AvatarSize, string> = {
  xs: 'size-6 text-[10px]',
  sm: 'size-7 text-xs',
  md: 'size-9 text-sm',
  lg: 'size-11 text-base',
  xl: 'size-14 text-lg',
}

function getInitials(name: string): string {
  const parts = name.trim().split(/\s+/)
  if (parts.length === 1) return parts[0].slice(0, 2).toUpperCase()
  return (parts[0][0] + parts[parts.length - 1][0]).toUpperCase()
}

/** Deterministic background color from a name string. */
function getAvatarColor(name: string): string {
  const colors = [
    'bg-amber/20 text-amber',
    'bg-success/20 text-success',
    'bg-warm/20 text-warm',
    'bg-gold/20 text-gold',
  ]
  let hash = 0
  for (let i = 0; i < name.length; i++) hash = name.charCodeAt(i) + ((hash << 5) - hash)
  return colors[Math.abs(hash) % colors.length]
}

export function Avatar({ name, src, size = 'md', className }: AvatarProps) {
  const initials = getInitials(name)
  const colorClass = getAvatarColor(name)

  return (
    <span
      className={cn(
        'inline-flex items-center justify-center rounded-full shrink-0',
        'font-medium font-body select-none',
        sizeStyles[size],
        !src && colorClass,
        className,
      )}
      aria-label={name}
      title={name}
    >
      {src ? (
        // eslint-disable-next-line @next/next/no-img-element
        <img
          src={src}
          alt={name}
          className="size-full rounded-full object-cover"
        />
      ) : (
        <span aria-hidden="true">{initials}</span>
      )}
    </span>
  )
}

Avatar.displayName = 'Avatar'
