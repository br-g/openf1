'use client'

import { cn } from '@/lib/utils'

interface SelectProps {
  value: string | number
  onChange: (value: string) => void
  options: { value: string | number; label: string }[]
  placeholder?: string
  className?: string
  label?: string
}

export function Select({ value, onChange, options, placeholder, className, label }: SelectProps) {
  return (
    <div className="flex flex-col gap-1">
      {label && <label className="text-xs text-white/40 uppercase tracking-wider">{label}</label>}
      <select
        value={value}
        onChange={e => onChange(e.target.value)}
        className={cn(
          'bg-f1-steel border border-white/10 rounded-lg px-3 py-2 text-sm text-white',
          'focus:outline-none focus:ring-2 focus:ring-f1-red/50 focus:border-f1-red/50',
          'appearance-none cursor-pointer',
          className
        )}
      >
        {placeholder && <option value="">{placeholder}</option>}
        {options.map(opt => (
          <option key={opt.value} value={opt.value}>{opt.label}</option>
        ))}
      </select>
    </div>
  )
}
