'use client'

import { useMemo } from 'react'
import type { Stint, Driver } from '@/types'
import { getCompoundColor, getTeamColor } from '@/lib/utils'

interface StintChartProps {
  stints: Stint[]
  drivers: Driver[]
  height?: number
}

interface DriverStintRow {
  driverNumber: number
  acronym: string
  teamColor: string
  stints: {
    compound: string
    lapStart: number
    lapEnd: number
    color: string
    tyreAge: number
  }[]
}

export function StintChart({ stints, drivers, height }: StintChartProps) {
  const driverMap = useMemo(() => {
    const map = new Map<number, Driver>()
    drivers.forEach(d => {
      if (!map.has(d.driver_number)) map.set(d.driver_number, d)
    })
    return map
  }, [drivers])

  const { rows, maxLap } = useMemo(() => {
    if (!stints.length) return { rows: [], maxLap: 0 }

    const byDriver = new Map<number, Stint[]>()
    let totalMaxLap = 0

    stints.forEach(s => {
      if (!byDriver.has(s.driver_number)) byDriver.set(s.driver_number, [])
      byDriver.get(s.driver_number)!.push(s)
      if (s.lap_end > totalMaxLap) totalMaxLap = s.lap_end
    })

    const driverRows: DriverStintRow[] = []
    byDriver.forEach((driverStints, driverNum) => {
      const driver = driverMap.get(driverNum)
      const sorted = driverStints.sort((a, b) => a.stint_number - b.stint_number)
      driverRows.push({
        driverNumber: driverNum,
        acronym: driver?.name_acronym || `#${driverNum}`,
        teamColor: driver ? getTeamColor(driver.team_name) : '#888',
        stints: sorted.map(s => ({
          compound: s.compound,
          lapStart: s.lap_start,
          lapEnd: s.lap_end,
          color: getCompoundColor(s.compound),
          tyreAge: s.tyre_age_at_start,
        })),
      })
    })

    // Sort by first stint starting position (approximate finishing order)
    driverRows.sort((a, b) => {
      const aTotal = a.stints.reduce((sum, s) => sum + (s.lapEnd - s.lapStart), 0)
      const bTotal = b.stints.reduce((sum, s) => sum + (s.lapEnd - s.lapStart), 0)
      return bTotal - aTotal
    })

    return { rows: driverRows, maxLap: totalMaxLap }
  }, [stints, driverMap])

  if (!rows.length) return null

  const rowHeight = 28
  const computedHeight = height || Math.max(300, rows.length * rowHeight + 60)
  const chartLeftPad = 60
  const chartRightPad = 16

  return (
    <div className="w-full overflow-x-auto">
      <div style={{ minWidth: 500, height: computedHeight }} className="relative">
        {/* Lap axis */}
        <div
          className="absolute top-0 flex justify-between text-[10px] text-white/40"
          style={{ left: chartLeftPad, right: chartRightPad, height: 20 }}
        >
          {Array.from({ length: Math.min(11, maxLap) }, (_, i) => {
            const lap = Math.round((maxLap / 10) * i)
            return (
              <span key={i}>{lap || 1}</span>
            )
          })}
        </div>

        {/* Driver rows */}
        <div className="absolute" style={{ top: 24, left: 0, right: 0, bottom: 0 }}>
          {rows.map((row, idx) => (
            <div
              key={row.driverNumber}
              className="flex items-center"
              style={{ height: rowHeight }}
            >
              {/* Driver label */}
              <div
                className="text-xs font-mono text-white/70 flex-shrink-0 text-right pr-2"
                style={{ width: chartLeftPad }}
              >
                <span
                  className="inline-block w-1 h-3 rounded-sm mr-1.5"
                  style={{ backgroundColor: row.teamColor }}
                />
                {row.acronym}
              </div>

              {/* Stint bars */}
              <div className="flex-1 relative" style={{ marginRight: chartRightPad, height: 18 }}>
                {/* Background track */}
                <div className="absolute inset-0 bg-white/5 rounded-sm" />

                {row.stints.map((stint, sIdx) => {
                  const left = ((stint.lapStart - 1) / maxLap) * 100
                  const width = ((stint.lapEnd - stint.lapStart + 1) / maxLap) * 100
                  return (
                    <div
                      key={sIdx}
                      className="absolute top-0 bottom-0 rounded-sm flex items-center justify-center text-[9px] font-bold text-black/80 transition-opacity hover:opacity-80 cursor-default"
                      style={{
                        left: `${left}%`,
                        width: `${Math.max(width, 0.5)}%`,
                        backgroundColor: stint.color,
                      }}
                      title={`${stint.compound} | Laps ${stint.lapStart}-${stint.lapEnd} | Age: ${stint.tyreAge}`}
                    >
                      {width > 5 ? stint.compound.charAt(0) : ''}
                    </div>
                  )
                })}
              </div>
            </div>
          ))}
        </div>

        {/* Legend */}
        <div
          className="absolute bottom-0 flex items-center gap-4 text-[10px] text-white/50"
          style={{ left: chartLeftPad }}
        >
          {['SOFT', 'MEDIUM', 'HARD', 'INTERMEDIATE', 'WET'].map(c => (
            <div key={c} className="flex items-center gap-1">
              <div className="w-3 h-3 rounded-sm" style={{ backgroundColor: getCompoundColor(c) }} />
              <span>{c}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
