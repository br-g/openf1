'use client'

import { useMemo } from 'react'
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  CartesianGrid,
  ScatterChart,
  Scatter,
  Cell,
} from 'recharts'
import type { Lap, Stint } from '@/types'
import { formatLapTime, getCompoundColor } from '@/lib/utils'

interface LapTimesChartProps {
  laps: Lap[]
  stints?: Stint[]
  mode?: 'line' | 'scatter'
  height?: number
  driverColor?: string
}

interface LapDataPoint {
  lap: number
  time: number
  compound: string
  isPitOut: boolean
}

export function LapTimesChart({
  laps,
  stints = [],
  mode = 'scatter',
  height = 300,
  driverColor = '#E10600',
}: LapTimesChartProps) {
  const chartData = useMemo(() => {
    if (!laps || laps.length === 0) return []

    return laps
      .filter((lap) => lap.lap_duration !== null && lap.lap_duration > 0)
      .map((lap) => {
        const stint = stints.find(
          (s) => lap.lap_number >= s.lap_start && lap.lap_number <= s.lap_end
        )
        return {
          lap: lap.lap_number,
          time: lap.lap_duration as number,
          compound: stint?.compound || 'UNKNOWN',
          isPitOut: lap.is_pit_out_lap,
        }
      })
      .sort((a, b) => a.lap - b.lap)
  }, [laps, stints])

  const yDomain = useMemo(() => {
    if (chartData.length === 0) return [0, 120]
    const times = chartData
      .filter((d) => !d.isPitOut)
      .map((d) => d.time)
    if (times.length === 0) return [0, 120]
    const min = Math.min(...times)
    const max = Math.max(...times)
    const padding = (max - min) * 0.15
    return [Math.max(0, min - padding), max + padding]
  }, [chartData])

  if (chartData.length === 0) {
    return (
      <div className="flex items-center justify-center text-white/30 text-sm" style={{ height }}>
        No lap time data available
      </div>
    )
  }

  const CustomTooltip = ({ active, payload }: { active?: boolean; payload?: Array<{ payload: LapDataPoint }> }) => {
    if (!active || !payload || payload.length === 0) return null
    const data = payload[0].payload
    return (
      <div className="bg-f1-black/95 border border-white/10 rounded-lg px-3 py-2 text-xs shadow-xl">
        <p className="text-white font-medium">Lap {data.lap}</p>
        <p className="text-white/70">{formatLapTime(data.time)}</p>
        <div className="flex items-center gap-1.5 mt-1">
          <span
            className="w-2 h-2 rounded-full"
            style={{ backgroundColor: getCompoundColor(data.compound) }}
          />
          <span className="text-white/50">{data.compound}</span>
        </div>
        {data.isPitOut && (
          <p className="text-yellow-400 mt-1">Pit out lap</p>
        )}
      </div>
    )
  }

  if (mode === 'scatter') {
    return (
      <ResponsiveContainer width="100%" height={height}>
        <ScatterChart margin={{ top: 10, right: 10, bottom: 10, left: 10 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
          <XAxis
            dataKey="lap"
            type="number"
            tick={{ fill: 'rgba(255,255,255,0.4)', fontSize: 11 }}
            axisLine={{ stroke: 'rgba(255,255,255,0.1)' }}
            tickLine={false}
            label={{
              value: 'Lap',
              position: 'insideBottomRight',
              offset: -5,
              fill: 'rgba(255,255,255,0.3)',
              fontSize: 11,
            }}
          />
          <YAxis
            dataKey="time"
            type="number"
            domain={yDomain}
            tick={{ fill: 'rgba(255,255,255,0.4)', fontSize: 11 }}
            axisLine={{ stroke: 'rgba(255,255,255,0.1)' }}
            tickLine={false}
            tickFormatter={(v: number) => formatLapTime(v)}
          />
          <Tooltip content={<CustomTooltip />} />
          <Scatter data={chartData} shape="circle">
            {chartData.map((entry, index) => (
              <Cell
                key={`cell-${index}`}
                fill={
                  stints.length > 0
                    ? getCompoundColor(entry.compound)
                    : driverColor
                }
                opacity={entry.isPitOut ? 0.3 : 0.8}
                r={entry.isPitOut ? 3 : 4}
              />
            ))}
          </Scatter>
        </ScatterChart>
      </ResponsiveContainer>
    )
  }

  return (
    <ResponsiveContainer width="100%" height={height}>
      <LineChart data={chartData} margin={{ top: 10, right: 10, bottom: 10, left: 10 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
        <XAxis
          dataKey="lap"
          tick={{ fill: 'rgba(255,255,255,0.4)', fontSize: 11 }}
          axisLine={{ stroke: 'rgba(255,255,255,0.1)' }}
          tickLine={false}
        />
        <YAxis
          domain={yDomain}
          tick={{ fill: 'rgba(255,255,255,0.4)', fontSize: 11 }}
          axisLine={{ stroke: 'rgba(255,255,255,0.1)' }}
          tickLine={false}
          tickFormatter={(v: number) => formatLapTime(v)}
        />
        <Tooltip content={<CustomTooltip />} />
        <Line
          type="monotone"
          dataKey="time"
          stroke={driverColor}
          strokeWidth={2}
          dot={false}
          activeDot={{ r: 4, fill: driverColor, stroke: '#fff', strokeWidth: 1 }}
        />
      </LineChart>
    </ResponsiveContainer>
  )
}
