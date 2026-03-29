import Link from 'next/link'
import { Button } from '@/components/ui/Button'

const PLANS = [
  {
    key:     'starter',
    name:    'Starter',
    price:   49,
    episodes: 4,
    highlight: false,
    features: [
      '4 episodes / month',
      'All 8 content formats',
      'Voice profile calibration',
      'Copy-to-clipboard',
      'Email support',
    ],
    cta: 'Start Starter',
  },
  {
    key:     'creator',
    name:    'Creator',
    price:   149,
    episodes: 15,
    highlight: true,
    features: [
      '15 episodes / month',
      'All 8 content formats',
      'Advanced voice calibration',
      'Direct publish to Buffer & LinkedIn',
      'Newsletter to Beehiiv',
      'Priority support',
    ],
    cta: 'Start Creator',
  },
  {
    key:     'studio',
    name:    'Studio',
    price:   399,
    episodes: Infinity,
    highlight: false,
    features: [
      'Unlimited episodes',
      'All 8 content formats',
      'Team seats (up to 5)',
      'All integrations',
      'API access',
      'Dedicated support',
    ],
    cta: 'Start Studio',
  },
] as const

export function PricingSection() {
  return (
    <section
      id="pricing"
      className="relative py-24 px-6"
      aria-labelledby="pricing-heading"
    >
      <div className="max-w-5xl mx-auto">
        {/* Heading */}
        <div className="text-center mb-12">
          <p className="text-xs text-amber uppercase tracking-widest font-medium mb-3">Pricing</p>
          <h2
            id="pricing-heading"
            className="font-display text-4xl sm:text-5xl font-bold text-primary"
          >
            Simple pricing. No surprises.
          </h2>
          <p className="text-secondary text-lg mt-4">
            Try one episode free — no card required.
          </p>
        </div>

        {/* Cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 items-start">
          {PLANS.map((plan) => (
            <div
              key={plan.key}
              className={`relative rounded-2xl border p-6 flex flex-col gap-6 ${
                plan.highlight
                  ? 'border-amber bg-bg-elevated shadow-[0_0_40px_rgba(245,166,35,0.12)]'
                  : 'border-border-subtle bg-bg-base'
              }`}
            >
              {plan.highlight && (
                <div className="absolute -top-3 left-1/2 -translate-x-1/2">
                  <span className="text-xs font-bold text-black bg-amber px-3 py-1 rounded-full">
                    Most popular
                  </span>
                </div>
              )}

              {/* Plan info */}
              <div>
                <p className="text-sm font-medium text-secondary mb-1">{plan.name}</p>
                <div className="flex items-baseline gap-1">
                  <span className="font-display text-4xl font-bold text-primary">${plan.price}</span>
                  <span className="text-sm text-tertiary">/mo</span>
                </div>
                <p className="text-xs text-tertiary mt-1">
                  {plan.episodes === Infinity ? 'Unlimited episodes' : `${plan.episodes} episodes / month`}
                </p>
              </div>

              {/* Feature list */}
              <ul className="space-y-2 flex-1">
                {plan.features.map((f) => (
                  <li key={f} className="flex items-start gap-2 text-sm text-secondary">
                    <svg className="size-4 text-amber shrink-0 mt-0.5" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.5" aria-hidden="true">
                      <polyline points="13 4 6.5 11 3 7.5" strokeLinecap="round" strokeLinejoin="round" />
                    </svg>
                    {f}
                  </li>
                ))}
              </ul>

              {/* CTA */}
              <Button
                variant={plan.highlight ? 'primary' : 'secondary'}
                size="md"
                fullWidth
                asChild
              >
                <Link href="/register">{plan.cta}</Link>
              </Button>
            </div>
          ))}
        </div>

        {/* Free trial note */}
        <p className="text-center text-xs text-tertiary mt-8">
          All plans start with a{' '}
          <Link href="/register" className="text-amber hover:underline">
            free trial episode
          </Link>{' '}
          — no credit card needed.
        </p>
      </div>
    </section>
  )
}

PricingSection.displayName = 'PricingSection'
