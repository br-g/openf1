'use client'

import { useState, useMemo } from 'react'
import type { Driver, Session } from '@/types'
import { getDrivers, getLatestSession } from '@/lib/api'
import { useOpenF1 } from '@/hooks/useOpenF1'
import { DriverCard, DriverCardSkeleton } from '@/components/drivers/DriverCard'
import { ErrorState } from '@/components/ui/ErrorState'
import { EmptyState } from '@/components/ui/EmptyState'
import { Select } from '@/components/ui/Select'

export default function DriversPage() {
  const [search, setSearch] = useState('')
  const [teamFilter, setTeamFilter] = useState('')

  // Fetch latest session
  const {
    data: session,
    loading: sessionLoading,
    error: sessionError,
  } = useOpenF1<Session | null>(() => getLatestSession())

  // Fetch drivers for the latest session
  const {
    data: drivers,
    loading: driversLoading,
    error: driversError,
    refetch,
  } = useOpenF1<Driver[]>(
    () => getDrivers({ session_key: session!.session_key }),
    [session?.session_key],
    { enabled: !!session }
  )

  const loading = sessionLoading || driversLoading
  const error = sessionError || driversError

  // Get unique team names for filter
  const teams = useMemo(() => {
    if (!drivers) return []
    const uniqueTeams = [...new Set(drivers.map((d) => d.team_name))].sort()
    return uniqueTeams.map((t) => ({ value: t, label: t }))
  }, [drivers])

  // Filter and search drivers
  const filteredDrivers = useMemo(() => {
    if (!drivers) return []
    return drivers.filter((driver) => {
      const matchesSearch =
        !search ||
        driver.full_name.toLowerCase().includes(search.toLowerCase()) ||
        driver.name_acronym.toLowerCase().includes(search.toLowerCase()) ||
        String(driver.driver_number).includes(search)
      const matchesTeam = !teamFilter || driver.team_name === teamFilter
      return matchesSearch && matchesTeam
    })
  }, [drivers, search, teamFilter])

  return (
    <div className="min-h-screen bg-f1-black">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-white mb-2">Drivers</h1>
          {session && (
            <p className="text-white/50 text-sm">
              {session.session_name} &mdash; {session.circuit_short_name},{' '}
              {session.country_name}
            </p>
          )}
        </div>

        {/* Filters */}
        <div className="flex flex-col sm:flex-row gap-4 mb-8">
          <div className="flex-1">
            <div className="relative">
              <svg
                className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-white/30"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
                />
              </svg>
              <input
                type="text"
                placeholder="Search by name or number..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                className="w-full bg-f1-steel border border-white/10 rounded-lg pl-10 pr-4 py-2 text-sm text-white placeholder-white/30 focus:outline-none focus:ring-2 focus:ring-f1-red/50 focus:border-f1-red/50"
              />
            </div>
          </div>
          <div className="w-full sm:w-56">
            <Select
              value={teamFilter}
              onChange={setTeamFilter}
              options={teams}
              placeholder="All Teams"
            />
          </div>
        </div>

        {/* Error state */}
        {error && <ErrorState message={error} onRetry={refetch} />}

        {/* Loading state */}
        {loading && !error && (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
            {Array.from({ length: 20 }).map((_, i) => (
              <DriverCardSkeleton key={i} />
            ))}
          </div>
        )}

        {/* Empty state */}
        {!loading && !error && filteredDrivers.length === 0 && (
          <EmptyState
            title="No drivers found"
            message={
              search || teamFilter
                ? 'Try adjusting your search or filter criteria.'
                : 'No driver data available for this session.'
            }
          />
        )}

        {/* Driver grid */}
        {!loading && !error && filteredDrivers.length > 0 && (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
            {filteredDrivers.map((driver) => (
              <DriverCard key={driver.driver_number} driver={driver} />
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
