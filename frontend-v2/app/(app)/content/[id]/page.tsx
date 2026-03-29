import type { Metadata } from 'next'
import { ContentPageClient } from './ContentPageClient'

export const metadata: Metadata = { title: 'Episode' }

// Dynamic — episode id comes from the URL
export const dynamic = 'force-dynamic'

export default async function ContentPage({
  params,
}: {
  params: Promise<{ id: string }>
}) {
  const { id } = await params
  return <ContentPageClient episodeId={id} />
}
