import Link from 'next/link'
import { Button } from '@/components/ui/Button'

export function LandingNav() {
  return (
    <header className="fixed top-0 left-0 right-0 z-50 h-14 flex items-center justify-between px-6 lg:px-12 border-b border-border-subtle bg-bg-base/80 backdrop-blur-sm">
      {/* Logo */}
      <Link href="/" className="flex items-baseline gap-0.5">
        <span className="font-display text-xl font-bold text-primary">Podcast</span>
        <span className="font-display text-xl font-bold text-amber">AI</span>
      </Link>

      {/* Nav links */}
      <nav className="hidden md:flex items-center gap-6" aria-label="Main navigation">
        <a href="#how-it-works" className="text-sm text-secondary hover:text-primary transition-colors duration-150">
          How it works
        </a>
        <a href="#formats" className="text-sm text-secondary hover:text-primary transition-colors duration-150">
          Formats
        </a>
        <a href="#pricing" className="text-sm text-secondary hover:text-primary transition-colors duration-150">
          Pricing
        </a>
      </nav>

      {/* CTAs */}
      <div className="flex items-center gap-3">
        <Link href="/login" className="text-sm text-secondary hover:text-primary transition-colors duration-150 hidden sm:block">
          Sign in
        </Link>
        <Button size="sm" asChild>
          <Link href="/register">Get started free</Link>
        </Button>
      </div>
    </header>
  )
}

LandingNav.displayName = 'LandingNav'
