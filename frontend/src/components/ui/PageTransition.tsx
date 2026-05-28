import type { ReactNode } from 'react'

interface PageTransitionProps {
  children: ReactNode
}

export function PageTransition({ children }: PageTransitionProps) {
  return (
    <div className="page-transition">
      <style>{`
        @keyframes page-enter {
          from { opacity: 0; transform: translateY(12px); }
          to   { opacity: 1; transform: translateY(0);    }
        }
        .page-transition {
          animation: page-enter 200ms ease-out both;
        }
        @media (prefers-reduced-motion: reduce) {
          .page-transition { animation: none !important; }
        }
      `}</style>
      {children}
    </div>
  )
}
