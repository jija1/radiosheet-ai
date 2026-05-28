import { useEffect, useState } from 'react'
import { Link, useLocation, useNavigate } from 'react-router-dom'

import { ScrollReveal } from '../../components/ui/ScrollReveal'

interface FaqItem {
  q: string
  a: string
}

const FAQS: FaqItem[] = [
  {
    q: 'What is RadioSheet AI?',
    a: 'RadioSheet AI is a decision-support system that helps community FM radio stations plan their broadcasts. It generates structured run-sheets from a few inputs, detects scheduling conflicts using ten built-in rules, and suggests improvements informed by broadcasting best practice.',
  },
  {
    q: 'Is this generative AI?',
    a: 'No. RadioSheet AI is a rule-based expert system. It does not generate creative content, music, or speech. It applies hand-coded scheduling rules, weighted scoring, and broadcasting compliance checks to assist a presenter, not to replace them. This assistive (not generative) distinction is the theoretical foundation of the project.',
  },
  {
    q: 'What programme types are supported?',
    a: 'Eight programme formats are supported: Morning Show, Drive Time, News Hour, Music Only, Talk Show, Sports, Religious, and Farmer/Agricultural. Each has its own segment patterns, talk-to-music ratios, and recommended structures.',
  },
  {
    q: 'What are conflict rules?',
    a: 'Conflict rules are scheduling problems the system catches automatically: consecutive adverts with no buffer (C001), duration overruns (C002), missing station IDs (C003), excessive advert density (C004), segment overlap (C005), and several more covering talk fatigue, content variety, and pacing.',
  },
  {
    q: 'What is broadcasting compliance?',
    a: 'A separate layer of five rules (G001–G005) that scores your run-sheet against general FM broadcasting best practice — opening and periodic station IDs, advert duration limits, advert separation, and programme classification. The score is a 0–100 indicator, with risk bands of compliant (90+), moderate (70–89), and high (below 70).',
  },
  {
    q: 'How does Deep Dive mode work?',
    a: 'Deep Dive mode expands the statistics view with detailed breakdowns of your station’s patterns over time — average compliance scores, conflict frequencies by rule, segment-type distributions, and pacing trends. It is intended for stations that want to study their own broadcasting patterns over weeks or months.',
  },
  {
    q: 'Is my data private?',
    a: 'Yes. Your run-sheets are stored locally to your account on the project server, never shared with any third party, and never used to train any model. You can export or delete your data at any time from the Privacy section in Settings.',
  },
  {
    q: 'How does pattern recognition work?',
    a: 'As you generate run-sheets over time, the system identifies recurring habits — your typical segment ordering, programme lengths, advert placements — and uses those personal patterns to make recommendations that match the way your station already broadcasts, rather than generic suggestions.',
  },
]

function FaqAccordion({ item, index }: { item: FaqItem; index: number }) {
  const [open, setOpen] = useState(false)
  const panelId = `faq-panel-${index}`
  const buttonId = `faq-button-${index}`

  return (
    <div className="bg-[#13151f] border border-[#1e2133] rounded-xl overflow-hidden">
      <button
        type="button"
        id={buttonId}
        aria-expanded={open}
        aria-controls={panelId}
        onClick={() => setOpen((v) => !v)}
        className="w-full text-left px-5 py-4 flex items-center justify-between gap-4 hover:bg-[#161826] transition-colors"
      >
        <span className="text-[#e8eaf0] font-medium text-sm md:text-base">{item.q}</span>
        <span
          aria-hidden="true"
          className="text-[#2E75B6] text-xl shrink-0 transition-transform duration-300"
          style={{ transform: open ? 'rotate(45deg)' : 'rotate(0deg)' }}
        >
          +
        </span>
      </button>
      <div
        id={panelId}
        role="region"
        aria-labelledby={buttonId}
        className="grid transition-[grid-template-rows] duration-300 ease-out"
        style={{ gridTemplateRows: open ? '1fr' : '0fr' }}
      >
        <div className="overflow-hidden">
          <p className="px-5 pb-5 pt-0 text-[#8891a8] text-sm leading-relaxed">{item.a}</p>
        </div>
      </div>
    </div>
  )
}

export default function InfoPage() {
  const navigate = useNavigate()
  const location = useLocation()

  useEffect(() => {
    if (!location.hash) return
    const id = location.hash.slice(1)
    const t = setTimeout(() => {
      const el = document.getElementById(id)
      if (el) el.scrollIntoView({ behavior: 'smooth', block: 'start' })
    }, 50)
    return () => clearTimeout(t)
  }, [location.hash])

  return (
    <div className="min-h-screen bg-[#0f1117] text-[#e8eaf0]" style={{ scrollBehavior: 'smooth' }}>
      <style>{`
        html { scroll-behavior: smooth; }
        .info-nav-link { transition: color 150ms ease; }
        .info-nav-link:hover { color: #e8eaf0; }
        .info-btn { transition: background-color 150ms ease, transform 150ms ease, box-shadow 150ms ease; }
        .info-btn:hover { transform: translateY(-2px); box-shadow: 0 6px 18px rgba(46,117,182,0.25); }
        .info-btn:active { transform: translateY(0); }
        @media (prefers-reduced-motion: reduce) {
          html { scroll-behavior: auto; }
          .info-btn:hover { transform: none !important; box-shadow: none !important; }
        }
      `}</style>

      {/* Header */}
      <header className="sticky top-0 z-30 bg-[#0f1117]/90 backdrop-blur border-b border-[#1e2133]">
        <div className="max-w-5xl mx-auto px-6 h-14 flex items-center justify-between">
          <button
            onClick={() => navigate('/')}
            className="font-bold text-[#2E75B6] text-lg"
          >
            RadioSheet AI
          </button>
          <nav className="flex items-center gap-5 text-sm text-[#8891a8]">
            <a href="#about" className="info-nav-link">About</a>
            <a href="#how" className="info-nav-link hidden sm:inline">How it works</a>
            <a href="#faq" className="info-nav-link">FAQ</a>
            <a href="#contact" className="info-nav-link hidden sm:inline">Contact</a>
          </nav>
        </div>
      </header>

      <main className="max-w-3xl mx-auto px-6 py-16 space-y-20">
        {/* About */}
        <ScrollReveal as="section">
          <section id="about" className="space-y-4 scroll-mt-24">
            <h1 className="text-3xl md:text-4xl font-bold" style={{ color: '#2E75B6' }}>About</h1>
            <p className="text-[#c0c8dd] leading-relaxed">
              RadioSheet AI is a decision-support tool for community FM radio stations across Ghana.
              It was built as a final year BSc Information Technology project at the Ghana Institute
              of Management and Public Administration (GIMPA).
            </p>
            <p className="text-[#8891a8] leading-relaxed">
              The system is deliberately assistive, not generative. It does not write scripts, compose
              music, or imitate a presenter. Instead, it applies rule-based reasoning, weighted
              scoring, and broadcasting compliance checks to a familiar problem: turning a programme
              brief into a workable run-sheet, and catching scheduling problems before they reach air.
            </p>
            <p className="text-[#8891a8] leading-relaxed">
              Community stations are often run by small teams without dedicated scheduling software.
              RadioSheet AI exists to close that gap with a focused, transparent tool whose logic can
              be inspected and defended — not a black box.
            </p>
          </section>
        </ScrollReveal>

        {/* How It Works */}
        <ScrollReveal as="section">
          <section id="how" className="space-y-6 scroll-mt-24">
            <h2 className="text-2xl md:text-3xl font-semibold text-[#e8eaf0]">How it works</h2>
            <ol className="space-y-4">
              {[
                {
                  step: 'Generate',
                  text: 'Enter your programme details — station name, presenter, broadcast date, total duration, programme type, talk-to-music preference, and any fixed segments. The system produces a complete time-coded run-sheet in seconds.',
                },
                {
                  step: 'Review',
                  text: 'Inspect the timeline. Each segment is colour-coded by type. The conflict panel highlights any scheduling rule violations, and the compliance panel reports a 0–100 score against broadcasting best practice.',
                },
                {
                  step: 'Fix',
                  text: 'Apply suggested fixes with a single click, edit segments directly, or drag them to reorder. The conflict and compliance checks re-run live, so you always see the current state of the run-sheet.',
                },
                {
                  step: 'Export',
                  text: 'Print a clean FRI-style table, or export to PDF for your team and station log. Everything you need to broadcast confidently is on one page.',
                },
              ].map((s, i) => (
                <li key={s.step} className="flex items-start gap-4">
                  <div
                    className="shrink-0 w-9 h-9 rounded-full flex items-center justify-center font-bold text-sm text-white"
                    style={{ backgroundColor: '#2E75B6' }}
                  >
                    {i + 1}
                  </div>
                  <div className="bg-[#13151f] border border-[#1e2133] rounded-xl px-5 py-4 flex-1">
                    <h3 className="text-[#e8eaf0] font-semibold text-sm mb-1">{s.step}</h3>
                    <p className="text-[#8891a8] text-sm leading-relaxed">{s.text}</p>
                  </div>
                </li>
              ))}
            </ol>
          </section>
        </ScrollReveal>

        {/* FAQ */}
        <ScrollReveal as="section">
          <section id="faq" className="space-y-6 scroll-mt-24">
            <h2 className="text-2xl md:text-3xl font-semibold text-[#e8eaf0]">Frequently asked questions</h2>
            <div className="space-y-3">
              {FAQS.map((item, i) => (
                <FaqAccordion key={item.q} item={item} index={i} />
              ))}
            </div>
          </section>
        </ScrollReveal>

        {/* Contact */}
        <ScrollReveal as="section">
          <section id="contact" className="space-y-4 scroll-mt-24">
            <h2 className="text-2xl md:text-3xl font-semibold text-[#e8eaf0]">Contact</h2>
            <div className="bg-[#13151f] border border-[#1e2133] rounded-xl p-6 space-y-3">
              <div>
                <p className="text-[#8891a8] text-xs uppercase tracking-wide mb-1">Project author</p>
                <p className="text-[#e8eaf0]">Jija — BSc Information Technology</p>
              </div>
              <div>
                <p className="text-[#8891a8] text-xs uppercase tracking-wide mb-1">Institution</p>
                <p className="text-[#e8eaf0]">Ghana Institute of Management and Public Administration (GIMPA)</p>
              </div>
              <div>
                <p className="text-[#8891a8] text-xs uppercase tracking-wide mb-1">Project status</p>
                <p className="text-[#8891a8] text-sm leading-relaxed">
                  This is an academic final year project. It is not a commercial product. Feedback
                  and questions from community stations and broadcasting practitioners are welcome
                  through the institution.
                </p>
              </div>
            </div>
          </section>
        </ScrollReveal>

        {/* Back to top / home */}
        <ScrollReveal as="section">
          <div className="text-center pt-8">
            <Link
              to="/"
              className="info-btn inline-block bg-[#2E75B6] hover:bg-[#1a5ea8] text-white px-8 py-3 rounded-xl font-semibold text-sm"
            >
              Back to home
            </Link>
          </div>
        </ScrollReveal>
      </main>

      <footer className="border-t border-[#1e2133] py-8 px-6 text-center">
        <p className="text-[#4a5166] text-sm">RadioSheet AI © 2026 · GIMPA BSc IT</p>
      </footer>
    </div>
  )
}
