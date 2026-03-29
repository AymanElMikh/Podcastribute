'use client'

import { Component, type ErrorInfo, type ReactNode } from 'react'
import { Button } from '@/components/ui/Button'

interface Props {
  children:  ReactNode
  /** Custom fallback. If omitted, shows a default error card. */
  fallback?: ReactNode
}

interface State {
  hasError: boolean
  error:    Error | null
}

/**
 * Class-based React error boundary.
 * Catches unhandled render errors in its subtree and shows a recovery UI.
 *
 * Usage:
 *   <ErrorBoundary>
 *     <SomeComponent />
 *   </ErrorBoundary>
 */
export class ErrorBoundary extends Component<Props, State> {
  static displayName = 'ErrorBoundary'

  constructor(props: Props) {
    super(props)
    this.state = { hasError: false, error: null }
  }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error }
  }

  componentDidCatch(error: Error, info: ErrorInfo) {
    // In production this would ship to an error-tracking service
    console.error('[ErrorBoundary]', error, info.componentStack)
  }

  private handleReset = () => {
    this.setState({ hasError: false, error: null })
  }

  render() {
    if (this.state.hasError) {
      if (this.props.fallback) return this.props.fallback

      return (
        <div className="flex flex-col items-center justify-center py-20 text-center px-6">
          <div className="size-12 rounded-full bg-error/10 flex items-center justify-center mb-4">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#EF4444" strokeWidth="1.5">
              <path d="M10.29 3.86L1.82 18a2 2 0 001.71 3h16.94a2 2 0 001.71-3L13.71 3.86a2 2 0 00-3.42 0z" />
              <line x1="12" y1="9" x2="12" y2="13" strokeLinecap="round" />
              <line x1="12" y1="17" x2="12.01" y2="17" strokeLinecap="round" />
            </svg>
          </div>
          <h2 className="text-lg font-semibold text-primary mb-2 font-display">
            Something went wrong
          </h2>
          <p className="text-sm text-secondary max-w-sm mb-6">
            {this.state.error?.message ?? 'An unexpected error occurred.'}
          </p>
          <div className="flex items-center gap-3">
            <Button size="sm" onClick={this.handleReset}>
              Try again
            </Button>
            <Button variant="ghost" size="sm" onClick={() => window.location.reload()}>
              Reload page
            </Button>
          </div>
        </div>
      )
    }

    return this.props.children
  }
}
