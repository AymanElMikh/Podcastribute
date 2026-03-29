import Link from 'next/link'

/**
 * Auth pages layout — no sidebar.
 * Centers the form card on the dark background with the brand logo above.
 */
export default function AuthLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="min-h-screen bg-bg-base flex flex-col items-center justify-center px-4">
      {/* Brand logo */}
      <Link href="/" className="mb-8 flex items-baseline gap-0.5">
        <span className="font-display text-2xl font-bold text-primary">Podcast</span>
        <span className="font-display text-2xl font-bold text-amber">AI</span>
      </Link>

      {/* Form card */}
      <div className="w-full max-w-sm bg-bg-surface border border-border-subtle rounded-xl p-8">
        {children}
      </div>

      {/* Footer */}
      <p className="mt-6 text-xs text-tertiary">
        Made for podcasters who care about their content.
      </p>
    </div>
  )
}
