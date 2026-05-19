import { useToastStore } from '../../store/toastStore'
import type { Toast } from '../../store/toastStore'

const COLOUR: Record<string, string> = {
  success: '#22c55e',
  error:   '#ef4444',
  info:    '#2E75B6',
}

function ToastItem({ toast }: { toast: Toast }) {
  const removeToast = useToastStore(s => s.removeToast)
  const colour = COLOUR[toast.type] ?? COLOUR.info

  return (
    <div
      className="flex items-start gap-3 px-4 py-3 rounded-lg shadow-xl text-sm min-w-[260px] max-w-xs"
      style={{ backgroundColor: '#13151f', border: `1px solid ${colour}55` }}
      role="alert"
    >
      <div className="w-1 self-stretch rounded-full shrink-0" style={{ backgroundColor: colour }} />
      <span className="flex-1 text-[#e8eaf0] leading-snug">{toast.message}</span>
      <button
        onClick={() => removeToast(toast.id)}
        className="text-[#4a5166] hover:text-[#8891a8] transition-colors shrink-0 mt-0.5"
        aria-label="Dismiss"
      >
        ✕
      </button>
    </div>
  )
}

export function ToastContainer() {
  const toasts = useToastStore(s => s.toasts)
  if (toasts.length === 0) return null

  return (
    <div className="fixed bottom-6 right-6 z-50 flex flex-col gap-2 pointer-events-none">
      {toasts.map(t => (
        <div key={t.id} className="pointer-events-auto">
          <ToastItem toast={t} />
        </div>
      ))}
    </div>
  )
}
