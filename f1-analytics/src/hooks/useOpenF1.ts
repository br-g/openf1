'use client'

import { useState, useEffect, useCallback } from 'react'

interface UseOpenF1Options {
  enabled?: boolean
  refetchInterval?: number
}

interface UseOpenF1Result<T> {
  data: T | null
  loading: boolean
  error: string | null
  refetch: () => void
}

export function useOpenF1<T>(
  fetcher: () => Promise<T>,
  deps: unknown[] = [],
  options: UseOpenF1Options = {}
): UseOpenF1Result<T> {
  const { enabled = true, refetchInterval } = options
  const [data, setData] = useState<T | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const fetchData = useCallback(async () => {
    if (!enabled) return
    setLoading(true)
    setError(null)
    try {
      const result = await fetcher()
      setData(result)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch data')
    } finally {
      setLoading(false)
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [enabled, ...deps])

  useEffect(() => {
    fetchData()
  }, [fetchData])

  useEffect(() => {
    if (!refetchInterval || !enabled) return
    const interval = setInterval(fetchData, refetchInterval)
    return () => clearInterval(interval)
  }, [refetchInterval, enabled, fetchData])

  return { data, loading, error, refetch: fetchData }
}
