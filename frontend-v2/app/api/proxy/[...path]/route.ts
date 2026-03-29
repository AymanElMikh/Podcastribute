import { type NextRequest, NextResponse } from 'next/server'

/**
 * Transparent proxy: forwards all /api/proxy/... requests to FastAPI.
 * Strips the /api/proxy prefix before forwarding.
 *
 * Why a proxy?
 * - Avoids CORS issues (browser → Next.js same-origin, Next.js → FastAPI server-side)
 * - Centralises the backend URL in one env var
 * - auth headers are forwarded transparently
 */

const BACKEND_URL = process.env.BACKEND_URL ?? 'http://localhost:8002'

async function handler(req: NextRequest, { params }: { params: Promise<{ path: string[] }> }) {
  const { path } = await params
  const targetPath = '/' + path.join('/')
  const search    = req.nextUrl.search

  const url = `${BACKEND_URL}${targetPath}${search}`

  // Forward all headers except host
  const headers = new Headers(req.headers)
  headers.delete('host')

  const upstream = await fetch(url, {
    method:  req.method,
    headers,
    body:    req.method !== 'GET' && req.method !== 'HEAD' ? req.body : undefined,
    // @ts-expect-error — Next.js fetch supports duplex
    duplex:  'half',
  })

  // Pass through response headers (strip transfer-encoding for Next.js compat)
  const responseHeaders = new Headers(upstream.headers)
  responseHeaders.delete('transfer-encoding')

  return new NextResponse(upstream.body, {
    status:  upstream.status,
    headers: responseHeaders,
  })
}

export const GET     = handler
export const POST    = handler
export const PUT     = handler
export const PATCH   = handler
export const DELETE  = handler

// Allow large audio uploads: disable static generation for this route
export const dynamic = 'force-dynamic'
