import { NextRequest, NextResponse } from 'next/server'

const OPENF1_BASE = 'https://api.openf1.org/v1'

// Server-side cache
const responseCache = new Map<string, { data: unknown; timestamp: number }>()
const CACHE_TTL = 30_000 // 30 seconds

export async function GET(
  request: NextRequest,
  { params }: { params: Promise<{ endpoint: string[] }> }
) {
  const { endpoint } = await params
  const path = endpoint.join('/')
  const searchParams = request.nextUrl.searchParams.toString()
  const cacheKey = `${path}?${searchParams}`

  // Check cache
  const cached = responseCache.get(cacheKey)
  if (cached && Date.now() - cached.timestamp < CACHE_TTL) {
    return NextResponse.json(cached.data, {
      headers: {
        'Cache-Control': 's-maxage=30, stale-while-revalidate=60',
        'X-Cache': 'HIT',
      },
    })
  }

  const url = `${OPENF1_BASE}/${path}${searchParams ? '?' + searchParams : ''}`

  try {
    const response = await fetch(url, {
      headers: {
        'Accept': 'application/json',
      },
    })

    if (!response.ok) {
      return NextResponse.json(
        { error: `OpenF1 API returned ${response.status}` },
        { status: response.status }
      )
    }

    const data = await response.json()

    // Cache the response
    responseCache.set(cacheKey, { data, timestamp: Date.now() })

    // Limit cache size
    if (responseCache.size > 500) {
      const oldest = [...responseCache.entries()].sort((a, b) => a[1].timestamp - b[1].timestamp)
      for (let i = 0; i < 100; i++) {
        responseCache.delete(oldest[i][0])
      }
    }

    return NextResponse.json(data, {
      headers: {
        'Cache-Control': 's-maxage=30, stale-while-revalidate=60',
        'X-Cache': 'MISS',
      },
    })
  } catch {
    return NextResponse.json(
      { error: 'Failed to fetch from OpenF1 API' },
      { status: 502 }
    )
  }
}
