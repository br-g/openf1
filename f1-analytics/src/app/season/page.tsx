'use client'

import { Suspense, useState, useEffect, useMemo, useCallback } from 'react'
import Link from 'next/link'
import { useSearchParams, useRouter } from 'next/navigation'
import {
  getMeetings, getSessions, getDrivers,
  getChampionshipDrivers, getChampionshipTeams,
} from '@/lib/api'
import { useOpenF1 } from '@/hooks/useOpenF1'
import { Card, CardHeader, CardContent } from '@/components/ui/Card'
import { Select } from '@/components/ui/Select'
import { Badge } from '@/components/ui/Badge'
import { Button } from '@/components/ui/Button'
import { Skeleton, CardSkeleton, TableSkeleton, ChartSkeleton } from '@/components/ui/Skeleton'
import { ErrorState } from '@/components/ui/ErrorState'
import { EmptyState } from '@/components/ui/EmptyState'
import { PointsChart, type PointsSeriesEntry } from '@/components/charts/PointsChart'
import { formatDateRange, getTeamColor } from '@/lib/utils'
import type { Meeting, Session, Driver, ChampionshipDriver, ChampionshipTeam } from '@/types'

const AVAILABLE_YEARS = [
  { value: '2025', label: '2025' },
  { value: '2024', label: '2024' },
  { value: '2023', label: '2023' },
]

type StandingsTab = 'drivers' | 'constructors'

export default function SeasonPageWrapper() {
  return (
    <Suspense>
      <SeasonPage />
    </Suspense>
  )
}

function SeasonPage() {
  const router = useRouter()
  const searchParams = useSearchParams()
  const initialYear = searchParams.get('year') || '2025'

  const [year, setYear] = useState(initialYear)
  const [standingsTab, setStandingsTab] = useState<StandingsTab>('drivers')

  // Update URL when year changes
  useEffect(() => {
    const params = new URLSearchParams(searchParams.toString())
    params.set('year', year)
    router.replace(`/season?${params.toString()}`, { scroll: false })
  }, [year, router, searchParams])

  // Fetch meetings for the selected year
  const {
    data: meetings,
    loading: meetingsLoading,
    error: meetingsError,
    refetch: refetchMeetings,
  } = useOpenF1<Meeting[]>(
    () => getMeetings({ year: Number(year) }),
    [year],
  )

  // Fetch sessions (Race only) for championship data
  const {
    data: raceSessions,
    loading: sessionsLoading,
  } = useOpenF1<Session[]>(
    () => getSessions({ year: Number(year), session_type: 'Race' }),
    [year],
  )

  // Find the latest race session for championship standings
  const latestRaceSession = useMemo(() => {
    if (!raceSessions?.length) return null
    const sorted = [...raceSessions].sort(
      (a, b) => new Date(b.date_start).getTime() - new Date(a.date_start).getTime()
    )
    // Find the most recent completed session
    const now = new Date()
    return sorted.find(s => new Date(s.date_end) < now) || sorted[sorted.length - 1]
  }, [raceSessions])

  // Championship drivers standings
  const {
    data: champDrivers,
    loading: champDriversLoading,
    error: champDriversError,
    refetch: refetchChampDrivers,
  } = useOpenF1<ChampionshipDriver[]>(
    () => getChampionshipDrivers({ session_key: latestRaceSession!.session_key }),
    [latestRaceSession?.session_key],
    { enabled: !!latestRaceSession },
  )

  // Championship constructors standings
  const {
    data: champTeams,
    loading: champTeamsLoading,
    error: champTeamsError,
    refetch: refetchChampTeams,
  } = useOpenF1<ChampionshipTeam[]>(
    () => getChampionshipTeams({ session_key: latestRaceSession!.session_key }),
    [latestRaceSession?.session_key],
    { enabled: !!latestRaceSession },
  )

  // Fetch drivers for the latest race session (to map driver numbers to names)
  const {
    data: drivers,
  } = useOpenF1<Driver[]>(
    () => getDrivers({ session_key: latestRaceSession!.session_key }),
    [latestRaceSession?.session_key],
    { enabled: !!latestRaceSession },
  )

  // Fetch championship data across all race sessions for points progression
  const [pointsSeries, setPointsSeries] = useState<PointsSeriesEntry[]>([])
  const [pointsLoading, setPointsLoading] = useState(false)

  const buildPointsSeries = useCallback(async () => {
    if (!raceSessions?.length) return
    setPointsLoading(true)
    try {
      const sorted = [...raceSessions].sort(
        (a, b) => new Date(a.date_start).getTime() - new Date(b.date_start).getTime()
      )
      const now = new Date()
      const completedSessions = sorted.filter(s => new Date(s.date_end) < now)
      if (!completedSessions.length) { setPointsLoading(false); return }

      // Fetch championship data for each completed race
      const allChampData = await Promise.all(
        completedSessions.map(s => getChampionshipDrivers({ session_key: s.session_key }))
      )

      // Fetch drivers from last session for names/colors
      const sessionDrivers = await getDrivers({ session_key: completedSessions[completedSessions.length - 1].session_key })
      const driverMap = new Map<number, Driver>()
      sessionDrivers.forEach(d => {
        if (!driverMap.has(d.driver_number)) driverMap.set(d.driver_number, d)
      })

      // Build series: top 10 drivers by final round points
      const finalRound = allChampData[allChampData.length - 1] || []
      const topDrivers = [...finalRound]
        .sort((a, b) => a.position_current - b.position_current)
        .slice(0, 10)

      const series: PointsSeriesEntry[] = topDrivers.map(td => {
        const driver = driverMap.get(td.driver_number)
        const pointsByRound: Record<number, number> = {}
        allChampData.forEach((roundData, roundIdx) => {
          const entry = roundData.find(d => d.driver_number === td.driver_number)
          pointsByRound[roundIdx + 1] = entry?.points_current ?? 0
        })
        return {
          name: driver?.name_acronym || `#${td.driver_number}`,
          color: driver ? getTeamColor(driver.team_name) : '#888',
          pointsByRound,
        }
      })

      setPointsSeries(series)
    } catch {
      // Silently fail - chart will just not render
    } finally {
      setPointsLoading(false)
    }
  }, [raceSessions])

  useEffect(() => {
    buildPointsSeries()
  }, [buildPointsSeries])

  const driverMap = useMemo(() => {
    const map = new Map<number, Driver>()
    drivers?.forEach(d => {
      if (!map.has(d.driver_number)) map.set(d.driver_number, d)
    })
    return map
  }, [drivers])

  const sortedMeetings = useMemo(() => {
    if (!meetings) return []
    return [...meetings].sort(
      (a, b) => new Date(a.date_start).getTime() - new Date(b.date_start).getTime()
    )
  }, [meetings])

  const sortedChampDrivers = useMemo(() => {
    if (!champDrivers) return []
    return [...champDrivers].sort((a, b) => a.position_current - b.position_current)
  }, [champDrivers])

  const sortedChampTeams = useMemo(() => {
    if (!champTeams) return []
    return [...champTeams].sort((a, b) => a.position_current - b.position_current)
  }, [champTeams])

  const totalRounds = raceSessions?.length ?? 0
  const completedRounds = useMemo(() => {
    if (!raceSessions) return 0
    const now = new Date()
    return raceSessions.filter(s => new Date(s.date_end) < now).length
  }, [raceSessions])

  return (
    <div className="min-h-screen bg-f1-black">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Header */}
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 mb-8">
          <div>
            <h1 className="text-3xl font-bold text-white">
              Season <span className="text-f1-red">{year}</span>
            </h1>
            <p className="text-white/50 mt-1">
              {completedRounds} of {totalRounds} rounds completed
            </p>
          </div>
          <Select
            value={year}
            onChange={setYear}
            options={AVAILABLE_YEARS}
            label="Season"
            className="w-32"
          />
        </div>

        {/* Race Calendar Grid */}
        <section className="mb-12">
          <h2 className="text-xl font-semibold text-white mb-4">Race Calendar</h2>

          {meetingsError && (
            <ErrorState message={meetingsError} onRetry={refetchMeetings} />
          )}

          {meetingsLoading && (
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
              {Array.from({ length: 8 }).map((_, i) => (
                <CardSkeleton key={i} />
              ))}
            </div>
          )}

          {!meetingsLoading && !meetingsError && sortedMeetings.length === 0 && (
            <EmptyState
              title="No races found"
              message={`No meetings found for the ${year} season.`}
            />
          )}

          {!meetingsLoading && !meetingsError && sortedMeetings.length > 0 && (
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
              {sortedMeetings.map((meeting, idx) => {
                const isPast = new Date(meeting.date_end) < new Date()
                const isOngoing = new Date(meeting.date_start) <= new Date() && new Date(meeting.date_end) >= new Date()
                return (
                  <Link
                    key={meeting.meeting_key}
                    href={`/grand-prix/${meeting.meeting_key}`}
                  >
                    <Card hover glow className="h-full">
                      <CardContent className="relative">
                        <div className="flex items-start justify-between mb-2">
                          <span className="text-xs font-mono text-white/40">
                            R{String(idx + 1).padStart(2, '0')}
                          </span>
                          {isOngoing && <Badge variant="green">Live</Badge>}
                          {isPast && !isOngoing && <Badge variant="default">Completed</Badge>}
                          {!isPast && !isOngoing && <Badge variant="outline">Upcoming</Badge>}
                        </div>
                        <h3 className="text-base font-semibold text-white mb-1 line-clamp-2">
                          {meeting.meeting_name}
                        </h3>
                        <p className="text-sm text-white/50 mb-1">
                          {meeting.circuit_short_name}
                        </p>
                        <p className="text-xs text-white/40">
                          {meeting.country_name}
                        </p>
                        <p className="text-xs text-white/30 mt-2">
                          {formatDateRange(meeting.date_start, meeting.date_end)}
                        </p>
                      </CardContent>
                    </Card>
                  </Link>
                )
              })}
            </div>
          )}
        </section>

        {/* Championship Standings */}
        <section className="mb-12">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-xl font-semibold text-white">Championship Standings</h2>
            <div className="flex gap-1 bg-f1-graphite rounded-lg p-1">
              <Button
                variant={standingsTab === 'drivers' ? 'primary' : 'ghost'}
                size="sm"
                onClick={() => setStandingsTab('drivers')}
              >
                Drivers
              </Button>
              <Button
                variant={standingsTab === 'constructors' ? 'primary' : 'ghost'}
                size="sm"
                onClick={() => setStandingsTab('constructors')}
              >
                Constructors
              </Button>
            </div>
          </div>

          {standingsTab === 'drivers' && (
            <>
              {champDriversError && (
                <ErrorState message={champDriversError} onRetry={refetchChampDrivers} />
              )}
              {(champDriversLoading || sessionsLoading) && <TableSkeleton rows={10} />}
              {!champDriversLoading && !sessionsLoading && !champDriversError && sortedChampDrivers.length === 0 && (
                <EmptyState
                  title="No standings available"
                  message="Championship data is not yet available for this season."
                />
              )}
              {!champDriversLoading && !sessionsLoading && sortedChampDrivers.length > 0 && (
                <Card>
                  <div className="overflow-x-auto">
                    <table className="w-full text-sm">
                      <thead>
                        <tr className="border-b border-white/10">
                          <th className="text-left px-4 py-3 text-xs text-white/40 uppercase tracking-wider">Pos</th>
                          <th className="text-left px-4 py-3 text-xs text-white/40 uppercase tracking-wider">Driver</th>
                          <th className="text-left px-4 py-3 text-xs text-white/40 uppercase tracking-wider">Team</th>
                          <th className="text-right px-4 py-3 text-xs text-white/40 uppercase tracking-wider">Points</th>
                        </tr>
                      </thead>
                      <tbody>
                        {sortedChampDrivers.map((cd) => {
                          const driver = driverMap.get(cd.driver_number)
                          return (
                            <tr
                              key={cd.driver_number}
                              className="border-b border-white/5 hover:bg-white/5 transition-colors"
                            >
                              <td className="px-4 py-3 text-white/80 font-mono">
                                {cd.position_current}
                              </td>
                              <td className="px-4 py-3">
                                <div className="flex items-center gap-2">
                                  <div
                                    className="w-1 h-5 rounded-full"
                                    style={{ backgroundColor: driver ? getTeamColor(driver.team_name) : '#888' }}
                                  />
                                  <span className="text-white font-medium">
                                    {driver?.full_name || `Driver #${cd.driver_number}`}
                                  </span>
                                </div>
                              </td>
                              <td className="px-4 py-3 text-white/50">
                                {driver?.team_name || '-'}
                              </td>
                              <td className="px-4 py-3 text-right text-white font-semibold font-mono">
                                {cd.points_current}
                              </td>
                            </tr>
                          )
                        })}
                      </tbody>
                    </table>
                  </div>
                </Card>
              )}
            </>
          )}

          {standingsTab === 'constructors' && (
            <>
              {champTeamsError && (
                <ErrorState message={champTeamsError} onRetry={refetchChampTeams} />
              )}
              {(champTeamsLoading || sessionsLoading) && <TableSkeleton rows={10} />}
              {!champTeamsLoading && !sessionsLoading && !champTeamsError && sortedChampTeams.length === 0 && (
                <EmptyState
                  title="No standings available"
                  message="Championship data is not yet available for this season."
                />
              )}
              {!champTeamsLoading && !sessionsLoading && sortedChampTeams.length > 0 && (
                <Card>
                  <div className="overflow-x-auto">
                    <table className="w-full text-sm">
                      <thead>
                        <tr className="border-b border-white/10">
                          <th className="text-left px-4 py-3 text-xs text-white/40 uppercase tracking-wider">Pos</th>
                          <th className="text-left px-4 py-3 text-xs text-white/40 uppercase tracking-wider">Team</th>
                          <th className="text-right px-4 py-3 text-xs text-white/40 uppercase tracking-wider">Points</th>
                        </tr>
                      </thead>
                      <tbody>
                        {sortedChampTeams.map((ct) => (
                          <tr
                            key={ct.team_name}
                            className="border-b border-white/5 hover:bg-white/5 transition-colors"
                          >
                            <td className="px-4 py-3 text-white/80 font-mono">
                              {ct.position_current}
                            </td>
                            <td className="px-4 py-3">
                              <div className="flex items-center gap-2">
                                <div
                                  className="w-1 h-5 rounded-full"
                                  style={{ backgroundColor: getTeamColor(ct.team_name) }}
                                />
                                <span className="text-white font-medium">
                                  {ct.team_name}
                                </span>
                              </div>
                            </td>
                            <td className="px-4 py-3 text-right text-white font-semibold font-mono">
                              {ct.points_current}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </Card>
              )}
            </>
          )}
        </section>

        {/* Points Progression Chart */}
        <section className="mb-12">
          <h2 className="text-xl font-semibold text-white mb-4">Points Progression</h2>
          {pointsLoading && <ChartSkeleton />}
          {!pointsLoading && pointsSeries.length === 0 && (
            <EmptyState
              title="No points data"
              message="Points progression data is not yet available for this season."
            />
          )}
          {!pointsLoading && pointsSeries.length > 0 && (
            <Card>
              <CardContent>
                <PointsChart
                  series={pointsSeries}
                  rounds={completedRounds}
                  height={450}
                  xLabel="Round"
                />
              </CardContent>
            </Card>
          )}
        </section>
      </div>
    </div>
  )
}
