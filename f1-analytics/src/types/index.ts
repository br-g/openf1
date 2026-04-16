// OpenF1 API Types

export interface Meeting {
  circuit_key: number
  circuit_short_name: string
  circuit_type: string
  country_code: string
  country_key: number
  country_name: string
  date_end: string
  date_start: string
  gmt_offset: string
  location: string
  meeting_key: number
  meeting_name: string
  meeting_official_name: string
  year: number
}

export interface Session {
  circuit_key: number
  circuit_short_name: string
  country_code: string
  country_key: number
  country_name: string
  date_end: string
  date_start: string
  gmt_offset: string
  location: string
  meeting_key: number
  session_key: number
  session_name: string
  session_type: string
  year: number
}

export interface Driver {
  broadcast_name: string
  driver_number: number
  first_name: string
  full_name: string
  headshot_url: string | null
  last_name: string
  meeting_key: number
  name_acronym: string
  session_key: number
  team_colour: string
  team_name: string
}

export interface Lap {
  date_start: string
  driver_number: number
  duration_sector_1: number | null
  duration_sector_2: number | null
  duration_sector_3: number | null
  i1_speed: number | null
  i2_speed: number | null
  is_pit_out_lap: boolean
  lap_duration: number | null
  lap_number: number
  meeting_key: number
  segments_sector_1: number[]
  segments_sector_2: number[]
  segments_sector_3: number[]
  session_key: number
  st_speed: number | null
}

export interface CarData {
  brake: number
  date: string
  driver_number: number
  drs: number
  meeting_key: number
  n_gear: number
  rpm: number
  session_key: number
  speed: number
  throttle: number
}

export interface Location {
  date: string
  driver_number: number
  meeting_key: number
  session_key: number
  x: number
  y: number
  z: number
}

export interface Interval {
  date: string
  driver_number: number
  gap_to_leader: number | string | null
  interval: number | string | null
  meeting_key: number
  session_key: number
}

export interface Position {
  date: string
  driver_number: number
  meeting_key: number
  position: number
  session_key: number
}

export interface Pit {
  date: string
  driver_number: number
  lane_duration: number | null
  lap_number: number
  meeting_key: number
  pit_duration: number | null
  session_key: number
  stop_duration: number | null
}

export interface Stint {
  compound: string
  driver_number: number
  lap_end: number
  lap_start: number
  meeting_key: number
  session_key: number
  stint_number: number
  tyre_age_at_start: number
}

export interface Weather {
  air_temperature: number
  date: string
  humidity: number
  meeting_key: number
  pressure: number
  rainfall: boolean
  session_key: number
  track_temperature: number
  wind_direction: number
  wind_speed: number
}

export interface RaceControl {
  category: string
  date: string
  driver_number: number | null
  flag: string | null
  lap_number: number | null
  meeting_key: number
  message: string
  qualifying_phase: number | null
  scope: string | null
  sector: number | null
  session_key: number
}

export interface TeamRadio {
  date: string
  driver_number: number
  meeting_key: number
  recording_url: string
  session_key: number
}

export interface Overtake {
  date: string
  meeting_key: number
  overtaken_driver_number: number
  overtaking_driver_number: number
  position: number
  session_key: number
}

export interface StartingGrid {
  driver_number: number
  lap_duration: number | null
  meeting_key: number
  position: number
  session_key: number
}

export interface SessionResult {
  dnf: boolean
  dns: boolean
  dsq: boolean
  driver_number: number
  duration: number | number[] | null
  gap_to_leader: number | string | number[] | null
  number_of_laps: number
  meeting_key: number
  position: number
  session_key: number
}

export interface ChampionshipDriver {
  driver_number: number
  meeting_key: number
  points_current: number
  points_start: number
  position_current: number
  position_start: number
  session_key: number
}

export interface ChampionshipTeam {
  meeting_key: number
  points_current: number
  points_start: number
  position_current: number
  position_start: number
  session_key: number
  team_name: string
}

// UI Types
export interface HighlightCard {
  title: string
  value: string
  subtitle: string
  icon: string
  color: string
}

export interface ComparisonPair {
  driver1: string
  driver2: string
  metric: string
}

export interface FilterState {
  year?: number
  meetingKey?: number
  sessionKey?: number
  driverNumber?: number
  teamName?: string
  compound?: string
}

export interface FeatureFlags {
  liveMode: boolean
  premiumMode: boolean
  aiInsights: boolean
}

export type CompoundColor = 'SOFT' | 'MEDIUM' | 'HARD' | 'INTERMEDIATE' | 'WET'

export const COMPOUND_COLORS: Record<string, string> = {
  SOFT: '#FF3333',
  MEDIUM: '#FFC700',
  HARD: '#CCCCCC',
  INTERMEDIATE: '#39B54A',
  WET: '#0067FF',
}

export const TEAM_COLORS: Record<string, string> = {
  'Red Bull Racing': '#3671C6',
  'Ferrari': '#E8002D',
  'Mercedes': '#27F4D2',
  'McLaren': '#FF8000',
  'Aston Martin': '#229971',
  'Alpine': '#FF87BC',
  'Williams': '#64C4FF',
  'AlphaTauri': '#6692FF',
  'RB': '#6692FF',
  'Alfa Romeo': '#C92D4B',
  'Haas F1 Team': '#B6BABD',
  'Kick Sauber': '#52E252',
}

export const SESSION_TYPES = ['Practice 1', 'Practice 2', 'Practice 3', 'Qualifying', 'Sprint', 'Sprint Qualifying', 'Sprint Shootout', 'Race'] as const
