import type { Metadata } from 'next'
import { PageHeader } from '@/components/layout/PageHeader'
import { Tabs, TabsList, TabsTrigger, TabsContent } from '@/components/ui/Tabs'
import { UploadZone } from '@/components/upload/UploadZone'
import { YouTubeInput } from '@/components/upload/YouTubeInput'
import { RSSInput } from '@/components/upload/RSSInput'

export const metadata: Metadata = { title: 'New Episode' }

export default function UploadPage() {
  return (
    <div className="max-w-2xl mx-auto">
      <PageHeader
        title="New episode"
        description="Upload audio, paste a YouTube link, or pull from an RSS feed."
      />

      <Tabs defaultValue="upload">
        <TabsList className="mb-6">
          <TabsTrigger value="upload">Upload file</TabsTrigger>
          <TabsTrigger value="youtube">YouTube URL</TabsTrigger>
          <TabsTrigger value="rss">RSS feed</TabsTrigger>
        </TabsList>

        <TabsContent value="upload">
          <UploadZone />
          <p className="text-xs text-tertiary text-center mt-3">
            Supports MP3, MP4, WAV, M4A · Max 500 MB
          </p>
        </TabsContent>

        <TabsContent value="youtube">
          <YouTubeInput />
        </TabsContent>

        <TabsContent value="rss">
          <RSSInput />
        </TabsContent>
      </Tabs>
    </div>
  )
}
