import Link from 'next/link'
import { cn } from '@/lib/utils'

interface ComparisonCardProps {
  driver1: string
  driver2: string
  team1Color: string
  team2Color: string
  className?: string
}

export function ComparisonCard({ driver1, driver2, team1Color, team2Color, className }: ComparisonCardProps) {
  return (
    <div
      className={cn(
        'relative overflow-hidden rounded-xl border border-white/5 bg-f1-graphite p-5',
        className
      )}
    >
      {/* Split accent */}
      <div className="absolute top-0 left-0 h-1 w-full flex">
        <div className="flex-1" style={{ backgroundColor: team1Color }} />
        <div className="flex-1" style={{ backgroundColor: team2Color }} />
      </div>

      <div className="flex items-center justify-between gap-3">
        <div className="flex items-center gap-3 min-w-0 flex-1">
          <div className="flex items-center gap-2">
            <div className="h-2 w-2 rounded-full" style={{ backgroundColor: team1Color }} />
            <span className="text-sm font-bold text-f1-white whitespace-nowrap">{driver1}</span>
          </div>
          <span className="text-xs font-medium text-white/30 uppercase tracking-wider">vs</span>
          <div className="flex items-center gap-2">
            <div className="h-2 w-2 rounded-full" style={{ backgroundColor: team2Color }} />
            <span className="text-sm font-bold text-f1-white whitespace-nowrap">{driver2}</span>
          </div>
        </div>
      </div>

      <Link
        href="/telemetry"
        className="mt-4 flex items-center justify-center gap-2 rounded-lg border border-white/10 bg-white/5 px-4 py-2 text-xs font-medium text-white/70 hover:bg-f1-red/10 hover:border-f1-red/30 hover:text-f1-white transition-all duration-300"
      >
        <svg className="h-3.5 w-3.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <path d="M3 3v18h18" strokeLinecap="round" strokeLinejoin="round" />
          <path d="M7 16l4-8 4 4 4-8" strokeLinecap="round" strokeLinejoin="round" />
        </svg>
        Compare
      </Link>
    </div>
  )
}
