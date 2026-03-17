'use client'

import { useState, useMemo } from 'react'
import Link from 'next/link'
import { getMeetings } from '@/lib/api'
import { useOpenF1 } from '@/hooks/useOpenF1'
import { Card, CardContent } from '@/components/ui/Card'
import { Badge } from '@/components/ui/Badge'
import { CardSkeleton } from '@/components/ui/Skeleton'
import { ErrorState } from '@/components/ui/ErrorState'
import { EmptyState } from '@/components/ui/EmptyState'
import { formatDateRange } from '@/lib/utils'
import type { Meeting } from '@/types'

export default function GrandPrixListPage() {
  const [search, setSearch] = useState('')
  const [filter, setFilter] = useState<'all' | 'completed' | 'upcoming'>('all')

  const {
    data: meetings,
    loading,
    error,
    refetch,
  } = useOpenF1<Meeting[]>(
    () => getMeetings({ year: 2025 }),
    [],
  )

  const filteredMeetings = useMemo(() => {
    if (!meetings) return []

    const now = new Date()
    let result = [...meetings].sort(
      (a, b) => new Date(a.date_start).getTime() - new Date(b.date_start).getTime()
    )

    // Apply text search
    if (search.trim()) {
      const q = search.toLowerCase()
      result = result.filter(
        m =>
          m.meeting_name.toLowerCase().includes(q) ||
          m.country_name.toLowerCase().includes(q) ||
          m.circuit_short_name.toLowerCase().includes(q) ||
          m.location.toLowerCase().includes(q)
      )
    }

    // Apply status filter
    if (filter === 'completed') {
      result = result.filter(m => new Date(m.date_end) < now)
    } else if (filter === 'upcoming') {
      result = result.filter(m => new Date(m.date_start) > now)
    }

    return result
  }, [meetings, search, filter])

  return (
    <div className="min-h-screen bg-f1-black">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-white">
            Grand Prix <span className="text-f1-red">2025</span>
          </h1>
          <p className="text-white/50 mt-1">
            Browse all Formula 1 Grand Prix events
          </p>
        </div>

        {/* Search and Filter */}
        <div className="flex flex-col sm:flex-row gap-4 mb-8">
          <div className="relative flex-1">
            <svg
              className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-white/30"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
              />
            </svg>
            <input
              type="text"
              placeholder="Search by name, country, or circuit..."
              value={search}
              onChange={e => setSearch(e.target.value)}
              className="w-full bg-f1-steel border border-white/10 rounded-lg pl-10 pr-4 py-2.5 text-sm text-white placeholder:text-white/30 focus:outline-none focus:ring-2 focus:ring-f1-red/50 focus:border-f1-red/50 transition-colors"
            />
          </div>
          <div className="flex gap-1 bg-f1-graphite rounded-lg p-1 self-start">
            {(['all', 'completed', 'upcoming'] as const).map(f => (
              <button
                key={f}
                onClick={() => setFilter(f)}
                className={`px-3 py-1.5 text-xs font-medium rounded-md transition-colors ${
                  filter === f
                    ? 'bg-f1-red text-white'
                    : 'text-white/50 hover:text-white hover:bg-white/5'
                }`}
              >
                {f.charAt(0).toUpperCase() + f.slice(1)}
              </button>
            ))}
          </div>
        </div>

        {/* Error state */}
        {error && <ErrorState message={error} onRetry={refetch} />}

        {/* Loading state */}
        {loading && (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
            {Array.from({ length: 9 }).map((_, i) => (
              <CardSkeleton key={i} />
            ))}
          </div>
        )}

        {/* Empty state */}
        {!loading && !error && filteredMeetings.length === 0 && (
          <EmptyState
            title="No Grand Prix found"
            message={search ? `No results matching "${search}".` : 'No events match the selected filter.'}
          />
        )}

        {/* Meetings grid */}
        {!loading && !error && filteredMeetings.length > 0 && (
          <>
            <p className="text-xs text-white/30 mb-4">
              {filteredMeetings.length} event{filteredMeetings.length !== 1 ? 's' : ''}
            </p>
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
              {filteredMeetings.map((meeting, idx) => {
                const isPast = new Date(meeting.date_end) < new Date()
                const isOngoing =
                  new Date(meeting.date_start) <= new Date() &&
                  new Date(meeting.date_end) >= new Date()

                return (
                  <Link
                    key={meeting.meeting_key}
                    href={`/grand-prix/${meeting.meeting_key}`}
                  >
                    <Card hover glow className="h-full">
                      <CardContent>
                        <div className="flex items-start justify-between mb-3">
                          <span className="text-xs font-mono text-white/30">
                            R{String(idx + 1).padStart(2, '0')}
                          </span>
                          {isOngoing && <Badge variant="green">Live</Badge>}
                          {isPast && !isOngoing && <Badge variant="default">Completed</Badge>}
                          {!isPast && !isOngoing && <Badge variant="outline">Upcoming</Badge>}
                        </div>
                        <h3 className="text-lg font-semibold text-white mb-1 line-clamp-2">
                          {meeting.meeting_name}
                        </h3>
                        <p className="text-sm text-white/50 mb-0.5">
                          {meeting.circuit_short_name}
                        </p>
                        <p className="text-sm text-white/40">
                          {meeting.location}, {meeting.country_name}
                        </p>
                        <div className="mt-3 pt-3 border-t border-white/5">
                          <p className="text-xs text-white/30">
                            {formatDateRange(meeting.date_start, meeting.date_end)}
                          </p>
                        </div>
                      </CardContent>
                    </Card>
                  </Link>
                )
              })}
            </div>
          </>
        )}
      </div>
    </div>
  )
}
