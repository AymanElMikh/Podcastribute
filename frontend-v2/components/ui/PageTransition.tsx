'use client'

import { motion } from 'framer-motion'

const variants = {
  hidden:  { opacity: 0, y: 8 },
  visible: { opacity: 1, y: 0 },
  exit:    { opacity: 0, y: -4 },
}

/**
 * Wraps page content with a Framer Motion fade-up entrance + fade-down exit.
 * Used inside Next.js template.tsx files so it re-mounts on every navigation.
 */
export function PageTransition({ children }: { children: React.ReactNode }) {
  return (
    <motion.div
      variants={variants}
      initial="hidden"
      animate="visible"
      exit="exit"
      transition={{ duration: 0.18, ease: 'easeOut' }}
    >
      {children}
    </motion.div>
  )
}

PageTransition.displayName = 'PageTransition'
