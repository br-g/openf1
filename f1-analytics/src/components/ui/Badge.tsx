import { cn } from '@/lib/utils'

interface BadgeProps {
  children: React.ReactNode
  variant?: 'default' | 'red' | 'green' | 'yellow' | 'blue' | 'outline'
  className?: string
  style?: React.CSSProperties
}

export function Badge({ children, variant = 'default', className, style }: BadgeProps) {
  const variants = {
    default: 'bg-white/10 text-white/80',
    red: 'bg-f1-red/20 text-f1-red',
    green: 'bg-green-500/20 text-green-400',
    yellow: 'bg-yellow-500/20 text-yellow-400',
    blue: 'bg-blue-500/20 text-blue-400',
    outline: 'border border-white/20 text-white/60',
  }

  return (
    <span className={cn('inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium', variants[variant], className)} style={style}>
      {children}
    </span>
  )
}
