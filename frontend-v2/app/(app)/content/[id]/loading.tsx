import { SkeletonCard } from '@/components/ui/Skeleton'

export default function ContentLoading() {
  return (
    <div className="max-w-lg mx-auto space-y-3 mt-8">
      <SkeletonCard />
      <SkeletonCard />
      <SkeletonCard />
    </div>
  )
}
