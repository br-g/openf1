'use client'

import { useMemo } from 'react'
import {
  LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid,
} from 'recharts'
import type { Position, Driver } from '@/types'
import { getTeamColor } from '@/lib/utils'

interface PositionChartProps {
  positions: Position[]
  drivers: Driver[]
  height?: number
}

interface LapDataPoint {
  lap: number
  [driverKey: string]: number
}

export function PositionChart({ positions, drivers, height = 400 }: PositionChartProps) {
  const driverMap = useMemo(() => {
    const map = new Map<number, Driver>()
    drivers.forEach(d => {
      if (!map.has(d.driver_number)) map.set(d.driver_number, d)
    })
    return map
  }, [drivers])

  const { chartData, driverNumbers } = useMemo(() => {
    if (!positions.length) return { chartData: [], driverNumbers: [] }

    // Group positions by driver, then extract per-lap snapshots
    const byDriver = new Map<number, Map<number, number>>()
    const allDriverNums = new Set<number>()

    // Sort by date so we process in order
    const sorted = [...positions].sort(
      (a, b) => new Date(a.date).getTime() - new Date(b.date).getTime()
    )

    // We infer "lap" by the order of position updates per driver.
    // Group position changes into sequential entries per driver.
    sorted.forEach(p => {
      allDriverNums.add(p.driver_number)
      if (!byDriver.has(p.driver_number)) byDriver.set(p.driver_number, new Map())
      const driverPositions = byDriver.get(p.driver_number)!
      const currentLap = driverPositions.size + 1
      driverPositions.set(currentLap, p.position)
    })

    // Find the max number of data points
    let maxLaps = 0
    byDriver.forEach(laps => {
      if (laps.size > maxLaps) maxLaps = laps.size
    })

    // Cap at a reasonable number of data points for performance
    const step = maxLaps > 200 ? Math.ceil(maxLaps / 100) : 1

    const data: LapDataPoint[] = []
    for (let lap = 1; lap <= maxLaps; lap += step) {
      const point: LapDataPoint = { lap }
      byDriver.forEach((laps, driverNum) => {
        // Find the closest lap data point at or before this lap
        let pos: number | undefined
        for (let l = lap; l >= Math.max(1, lap - step); l--) {
          if (laps.has(l)) { pos = laps.get(l); break }
        }
        if (pos !== undefined) {
          point[`d${driverNum}`] = pos
        }
      })
      data.push(point)
    }

    return {
      chartData: data,
      driverNumbers: Array.from(allDriverNums),
    }
  }, [positions])

  if (!chartData.length) return null

  return (
    <ResponsiveContainer width="100%" height={height}>
      <LineChart data={chartData} margin={{ top: 8, right: 16, left: 0, bottom: 8 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.06)" />
        <XAxis
          dataKey="lap"
          stroke="rgba(255,255,255,0.3)"
          tick={{ fill: 'rgba(255,255,255,0.5)', fontSize: 11 }}
          label={{ value: 'Lap', position: 'insideBottom', offset: -2, fill: 'rgba(255,255,255,0.4)', fontSize: 11 }}
        />
        <YAxis
          reversed
          domain={[1, 20]}
          stroke="rgba(255,255,255,0.3)"
          tick={{ fill: 'rgba(255,255,255,0.5)', fontSize: 11 }}
          label={{ value: 'Position', angle: -90, position: 'insideLeft', fill: 'rgba(255,255,255,0.4)', fontSize: 11 }}
          allowDecimals={false}
        />
        <Tooltip
          contentStyle={{
            backgroundColor: '#1A1A1A',
            border: '1px solid rgba(255,255,255,0.1)',
            borderRadius: '8px',
            fontSize: '12px',
            color: '#fff',
          }}
          formatter={(value: number, name: string) => {
            const num = parseInt(name.replace('d', ''))
            const driver = driverMap.get(num)
            return [
              `P${value}`,
              driver ? `${driver.name_acronym} (${driver.driver_number})` : `#${num}`,
            ]
          }}
          labelFormatter={(lap: number) => `Lap ${lap}`}
        />
        {driverNumbers.map(num => {
          const driver = driverMap.get(num)
          const color = driver ? getTeamColor(driver.team_name) : '#888'
          return (
            <Line
              key={num}
              type="stepAfter"
              dataKey={`d${num}`}
              stroke={color}
              strokeWidth={1.5}
              dot={false}
              connectNulls
              name={`d${num}`}
            />
          )
        })}
      </LineChart>
    </ResponsiveContainer>
  )
}
