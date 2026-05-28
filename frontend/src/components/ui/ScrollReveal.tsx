import type { CSSProperties, ReactNode } from 'react'

import { useScrollReveal } from '../../hooks/useScrollReveal'

interface ScrollRevealProps {
  children: ReactNode
  delay?: number
  duration?: number
  translateY?: number
  className?: string
  as?: 'div' | 'section' | 'article' | 'header' | 'footer' | 'li' | 'span'
  threshold?: number
}

export function ScrollReveal({
  children,
  delay = 0,
  duration = 500,
  translateY = 24,
  className = '',
  as: Tag = 'div',
  threshold,
}: ScrollRevealProps) {
  const { ref, visible } = useScrollReveal<HTMLDivElement>({ threshold })

  const style: CSSProperties = {
    opacity: visible ? 1 : 0,
    transform: visible ? 'translateY(0)' : `translateY(${translateY}px)`,
    transition: `opacity ${duration}ms ease-out ${delay}ms, transform ${duration}ms ease-out ${delay}ms`,
    willChange: 'opacity, transform',
  }

  const Component = Tag as 'div'
  return (
    <Component ref={ref} style={style} className={className}>
      {children}
    </Component>
  )
}
