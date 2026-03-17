import type { Config } from 'tailwindcss'

const config: Config = {
  content: [
    './src/pages/**/*.{js,ts,jsx,tsx,mdx}',
    './src/components/**/*.{js,ts,jsx,tsx,mdx}',
    './src/app/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        f1: {
          red: '#E10600',
          darkRed: '#B30500',
          black: '#0A0A0A',
          carbon: '#111111',
          graphite: '#1A1A1A',
          steel: '#2A2A2A',
          silver: '#C0C0C0',
          white: '#F5F5F5',
          accent: '#E10600',
        },
        team: {
          redbull: '#3671C6',
          ferrari: '#E8002D',
          mercedes: '#27F4D2',
          mclaren: '#FF8000',
          astonmartin: '#229971',
          alpine: '#FF87BC',
          williams: '#64C4FF',
          alphatauri: '#6692FF',
          rb: '#6692FF',
          alfaromeo: '#C92D4B',
          haas: '#B6BABD',
          sauber: '#52E252',
        },
        compound: {
          soft: '#FF3333',
          medium: '#FFC700',
          hard: '#CCCCCC',
          intermediate: '#39B54A',
          wet: '#0067FF',
        },
      },
      fontFamily: {
        sans: ['var(--font-geist-sans)', 'system-ui', 'sans-serif'],
        mono: ['var(--font-geist-mono)', 'monospace'],
        display: ['var(--font-geist-sans)', 'system-ui', 'sans-serif'],
      },
      animation: {
        'fade-in': 'fadeIn 0.5s ease-in-out',
        'slide-up': 'slideUp 0.5s ease-out',
        'slide-in': 'slideIn 0.3s ease-out',
        'pulse-glow': 'pulseGlow 2s ease-in-out infinite',
        'shimmer': 'shimmer 2s linear infinite',
      },
      keyframes: {
        fadeIn: {
          '0%': { opacity: '0' },
          '100%': { opacity: '1' },
        },
        slideUp: {
          '0%': { opacity: '0', transform: 'translateY(20px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
        slideIn: {
          '0%': { opacity: '0', transform: 'translateX(-10px)' },
          '100%': { opacity: '1', transform: 'translateX(0)' },
        },
        pulseGlow: {
          '0%, 100%': { boxShadow: '0 0 5px rgba(225, 6, 0, 0.3)' },
          '50%': { boxShadow: '0 0 20px rgba(225, 6, 0, 0.6)' },
        },
        shimmer: {
          '0%': { backgroundPosition: '-200% 0' },
          '100%': { backgroundPosition: '200% 0' },
        },
      },
      backgroundImage: {
        'gradient-radial': 'radial-gradient(var(--tw-gradient-stops))',
        'carbon-fiber': 'repeating-linear-gradient(45deg, transparent, transparent 2px, rgba(255,255,255,0.02) 2px, rgba(255,255,255,0.02) 4px)',
      },
    },
  },
  plugins: [],
}

export default config
