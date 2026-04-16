import Link from 'next/link'
import { QuickLinkCard } from '@/components/cards/QuickLinkCard'
import { HighlightCard } from '@/components/cards/HighlightCard'
import { ComparisonCard } from '@/components/cards/ComparisonCard'
import { RecentSessions } from './RecentSessions'
import { Badge } from '@/components/ui/Badge'

// Quick links configuration
const quickLinks = [
  {
    href: '/drivers',
    icon: <svg className="h-5 w-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5"><circle cx="12" cy="8" r="4" /><path d="M6 21v-2a4 4 0 0 1 4-4h4a4 4 0 0 1 4 4v2" /></svg>,
    label: 'Drivers',
    description: 'Performance stats, lap times, and career data for every driver on the grid.',
  },
  {
    href: '/teams',
    icon: <svg className="h-5 w-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2" /><circle cx="9" cy="7" r="4" /><path d="M23 21v-2a4 4 0 0 0-3-3.87" /><path d="M16 3.13a4 4 0 0 1 0 7.75" /></svg>,
    label: 'Teams',
    description: 'Constructor standings, team performance, and head-to-head battles.',
  },
  {
    href: '/season',
    icon: <svg className="h-5 w-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5"><rect x="3" y="4" width="18" height="18" rx="2" /><path d="M16 2v4M8 2v4M3 10h18" /></svg>,
    label: 'Schedule',
    description: 'Full race calendar with session times and circuit information.',
  },
  {
    href: '/season',
    icon: <svg className="h-5 w-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5"><path d="M8 6h13M8 12h13M8 18h13M3 6h.01M3 12h.01M3 18h.01" /></svg>,
    label: 'Results',
    description: 'Race results, qualifying order, sprint outcomes, and session data.',
  },
  {
    href: '/telemetry',
    icon: <svg className="h-5 w-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5"><path d="M3 3v18h18" strokeLinecap="round" strokeLinejoin="round" /><path d="M7 16l4-8 4 4 4-8" strokeLinecap="round" strokeLinejoin="round" /></svg>,
    label: 'Telemetry',
    description: 'Speed, throttle, brake, and gear data visualized in real-time.',
  },
  {
    href: '/radio',
    icon: <svg className="h-5 w-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5"><path d="M12 1a3 3 0 0 0-3 3v8a3 3 0 0 0 6 0V4a3 3 0 0 0-3-3z" /><path d="M19 10v2a7 7 0 0 1-14 0v-2" /><line x1="12" y1="19" x2="12" y2="23" /><line x1="8" y1="23" x2="16" y2="23" /></svg>,
    label: 'Radio',
    description: 'Team radio communications captured during sessions.',
  },
  {
    href: '/weather',
    icon: <svg className="h-5 w-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5"><path d="M18 10h-1.26A8 8 0 1 0 9 20h9a5 5 0 0 0 0-10z" /></svg>,
    label: 'Weather',
    description: 'Track conditions, temperature, humidity, and wind data.',
  },
  {
    href: '/strategy',
    icon: <svg className="h-5 w-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5"><circle cx="12" cy="12" r="10" /><path d="M12 6v6l4 2" /></svg>,
    label: 'Pit Stops',
    description: 'Pit stop timing, tyre strategy, and stint analysis.',
  },
  {
    href: '/season',
    icon: <svg className="h-5 w-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5"><path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z" /></svg>,
    label: 'Standings',
    description: 'Live championship standings for drivers and constructors.',
  },
]

// 2024 season highlight data
const highlights = [
  {
    title: 'Fastest Lap',
    value: '1:10.166',
    subtitle: 'Carlos Sainz — Australian GP',
    accentColor: '#E10600',
    icon: <svg className="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M13 2L3 14h9l-1 8 10-12h-9l1-8z" /></svg>,
  },
  {
    title: 'Most Overtakes',
    value: '152',
    subtitle: 'Max Verstappen — 2024 Season',
    accentColor: '#3671C6',
    icon: <svg className="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M17 1l4 4-4 4" /><path d="M3 11V9a4 4 0 0 1 4-4h14" /><path d="M7 23l-4-4 4-4" /><path d="M21 13v2a4 4 0 0 1-4 4H3" /></svg>,
  },
  {
    title: 'Biggest Position Gain',
    value: '+18',
    subtitle: 'Kevin Magnussen — Sao Paulo GP',
    accentColor: '#B6BABD',
    icon: <svg className="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M12 19V5M5 12l7-7 7 7" /></svg>,
  },
  {
    title: 'Longest Stint',
    value: '40 laps',
    subtitle: 'Fernando Alonso — Bahrain GP (Hard)',
    accentColor: '#229971',
    icon: <svg className="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><circle cx="12" cy="12" r="10" /><path d="M12 6v6l4 2" /></svg>,
  },
  {
    title: 'Fastest Speed Trap',
    value: '351.7 km/h',
    subtitle: 'Carlos Sainz — Monza Qualifying',
    accentColor: '#FF8000',
    icon: <svg className="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M12 2C6.5 2 2 6.5 2 12s4.5 10 10 10 10-4.5 10-10" /><path d="M12 12l7-7" /><circle cx="12" cy="12" r="2" /></svg>,
  },
]

// Trending comparison data
const comparisons = [
  { driver1: 'Verstappen', driver2: 'Leclerc', team1Color: '#3671C6', team2Color: '#E8002D' },
  { driver1: 'Hamilton', driver2: 'Russell', team1Color: '#E8002D', team2Color: '#27F4D2' },
  { driver1: 'Norris', driver2: 'Piastri', team1Color: '#FF8000', team2Color: '#FF8000' },
]

// Example race control messages
const raceControlMessages = [
  { time: '14:32:07', category: 'Flag', message: 'GREEN FLAG — Track Clear', flag: 'green' },
  { time: '14:28:45', category: 'DRS', message: 'DRS ENABLED', flag: 'none' },
  { time: '14:25:12', category: 'Flag', message: 'YELLOW FLAG in Sector 2', flag: 'yellow' },
  { time: '14:22:30', category: 'Other', message: 'Car 11 (PER) off track Turn 4', flag: 'none' },
  { time: '14:18:00', category: 'SafetyCar', message: 'VIRTUAL SAFETY CAR DEPLOYED', flag: 'yellow' },
]

// Example weather data
const weatherSummary = {
  airTemp: '28.4',
  trackTemp: '42.1',
  humidity: '52',
  windSpeed: '3.2',
  windDirection: '185',
  rainfall: false,
  pressure: '1013.2',
}

export default function HomePage() {
  return (
    <div className="relative">
      {/* ─── Hero Section ─── */}
      <section className="relative overflow-hidden">
        {/* Background layers */}
        <div className="absolute inset-0 bg-gradient-to-b from-f1-black via-f1-carbon to-f1-black" />
        <div className="absolute inset-0 bg-carbon-fiber opacity-40" />
        <div className="absolute inset-0 bg-gradient-to-r from-f1-red/5 via-transparent to-f1-red/5" />

        {/* Radial glow */}
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[800px] h-[400px] bg-f1-red/[0.04] rounded-full blur-[120px]" />

        {/* Decorative grid lines */}
        <div className="absolute inset-0 overflow-hidden pointer-events-none">
          <div className="absolute top-0 left-1/4 w-px h-full bg-gradient-to-b from-transparent via-white/[0.03] to-transparent" />
          <div className="absolute top-0 left-2/4 w-px h-full bg-gradient-to-b from-transparent via-white/[0.03] to-transparent" />
          <div className="absolute top-0 left-3/4 w-px h-full bg-gradient-to-b from-transparent via-white/[0.03] to-transparent" />
        </div>

        <div className="relative mx-auto max-w-7xl px-6 py-28 sm:py-36 lg:py-44">
          <div className="mx-auto max-w-3xl text-center">
            <Badge variant="red" className="mb-6">
              2024 Season Data Available
            </Badge>

            <h1 className="text-4xl font-bold tracking-tight text-f1-white sm:text-5xl lg:text-6xl">
              <span className="block">Live the race</span>
              <span className="block mt-1 bg-gradient-to-r from-f1-red via-f1-red to-red-400 bg-clip-text text-transparent">
                through data
              </span>
            </h1>

            <p className="mt-6 text-base sm:text-lg text-white/40 leading-relaxed max-w-xl mx-auto">
              Premium Formula 1 analytics. Explore telemetry, race strategy,
              driver performance, and real-time data from every session on the calendar.
            </p>

            <div className="mt-10 flex items-center justify-center gap-4">
              <Link
                href="/season"
                className="inline-flex items-center gap-2 rounded-lg bg-f1-red px-6 py-3 text-sm font-semibold text-white shadow-lg shadow-f1-red/20 hover:bg-f1-darkRed transition-all duration-300 hover:shadow-f1-red/30"
              >
                Explore Season
                <svg className="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M5 12h14M12 5l7 7-7 7" strokeLinecap="round" strokeLinejoin="round" />
                </svg>
              </Link>
              <Link
                href="/live"
                className="inline-flex items-center gap-2 rounded-lg border border-white/10 bg-white/5 px-6 py-3 text-sm font-medium text-white/70 hover:bg-white/10 hover:text-white transition-all duration-300"
              >
                <span className="relative flex h-2 w-2">
                  <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-green-400 opacity-75" />
                  <span className="relative inline-flex rounded-full h-2 w-2 bg-green-500" />
                </span>
                Live Timing
              </Link>
            </div>
          </div>
        </div>

        {/* Bottom fade */}
        <div className="absolute bottom-0 left-0 right-0 h-24 bg-gradient-to-t from-f1-black to-transparent" />
      </section>

      {/* ─── Quick Links Grid ─── */}
      <section className="relative mx-auto max-w-7xl px-6 py-16">
        <div className="mb-8">
          <h2 className="text-xl font-bold text-f1-white">Explore</h2>
          <p className="mt-1 text-sm text-white/40">Dive into every aspect of Formula 1 data</p>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
          {quickLinks.map((link) => (
            <QuickLinkCard
              key={link.label}
              href={link.href}
              icon={link.icon}
              label={link.label}
              description={link.description}
            />
          ))}
        </div>
      </section>

      {/* ─── Highlight Cards ─── */}
      <section className="relative mx-auto max-w-7xl px-6 py-16">
        <div className="mb-8">
          <h2 className="text-xl font-bold text-f1-white">2024 Season Highlights</h2>
          <p className="mt-1 text-sm text-white/40">Standout moments from the season so far</p>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-5 gap-4">
          {highlights.map((h) => (
            <HighlightCard
              key={h.title}
              title={h.title}
              value={h.value}
              subtitle={h.subtitle}
              accentColor={h.accentColor}
              icon={h.icon}
            />
          ))}
        </div>
      </section>

      {/* ─── Trending Comparisons ─── */}
      <section className="relative mx-auto max-w-7xl px-6 py-16">
        <div className="mb-8">
          <h2 className="text-xl font-bold text-f1-white">Trending Comparisons</h2>
          <p className="mt-1 text-sm text-white/40">Head-to-head driver battles the community is watching</p>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {comparisons.map((c) => (
            <ComparisonCard
              key={`${c.driver1}-${c.driver2}`}
              driver1={c.driver1}
              driver2={c.driver2}
              team1Color={c.team1Color}
              team2Color={c.team2Color}
            />
          ))}
        </div>
      </section>

      {/* ─── Recent Sessions ─── */}
      <section className="relative mx-auto max-w-7xl px-6 py-16">
        <div className="mb-8">
          <h2 className="text-xl font-bold text-f1-white">Recent Sessions</h2>
          <p className="mt-1 text-sm text-white/40">Latest sessions from the 2024 calendar</p>
        </div>

        <RecentSessions />
      </section>

      {/* ─── What's Happening on Track ─── */}
      <section className="relative mx-auto max-w-7xl px-6 py-16 pb-24">
        <div className="mb-8">
          <h2 className="text-xl font-bold text-f1-white">What&apos;s Happening on Track</h2>
          <p className="mt-1 text-sm text-white/40">Race control messages and track conditions</p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Race Control Messages */}
          <div className="lg:col-span-2 rounded-xl border border-white/5 bg-f1-graphite overflow-hidden">
            <div className="px-5 py-3 border-b border-white/5 flex items-center justify-between">
              <div className="flex items-center gap-2">
                <svg className="h-4 w-4 text-white/40" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
                  <path d="M14.857 17.082a23.848 23.848 0 0 0 5.454-1.31A8.967 8.967 0 0 1 18 9.75V9A6 6 0 0 0 6 9v.75a8.967 8.967 0 0 1-2.312 6.022c1.733.64 3.56 1.085 5.455 1.31m5.714 0a24.255 24.255 0 0 1-5.714 0m5.714 0a3 3 0 1 1-5.714 0" />
                </svg>
                <h3 className="text-sm font-semibold text-f1-white">Race Control</h3>
              </div>
              <Badge variant="outline">Example Data</Badge>
            </div>
            <div className="divide-y divide-white/5">
              {raceControlMessages.map((msg, i) => (
                <div key={i} className="flex items-start gap-3 px-5 py-3 hover:bg-white/[0.02] transition-colors">
                  <span className="text-[10px] font-mono text-white/30 pt-0.5 shrink-0 w-14">
                    {msg.time}
                  </span>
                  <div className="flex items-center gap-2 min-w-0 flex-1">
                    {msg.flag === 'green' && (
                      <div className="h-2 w-2 rounded-full bg-green-500 shrink-0" />
                    )}
                    {msg.flag === 'yellow' && (
                      <div className="h-2 w-2 rounded-full bg-yellow-500 shrink-0" />
                    )}
                    {msg.flag === 'none' && (
                      <div className="h-2 w-2 rounded-full bg-white/20 shrink-0" />
                    )}
                    <p className="text-xs text-white/60 truncate">{msg.message}</p>
                  </div>
                  <Badge
                    variant={
                      msg.category === 'Flag' ? 'yellow'
                        : msg.category === 'SafetyCar' ? 'red'
                          : 'default'
                    }
                    className="shrink-0"
                  >
                    {msg.category}
                  </Badge>
                </div>
              ))}
            </div>
          </div>

          {/* Weather Summary */}
          <div className="rounded-xl border border-white/5 bg-f1-graphite overflow-hidden">
            <div className="px-5 py-3 border-b border-white/5 flex items-center justify-between">
              <div className="flex items-center gap-2">
                <svg className="h-4 w-4 text-white/40" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
                  <path d="M18 10h-1.26A8 8 0 1 0 9 20h9a5 5 0 0 0 0-10z" />
                </svg>
                <h3 className="text-sm font-semibold text-f1-white">Track Conditions</h3>
              </div>
              <Badge variant="green">Dry</Badge>
            </div>
            <div className="p-5 space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <p className="text-[10px] uppercase tracking-wider text-white/30 mb-1">Air Temp</p>
                  <p className="text-lg font-bold text-f1-white">{weatherSummary.airTemp}&deg;C</p>
                </div>
                <div>
                  <p className="text-[10px] uppercase tracking-wider text-white/30 mb-1">Track Temp</p>
                  <p className="text-lg font-bold text-f1-white">{weatherSummary.trackTemp}&deg;C</p>
                </div>
                <div>
                  <p className="text-[10px] uppercase tracking-wider text-white/30 mb-1">Humidity</p>
                  <p className="text-lg font-bold text-f1-white">{weatherSummary.humidity}%</p>
                </div>
                <div>
                  <p className="text-[10px] uppercase tracking-wider text-white/30 mb-1">Wind</p>
                  <p className="text-lg font-bold text-f1-white">{weatherSummary.windSpeed} m/s</p>
                </div>
              </div>
              <div className="pt-3 border-t border-white/5">
                <div className="flex items-center justify-between">
                  <p className="text-[10px] uppercase tracking-wider text-white/30">Pressure</p>
                  <p className="text-xs font-mono text-white/50">{weatherSummary.pressure} hPa</p>
                </div>
                <div className="flex items-center justify-between mt-2">
                  <p className="text-[10px] uppercase tracking-wider text-white/30">Wind Dir</p>
                  <p className="text-xs font-mono text-white/50">{weatherSummary.windDirection}&deg;</p>
                </div>
                <div className="flex items-center justify-between mt-2">
                  <p className="text-[10px] uppercase tracking-wider text-white/30">Rainfall</p>
                  <p className="text-xs font-mono text-white/50">{weatherSummary.rainfall ? 'Yes' : 'No'}</p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>
    </div>
  )
}
