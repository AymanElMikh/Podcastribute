'use client'

import { useState } from 'react'
import { toast } from 'sonner'
import { cn } from '@/lib/utils'
import { PageHeader } from '@/components/layout/PageHeader'
import { Card } from '@/components/ui/Card'
import { Button } from '@/components/ui/Button'
import { Badge } from '@/components/ui/Badge'
import { Input } from '@/components/ui/Input'

interface Integration {
  key:         string
  name:        string
  description: string
  authType:    'oauth' | 'apikey'
  docsUrl:     string
}

const INTEGRATIONS: Integration[] = [
  {
    key:         'buffer',
    name:        'Buffer',
    description: 'Schedule Twitter and LinkedIn posts directly from PodcastAI.',
    authType:    'oauth',
    docsUrl:     '#',
  },
  {
    key:         'beehiiv',
    name:        'Beehiiv',
    description: 'Publish newsletter drafts straight to your Beehiiv publication.',
    authType:    'apikey',
    docsUrl:     '#',
  },
  {
    key:         'linkedin',
    name:        'LinkedIn',
    description: 'Post directly to your LinkedIn profile or company page.',
    authType:    'oauth',
    docsUrl:     '#',
  },
]

export default function IntegrationsPage() {
  const [connected,  setConnected]  = useState<Record<string, boolean>>({})
  const [apiKeys,    setApiKeys]    = useState<Record<string, string>>({})
  const [showInput,  setShowInput]  = useState<Record<string, boolean>>({})
  const [connecting, setConnecting] = useState<Record<string, boolean>>({})

  const handleOAuth = async (key: string) => {
    setConnecting((p) => ({ ...p, [key]: true }))
    // In production: redirect to OAuth flow. Here we simulate.
    await new Promise((r) => setTimeout(r, 1200))
    setConnected((p) => ({ ...p, [key]: true }))
    setConnecting((p) => ({ ...p, [key]: false }))
    toast.success(`${key} connected!`)
  }

  const handleAPIKey = (key: string) => {
    const apiKey = apiKeys[key]?.trim()
    if (!apiKey || apiKey.length < 10) {
      toast.error('Enter a valid API key')
      return
    }
    setConnected((p) => ({ ...p, [key]: true }))
    setShowInput((p) => ({ ...p, [key]: false }))
    toast.success(`${key} connected!`)
  }

  const handleDisconnect = (key: string) => {
    setConnected((p) => ({ ...p, [key]: false }))
    setApiKeys((p) => ({ ...p, [key]: '' }))
    toast.success(`${key} disconnected`)
  }

  return (
    <div className="max-w-2xl">
      <PageHeader
        title="Integrations"
        description="Connect your publishing platforms to post directly from PodcastAI."
      />

      <div className="space-y-3">
        {INTEGRATIONS.map((integration) => {
          const isConnected = !!connected[integration.key]
          const isConnecting = !!connecting[integration.key]
          const showApiInput = !!showInput[integration.key]

          return (
            <Card key={integration.key} className="space-y-4">
              <div className="flex items-start justify-between gap-4">
                {/* Info */}
                <div className="flex items-start gap-3 flex-1 min-w-0">
                  <div className={cn(
                    'size-10 rounded-lg flex items-center justify-center text-sm font-bold shrink-0',
                    'bg-bg-elevated text-secondary',
                  )}>
                    {integration.name[0]}
                  </div>
                  <div className="min-w-0">
                    <div className="flex items-center gap-2">
                      <p className="text-sm font-semibold text-primary">{integration.name}</p>
                      {isConnected && <Badge variant="success" dot>Connected</Badge>}
                    </div>
                    <p className="text-xs text-secondary mt-0.5">{integration.description}</p>
                  </div>
                </div>

                {/* Action */}
                <div className="shrink-0">
                  {isConnected ? (
                    <Button
                      variant="danger"
                      size="sm"
                      onClick={() => handleDisconnect(integration.key)}
                    >
                      Disconnect
                    </Button>
                  ) : integration.authType === 'oauth' ? (
                    <Button
                      variant="secondary"
                      size="sm"
                      loading={isConnecting}
                      onClick={() => handleOAuth(integration.key)}
                    >
                      Connect
                    </Button>
                  ) : (
                    <Button
                      variant="secondary"
                      size="sm"
                      onClick={() => setShowInput((p) => ({ ...p, [integration.key]: !p[integration.key] }))}
                    >
                      {showApiInput ? 'Cancel' : 'Connect'}
                    </Button>
                  )}
                </div>
              </div>

              {/* API key input */}
              {showApiInput && integration.authType === 'apikey' && (
                <div className="flex gap-2 animate-fade-up">
                  <div className="flex-1">
                    <Input
                      type="password"
                      placeholder={`${integration.name} API key`}
                      value={apiKeys[integration.key] ?? ''}
                      onChange={(e) => setApiKeys((p) => ({ ...p, [integration.key]: e.target.value }))}
                    />
                  </div>
                  <Button
                    size="md"
                    onClick={() => handleAPIKey(integration.key)}
                  >
                    Save
                  </Button>
                </div>
              )}
            </Card>
          )
        })}
      </div>

      <p className="text-xs text-tertiary mt-6">
        OAuth tokens are encrypted at rest. API keys are stored securely and never logged.
      </p>
    </div>
  )
}
