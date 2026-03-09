'use client'

import Link from 'next/link'

export function Footer() {
  return (
    <footer className="border-t border-white/5 bg-f1-black mt-auto">
      <div className="max-w-[1440px] mx-auto px-4 sm:px-6 py-12">
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-8">
          {/* Brand */}
          <div>
            <div className="flex items-center gap-2 mb-4">
              <div className="w-8 h-8 bg-f1-red rounded-md flex items-center justify-center">
                <span className="text-white font-bold text-sm">PW</span>
              </div>
              <span className="text-white font-bold text-lg">
                Pit<span className="text-f1-red">Wall</span>
              </span>
            </div>
            <p className="text-white/40 text-sm leading-relaxed">
              Premium F1 analytics powered by data. Explore telemetry, race strategy, and performance insights.
            </p>
          </div>

          {/* Explore */}
          <div>
            <h4 className="text-white font-semibold text-sm mb-4 uppercase tracking-wider">Explore</h4>
            <ul className="space-y-2">
              {[
                { href: '/season', label: 'Season Overview' },
                { href: '/drivers', label: 'Drivers' },
                { href: '/teams', label: 'Teams' },
                { href: '/grand-prix', label: 'Grands Prix' },
                { href: '/telemetry', label: 'Telemetry Center' },
              ].map(link => (
                <li key={link.href}>
                  <Link href={link.href} className="text-white/40 hover:text-white text-sm transition-colors">
                    {link.label}
                  </Link>
                </li>
              ))}
            </ul>
          </div>

          {/* Analysis */}
          <div>
            <h4 className="text-white font-semibold text-sm mb-4 uppercase tracking-wider">Analysis</h4>
            <ul className="space-y-2">
              {[
                { href: '/laps', label: 'Lap Analysis' },
                { href: '/strategy', label: 'Race Strategy' },
                { href: '/weather', label: 'Weather Data' },
                { href: '/radio', label: 'Team Radio' },
                { href: '/race-control', label: 'Race Control' },
              ].map(link => (
                <li key={link.href}>
                  <Link href={link.href} className="text-white/40 hover:text-white text-sm transition-colors">
                    {link.label}
                  </Link>
                </li>
              ))}
            </ul>
          </div>

          {/* Newsletter */}
          <div>
            <h4 className="text-white font-semibold text-sm mb-4 uppercase tracking-wider">Stay Updated</h4>
            <p className="text-white/40 text-sm mb-4">Get race insights and analysis delivered to your inbox.</p>
            <form className="flex gap-2" onSubmit={e => e.preventDefault()}>
              <input
                type="email"
                placeholder="your@email.com"
                className="flex-1 bg-f1-steel border border-white/10 rounded-lg px-3 py-2 text-sm text-white placeholder:text-white/30 focus:outline-none focus:ring-2 focus:ring-f1-red/50"
              />
              <button
                type="submit"
                className="px-4 py-2 bg-f1-red hover:bg-f1-darkRed text-white rounded-lg text-sm font-medium transition-colors"
              >
                Join
              </button>
            </form>
          </div>
        </div>

        <div className="mt-12 pt-8 border-t border-white/5">
          <div className="flex flex-col sm:flex-row items-center justify-between gap-4">
            <p className="text-white/30 text-xs">
              &copy; {new Date().getFullYear()} PitWall Analytics. This is an unofficial fan analytics website.
            </p>
            <p className="text-white/20 text-xs text-center sm:text-right">
              Not affiliated with Formula 1, FIA, or Formula One Management. Powered by{' '}
              <a href="https://openf1.org" target="_blank" rel="noopener noreferrer" className="text-white/40 hover:text-white underline">
                OpenF1
              </a>
              .
            </p>
          </div>
        </div>
      </div>
    </footer>
  )
}
