import type { ReactNode } from 'react'
import { Pencil } from 'lucide-react'
import { useNavigate } from 'react-router-dom'

import { ScrollReveal } from '../../components/ui/ScrollReveal'

const FEATURES: { icon: ReactNode; title: string; desc: string }[] = [
  {
    icon: '📋',
    title: 'Generate Run-Sheets',
    desc: 'AI-powered scheduling in seconds. Fill in your programme details and get a fully structured, time-coded broadcast schedule instantly.',
  },
  {
    icon: '⚠️',
    title: 'Detect Conflicts',
    desc: '10 rules catch problems before broadcast — consecutive adverts, duration overruns, missing station IDs, talk fatigue, and more.',
  },
  {
    icon: '📡',
    title: 'Broadcasting Compliance',
    desc: 'Ghana broadcasting standards built in. Compliance scoring against industry best practice keeps your station on the right side of regulation.',
  },
  {
    icon: <Pencil size={28} className="text-[#2E75B6]" />,
    title: 'Interactive Editing',
    desc: 'Edit, reorder and fine-tune every segment directly on the timeline — changes update instantly.',
  },
]

const STATS = [
  { value: '121', label: 'Tests', sub: 'battle-tested reliability' },
  { value: '10',  label: 'Conflict Rules', sub: 'comprehensive scheduling validation' },
  { value: '80+', label: 'Smart Recommendations', sub: 'intelligent, Ghana-specific advice' },
  { value: '8',   label: 'Programme Types', sub: 'morning, drive, news, sports, talk, religious, farmer, music' },
]

const STEPS = [
  { n: '1', text: 'Enter your programme details' },
  { n: '2', text: 'System generates your run-sheet — edit and refine it live' },
  { n: '3', text: 'Review conflicts and apply fixes' },
  { n: '4', text: 'Export or broadcast with confidence' },
]

export default function LandingPage() {
  const navigate = useNavigate()

  return (
    <>
      <style>{`
        html { scroll-behavior: smooth; }
        @keyframes gradient-shift {
          0%   { background-position: 0%   50%; }
          50%  { background-position: 100% 50%; }
          100% { background-position: 0%   50%; }
        }
        .hero-bg {
          background: linear-gradient(-45deg, #0f1117, #0d1a2d, #0f1117, #091520);
          background-size: 400% 400%;
          animation: gradient-shift 18s ease infinite;
        }
        @keyframes float-up {
          0%, 100% { transform: translateY(0);    opacity: 0.18; }
          50%       { transform: translateY(-14px); opacity: 0.35; }
        }
        .dot { animation: float-up var(--dur, 6s) ease-in-out infinite; animation-delay: var(--delay, 0s); }
        @keyframes fade-in-up {
          from { opacity: 0; transform: translateY(18px); }
          to   { opacity: 1; transform: translateY(0);    }
        }
        @keyframes hero-scale-in {
          from { opacity: 0; transform: scale(0.96); }
          to   { opacity: 1; transform: scale(1);    }
        }
        .hero-heading { animation: hero-scale-in 800ms ease-out both; }
        .fade-in { animation: fade-in-up 0.6s ease-out both; }
        .fade-in-1 { animation-delay: 0.15s; }
        .fade-in-2 { animation-delay: 0.35s; }
        .fade-in-3 { animation-delay: 0.55s; }
        .card-hover { transition: transform 200ms ease, box-shadow 200ms ease, border-color 200ms ease; }
        .card-hover:hover {
          transform: translateY(-3px);
          box-shadow: 0 10px 28px rgba(46,117,182,0.18);
          border-color: #2E75B6 !important;
        }
        .stat-hover { transition: transform 200ms ease, box-shadow 200ms ease, border-color 200ms ease; }
        .stat-hover:hover {
          transform: translateY(-2px);
          box-shadow: 0 6px 18px rgba(46,117,182,0.12);
          border-color: #2E75B6 !important;
        }
        .btn-primary { transition: background-color 150ms ease, transform 150ms ease, box-shadow 150ms ease; }
        .btn-primary:hover { transform: translateY(-2px); box-shadow: 0 8px 20px rgba(46,117,182,0.28); }
        .btn-primary:active { transform: translateY(0); box-shadow: 0 2px 6px rgba(46,117,182,0.15); }
        .nav-link { position: relative; }
        .nav-link::after {
          content: ''; position: absolute; bottom: -2px; left: 0;
          width: 0; height: 1px; background: #2E75B6;
          transition: width 200ms ease;
        }
        .nav-link:hover::after { width: 100%; }
        @media (prefers-reduced-motion: reduce) {
          html { scroll-behavior: auto; }
          * { animation: none !important; transition: none !important; }
          .btn-primary:hover, .card-hover:hover, .stat-hover:hover {
            transform: none !important; box-shadow: none !important;
          }
        }
      `}</style>

      <div className="min-h-screen bg-[#0f1117] text-[#e8eaf0]">

        {/* ── Nav ──────────────────────────────────────────────────── */}
        <header className="sticky top-0 z-30 bg-[#0f1117]/90 backdrop-blur border-b border-[#1e2133]">
          <div className="max-w-6xl mx-auto px-6 h-14 flex items-center justify-between">
            <span className="font-bold text-[#2E75B6] text-lg">RadioSheet AI</span>
            <div className="flex items-center gap-6 text-sm text-[#8891a8]">
              <button onClick={() => navigate('/login')}    className="nav-link hover:text-[#e8eaf0] transition-colors">Sign In</button>
              <button
                onClick={() => navigate('/register')}
                className="btn-primary bg-[#2E75B6] hover:bg-[#1a5ea8] text-white px-4 py-1.5 rounded-lg text-sm font-medium"
              >
                Get Started
              </button>
            </div>
          </div>
        </header>

        {/* ── Hero ─────────────────────────────────────────────────── */}
        <section className="hero-bg relative overflow-hidden">
          {/* Decorative floating dots */}
          <div className="pointer-events-none absolute inset-0 overflow-hidden">
            {[
              { top: '20%', left: '10%', size: 3, dur: '7s', delay: '0s'   },
              { top: '60%', left: '80%', size: 4, dur: '9s', delay: '1.5s' },
              { top: '30%', left: '70%', size: 2, dur: '6s', delay: '3s'   },
              { top: '70%', left: '20%', size: 3, dur: '8s', delay: '0.8s' },
              { top: '50%', left: '50%', size: 2, dur: '11s', delay: '2s'  },
              { top: '15%', left: '55%', size: 5, dur: '8s', delay: '1s'   },
              { top: '80%', left: '60%', size: 3, dur: '7s', delay: '4s'   },
            ].map((d, i) => (
              <div
                key={i}
                className="dot absolute rounded-full"
                style={{
                  top: d.top, left: d.left,
                  width: d.size * 4, height: d.size * 4,
                  backgroundColor: '#2E75B6',
                  '--dur': d.dur, '--delay': d.delay,
                } as React.CSSProperties}
              />
            ))}
          </div>

          <div className="relative max-w-4xl mx-auto px-6 py-24 md:py-36 text-center">
            <div className="hero-heading">
              <h1 className="text-4xl md:text-6xl font-bold mb-4" style={{ color: '#2E75B6' }}>
                RadioSheet AI
              </h1>
              <p className="text-lg md:text-2xl text-[#c0c8dd] mb-10 max-w-2xl mx-auto leading-relaxed">
                Intelligent run-sheet planning for Ghana's community radio stations
              </p>
            </div>
            <div className="fade-in fade-in-2 flex flex-col sm:flex-row items-center justify-center gap-4">
              <button
                onClick={() => navigate('/register')}
                className="btn-primary bg-[#2E75B6] hover:bg-[#1a5ea8] text-white px-8 py-3 rounded-xl font-semibold text-base w-full sm:w-auto"
              >
                Get Started
              </button>
              <button
                onClick={() => navigate('/login')}
                className="btn-primary bg-transparent border border-[#1e2133] hover:border-[#2E75B6] text-[#8891a8] hover:text-[#e8eaf0] px-8 py-3 rounded-xl font-semibold text-base w-full sm:w-auto"
              >
                Sign In
              </button>
            </div>
          </div>
        </section>

        {/* ── What It Does ─────────────────────────────────────────── */}
        <section className="py-20 px-6">
          <div className="max-w-5xl mx-auto">
            <ScrollReveal>
              <h2 className="text-2xl md:text-3xl font-semibold text-center text-[#e8eaf0] mb-12">
                What it does
              </h2>
            </ScrollReveal>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              {FEATURES.map((f, i) => (
                <ScrollReveal key={f.title} delay={i * 100}>
                  <div className="card-hover bg-[#13151f] border border-[#1e2133] rounded-2xl p-7 flex flex-col gap-3 h-full">
                    <span className="text-3xl">{f.icon}</span>
                    <h3 className="text-[#e8eaf0] font-semibold text-lg">{f.title}</h3>
                    <p className="text-[#8891a8] text-sm leading-relaxed">{f.desc}</p>
                  </div>
                </ScrollReveal>
              ))}
            </div>
          </div>
        </section>

        {/* ── Why RadioSheet ────────────────────────────────────────── */}
        <section className="py-16 px-6 bg-[#13151f] border-y border-[#1e2133]">
          <div className="max-w-5xl mx-auto">
            <ScrollReveal>
              <h2 className="text-2xl md:text-3xl font-semibold text-center text-[#e8eaf0] mb-12">
                Why RadioSheet?
              </h2>
            </ScrollReveal>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
              {STATS.map((s, i) => (
                <ScrollReveal key={s.label} delay={i * 100}>
                  <div className="stat-hover text-center bg-[#0f1117] border border-[#1e2133] rounded-xl p-5 h-full">
                    <div className="text-3xl md:text-4xl font-bold mb-1" style={{ color: '#2E75B6' }}>
                      {s.value}
                    </div>
                    <div className="text-[#e8eaf0] font-medium text-sm mb-1">{s.label}</div>
                    <div className="text-[#8891a8] text-xs leading-snug">{s.sub}</div>
                  </div>
                </ScrollReveal>
              ))}
            </div>
          </div>
        </section>

        {/* ── How It Works ─────────────────────────────────────────── */}
        <section className="py-20 px-6">
          <div className="max-w-3xl mx-auto">
            <ScrollReveal>
              <h2 className="text-2xl md:text-3xl font-semibold text-center text-[#e8eaf0] mb-12">
                How it works
              </h2>
            </ScrollReveal>
            <div className="space-y-5">
              {STEPS.map((step, i) => (
                <ScrollReveal key={i} delay={i * 100}>
                  <div className="flex items-start gap-5">
                    <div
                      className="shrink-0 w-9 h-9 rounded-full flex items-center justify-center font-bold text-sm text-white"
                      style={{ backgroundColor: '#2E75B6' }}
                    >
                      {step.n}
                    </div>
                    <div className="card-hover bg-[#13151f] border border-[#1e2133] rounded-xl px-5 py-4 flex-1">
                      <p className="text-[#e8eaf0] text-sm">{step.text}</p>
                    </div>
                  </div>
                </ScrollReveal>
              ))}
            </div>
          </div>
        </section>

        {/* ── About ────────────────────────────────────────────────── */}
        <section className="py-16 px-6 bg-[#13151f] border-y border-[#1e2133]">
          <ScrollReveal>
            <div className="max-w-3xl mx-auto text-center">
              <h2 className="text-2xl font-semibold text-[#e8eaf0] mb-6">About</h2>
              <p className="text-[#8891a8] leading-relaxed">
                RadioSheet AI was built as a final year BSc IT project at GIMPA, Ghana. It applies
                rule-based expert system principles to a real problem faced by community FM stations
                across Ghana — the lack of accessible, intelligent tools for programme planning.
              </p>
              <button
                onClick={() => navigate('/info')}
                className="mt-6 text-[#2E75B6] hover:text-[#1a5ea8] text-sm nav-link"
              >
                Learn more →
              </button>
            </div>
          </ScrollReveal>
        </section>

        {/* ── CTA ──────────────────────────────────────────────────── */}
        <section className="py-20 px-6 text-center">
          <ScrollReveal>
            <h2 className="text-2xl md:text-3xl font-semibold text-[#e8eaf0] mb-4">
              Ready to plan your next broadcast?
            </h2>
            <p className="text-[#8891a8] mb-8">Built for community FM stations across Ghana.</p>
            <button
              onClick={() => navigate('/register')}
              className="btn-primary bg-[#2E75B6] hover:bg-[#1a5ea8] text-white px-10 py-3 rounded-xl font-semibold text-base"
            >
              Create your first run-sheet
            </button>
          </ScrollReveal>
        </section>

        {/* ── Footer ───────────────────────────────────────────────── */}
        <footer className="border-t border-[#1e2133] py-8 px-6 text-center">
          <nav className="flex flex-wrap items-center justify-center gap-x-6 gap-y-2 text-sm text-[#8891a8] mb-3">
            <button onClick={() => navigate('/info#about')} className="nav-link hover:text-[#e8eaf0] transition-colors">About</button>
            <button onClick={() => navigate('/info#how')} className="nav-link hover:text-[#e8eaf0] transition-colors">How it works</button>
            <button onClick={() => navigate('/info#faq')} className="nav-link hover:text-[#e8eaf0] transition-colors">FAQ</button>
            <button onClick={() => navigate('/info#contact')} className="nav-link hover:text-[#e8eaf0] transition-colors">Contact</button>
          </nav>
          <p className="text-[#4a5166] text-sm">RadioSheet AI © 2026 · GIMPA BSc IT</p>
        </footer>

      </div>
    </>
  )
}
