import Link from 'next/link'
import type { Metadata } from 'next'
import { PageHeader } from '@/components/layout/PageHeader'
import { Card } from '@/components/ui/Card'

export const metadata: Metadata = { title: 'Settings' }

const SETTINGS_LINKS = [
  {
    href:        '/settings/voice',
    title:       'Voice profile',
    description: 'Calibrate the AI to write content that sounds like you.',
    icon:        '🎙',
  },
  {
    href:        '/settings/integrations',
    title:       'Integrations',
    description: 'Connect Buffer, Beehiiv, and LinkedIn for direct publishing.',
    icon:        '🔌',
  },
  {
    href:        '/settings/billing',
    title:       'Billing',
    description: 'Manage your subscription plan and episode usage.',
    icon:        '💳',
  },
]

export default function SettingsPage() {
  return (
    <div className="max-w-xl">
      <PageHeader title="Settings" />
      <div className="space-y-3">
        {SETTINGS_LINKS.map((link) => (
          <Link key={link.href} href={link.href}>
            <Card hoverable className="flex items-center gap-4">
              <div className="size-10 rounded-lg bg-bg-elevated flex items-center justify-center text-xl shrink-0">
                {link.icon}
              </div>
              <div>
                <p className="text-sm font-semibold text-primary">{link.title}</p>
                <p className="text-xs text-secondary mt-0.5">{link.description}</p>
              </div>
            </Card>
          </Link>
        ))}
      </div>
    </div>
  )
}
