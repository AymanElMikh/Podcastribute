import Link from 'next/link'
import { Button } from '@/components/ui/Button'
import { WaveformAnimation } from './WaveformAnimation'

const SOCIAL_PROOF = [
  'My First Million', 'How I Built This', 'Acquired', 'Huberman Lab', 'Lex Fridman',
]

export function HeroSection() {
  return (
    <section
      className="relative min-h-screen flex flex-col items-center justify-center pt-14 px-6 text-center overflow-hidden"
      aria-label="Hero"
    >
      {/* Grain overlay */}
      <div
        aria-hidden="true"
        className="pointer-events-none absolute inset-0 opacity-[0.03]"
        style={{
          backgroundImage: `url("data:image/svg+xml,%3Csvg viewBox='0 0 256 256' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='noise'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='4' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23noise)' opacity='1'/%3E%3C/svg%3E")`,
          backgroundRepeat: 'repeat',
          backgroundSize: '128px',
        }}
      />

      {/* Radial amber glow behind content */}
      <div
        aria-hidden="true"
        className="pointer-events-none absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[400px] rounded-full opacity-10"
        style={{ background: 'radial-gradient(ellipse at center, #F5A623 0%, transparent 70%)' }}
      />

      {/* Content */}
      <div className="relative z-10 max-w-4xl mx-auto">
        {/* Badge */}
        <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full border border-amber/30 bg-amber/10 text-amber text-xs font-medium mb-8">
          <span className="size-1.5 rounded-full bg-amber animate-pulse-amber" aria-hidden="true" />
          AI-powered in 90 seconds
        </div>

        {/* Headline */}
        <h1 className="font-display text-5xl sm:text-6xl lg:text-7xl font-bold text-primary leading-[1.05] mb-6">
          Your podcast.{' '}
          <span className="text-amber">Everywhere.</span>
        </h1>

        {/* Sub-headline */}
        <p className="text-lg sm:text-xl text-secondary max-w-xl mx-auto mb-10 leading-relaxed">
          Upload one episode. Get 8 content formats in 90 seconds — written in{' '}
          <em className="text-primary not-italic font-medium">your voice</em>, ready to publish.
        </p>

        {/* CTAs */}
        <div className="flex flex-col sm:flex-row items-center justify-center gap-3 mb-16">
          <Button size="lg" asChild>
            <Link href="/register">Start free — no card needed</Link>
          </Button>
          <a
            href="#formats"
            className="inline-flex items-center gap-2 h-11 px-6 text-sm text-secondary hover:text-primary transition-colors duration-150"
          >
            See it work
            <ArrowDownIcon />
          </a>
        </div>

        {/* Waveform */}
        <div className="relative w-full max-w-2xl mx-auto">
          <WaveformAnimation />
          <div
            aria-hidden="true"
            className="absolute inset-x-0 bottom-0 h-12 pointer-events-none"
            style={{ background: 'linear-gradient(to top, var(--bg-base), transparent)' }}
          />
        </div>
      </div>

      {/* Social proof strip */}
      <div className="relative z-10 mt-16 pb-12">
        <p className="text-xs text-tertiary uppercase tracking-widest mb-4">
          Trusted by 500+ podcasters
        </p>
        <div className="flex flex-wrap items-center justify-center gap-x-8 gap-y-2">
          {SOCIAL_PROOF.map((name) => (
            <span key={name} className="text-sm text-tertiary font-medium">
              {name}
            </span>
          ))}
        </div>
      </div>

      {/* Bottom fade to next section */}
      <div
        aria-hidden="true"
        className="absolute bottom-0 left-0 right-0 h-24 pointer-events-none"
        style={{ background: 'linear-gradient(to bottom, transparent, var(--bg-base))' }}
      />
    </section>
  )
}

HeroSection.displayName = 'HeroSection'

function ArrowDownIcon() {
  return (
    <svg width="14" height="14" viewBox="0 0 14 14" fill="none" stroke="currentColor" strokeWidth="1.5">
      <path d="M7 3v8M4 8l3 3 3-3" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  )
}
