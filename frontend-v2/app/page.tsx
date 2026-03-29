import type { Metadata } from 'next'
import Link from 'next/link'
import { LandingNav } from '@/components/landing/LandingNav'
import { HeroSection } from '@/components/landing/HeroSection'
import { HowItWorksSection } from '@/components/landing/HowItWorksSection'
import { FormatShowcase } from '@/components/landing/FormatShowcase'
import { PricingSection } from '@/components/landing/PricingSection'
import { LandingFooter } from '@/components/landing/LandingFooter'

export const metadata: Metadata = {
  title: 'PodcastAI — Your podcast. Everywhere.',
  description:
    'Upload one episode. Get 8 content formats in 90 seconds. AI-powered podcast content repurposing.',
}

export default function LandingPage() {
  return (
    <div className="min-h-screen bg-bg-base text-primary overflow-x-hidden">
      <LandingNav />
      <HeroSection />
      <HowItWorksSection />
      <FormatShowcase />
      <PricingSection />
      <LandingFooter />
    </div>
  )
}
