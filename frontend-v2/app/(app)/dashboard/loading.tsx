import { SkeletonCard } from '@/components/ui/Skeleton'
import { Skeleton }     from '@/components/ui/Skeleton'

/**
 * Next.js Suspense boundary shown while the dashboard page shell loads.
 */
export default function DashboardLoading() {
  return (
    <div className="max-w-6xl mx-auto">
      {/* Page header skeleton */}
      <div className="flex items-center justify-between mb-6">
        <div className="space-y-2">
          <Skeleton height="h-7" width="w-40" />
          <Skeleton height="h-4" width="w-64" />
        </div>
        <Skeleton height="h-9" width="w-32" className="rounded-lg" />
      </div>

      {/* Two-column skeleton */}
      <div className="grid grid-cols-1 lg:grid-cols-[1fr_280px] gap-6">
        {/* Episode list */}
        <div className="space-y-2.5">
          <SkeletonCard />
          <SkeletonCard />
          <SkeletonCard />
        </div>

        {/* Stats panel */}
        <div className="space-y-4">
          <SkeletonCard />
          <SkeletonCard />
        </div>
      </div>
    </div>
  )
}
