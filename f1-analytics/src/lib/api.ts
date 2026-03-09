import type {
  Meeting,
  Session,
  Driver,
  Lap,
  Stint,
  CarData,
  Location,
  ChampionshipDriver,
  ChampionshipTeam,
} from '@/types'

const BASE_URL = 'https://api.openf1.org/v1'

async function fetchAPI<T>(endpoint: string, params?: Record<string, string | number>): Promise<T> {
  const url = new URL(`${BASE_URL}${endpoint}`)
  if (params) {
    Object.entries(params).forEach(([key, value]) => {
      if (value !== undefined && value !== null && value !== '') {
        url.searchParams.set(key, String(value))
      }
    })
  }
  const res = await fetch(url.toString())
  if (!res.ok) {
    throw new Error(`API error: ${res.status} ${res.statusText}`)
  }
  return res.json()
}

export async function getMeetings(params?: { year?: number }): Promise<Meeting[]> {
  return fetchAPI<Meeting[]>('/meetings', params as Record<string, string | number>)
}

export async function getSessions(params?: {
  year?: number
  meeting_key?: number
  session_type?: string
}): Promise<Session[]> {
  return fetchAPI<Session[]>('/sessions', params as Record<string, string | number>)
}

export async function getDrivers(params?: {
  session_key?: number
  meeting_key?: number
}): Promise<Driver[]> {
  return fetchAPI<Driver[]>('/drivers', params as Record<string, string | number>)
}

export async function getLatestSession(): Promise<Session | null> {
  const sessions = await fetchAPI<Session[]>('/sessions', { session_key: 'latest' } as Record<string, string | number>)
  return sessions.length > 0 ? sessions[0] : null
}

export async function getLaps(params?: {
  session_key?: number
  driver_number?: number
}): Promise<Lap[]> {
  return fetchAPI<Lap[]>('/laps', params as Record<string, string | number>)
}

export async function getStints(params?: {
  session_key?: number
  driver_number?: number
}): Promise<Stint[]> {
  return fetchAPI<Stint[]>('/stints', params as Record<string, string | number>)
}

export async function getCarData(params?: {
  session_key?: number
  driver_number?: number
}): Promise<CarData[]> {
  return fetchAPI<CarData[]>('/car_data', params as Record<string, string | number>)
}

export async function getLocationData(params?: {
  session_key?: number
  driver_number?: number
}): Promise<Location[]> {
  return fetchAPI<Location[]>('/location', params as Record<string, string | number>)
}

export async function getChampionshipDrivers(params?: {
  session_key?: number
}): Promise<ChampionshipDriver[]> {
  return fetchAPI<ChampionshipDriver[]>('/drivers_ranking', params as Record<string, string | number>)
}

export async function getChampionshipTeams(params?: {
  session_key?: number
}): Promise<ChampionshipTeam[]> {
  return fetchAPI<ChampionshipTeam[]>('/teams_ranking', params as Record<string, string | number>)
}
