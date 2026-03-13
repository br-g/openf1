export const featureFlags = {
  liveMode: process.env.NEXT_PUBLIC_FEATURE_LIVE_MODE === 'true',
  premiumMode: process.env.NEXT_PUBLIC_FEATURE_PREMIUM === 'true',
  aiInsights: process.env.NEXT_PUBLIC_FEATURE_AI === 'true',
  newsletter: true,
  socialShare: true,
  csvExport: true,
  quiz: true,
}

export const siteConfig = {
  name: 'PitWall Analytics',
  description: 'Premium Formula 1 data analytics platform powered by OpenF1',
  url: process.env.NEXT_PUBLIC_SITE_URL || 'https://pitwall.analytics',
  ogImage: '/og-default.png',
  links: {
    github: 'https://github.com',
    openf1: 'https://openf1.org',
  },
  availableYears: [2023, 2024, 2025],
  defaultYear: 2025,
}

export const navLinks = [
  { href: '/', label: 'Home' },
  { href: '/season', label: 'Season' },
  { href: '/grand-prix', label: 'Grands Prix' },
  { href: '/drivers', label: 'Drivers' },
  { href: '/teams', label: 'Teams' },
  { href: '/telemetry', label: 'Telemetry' },
  { href: '/laps', label: 'Lap Lab' },
  { href: '/strategy', label: 'Strategy' },
  { href: '/live', label: 'Live', premium: true },
  { href: '/weather', label: 'Weather' },
  { href: '/radio', label: 'Radio' },
  { href: '/race-control', label: 'Race Control' },
]
