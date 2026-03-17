import { clsx, type ClassValue } from 'clsx'
import { TEAM_COLORS, COMPOUND_COLORS } from '@/types'
import { format, parseISO } from 'date-fns'

export function cn(...inputs: ClassValue[]) {
  return clsx(inputs)
}

export function formatLapTime(seconds: number | null | undefined): string {
  if (seconds == null || seconds <= 0) return '--'
  const mins = Math.floor(seconds / 60)
  const secs = seconds % 60
  if (mins > 0) {
    return `${mins}:${secs.toFixed(3).padStart(6, '0')}`
  }
  return secs.toFixed(3)
}

export function getTeamColor(teamName: string): string {
  return TEAM_COLORS[teamName] || '#888888'
}

export function getCompoundColor(compound: string): string {
  return COMPOUND_COLORS[compound?.toUpperCase()] || '#888888'
}

export function formatDate(dateString: string): string {
  try {
    return format(parseISO(dateString), 'MMM d, yyyy')
  } catch {
    return dateString
  }
}

export function formatDateRange(start: string, end: string): string {
  try {
    const startDate = parseISO(start)
    const endDate = parseISO(end)
    const startStr = format(startDate, 'MMM d')
    const endStr = format(endDate, 'd, yyyy')
    return `${startStr} - ${endStr}`
  } catch {
    return `${start} - ${end}`
  }
}

export function getSessionTypeIcon(sessionType: string): string {
  switch (sessionType) {
    case 'Race':
      return 'flag'
    case 'Qualifying':
    case 'Sprint Qualifying':
    case 'Sprint Shootout':
      return 'clock'
    case 'Sprint':
      return 'zap'
    default:
      return 'wrench'
  }
}

export function exportToCsv(data: Record<string, unknown>[], filename: string): void {
  if (data.length === 0) return
  const headers = Object.keys(data[0])
  const csvContent = [
    headers.join(','),
    ...data.map(row =>
      headers.map(h => {
        const val = row[h]
        if (typeof val === 'string' && val.includes(',')) {
          return `"${val}"`
        }
        return val ?? ''
      }).join(',')
    ),
  ].join('\n')

  const blob = new Blob([csvContent], { type: 'text/csv' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `${filename}.csv`
  a.click()
  URL.revokeObjectURL(url)
}
