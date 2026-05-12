import type { ReactNode } from 'react'

export const inputNormal =
  'w-full rounded-lg border border-[#1e2133] bg-[#13151f] px-3 py-2 ' +
  'text-[#e8eaf0] placeholder-[#8891a8] focus:outline-none ' +
  'focus:border-[#3b82f6] transition-colors'

export const inputError =
  'w-full rounded-lg border border-[#ef4444] bg-[#13151f] px-3 py-2 ' +
  'text-[#e8eaf0] placeholder-[#8891a8] focus:outline-none ' +
  'focus:border-[#ef4444] transition-colors'

interface FormFieldProps {
  label: string
  error?: string
  children: ReactNode
}

export function FormField({ label, error, children }: FormFieldProps) {
  return (
    <div className="flex flex-col">
      <label className="text-[#8891a8] text-sm mb-1">{label}</label>
      {children}
      {error && (
        <p className="text-[#ef4444] text-xs mt-1">{error}</p>
      )}
    </div>
  )
}
