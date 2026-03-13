import { cn } from '@/lib/utils'

interface HighlightCardProps {
  title: string
  value: string
  subtitle: string
  accentColor: string
  icon: React.ReactNode
  className?: string
}

export function HighlightCard({ title, value, subtitle, accentColor, icon, className }: HighlightCardProps) {
  return (
    <div
      className={cn(
        'relative overflow-hidden rounded-xl border border-white/5 bg-f1-graphite p-5',
        className
      )}
    >
      {/* Accent bar */}
      <div
        className="absolute top-0 left-0 h-1 w-full"
        style={{ background: `linear-gradient(to right, ${accentColor}, transparent)` }}
      />

      <div className="flex items-start justify-between">
        <div className="min-w-0 flex-1">
          <p className="text-xs font-medium uppercase tracking-wider text-white/40">
            {title}
          </p>
          <p className="mt-2 text-2xl font-bold text-f1-white tracking-tight">
            {value}
          </p>
          <p className="mt-1 text-xs text-white/50 truncate">
            {subtitle}
          </p>
        </div>
        <div
          className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg text-sm"
          style={{ backgroundColor: `${accentColor}15`, color: accentColor }}
        >
          {icon}
        </div>
      </div>
    </div>
  )
}
