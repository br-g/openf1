'use client'

import { useEffect, useState } from 'react'
import { getMeetings, getSessions } from '@/lib/api'
import { SessionCard } from '@/components/cards/SessionCard'
import { Skeleton } from '@/components/ui/Skeleton'
import type { Meeting, Session } from '@/types'

export function RecentSessions() {
  const [sessions, setSessions] = useState<Session[]>([])
  const [meetings, setMeetings] = useState<Meeting[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    async function fetchData() {
      try {
        setLoading(true)
        const [meetingsData, sessionsData] = await Promise.all([
          getMeetings({ year: 2024 }),
          getSessions({ year: 2024 }),
        ])
        setMeetings(meetingsData)
        setSessions(sessionsData)
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load sessions')
      } finally {
        setLoading(false)
      }
    }

    fetchData()
  }, [])

  if (error) {
    return (
      <div className="rounded-xl border border-white/5 bg-f1-graphite p-8 text-center">
        <p className="text-sm text-white/40">Unable to load recent sessions</p>
        <p className="mt-1 text-xs text-white/25">{error}</p>
      </div>
    )
  }

  if (loading) {
    return (
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
        {Array.from({ length: 8 }).map((_, i) => (
          <div key={i} className="rounded-xl border border-white/5 bg-f1-graphite p-4 space-y-3">
            <div className="flex items-center justify-between">
              <Skeleton className="h-5 w-20" />
              <Skeleton className="h-3 w-16" />
            </div>
            <Skeleton className="h-4 w-3/4" />
            <Skeleton className="h-3 w-1/2" />
          </div>
        ))}
      </div>
    )
  }

  // Build a lookup of meeting_key -> meeting
  const meetingMap = new Map(meetings.map(m => [m.meeting_key, m]))

  // Get the most recent sessions (sorted by date descending), limited to 8
  const recentSessions = [...sessions]
    .sort((a, b) => new Date(b.date_start).getTime() - new Date(a.date_start).getTime())
    .slice(0, 8)

  if (recentSessions.length === 0) {
    return (
      <div className="rounded-xl border border-white/5 bg-f1-graphite p-8 text-center">
        <p className="text-sm text-white/40">No recent sessions found</p>
      </div>
    )
  }

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
      {recentSessions.map((session) => {
        const meeting = meetingMap.get(session.meeting_key)
        return (
          <SessionCard
            key={session.session_key}
            sessionKey={session.session_key}
            meetingName={meeting?.meeting_name ?? `Meeting ${session.meeting_key}`}
            sessionName={session.session_name}
            sessionType={session.session_type}
            dateStart={session.date_start}
            circuitShortName={session.circuit_short_name}
            countryName={session.country_name}
          />
        )
      })}
    </div>
  )
}
