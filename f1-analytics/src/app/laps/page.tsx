'use client'

import { useState, useEffect, useMemo } from 'react'
import { Card, CardHeader, CardContent } from '@/components/ui/Card'
import { Select } from '@/components/ui/Select'
import { Button } from '@/components/ui/Button'
import { Skeleton } from '@/components/ui/Skeleton'
import { ErrorState } from '@/components/ui/ErrorState'
import { EmptyState } from '@/components/ui/EmptyState'
import { Badge } from '@/components/ui/Badge'
import { getSessions, getDrivers, getLaps, getStints, getMeetings } from '@/lib/api'
import { formatLapTime, getTeamColor, getCompoundColor, exportToCsv } from '@/lib/utils'
import type { Session, Driver, Lap, Stint } from '@/types'
import {
  LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer,
  CartesianGrid, ScatterChart, Scatter
} from 'recharts'

export default function LapAnalysisPage() {
  const [year, setYear] = useState('2024')
  const [sessions, setSessions] = useState<Session[]>([])
  const [selectedSession, setSelectedSession] = useState('')
  const [drivers, setDrivers] = useState<Driver[]>([])
  const [selectedDriver, setSelectedDriver] = useState('')
  const [laps, setLaps] = useState<Lap[]>([])
  const [allLaps, setAllLaps] = useState<Lap[]>([])
  const [stints, setStints] = useState<Stint[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [view, setView] = useState<'table' | 'chart' | 'leaderboard'>('table')

  useEffect(() => {
    getMeetings({ year: parseInt(year) }).then(async meetings => {
      const allSessions: Session[] = []
      for (const m of meetings.slice(0, 24)) {
        try {
          const s = await getSessions({ meeting_key: m.meeting_key })
          allSessions.push(...s)
        } catch { /* skip */ }
      }
      setSessions(allSessions)
    }).catch(() => setError('Failed to load sessions'))
  }, [year])

  useEffect(() => {
    if (!selectedSession) return
    setLoading(true)
    Promise.all([
      getDrivers({ session_key: parseInt(selectedSession) }),
      getLaps({ session_key: parseInt(selectedSession) }),
      getStints({ session_key: parseInt(selectedSession) }),
    ]).then(([d, l, s]) => {
      setDrivers(d)
      setAllLaps(l)
      setStints(s)
      setLoading(false)
    }).catch(() => {
      setError('Failed to load session data')
      setLoading(false)
    })
  }, [selectedSession])

  // Filter laps by driver
  useEffect(() => {
    if (selectedDriver) {
      setLaps(allLaps.filter(l => l.driver_number === parseInt(selectedDriver)))
    } else {
      setLaps(allLaps)
    }
  }, [selectedDriver, allLaps])

  // Best laps leaderboard
  const leaderboard = useMemo(() => {
    const bestByDriver = new Map<number, Lap>()
    allLaps.forEach(lap => {
      if (!lap.lap_duration || lap.is_pit_out_lap) return
      const current = bestByDriver.get(lap.driver_number)
      if (!current || (lap.lap_duration && current.lap_duration && lap.lap_duration < current.lap_duration)) {
        bestByDriver.set(lap.driver_number, lap)
      }
    })
    return [...bestByDriver.values()].sort((a, b) => (a.lap_duration || 999) - (b.lap_duration || 999))
  }, [allLaps])

  // Lap times chart data
  const chartData = useMemo(() => {
    const validLaps = laps.filter(l => l.lap_duration && l.lap_duration > 0 && !l.is_pit_out_lap)
    return validLaps.map(l => {
      const stint = stints.find(s =>
        s.driver_number === l.driver_number &&
        l.lap_number >= s.lap_start &&
        l.lap_number <= s.lap_end
      )
      return {
        lap: l.lap_number,
        time: l.lap_duration,
        compound: stint?.compound || 'UNKNOWN',
        driver: l.driver_number,
        s1: l.duration_sector_1,
        s2: l.duration_sector_2,
        s3: l.duration_sector_3,
      }
    })
  }, [laps, stints])

  // Consistency score
  const consistencyScore = useMemo(() => {
    const validTimes = chartData.filter(d => d.time).map(d => d.time!)
    if (validTimes.length < 3) return null
    const mean = validTimes.reduce((a, b) => a + b, 0) / validTimes.length
    const variance = validTimes.reduce((acc, t) => acc + Math.pow(t - mean, 2), 0) / validTimes.length
    const stdDev = Math.sqrt(variance)
    const score = Math.max(0, 100 - stdDev * 50)
    return { score: score.toFixed(1), stdDev: stdDev.toFixed(3), mean: formatLapTime(mean) }
  }, [chartData])

  const driverInfo = drivers.find(d => d.driver_number === parseInt(selectedDriver))

  return (
    <div className="max-w-[1440px] mx-auto section-padding">
      <div className="mb-8">
        <h1 className="text-3xl sm:text-4xl font-bold text-white mb-2">Lap Analysis Lab</h1>
        <p className="text-white/50">Deep dive into lap times, sectors, and pace analysis</p>
      </div>

      {/* Controls */}
      <Card className="mb-6">
        <CardContent className="py-4">
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
            <Select
              label="Year"
              value={year}
              onChange={setYear}
              options={[{ value: '2024', label: '2024' }, { value: '2023', label: '2023' }]}
            />
            <Select
              label="Session"
              value={selectedSession}
              onChange={setSelectedSession}
              placeholder="Select session"
              options={sessions.map(s => ({
                value: s.session_key,
                label: `${s.circuit_short_name} - ${s.session_name}`,
              }))}
            />
            <Select
              label="Driver"
              value={selectedDriver}
              onChange={setSelectedDriver}
              placeholder="All drivers"
              options={[
                { value: '', label: 'All Drivers' },
                ...drivers.map(d => ({ value: d.driver_number, label: `${d.name_acronym} #${d.driver_number}` })),
              ]}
            />
            <div className="flex items-end gap-2">
              <Button variant={view === 'table' ? 'primary' : 'outline'} size="sm" onClick={() => setView('table')}>Table</Button>
              <Button variant={view === 'chart' ? 'primary' : 'outline'} size="sm" onClick={() => setView('chart')}>Chart</Button>
              <Button variant={view === 'leaderboard' ? 'primary' : 'outline'} size="sm" onClick={() => setView('leaderboard')}>Best Laps</Button>
            </div>
          </div>
        </CardContent>
      </Card>

      {error && <ErrorState message={error} />}

      {loading && <Skeleton className="h-96 w-full" />}

      {!loading && laps.length > 0 && (
        <>
          {/* Consistency Score */}
          {consistencyScore && selectedDriver && (
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-6">
              <Card>
                <CardContent className="py-4 text-center">
                  <p className="text-white/40 text-xs uppercase tracking-wider mb-1">Consistency Score</p>
                  <p className="text-3xl font-bold text-white">{consistencyScore.score}</p>
                  <p className="text-white/30 text-xs">out of 100</p>
                </CardContent>
              </Card>
              <Card>
                <CardContent className="py-4 text-center">
                  <p className="text-white/40 text-xs uppercase tracking-wider mb-1">Std Deviation</p>
                  <p className="text-3xl font-bold text-white font-mono">{consistencyScore.stdDev}s</p>
                </CardContent>
              </Card>
              <Card>
                <CardContent className="py-4 text-center">
                  <p className="text-white/40 text-xs uppercase tracking-wider mb-1">Average Lap</p>
                  <p className="text-3xl font-bold text-white font-mono">{consistencyScore.mean}</p>
                </CardContent>
              </Card>
            </div>
          )}

          {view === 'chart' && (
            <Card>
              <CardHeader>
                <div className="flex items-center justify-between">
                  <h3 className="text-white font-semibold">Lap Times</h3>
                  <Button variant="ghost" size="sm" onClick={() => exportToCsv(chartData as Record<string, unknown>[], 'lap-times')}>
                    Export CSV
                  </Button>
                </div>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={400}>
                  <ScatterChart>
                    <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
                    <XAxis dataKey="lap" type="number" name="Lap" tick={{ fontSize: 10 }} />
                    <YAxis dataKey="time" type="number" name="Time" domain={['auto', 'auto']} tick={{ fontSize: 10 }} reversed />
                    <Tooltip
                      contentStyle={{ backgroundColor: '#1A1A1A', border: '1px solid rgba(255,255,255,0.1)', borderRadius: '8px' }}
                      formatter={(value: number) => [formatLapTime(value), 'Lap Time']}
                    />
                    <Scatter
                      data={chartData}
                      fill={driverInfo ? `#${driverInfo.team_colour}` : '#E10600'}
                    />
                  </ScatterChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>
          )}

          {view === 'leaderboard' && (
            <Card>
              <CardHeader>
                <h3 className="text-white font-semibold">Best Laps Leaderboard</h3>
              </CardHeader>
              <CardContent className="p-0">
                <div className="overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="border-b border-white/10">
                        <th className="text-left px-4 py-3 text-white/40 font-medium">Pos</th>
                        <th className="text-left px-4 py-3 text-white/40 font-medium">Driver</th>
                        <th className="text-right px-4 py-3 text-white/40 font-medium">Time</th>
                        <th className="text-right px-4 py-3 text-white/40 font-medium">S1</th>
                        <th className="text-right px-4 py-3 text-white/40 font-medium">S2</th>
                        <th className="text-right px-4 py-3 text-white/40 font-medium">S3</th>
                        <th className="text-right px-4 py-3 text-white/40 font-medium">Lap</th>
                        <th className="text-right px-4 py-3 text-white/40 font-medium">Gap</th>
                      </tr>
                    </thead>
                    <tbody>
                      {leaderboard.map((lap, idx) => {
                        const driver = drivers.find(d => d.driver_number === lap.driver_number)
                        const gap = idx === 0 ? 0 : (lap.lap_duration || 0) - (leaderboard[0].lap_duration || 0)
                        return (
                          <tr key={lap.driver_number} className="border-b border-white/5 hover:bg-white/5 transition-colors">
                            <td className="px-4 py-3 text-white font-bold">{idx + 1}</td>
                            <td className="px-4 py-3">
                              <div className="flex items-center gap-2">
                                <span className="w-1 h-6 rounded" style={{ backgroundColor: driver ? `#${driver.team_colour}` : '#888' }} />
                                <span className="text-white font-medium">{driver?.name_acronym || lap.driver_number}</span>
                                <span className="text-white/30 text-xs">{driver?.team_name}</span>
                              </div>
                            </td>
                            <td className="px-4 py-3 text-right font-mono text-white font-medium">{formatLapTime(lap.lap_duration)}</td>
                            <td className="px-4 py-3 text-right font-mono text-white/60">{formatLapTime(lap.duration_sector_1)}</td>
                            <td className="px-4 py-3 text-right font-mono text-white/60">{formatLapTime(lap.duration_sector_2)}</td>
                            <td className="px-4 py-3 text-right font-mono text-white/60">{formatLapTime(lap.duration_sector_3)}</td>
                            <td className="px-4 py-3 text-right text-white/40">{lap.lap_number}</td>
                            <td className="px-4 py-3 text-right font-mono text-white/40">{gap === 0 ? '--' : `+${gap.toFixed(3)}`}</td>
                          </tr>
                        )
                      })}
                    </tbody>
                  </table>
                </div>
              </CardContent>
            </Card>
          )}

          {view === 'table' && (
            <Card>
              <CardHeader>
                <div className="flex items-center justify-between">
                  <h3 className="text-white font-semibold">Lap Data ({laps.filter(l => l.lap_duration).length} laps)</h3>
                  <Button variant="ghost" size="sm" onClick={() => exportToCsv(laps as unknown as Record<string, unknown>[], 'laps')}>
                    Export CSV
                  </Button>
                </div>
              </CardHeader>
              <CardContent className="p-0">
                <div className="overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="border-b border-white/10">
                        <th className="text-left px-4 py-3 text-white/40 font-medium">Lap</th>
                        {!selectedDriver && <th className="text-left px-4 py-3 text-white/40 font-medium">Driver</th>}
                        <th className="text-right px-4 py-3 text-white/40 font-medium">Time</th>
                        <th className="text-right px-4 py-3 text-white/40 font-medium">S1</th>
                        <th className="text-right px-4 py-3 text-white/40 font-medium">S2</th>
                        <th className="text-right px-4 py-3 text-white/40 font-medium">S3</th>
                        <th className="text-center px-4 py-3 text-white/40 font-medium">Compound</th>
                        <th className="text-right px-4 py-3 text-white/40 font-medium">ST Speed</th>
                      </tr>
                    </thead>
                    <tbody>
                      {laps.filter(l => l.lap_duration).slice(0, 100).map(lap => {
                        const driver = drivers.find(d => d.driver_number === lap.driver_number)
                        const stint = stints.find(s =>
                          s.driver_number === lap.driver_number &&
                          lap.lap_number >= s.lap_start && lap.lap_number <= s.lap_end
                        )
                        return (
                          <tr key={`${lap.driver_number}-${lap.lap_number}`} className="border-b border-white/5 hover:bg-white/5">
                            <td className="px-4 py-2 text-white">{lap.lap_number}</td>
                            {!selectedDriver && (
                              <td className="px-4 py-2">
                                <span className="text-white" style={{ color: driver ? `#${driver.team_colour}` : undefined }}>
                                  {driver?.name_acronym || lap.driver_number}
                                </span>
                              </td>
                            )}
                            <td className="px-4 py-2 text-right font-mono text-white">{formatLapTime(lap.lap_duration)}</td>
                            <td className="px-4 py-2 text-right font-mono text-white/60">{formatLapTime(lap.duration_sector_1)}</td>
                            <td className="px-4 py-2 text-right font-mono text-white/60">{formatLapTime(lap.duration_sector_2)}</td>
                            <td className="px-4 py-2 text-right font-mono text-white/60">{formatLapTime(lap.duration_sector_3)}</td>
                            <td className="px-4 py-2 text-center">
                              {stint && (
                                <Badge className="text-xs" style={{ backgroundColor: getCompoundColor(stint.compound) + '30', color: getCompoundColor(stint.compound) } as React.CSSProperties}>
                                  {stint.compound}
                                </Badge>
                              )}
                            </td>
                            <td className="px-4 py-2 text-right font-mono text-white/40">{lap.st_speed || '--'}</td>
                          </tr>
                        )
                      })}
                    </tbody>
                  </table>
                </div>
              </CardContent>
            </Card>
          )}
        </>
      )}

      {!loading && laps.length === 0 && !error && (
        <EmptyState
          title="Select a session to analyze"
          message="Choose a year and session to explore lap times, sector splits, consistency scores, and more."
        />
      )}
    </div>
  )
}
