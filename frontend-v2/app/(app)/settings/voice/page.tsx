'use client'

import useSWR from 'swr'
import { PageHeader } from '@/components/layout/PageHeader'
import { VoiceCalibrator } from '@/components/voice/VoiceCalibrator'
import { SkeletonCard } from '@/components/ui/Skeleton'
import { getVoiceProfile } from '@/lib/api'
import { getToken } from '@/lib/utils'
import type { VoiceProfile } from '@/lib/types'

export default function VoiceSettingsPage() {
  const { data: profile, isLoading, mutate } = useSWR<VoiceProfile>(
    () => { if (!getToken()) throw new Error('no-token'); return '/v1/voice' },
    () => getVoiceProfile(),
    { shouldRetryOnError: false },
  )

  return (
    <div className="max-w-xl">
      <PageHeader
        title="Voice profile"
        description="Calibrate the AI to write content that sounds like you."
      />

      {isLoading ? (
        <SkeletonCard />
      ) : (
        <VoiceCalibrator
          existing={profile ?? null}
          onSaved={() => mutate()}
        />
      )}
    </div>
  )
}
