import Link from 'next/link'
import { cn, formatDate, getSessionTypeIcon } from '@/lib/utils'
import { Badge } from '@/components/ui/Badge'

interface SessionCardProps {
  sessionKey: number
  meetingName: string
  sessionName: string
  sessionType: string
  dateStart: string
  circuitShortName: string
  countryName: string
  className?: string
}

export function SessionCard({
  sessionKey,
  meetingName,
  sessionName,
  sessionType,
  dateStart,
  circuitShortName,
  countryName,
  className,
}: SessionCardProps) {
  const icon = getSessionTypeIcon(sessionType)

  const badgeVariant =
    sessionType === 'Race' ? 'red' as const
    : sessionType === 'Qualifying' ? 'yellow' as const
    : sessionType === 'Sprint' ? 'blue' as const
    : 'default' as const

  return (
    <Link
      href={`/session/${sessionKey}`}
      className={cn(
        'group block rounded-xl border border-white/5 bg-f1-graphite p-4',
        'hover:border-white/10 hover:bg-f1-steel/50 transition-all duration-300',
        className
      )}
    >
      <div className="flex items-center justify-between mb-3">
        <Badge variant={badgeVariant}>
          <span className="mr-1">{icon}</span>
          {sessionName}
        </Badge>
        <span className="text-[10px] text-white/30 font-mono">
          {formatDate(dateStart)}
        </span>
      </div>
      <h3 className="text-sm font-semibold text-f1-white group-hover:text-white transition-colors truncate">
        {meetingName}
      </h3>
      <p className="mt-1 text-xs text-white/40">
        {circuitShortName} &middot; {countryName}
      </p>
    </Link>
  )
}
