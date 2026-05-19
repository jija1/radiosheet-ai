import { useState } from 'react'
import type { ReactNode } from 'react'
import { Link } from 'react-router-dom'

export interface NavItem {
  label: string
  to?: string
  onClick?: () => void
  danger?: boolean
}

interface NavBarProps {
  subtitle?: ReactNode
  rightFixed?: ReactNode
  items: NavItem[]
}

export function NavBar({ subtitle, rightFixed, items }: NavBarProps) {
  const [open, setOpen] = useState(false)

  function renderItem(item: NavItem, mobile?: boolean) {
    const cls = mobile
      ? `block w-full text-left px-4 py-3 text-sm border-b border-[#1e2133] last:border-0 ${item.danger ? 'text-[#ef4444]' : 'text-[#8891a8] hover:text-[#e8eaf0]'} transition-colors`
      : `text-sm transition-colors ${item.danger ? 'text-[#8891a8] hover:text-[#ef4444]' : 'text-[#8891a8] hover:text-[#e8eaf0]'}`

    if (item.to) {
      return (
        <Link
          key={item.label}
          to={item.to}
          className={cls}
          onClick={() => setOpen(false)}
        >
          {item.label}
        </Link>
      )
    }
    return (
      <button
        key={item.label}
        type="button"
        onClick={() => { item.onClick?.(); setOpen(false) }}
        className={cls}
      >
        {item.label}
      </button>
    )
  }

  return (
    <header className="border-b border-[#1e2133] bg-[#13151f] shrink-0 relative">
      <div className="px-4 md:px-6 py-3 flex items-center justify-between gap-3">

        {/* Brand */}
        <div className="flex items-center gap-2 shrink-0">
          <div className="w-7 h-7 rounded-lg bg-[#1a2a4a] flex items-center justify-center">
            <span className="text-[#2E75B6] font-bold text-xs">R</span>
          </div>
          <span className="text-[#e8eaf0] font-medium text-sm">
            Radio<span className="text-[#2E75B6]">Sheet</span> AI
          </span>
          {subtitle && (
            <span className="hidden md:inline text-[#8891a8] text-sm ml-1">{subtitle}</span>
          )}
        </div>

        {/* Desktop nav + rightFixed */}
        <div className="hidden md:flex items-center gap-4 ml-auto">
          {items.map(item => renderItem(item))}
          {rightFixed}
        </div>

        {/* Mobile: rightFixed always visible + hamburger */}
        <div className="flex md:hidden items-center gap-3 ml-auto">
          {rightFixed}
          <button
            type="button"
            onClick={() => setOpen(v => !v)}
            aria-label="Toggle menu"
            className="text-[#8891a8] hover:text-[#e8eaf0] transition-colors p-1"
          >
            {open ? (
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M18 6 6 18M6 6l12 12" />
              </svg>
            ) : (
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M4 6h16M4 12h16M4 18h16" />
              </svg>
            )}
          </button>
        </div>
      </div>

      {/* Mobile subtitle */}
      {subtitle && open && (
        <div className="md:hidden px-4 pb-1 text-[#8891a8] text-xs">{subtitle}</div>
      )}

      {/* Mobile dropdown */}
      {open && (
        <div className="md:hidden bg-[#13151f] border-t border-[#1e2133] absolute top-full left-0 right-0 z-40 shadow-xl">
          {items.map(item => renderItem(item, true))}
        </div>
      )}
    </header>
  )
}
