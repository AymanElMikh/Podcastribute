import { type NextRequest, NextResponse } from 'next/server'

/**
 * SSE proxy: forwards the FastAPI event stream to the browser.
 *
 * Why a separate proxy from the generic one?
 * - SSE needs specific headers (no buffering, persistent connection)
 * - X-Accel-Buffering: no tells Nginx not to buffer the response
 * - Cache-Control: no-cache keeps every chunk immediate
 */

const BACKEND_URL = process.env.BACKEND_URL ?? 'http://localhost:8002'

export async function GET(
  req: NextRequest,
  { params }: { params: Promise<{ id: string }> },
) {
  const { id }     = await params
  const token      = req.headers.get('authorization')
  const url        = `${BACKEND_URL}/v1/stream/${id}`

  const upstream = await fetch(url, {
    headers: {
      Accept:        'text/event-stream',
      ...(token ? { Authorization: token } : {}),
    },
  })

  if (!upstream.ok || !upstream.body) {
    return NextResponse.json(
      { error: 'Stream unavailable' },
      { status: upstream.status },
    )
  }

  return new NextResponse(upstream.body, {
    headers: {
      'Content-Type':      'text/event-stream',
      'Cache-Control':     'no-cache',
      'X-Accel-Buffering': 'no',
      Connection:          'keep-alive',
    },
  })
}
