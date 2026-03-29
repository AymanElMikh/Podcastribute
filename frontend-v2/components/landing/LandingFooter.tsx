import Link from 'next/link'

const LINKS = [
  { label: 'How it works', href: '#how-it-works' },
  { label: 'Formats',      href: '#formats'      },
  { label: 'Pricing',      href: '#pricing'       },
  { label: 'Sign in',      href: '/login'         },
  { label: 'Get started',  href: '/register'      },
]

export function LandingFooter() {
  return (
    <footer className="border-t border-border-subtle py-10 px-6">
      <div className="max-w-5xl mx-auto flex flex-col sm:flex-row items-center justify-between gap-6">
        {/* Brand */}
        <Link href="/" className="flex items-baseline gap-0.5 shrink-0">
          <span className="font-display text-lg font-bold text-primary">Podcast</span>
          <span className="font-display text-lg font-bold text-amber">AI</span>
        </Link>

        {/* Links */}
        <nav className="flex flex-wrap items-center justify-center gap-x-6 gap-y-2" aria-label="Footer navigation">
          {LINKS.map(({ label, href }) => (
            <a
              key={href}
              href={href}
              className="text-sm text-tertiary hover:text-primary transition-colors duration-150"
            >
              {label}
            </a>
          ))}
        </nav>

        {/* Legal */}
        <p className="text-xs text-tertiary shrink-0">
          © {new Date().getFullYear()} PodcastAI
        </p>
      </div>
    </footer>
  )
}

LandingFooter.displayName = 'LandingFooter'
