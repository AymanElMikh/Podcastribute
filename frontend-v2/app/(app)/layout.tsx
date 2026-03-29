import { Sidebar }       from '@/components/layout/Sidebar'
import { Header }        from '@/components/layout/Header'
import { ErrorBoundary } from '@/components/ui/ErrorBoundary'

/**
 * Auth-protected app shell.
 * All pages inside (app)/ get: fixed sidebar (desktop) + sticky header + main content area.
 * Authentication redirect is handled client-side inside useAuth().
 * Page transitions are handled by (app)/template.tsx.
 */
export default function AppLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="min-h-screen bg-bg-base">
      <Sidebar />

      {/* Main area — offset by sidebar width on desktop */}
      <div className="lg:pl-60 flex flex-col min-h-screen">
        <Header />

        <main className="flex-1 px-5 py-6 pb-24 lg:pb-6">
          <ErrorBoundary>
            {children}
          </ErrorBoundary>
        </main>
      </div>
    </div>
  )
}
