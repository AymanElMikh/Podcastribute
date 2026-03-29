'use client'

import useSWR from 'swr'
import { useState } from 'react'
import { toast } from 'sonner'
import { cn } from '@/lib/utils'
import { PageHeader } from '@/components/layout/PageHeader'
import { Card } from '@/components/ui/Card'
import { Badge } from '@/components/ui/Badge'
import { Button } from '@/components/ui/Button'
import { Progress } from '@/components/ui/Progress'
import { SkeletonCard } from '@/components/ui/Skeleton'
import { getBillingUsage, createCheckout, createPortalSession } from '@/lib/api'
import { getToken } from '@/lib/utils'
import { PLAN_LABELS, PLAN_PRICES } from '@/lib/constants'
import { APIError } from '@/lib/types'
import type { Plan } from '@/lib/types'

/* ─── Pricing plan config ─── */

const PLANS: {
  key:       Exclude<Plan, 'free'>
  features:  string[]
  highlight: boolean
}[] = [
  {
    key:      'starter',
    features: ['4 episodes / month', '8 content formats each', 'Voice profile', 'Copy to clipboard'],
    highlight: false,
  },
  {
    key:      'creator',
    features: ['15 episodes / month', '8 content formats each', 'Direct publish to LinkedIn', 'Buffer scheduling', 'Beehiiv newsletter'],
    highlight: true,
  },
  {
    key:      'studio',
    features: ['Unlimited episodes', 'Everything in Creator', 'Priority processing', 'API access (coming soon)'],
    highlight: false,
  },
]

export default function BillingPage() {
  const { data: usage, isLoading } = useSWR(
    () => { if (!getToken()) throw new Error('no-token'); return '/v1/billing/usage' },
    () => getBillingUsage(),
    { shouldRetryOnError: false },
  )

  const [checkingOut, setCheckingOut] = useState<Plan | null>(null)
  const [openPortal,  setOpenPortal]  = useState(false)

  const handleUpgrade = async (plan: Plan) => {
    setCheckingOut(plan)
    try {
      const { url } = await createCheckout(plan)
      window.location.href = url
    } catch (err) {
      const msg = err instanceof APIError ? err.message : 'Could not start checkout'
      toast.error('Checkout failed', { description: msg })
      setCheckingOut(null)
    }
  }

  const handlePortal = async () => {
    setOpenPortal(true)
    try {
      const { url } = await createPortalSession()
      window.location.href = url
    } catch (err) {
      const msg = err instanceof APIError ? err.message : 'Could not open portal'
      toast.error('Portal failed', { description: msg })
      setOpenPortal(false)
    }
  }

  const currentPlan = (usage?.plan ?? 'free') as Plan
  const isStudio    = currentPlan === 'studio'

  return (
    <div className="max-w-3xl">
      <PageHeader
        title="Billing"
        description="Manage your plan and episode usage."
      />

      {/* Current usage */}
      <section className="mb-8">
        <h2 className="text-sm font-semibold text-secondary uppercase tracking-wide mb-3">
          Current usage
        </h2>
        {isLoading ? (
          <SkeletonCard />
        ) : usage ? (
          <Card className="space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-base font-semibold text-primary">
                  {PLAN_LABELS[currentPlan]} plan
                </p>
                {usage.reset_at && (
                  <p className="text-xs text-tertiary mt-0.5">
                    Resets {new Date(usage.reset_at).toLocaleDateString('en-US', { month: 'long', day: 'numeric' })}
                  </p>
                )}
              </div>
              <Badge variant={isStudio ? 'amber' : 'muted'}>
                {PLAN_LABELS[currentPlan]}
              </Badge>
            </div>

            {usage.limit !== null ? (
              <Progress
                value={Math.min(100, Math.round((usage.episodes_this_month / usage.limit) * 100))}
                label={`${usage.episodes_this_month} / ${usage.limit} episodes this month`}
                trackHeight="h-2"
                showPct
              />
            ) : (
              <p className="text-sm text-success">Unlimited episodes</p>
            )}

            {currentPlan !== 'free' && (
              <Button
                variant="ghost"
                size="sm"
                loading={openPortal}
                onClick={handlePortal}
              >
                Manage subscription →
              </Button>
            )}
          </Card>
        ) : null}
      </section>

      {/* Pricing cards */}
      {!isStudio && (
        <section>
          <h2 className="text-sm font-semibold text-secondary uppercase tracking-wide mb-3">
            Upgrade your plan
          </h2>
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            {PLANS.map(({ key, features, highlight }) => {
              const isCurrent = currentPlan === key
              const price     = PLAN_PRICES[key]

              return (
                <div
                  key={key}
                  className={cn(
                    'flex flex-col rounded-xl border p-5 relative',
                    highlight
                      ? 'border-amber bg-amber/5'
                      : 'border-border-default bg-bg-surface',
                  )}
                >
                  {/* Most popular badge */}
                  {highlight && (
                    <div className="absolute -top-3 left-1/2 -translate-x-1/2">
                      <Badge variant="amber">Most popular</Badge>
                    </div>
                  )}

                  {/* Plan name + price */}
                  <div className="mb-4">
                    <p className="text-base font-bold text-primary font-display">
                      {PLAN_LABELS[key]}
                    </p>
                    <div className="flex items-baseline gap-1 mt-1">
                      <span className="text-2xl font-bold text-primary">${price}</span>
                      <span className="text-xs text-secondary">/mo</span>
                    </div>
                  </div>

                  {/* Features */}
                  <ul className="flex-1 space-y-2 mb-5">
                    {features.map((f) => (
                      <li key={f} className="flex items-start gap-2 text-xs text-secondary">
                        <span className="text-success mt-0.5 shrink-0">✓</span>
                        {f}
                      </li>
                    ))}
                  </ul>

                  {/* CTA */}
                  {isCurrent ? (
                    <Button variant="secondary" size="sm" disabled fullWidth>
                      Current plan
                    </Button>
                  ) : (
                    <Button
                      variant={highlight ? 'primary' : 'secondary'}
                      size="sm"
                      fullWidth
                      loading={checkingOut === key}
                      onClick={() => handleUpgrade(key)}
                    >
                      {currentPlan === 'free' ? 'Start plan' : 'Upgrade'}
                    </Button>
                  )}
                </div>
              )
            })}
          </div>

          <p className="text-xs text-tertiary mt-4 text-center">
            All plans include a 7-day trial. Cancel anytime.
          </p>
        </section>
      )}
    </div>
  )
}
