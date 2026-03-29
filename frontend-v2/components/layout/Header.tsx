'use client'

import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { cn } from '@/lib/utils'
import { Button } from '@/components/ui/Button'
import { Avatar } from '@/components/ui/Avatar'
import { useAuth } from '@/hooks/useAuth'
import { clearToken } from '@/lib/utils'
import { useRouter } from 'next/navigation'

/* ─── Breadcrumb label per route ─── */

const ROUTE_LABELS: Record<string, string> = {
  '/dashboard':         'Dashboard',
  '/upload':            'New Episode',
  '/settings':          'Settings',
  '/settings/voice':    'Voice Profile',
  '/settings/billing':  'Billing',
  '/settings/integrations': 'Integrations',
  '/onboarding':        'Get started',
}

function getPageLabel(pathname: string): string {
  if (pathname.startsWith('/content/')) return 'Content Review'
  return ROUTE_LABELS[pathname] ?? 'PodcastAI'
}

/* ─── Component ─── */

export function Header() {
  const pathname = usePathname()
  const { user }  = useAuth(false)
  const router    = useRouter()
  const label     = getPageLabel(pathname)

  const handleSignOut = () => {
    clearToken()
    router.push('/login')
  }

  return (
    <header
      className={cn(
        'h-14 flex items-center justify-between px-5',
        'bg-bg-base border-b border-border-subtle',
        'sticky top-0 z-30',
      )}
    >
      {/* Left: page label */}
      <p className="text-sm font-medium text-secondary">{label}</p>

      {/* Right: actions */}
      <div className="flex items-center gap-3">
        {/* Quick "New Episode" shortcut — hidden on upload page */}
        {pathname !== '/upload' && (
          <Button variant="primary" size="sm" asChild>
            <Link href="/upload">+ New episode</Link>
          </Button>
        )}

        {/* User menu — simple for now, just sign out */}
        {user && (
          <button
            onClick={handleSignOut}
            className={cn(
              'flex items-center gap-2 px-2 py-1 rounded-md',
              'text-secondary hover:text-primary hover:bg-bg-elevated',
              'transition-colors duration-150 text-xs cursor-pointer',
            )}
            aria-label="Sign out"
          >
            <Avatar name={user.email} size="xs" />
            <span className="hidden sm:block max-w-[120px] truncate">{user.email}</span>
          </button>
        )}
      </div>
    </header>
  )
}

Header.displayName = 'Header'
