import { useEffect, useState } from 'react'

const STANDARD_MESSAGES = [
  'Analysing programme structure...',
  'Applying scheduling rules...',
  'Detecting conflicts...',
  'Scoring recommendations...',
  'Finalising run-sheet...',
]

const DEEP_DIVE_MESSAGES = [
  'Analysing programme structure...',
  'Applying all 80+ recommendation rules...',
  'Checking cultural calendar...',
  'Applying mood advisor...',
  'Loading your station statistics...',
  'Detecting conflicts (10 rules)...',
  'Running compliance validation...',
  'Analysing your run-sheet history...',
  'Scoring and ranking recommendations...',
  'Finalising deep dive analysis...',
]

interface GeneratingLoaderProps {
  deepDive?: boolean
}

export function GeneratingLoader({ deepDive = false }: GeneratingLoaderProps) {
  const messages  = deepDive ? DEEP_DIVE_MESSAGES : STANDARD_MESSAGES
  const [msgIdx, setMsgIdx] = useState(0)
  const [fade, setFade]     = useState(true)

  useEffect(() => {
    const interval = setInterval(() => {
      setFade(false)
      setTimeout(() => {
        setMsgIdx(i => (i + 1) % messages.length)
        setFade(true)
      }, 150)
    }, 600)
    return () => clearInterval(interval)
  }, [messages.length])

  return (
    <>
      <style>{`
        @keyframes progress-fill {
          from { width: 0%; }
          to   { width: 100%; }
        }
        .progress-bar {
          animation: progress-fill 2s ease-in-out infinite alternate;
          background: linear-gradient(90deg, #2E75B6, #3b82f6, #2E75B6);
          background-size: 200% 100%;
        }
        .loader-msg {
          transition: opacity 150ms ease;
        }
        .loader-msg.visible   { opacity: 1; }
        .loader-msg.invisible { opacity: 0; }
        @media (prefers-reduced-motion: reduce) {
          .progress-bar { animation: none !important; width: 60% !important; }
          .loader-msg   { transition: none !important; }
        }
      `}</style>

      <div className="flex flex-col items-center gap-6 py-12 px-6">
        {/* Wordmark */}
        <div className="flex items-center gap-2">
          <span className="text-2xl font-bold" style={{ color: '#2E75B6' }}>RadioSheet AI</span>
          {deepDive && (
            <span
              className="text-xs font-semibold px-2 py-0.5 rounded-full"
              style={{ backgroundColor: '#2E75B622', color: '#2E75B6', border: '1px solid #2E75B655' }}
            >
              Deep Dive
            </span>
          )}
        </div>

        {/* Progress bar */}
        <div className="w-64 h-1 bg-[#1e2133] rounded-full overflow-hidden">
          <div className="progress-bar h-full rounded-full" />
        </div>

        {/* Cycling message */}
        <p className={`loader-msg text-[#8891a8] text-sm text-center ${fade ? 'visible' : 'invisible'}`}>
          {messages[msgIdx]}
        </p>
      </div>
    </>
  )
}
