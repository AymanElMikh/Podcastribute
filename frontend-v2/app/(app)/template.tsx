'use client'

import { AnimatePresence } from 'framer-motion'
import { PageTransition } from '@/components/ui/PageTransition'

/**
 * template.tsx re-mounts on every navigation (unlike layout.tsx which persists).
 * This is the correct place for AnimatePresence-based page transitions in App Router.
 */
export default function AppTemplate({ children }: { children: React.ReactNode }) {
  return (
    <AnimatePresence mode="wait">
      <PageTransition>{children}</PageTransition>
    </AnimatePresence>
  )
}
