'use client'

import { useState, useEffect, useMemo } from 'react'
import { Card, CardHeader, CardContent } from '@/components/ui/Card'
import { Select } from '@/components/ui/Select'
import { Button } from '@/components/ui/Button'
import { Skeleton } from '@/components/ui/Skeleton'
import { ErrorState } from '@/components/ui/ErrorState'
import { EmptyState } from '@/components/ui/EmptyState'
import { getSessions, getDrivers, getCarData, getLaps, getLocationData } from '@/lib/api'
import { getMeetings } from '@/lib/api'
import { formatLapTime, getTeamColor, exportToCsv } from '@/lib/utils'
import type { Session, Driver, CarData, Lap, Location } from '@/types'
import {
  LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer,
  CartesianGrid, Legend
} from 'recharts'

export default function TelemetryPage() {
  const [year, setYear] = useState('2024')
  const [sessions, setSessions] = useState<Session[]>([])
  const [selectedSession, setSelectedSession] = useState('')
  const [drivers, setDrivers] = useState<Driver[]>([])
  const [driver1, setDriver1] = useState('')
  const [driver2, setDriver2] = useState('')
  const [laps, setLaps] = useState<Lap[]>([])
  const [selectedLap, setSelectedLap] = useState('')
  const [telemetry1, setTelemetry1] = useState<CarData[]>([])
  const [telemetry2, setTelemetry2] = useState<CarData[]>([])
  const [locations1, setLocations1] = useState<Location[]>([])
  const [locations2, setLocations2] = useState<Location[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [activeChart, setActiveChart] = useState<'speed' | 'throttle' | 'brake' | 'gear' | 'rpm'>('speed')

  // Fetch sessions for year
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

  // Fetch drivers for session
  useEffect(() => {
    if (!selectedSession) return
    getDrivers({ session_key: parseInt(selectedSession) })
      .then(setDrivers)
      .catch(() => setError('Failed to load drivers'))
  }, [selectedSession])

  // Fetch laps for driver1
  useEffect(() => {
    if (!selectedSession || !driver1) return
    getLaps({ session_key: parseInt(selectedSession), driver_number: parseInt(driver1) })
      .then(l => setLaps(l.filter(lap => lap.lap_duration && lap.lap_duration > 0)))
      .catch(() => {})
  }, [selectedSession, driver1])

  // Fetch telemetry
  const loadTelemetry = async () => {
    if (!selectedSession || !driver1 || !selectedLap) return
    setLoading(true)
    setError(null)
    try {
      const lap = laps.find(l => l.lap_number === parseInt(selectedLap))
      if (!lap?.date_start) return

      const dateStart = lap.date_start
      const dateEnd = new Date(new Date(dateStart).getTime() + (lap.lap_duration || 100) * 1000).toISOString()

      const [t1, l1] = await Promise.all([
        getCarData({ session_key: parseInt(selectedSession), driver_number: parseInt(driver1) }),
        getLocationData({ session_key: parseInt(selectedSession), driver_number: parseInt(driver1) }),
      ])

      const filteredT1 = t1.filter(d => d.date >= dateStart && d.date <= dateEnd)
      const filteredL1 = l1.filter(d => d.date >= dateStart && d.date <= dateEnd)
      setTelemetry1(filteredT1)
      setLocations1(filteredL1)

      if (driver2) {
        const [t2, l2] = await Promise.all([
          getCarData({ session_key: parseInt(selectedSession), driver_number: parseInt(driver2) }),
          getLocationData({ session_key: parseInt(selectedSession), driver_number: parseInt(driver2) }),
        ])
        const filteredT2 = t2.filter(d => d.date >= dateStart && d.date <= dateEnd)
        const filteredL2 = l2.filter(d => d.date >= dateStart && d.date <= dateEnd)
        setTelemetry2(filteredT2)
        setLocations2(filteredL2)
      }
    } catch {
      setError('Failed to load telemetry data. Try a different selection.')
    } finally {
      setLoading(false)
    }
  }

  const driver1Info = drivers.find(d => d.driver_number === parseInt(driver1))
  const driver2Info = drivers.find(d => d.driver_number === parseInt(driver2))

  // Merge telemetry data for chart
  const chartData = useMemo(() => {
    if (telemetry1.length === 0) return []
    const maxLen = Math.max(telemetry1.length, telemetry2.length)
    const data = []
    for (let i = 0; i < Math.min(maxLen, 500); i++) {
      const t1 = telemetry1[Math.min(i, telemetry1.length - 1)]
      const t2 = telemetry2.length > 0 ? telemetry2[Math.min(i, telemetry2.length - 1)] : null
      data.push({
        index: i,
        speed1: t1?.speed,
        throttle1: t1?.throttle,
        brake1: t1?.brake,
        gear1: t1?.n_gear,
        rpm1: t1?.rpm,
        drs1: t1?.drs,
        ...(t2 ? {
          speed2: t2.speed,
          throttle2: t2.throttle,
          brake2: t2.brake,
          gear2: t2.n_gear,
          rpm2: t2.rpm,
          drs2: t2.drs,
        } : {}),
      })
    }
    return data
  }, [telemetry1, telemetry2])

  // Track map from location data
  const trackPoints = useMemo(() => {
    const locs = locations1.length > 0 ? locations1 : locations2
    if (locs.length === 0) return null
    const xs = locs.map(l => l.x)
    const ys = locs.map(l => l.y)
    const minX = Math.min(...xs), maxX = Math.max(...xs)
    const minY = Math.min(...ys), maxY = Math.max(...ys)
    const rangeX = maxX - minX || 1, rangeY = maxY - minY || 1
    const scale = 300 / Math.max(rangeX, rangeY)
    return locs.map(l => ({
      x: (l.x - minX) * scale + 20,
      y: (l.y - minY) * scale + 20,
    }))
  }, [locations1, locations2])

  const chartConfig: Record<string, { key1: string; key2: string; label: string; domain?: [number, number] }> = {
    speed: { key1: 'speed1', key2: 'speed2', label: 'Speed (km/h)' },
    throttle: { key1: 'throttle1', key2: 'throttle2', label: 'Throttle (%)', domain: [0, 100] },
    brake: { key1: 'brake1', key2: 'brake2', label: 'Brake', domain: [0, 100] },
    gear: { key1: 'gear1', key2: 'gear2', label: 'Gear', domain: [0, 8] },
    rpm: { key1: 'rpm1', key2: 'rpm2', label: 'RPM' },
  }

  const config = chartConfig[activeChart]

  return (
    <div className="max-w-[1440px] mx-auto section-padding">
      <div className="mb-8">
        <h1 className="text-3xl sm:text-4xl font-bold text-white mb-2">Telemetry Center</h1>
        <p className="text-white/50">Compare driver telemetry traces lap by lap</p>
      </div>

      {/* Controls */}
      <Card className="mb-6">
        <CardContent className="py-4">
          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-4">
            <Select
              label="Year"
              value={year}
              onChange={setYear}
              options={[
                { value: '2024', label: '2024' },
                { value: '2023', label: '2023' },
              ]}
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
              label="Driver 1"
              value={driver1}
              onChange={setDriver1}
              placeholder="Select driver"
              options={drivers.map(d => ({
                value: d.driver_number,
                label: `${d.name_acronym} #${d.driver_number}`,
              }))}
            />
            <Select
              label="Driver 2"
              value={driver2}
              onChange={setDriver2}
              placeholder="(Optional)"
              options={[
                { value: '', label: 'None' },
                ...drivers.filter(d => d.driver_number !== parseInt(driver1)).map(d => ({
                  value: d.driver_number,
                  label: `${d.name_acronym} #${d.driver_number}`,
                })),
              ]}
            />
            <Select
              label="Lap"
              value={selectedLap}
              onChange={setSelectedLap}
              placeholder="Select lap"
              options={laps.map(l => ({
                value: l.lap_number,
                label: `Lap ${l.lap_number} ${l.lap_duration ? `(${formatLapTime(l.lap_duration)})` : ''}`,
              }))}
            />
            <div className="flex items-end">
              <Button onClick={loadTelemetry} disabled={loading || !selectedSession || !driver1 || !selectedLap}>
                {loading ? 'Loading...' : 'Load Telemetry'}
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>

      {error && <ErrorState message={error} onRetry={loadTelemetry} />}

      {chartData.length > 0 && (
        <>
          {/* Chart Type Selector */}
          <div className="flex gap-2 mb-4 flex-wrap">
            {(['speed', 'throttle', 'brake', 'gear', 'rpm'] as const).map(type => (
              <Button
                key={type}
                variant={activeChart === type ? 'primary' : 'outline'}
                size="sm"
                onClick={() => setActiveChart(type)}
              >
                {type.charAt(0).toUpperCase() + type.slice(1)}
              </Button>
            ))}
            <div className="ml-auto">
              <Button
                variant="ghost"
                size="sm"
                onClick={() => exportToCsv(chartData as Record<string, unknown>[], `telemetry-${activeChart}`)}
              >
                Export CSV
              </Button>
            </div>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Main Chart */}
            <Card className="lg:col-span-2">
              <CardHeader>
                <div className="flex items-center gap-4">
                  <h3 className="text-white font-semibold">{config.label}</h3>
                  <div className="flex items-center gap-4 text-xs">
                    {driver1Info && (
                      <span className="flex items-center gap-1">
                        <span className="w-3 h-0.5 rounded" style={{ backgroundColor: `#${driver1Info.team_colour}` }} />
                        {driver1Info.name_acronym}
                      </span>
                    )}
                    {driver2Info && (
                      <span className="flex items-center gap-1">
                        <span className="w-3 h-0.5 rounded" style={{ backgroundColor: `#${driver2Info.team_colour}` }} />
                        {driver2Info.name_acronym}
                      </span>
                    )}
                  </div>
                </div>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={400}>
                  <LineChart data={chartData}>
                    <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
                    <XAxis dataKey="index" tick={{ fontSize: 10 }} />
                    <YAxis domain={config.domain || ['auto', 'auto']} tick={{ fontSize: 10 }} />
                    <Tooltip
                      contentStyle={{ backgroundColor: '#1A1A1A', border: '1px solid rgba(255,255,255,0.1)', borderRadius: '8px' }}
                      labelStyle={{ color: 'rgba(255,255,255,0.5)' }}
                    />
                    <Line
                      type="monotone"
                      dataKey={config.key1}
                      stroke={driver1Info ? `#${driver1Info.team_colour}` : '#E10600'}
                      dot={false}
                      strokeWidth={1.5}
                      name={driver1Info?.name_acronym || 'Driver 1'}
                    />
                    {driver2 && (
                      <Line
                        type="monotone"
                        dataKey={config.key2}
                        stroke={driver2Info ? `#${driver2Info.team_colour}` : '#3671C6'}
                        dot={false}
                        strokeWidth={1.5}
                        name={driver2Info?.name_acronym || 'Driver 2'}
                      />
                    )}
                  </LineChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>

            {/* Mini Track Map */}
            <Card>
              <CardHeader>
                <h3 className="text-white font-semibold text-sm">Track Map</h3>
              </CardHeader>
              <CardContent>
                {trackPoints ? (
                  <svg viewBox="0 0 340 340" className="w-full h-auto">
                    <polyline
                      points={trackPoints.map(p => `${p.x},${p.y}`).join(' ')}
                      fill="none"
                      stroke="rgba(255,255,255,0.2)"
                      strokeWidth="3"
                      strokeLinecap="round"
                      strokeLinejoin="round"
                    />
                  </svg>
                ) : (
                  <div className="flex items-center justify-center h-60 text-white/20 text-sm">
                    Load telemetry to see track map
                  </div>
                )}
              </CardContent>
            </Card>
          </div>

          {/* Speed Trap Analysis */}
          {laps.length > 0 && (
            <Card className="mt-6">
              <CardHeader>
                <h3 className="text-white font-semibold">Speed Trap Data</h3>
              </CardHeader>
              <CardContent>
                <div className="overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="border-b border-white/5">
                        <th className="text-left py-2 text-white/40 font-medium">Lap</th>
                        <th className="text-right py-2 text-white/40 font-medium">Lap Time</th>
                        <th className="text-right py-2 text-white/40 font-medium">S1</th>
                        <th className="text-right py-2 text-white/40 font-medium">S2</th>
                        <th className="text-right py-2 text-white/40 font-medium">S3</th>
                        <th className="text-right py-2 text-white/40 font-medium">I1 Speed</th>
                        <th className="text-right py-2 text-white/40 font-medium">I2 Speed</th>
                        <th className="text-right py-2 text-white/40 font-medium">ST Speed</th>
                      </tr>
                    </thead>
                    <tbody>
                      {laps.slice(0, 20).map(lap => (
                        <tr key={lap.lap_number} className="border-b border-white/5 hover:bg-white/5">
                          <td className="py-2 text-white">{lap.lap_number}</td>
                          <td className="py-2 text-right font-mono text-white">{formatLapTime(lap.lap_duration)}</td>
                          <td className="py-2 text-right font-mono text-white/70">{formatLapTime(lap.duration_sector_1)}</td>
                          <td className="py-2 text-right font-mono text-white/70">{formatLapTime(lap.duration_sector_2)}</td>
                          <td className="py-2 text-right font-mono text-white/70">{formatLapTime(lap.duration_sector_3)}</td>
                          <td className="py-2 text-right font-mono text-white/50">{lap.i1_speed || '--'}</td>
                          <td className="py-2 text-right font-mono text-white/50">{lap.i2_speed || '--'}</td>
                          <td className="py-2 text-right font-mono text-white/50">{lap.st_speed || '--'}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </CardContent>
            </Card>
          )}
        </>
      )}

      {chartData.length === 0 && !loading && !error && (
        <EmptyState
          title="Select a session and drivers"
          message="Choose a session, driver(s), and lap to view telemetry traces. Compare speed, throttle, brake, gear, and RPM data."
        />
      )}

      {loading && (
        <div className="space-y-4">
          <Skeleton className="h-96 w-full" />
          <div className="grid grid-cols-3 gap-4">
            <Skeleton className="h-48" />
            <Skeleton className="h-48" />
            <Skeleton className="h-48" />
          </div>
        </div>
      )}
    </div>
  )
}
