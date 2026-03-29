'use client'

import { useState } from 'react'
import { cn } from '@/lib/utils'
import { ContentEditor, EditableText } from './ContentEditor'
import { CopyButton } from './CopyButton'
import type { TwitterContent } from '@/lib/types'

const TWEET_LIMIT = 280

interface TwitterPreviewProps {
  content: TwitterContent
}

export function TwitterPreview({ content: initial }: TwitterPreviewProps) {
  const [content, setContent] = useState(initial)
  const isDirty = JSON.stringify(content) !== JSON.stringify(initial)

  const updateThread = (i: number, v: string) =>
    setContent((c) => ({ ...c, mainThread: c.mainThread.map((t, j) => (j === i ? v : t)) }))

  const updateHook = (i: number, v: string) =>
    setContent((c) => ({ ...c, standaloneHooks: c.standaloneHooks.map((h, j) => (j === i ? v : h)) }))

  return (
    <ContentEditor
      formatName="Twitter / X"
      isDirty={isDirty}
      onReset={() => setContent(initial)}
    >
      <div className="space-y-6 max-w-xl">
        {/* Thread */}
        <section>
          <p className="text-xs font-semibold text-secondary uppercase tracking-wide mb-3">
            Thread · {content.mainThread.length} tweets
          </p>
          <ol className="relative space-y-0">
            {content.mainThread.map((tweet, i) => {
              const over = tweet.length > TWEET_LIMIT
              return (
                <li key={i} className="flex gap-3">
                  {/* Connector line */}
                  <div className="flex flex-col items-center shrink-0">
                    <div className="size-8 rounded-full bg-bg-elevated border border-border-default flex items-center justify-center text-xs font-mono text-secondary">
                      {i + 1}
                    </div>
                    {i < content.mainThread.length - 1 && (
                      <div className="w-px flex-1 bg-border-subtle mt-1 mb-1" aria-hidden="true" />
                    )}
                  </div>

                  {/* Tweet card */}
                  <div className={cn(
                    'flex-1 p-3 rounded-lg border mb-2',
                    'bg-bg-surface',
                    over ? 'border-error/40' : 'border-border-subtle',
                  )}>
                    <EditableText
                      value={tweet}
                      onChange={(v) => updateThread(i, v)}
                      multiline
                      charLimit={TWEET_LIMIT}
                      placeholder="Tweet text…"
                      className="text-sm"
                    />
                    <div className="flex items-center justify-between mt-2">
                      <span className={cn(
                        'text-[10px] font-mono',
                        over ? 'text-error' : 'text-tertiary',
                      )}>
                        {tweet.length}/{TWEET_LIMIT}
                      </span>
                      <CopyButton text={tweet} size="xs" />
                    </div>
                  </div>
                </li>
              )
            })}
          </ol>
          <div className="mt-2 flex justify-end">
            <CopyButton text={content.mainThread.join('\n\n')} label="Copy thread" />
          </div>
        </section>

        {/* Standalone hooks */}
        <section>
          <p className="text-xs font-semibold text-secondary uppercase tracking-wide mb-3">
            Standalone hooks
          </p>
          <div className="space-y-2">
            {content.standaloneHooks.map((hook, i) => (
              <div
                key={i}
                className="flex items-start gap-2 p-3 rounded-lg bg-bg-surface border border-border-subtle"
              >
                <div className="flex-1">
                  <EditableText
                    value={hook}
                    onChange={(v) => updateHook(i, v)}
                    multiline
                    charLimit={TWEET_LIMIT}
                  />
                </div>
                <CopyButton text={hook} size="xs" className="shrink-0 mt-0.5" />
              </div>
            ))}
          </div>
        </section>

        {/* Listen tweet */}
        <section>
          <p className="text-xs font-semibold text-secondary uppercase tracking-wide mb-3">
            Listen tweet
          </p>
          <div className="p-3 rounded-lg bg-bg-surface border border-border-subtle">
            <EditableText
              value={content.listenTweet}
              onChange={(v) => setContent((c) => ({ ...c, listenTweet: v }))}
              multiline
              charLimit={TWEET_LIMIT}
            />
            <div className="flex justify-end mt-2">
              <CopyButton text={content.listenTweet} size="xs" />
            </div>
          </div>
        </section>
      </div>
    </ContentEditor>
  )
}

TwitterPreview.displayName = 'TwitterPreview'
