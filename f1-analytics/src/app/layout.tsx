import type { Metadata } from 'next'
import { GeistSans } from 'geist/font/sans'
import { GeistMono } from 'geist/font/mono'
import { Navbar } from '@/components/layout/Navbar'
import { Footer } from '@/components/layout/Footer'
import './globals.css'

const geistSans = GeistSans
const geistMono = GeistMono

export const metadata: Metadata = {
  title: {
    default: 'PitWall Analytics | F1 Data Intelligence',
    template: '%s | PitWall Analytics',
  },
  description: 'Premium Formula 1 analytics platform. Explore telemetry, race strategy, lap analysis, and driver performance powered by real F1 data.',
  keywords: ['Formula 1', 'F1', 'analytics', 'telemetry', 'race data', 'lap times', 'driver comparison', 'race strategy'],
  authors: [{ name: 'PitWall Analytics' }],
  openGraph: {
    type: 'website',
    locale: 'en_US',
    siteName: 'PitWall Analytics',
    title: 'PitWall Analytics | F1 Data Intelligence',
    description: 'Premium Formula 1 analytics platform powered by real race data.',
  },
  twitter: {
    card: 'summary_large_image',
    title: 'PitWall Analytics',
    description: 'Premium F1 analytics platform',
  },
  robots: {
    index: true,
    follow: true,
  },
}

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode
}>) {
  return (
    <html lang="en" className="dark">
      <body className={`${geistSans.variable} ${geistMono.variable} antialiased bg-f1-black text-f1-white min-h-screen flex flex-col`}>
        <Navbar />
        <main className="flex-1">{children}</main>
        <Footer />
      </body>
    </html>
  )
}
