'use client'

import { Progress } from '@/components/ui/Progress'

interface UploadProgressProps {
  progress:  number
  fileName?: string
}

/**
 * Standalone upload progress bar — used inline inside UploadZone
 * and exported for reuse in other contexts (e.g. voice calibration).
 */
export function UploadProgress({ progress, fileName }: UploadProgressProps) {
  return (
    <div className="space-y-2 w-full px-6">
      {fileName && (
        <p className="text-xs text-secondary truncate text-center">{fileName}</p>
      )}
      <Progress
        value={progress}
        trackHeight="h-1.5"
        showPct
        label={progress < 100 ? 'Uploading…' : 'Processing…'}
      />
    </div>
  )
}

UploadProgress.displayName = 'UploadProgress'
