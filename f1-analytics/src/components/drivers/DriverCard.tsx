'use client'

import Link from 'next/link'
import Image from 'next/image'
import type { Driver } from '@/types'
import { cn, getTeamColor } from '@/lib/utils'
import { Card } from '@/components/ui/Card'
import { Badge } from '@/components/ui/Badge'

interface DriverCardProps {
  driver: Driver
  className?: string
}

export function DriverCard({ driver, className }: DriverCardProps) {
  const teamColor = driver.team_colour
    ? `#${driver.team_colour}`
    : getTeamColor(driver.team_name)

  return (
    <Link href={`/drivers/${driver.driver_number}`}>
      <Card hover glow className={cn('relative overflow-hidden group', className)}>
        {/* Team color top border */}
        <div
          className="absolute top-0 left-0 right-0 h-1 transition-all duration-300 group-hover:h-1.5"
          style={{ backgroundColor: teamColor }}
        />

        <div className="p-5 pt-6">
          <div className="flex items-start gap-4">
            {/* Headshot */}
            <div className="relative w-16 h-16 rounded-full overflow-hidden bg-f1-steel flex-shrink-0 border-2 border-white/10">
              {driver.headshot_url ? (
                <Image
                  src={driver.headshot_url}
                  alt={driver.full_name}
                  fill
                  className="object-cover"
                  sizes="64px"
                />
              ) : (
                <div className="w-full h-full flex items-center justify-center text-white/30 text-xl font-bold">
                  {driver.name_acronym}
                </div>
              )}
            </div>

            {/* Info */}
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-2 mb-1">
                <span
                  className="text-2xl font-bold tabular-nums"
                  style={{ color: teamColor }}
                >
                  {driver.driver_number}
                </span>
              </div>
              <h3 className="text-white font-semibold text-sm truncate">
                {driver.full_name}
              </h3>
              <p className="text-white/50 text-xs mt-0.5 truncate">
                {driver.team_name}
              </p>
            </div>

            {/* Acronym badge */}
            <Badge variant="outline" className="flex-shrink-0">
              {driver.name_acronym}
            </Badge>
          </div>
        </div>
      </Card>
    </Link>
  )
}

export function DriverCardSkeleton() {
  return (
    <div className="rounded-xl border border-white/5 bg-f1-graphite p-5 pt-6 relative overflow-hidden">
      <div className="absolute top-0 left-0 right-0 h-1 bg-white/10 animate-pulse" />
      <div className="flex items-start gap-4">
        <div className="w-16 h-16 rounded-full bg-f1-steel animate-pulse flex-shrink-0" />
        <div className="flex-1 space-y-2">
          <div className="h-6 w-12 bg-f1-steel rounded animate-pulse" />
          <div className="h-4 w-32 bg-f1-steel rounded animate-pulse" />
          <div className="h-3 w-24 bg-f1-steel rounded animate-pulse" />
        </div>
      </div>
    </div>
  )
}
