'use client'

import { useMemo } from 'react'
import {
  LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid,
} from 'recharts'

export interface PointsSeriesEntry {
  name: string
  color: string
  /** Cumulative points keyed by round number */
  pointsByRound: Record<number, number>
}

interface PointsChartProps {
  series: PointsSeriesEntry[]
  /** Total number of rounds to display on X axis */
  rounds: number
  height?: number
  xLabel?: string
}

export function PointsChart({ series, rounds, height = 400, xLabel = 'Round' }: PointsChartProps) {
  const chartData = useMemo(() => {
    if (!series.length || rounds === 0) return []

    const data: Record<string, number | string>[] = []
    for (let r = 1; r <= rounds; r++) {
      const point: Record<string, number | string> = { round: r }
      series.forEach(s => {
        point[s.name] = s.pointsByRound[r] ?? 0
      })
      data.push(point)
    }
    return data
  }, [series, rounds])

  if (!chartData.length) return null

  return (
    <ResponsiveContainer width="100%" height={height}>
      <LineChart data={chartData} margin={{ top: 8, right: 16, left: 0, bottom: 8 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.06)" />
        <XAxis
          dataKey="round"
          stroke="rgba(255,255,255,0.3)"
          tick={{ fill: 'rgba(255,255,255,0.5)', fontSize: 11 }}
          label={{ value: xLabel, position: 'insideBottom', offset: -2, fill: 'rgba(255,255,255,0.4)', fontSize: 11 }}
        />
        <YAxis
          stroke="rgba(255,255,255,0.3)"
          tick={{ fill: 'rgba(255,255,255,0.5)', fontSize: 11 }}
          label={{ value: 'Points', angle: -90, position: 'insideLeft', fill: 'rgba(255,255,255,0.4)', fontSize: 11 }}
        />
        <Tooltip
          contentStyle={{
            backgroundColor: '#1A1A1A',
            border: '1px solid rgba(255,255,255,0.1)',
            borderRadius: '8px',
            fontSize: '12px',
            color: '#fff',
          }}
          labelFormatter={(round: number) => `Round ${round}`}
        />
        {series.map(s => (
          <Line
            key={s.name}
            type="monotone"
            dataKey={s.name}
            stroke={s.color}
            strokeWidth={2}
            dot={{ r: 3, fill: s.color }}
            activeDot={{ r: 5 }}
          />
        ))}
      </LineChart>
    </ResponsiveContainer>
  )
}
