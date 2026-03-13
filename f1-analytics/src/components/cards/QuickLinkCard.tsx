import Link from 'next/link'
import { cn } from '@/lib/utils'

interface QuickLinkCardProps {
  href: string
  icon: React.ReactNode
  label: string
  description: string
  className?: string
}

export function QuickLinkCard({ href, icon, label, description, className }: QuickLinkCardProps) {
  return (
    <Link
      href={href}
      className={cn(
        'group relative rounded-xl border border-white/5 bg-f1-graphite p-5',
        'hover:border-f1-red/30 hover:bg-f1-steel/50 transition-all duration-300',
        'hover:shadow-[0_0_30px_rgba(225,6,0,0.08)]',
        className
      )}
    >
      <div className="flex items-start gap-4">
        <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-white/5 text-lg group-hover:bg-f1-red/10 transition-colors duration-300">
          {icon}
        </div>
        <div className="min-w-0">
          <h3 className="text-sm font-semibold text-f1-white group-hover:text-white transition-colors">
            {label}
          </h3>
          <p className="mt-1 text-xs text-white/40 leading-relaxed line-clamp-2">
            {description}
          </p>
        </div>
      </div>
      <div className="absolute bottom-0 left-0 h-[2px] w-0 bg-gradient-to-r from-f1-red to-f1-red/0 group-hover:w-full transition-all duration-500" />
    </Link>
  )
}
