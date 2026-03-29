'use client'

import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { cn } from '@/lib/utils'
import { Avatar } from '@/components/ui/Avatar'
import { Badge } from '@/components/ui/Badge'
import { Progress } from '@/components/ui/Progress'
import { PLAN_LABELS, PLAN_LIMITS } from '@/lib/constants'
import { useAuth } from '@/hooks/useAuth'
import type { Plan } from '@/lib/types'

/* ─── Nav items ─── */

interface NavItem {
  href:  string
  label: string
  icon:  React.ReactNode
  exact?: boolean
}

const NAV_ITEMS: NavItem[] = [
  {
    href:  '/dashboard',
    label: 'Dashboard',
    icon:  <GridIcon />,
    exact: true,
  },
  {
    href:  '/upload',
    label: 'New Episode',
    icon:  <UploadIcon />,
  },
]

const BOTTOM_NAV_ITEMS: NavItem[] = [
  {
    href:  '/settings',
    label: 'Settings',
    icon:  <GearIcon />,
  },
  {
    href:  '/settings/billing',
    label: 'Billing',
    icon:  <CardIcon />,
  },
]

/* ─── Mobile bottom nav items (4 icons only) ─── */

const MOBILE_NAV: NavItem[] = [
  { href: '/dashboard', label: 'Home',    icon: <GridIcon /> },
  { href: '/upload',    label: 'Upload',  icon: <UploadIcon /> },
  { href: '/settings',  label: 'Settings', icon: <GearIcon /> },
  { href: '/settings/billing', label: 'Billing', icon: <CardIcon /> },
]

/* ─── Component ─── */

export function Sidebar() {
  const pathname = usePathname()
  const { user } = useAuth(false)

  const limit        = user ? PLAN_LIMITS[user.plan as Plan] : null
  const used         = user?.episodesThisMonth ?? 0
  const usagePct     = limit ? Math.round((used / limit) * 100) : 0
  const planLabel    = user ? PLAN_LABELS[user.plan as Plan] : ''
  const showUpgrade  = user?.plan !== 'studio'

  return (
    <>
      {/* ── Desktop sidebar ── */}
      <aside
        aria-label="Main navigation"
        className={cn(
          'hidden lg:flex flex-col',
          'fixed left-0 top-0 bottom-0 w-60',
          'bg-bg-surface border-r border-border-subtle',
          'z-40',
        )}
      >
        {/* Logo */}
        <div className="px-5 py-5 border-b border-border-subtle shrink-0">
          <Link href="/dashboard" className="flex items-baseline gap-0.5">
            <span className="font-display text-xl font-bold text-primary">Podcast</span>
            <span className="font-display text-xl font-bold text-amber">AI</span>
          </Link>
        </div>

        {/* User info */}
        {user && (
          <div className="px-4 py-4 border-b border-border-subtle shrink-0">
            <div className="flex items-center gap-3">
              <Avatar name={user.email} size="sm" />
              <div className="min-w-0 flex-1">
                <p className="text-sm text-primary truncate">{user.email}</p>
                <Badge variant="amber" className="mt-0.5">{planLabel}</Badge>
              </div>
            </div>
          </div>
        )}

        {/* Primary nav */}
        <nav className="flex-1 px-3 py-3 space-y-0.5 overflow-y-auto">
          {NAV_ITEMS.map((item) => (
            <NavLink key={item.href} item={item} pathname={pathname} />
          ))}

          <div className="my-3 border-t border-border-subtle" />

          {BOTTOM_NAV_ITEMS.map((item) => (
            <NavLink key={item.href} item={item} pathname={pathname} />
          ))}
        </nav>

        {/* Usage + upgrade */}
        <div className="px-4 py-4 border-t border-border-subtle shrink-0 space-y-3">
          {user && limit !== null && (
            <Progress
              value={usagePct}
              trackHeight="h-1"
              label={`${used} / ${limit} episodes`}
            />
          )}
          {user && limit === null && (
            <p className="text-xs text-secondary">Unlimited episodes</p>
          )}
          {showUpgrade && (
            <Link
              href="/settings/billing"
              className="text-xs text-amber hover:text-gold transition-colors duration-150"
            >
              Upgrade for more →
            </Link>
          )}
        </div>
      </aside>

      {/* ── Mobile bottom tab bar ── */}
      <nav
        aria-label="Mobile navigation"
        className={cn(
          'lg:hidden fixed bottom-0 left-0 right-0 z-40',
          'bg-bg-surface border-t border-border-subtle',
          'flex items-center justify-around px-2 py-2 safe-area-pb',
        )}
      >
        {MOBILE_NAV.map((item) => {
          const isActive = item.href === '/dashboard'
            ? pathname === item.href
            : pathname.startsWith(item.href)
          return (
            <Link
              key={item.href}
              href={item.href}
              aria-label={item.label}
              className={cn(
                'flex flex-col items-center gap-1 px-3 py-1.5 rounded-md',
                'text-xs transition-colors duration-150',
                isActive ? 'text-amber' : 'text-secondary hover:text-primary',
              )}
            >
              <span className="size-5">{item.icon}</span>
              <span>{item.label}</span>
            </Link>
          )
        })}
      </nav>
    </>
  )
}

Sidebar.displayName = 'Sidebar'

/* ─── NavLink ─── */

function NavLink({ item, pathname }: { item: NavItem; pathname: string }) {
  const isActive = item.exact
    ? pathname === item.href
    : pathname.startsWith(item.href)

  const isUpload = item.href === '/upload'

  return (
    <Link
      href={item.href}
      aria-current={isActive ? 'page' : undefined}
      className={cn(
        'flex items-center gap-3 px-3 py-2 rounded-md text-sm',
        'transition-colors duration-150',
        isActive
          ? 'bg-bg-elevated text-primary'
          : 'text-secondary hover:text-primary hover:bg-bg-elevated',
        // "New Episode" gets the amber accent treatment
        isUpload && !isActive && 'text-amber hover:text-gold',
        isUpload && isActive && 'text-amber bg-amber/10',
      )}
    >
      <span className="size-4 shrink-0">{item.icon}</span>
      {item.label}
    </Link>
  )
}

/* ─── SVG Icons ─── */

function GridIcon() {
  return (
    <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.5" className="size-full">
      <rect x="1" y="1" width="6" height="6" rx="1.5" />
      <rect x="9" y="1" width="6" height="6" rx="1.5" />
      <rect x="1" y="9" width="6" height="6" rx="1.5" />
      <rect x="9" y="9" width="6" height="6" rx="1.5" />
    </svg>
  )
}

function UploadIcon() {
  return (
    <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.5" className="size-full">
      <path d="M8 11V3M5 6l3-3 3 3" strokeLinecap="round" strokeLinejoin="round" />
      <path d="M2 13h12" strokeLinecap="round" />
    </svg>
  )
}

function GearIcon() {
  return (
    <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.5" className="size-full">
      <circle cx="8" cy="8" r="2.5" />
      <path d="M8 1v1.5M8 13.5V15M1 8h1.5M13.5 8H15M3.05 3.05l1.06 1.06M11.89 11.89l1.06 1.06M3.05 12.95l1.06-1.06M11.89 4.11l1.06-1.06" strokeLinecap="round" />
    </svg>
  )
}

function CardIcon() {
  return (
    <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.5" className="size-full">
      <rect x="1" y="3" width="14" height="10" rx="2" />
      <path d="M1 6.5h14" strokeLinecap="round" />
      <path d="M4 10h2M9 10h3" strokeLinecap="round" />
    </svg>
  )
}
