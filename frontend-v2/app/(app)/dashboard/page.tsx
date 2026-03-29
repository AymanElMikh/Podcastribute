import Link from 'next/link'
import type { Metadata } from 'next'
import { Button } from '@/components/ui/Button'
import { EpisodeList } from '@/components/dashboard/EpisodeList'
import { StatsPanel } from '@/components/dashboard/StatsPanel'

export const metadata: Metadata = { title: 'Dashboard' }

export default function DashboardPage() {
  return (
    <div className="max-w-6xl mx-auto">
      {/* Page header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-primary font-display">Your episodes</h1>
          <p className="text-sm text-secondary mt-0.5">
            Upload a podcast and get 8 content formats in minutes.
          </p>
        </div>
        <Button asChild size="md">
          <Link href="/upload">+ New episode</Link>
        </Button>
      </div>

      {/* Two-column layout: 70/30 */}
      <div className="grid grid-cols-1 lg:grid-cols-[1fr_280px] gap-6">
        {/* Left — episode list */}
        <section aria-label="Episodes">
          <EpisodeList />
        </section>

        {/* Right — stats panel */}
        <section aria-label="Stats and status">
          <StatsPanel />
        </section>
      </div>
    </div>
  )
}
