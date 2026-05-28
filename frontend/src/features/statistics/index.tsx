import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'

import { deleteStatistic, listStatistics, upsertStatistic } from '../../api/user'
import type { UserStatistic } from '../../api/user'
import { BackButton } from '../../components/ui/BackButton'
import { useAuthStore } from '../../store/authStore'
import { useToastStore } from '../../store/toastStore'
import { NavBar } from '../../components/layout/NavBar'

/* ── Helpers ─────────────────────────────────────────────────────────────── */

type AudienceMap = Record<string, number>

const TIME_RE = /^([01]?\d|2[0-3]):([0-5]\d)\s*[-–]\s*([01]?\d|2[0-3]):([0-5]\d)$/

function parseJsonOr<T>(raw: string, fallback: T): T {
  try {
    const parsed = JSON.parse(raw)
    return parsed === null || parsed === undefined ? fallback : (parsed as T)
  } catch {
    return fallback
  }
}

/** Parse "HH:MM-HH:MM,HH:MM-HH:MM" or legacy JSON ({label,start_time,end_time}). */
function parseTimeRanges(raw: string | undefined | null): string[] {
  if (!raw) return []
  // Legacy JSON object → migrate to "HH:MM-HH:MM"
  if (raw.trim().startsWith('{')) {
    try {
      const obj = JSON.parse(raw) as { start_time?: string; end_time?: string }
      if (obj.start_time && obj.end_time) return [`${obj.start_time}-${obj.end_time}`]
    } catch {
      /* ignore */
    }
    return []
  }
  return raw
    .split(/[;,]/)
    .map((piece) => piece.trim())
    .filter((piece) => TIME_RE.test(piece))
    .map((piece) => piece.replace(/\s*[-–]\s*/, '-'))
}

function formatRanges(ranges: string[]): string {
  return ranges.join(',')
}

function parseCsv(raw: string | undefined | null): string[] {
  if (!raw) return []
  return raw
    .split(/[;,]/)
    .map((s) => s.trim())
    .filter(Boolean)
}

/* ── Page ────────────────────────────────────────────────────────────────── */

export default function StatisticsPage() {
  const logout = useAuthStore((s) => s.logout)
  const navigate = useNavigate()
  const toast = useToastStore()

  const [stats, setStats] = useState<Record<string, UserStatistic>>({})
  const [loading, setLoading] = useState(true)
  const [savingKey, setSavingKey] = useState<string | null>(null)

  useEffect(() => {
    listStatistics()
      .then((items) => {
        const map: Record<string, UserStatistic> = {}
        for (const s of items) map[s.stat_key] = s
        setStats(map)
      })
      .catch(() => toast.error('Could not load statistics'))
      .finally(() => setLoading(false))
  }, [toast])

  async function saveStat(stat_key: string, stat_value: string, notes?: string | null) {
    setSavingKey(stat_key)
    try {
      const updated = await upsertStatistic({ stat_key, stat_value, notes: notes ?? null })
      setStats((prev) => ({ ...prev, [stat_key]: updated }))
      toast.success('Saved')
    } catch {
      toast.error('Could not save')
    } finally {
      setSavingKey(null)
    }
  }

  async function removeStat(stat_key: string) {
    try {
      await deleteStatistic(stat_key)
      setStats((prev) => {
        const next = { ...prev }
        delete next[stat_key]
        return next
      })
      toast.success('Removed')
    } catch {
      toast.error('Could not remove')
    }
  }

  const navItems = [
    { label: 'Dashboard', to: '/dashboard' },
    { label: 'New Run-sheet', to: '/app' },
    { label: 'Settings', to: '/settings' },
    { label: 'Help', to: '/info' },
    { label: 'Sign out', onClick: () => { logout(); navigate('/login') }, danger: true as const },
  ]

  return (
    <div className="min-h-screen bg-[#0f1117] text-[#e8eaf0]">
      <NavBar items={navItems} />

      <main className="max-w-4xl mx-auto px-4 md:px-6 py-8 space-y-8">
        <BackButton />

        <div>
          <h1 className="text-2xl font-semibold text-[#2E75B6]">My Station Stats</h1>
          <p className="text-[#8891a8] text-sm mt-1">
            Tell the engine what you know about your audience. These values feed into
            recommendations whenever you generate or edit a run-sheet.
          </p>
        </div>

        {loading ? (
          <div className="space-y-4">
            {[1, 2, 3, 4, 5].map((i) => (
              <div key={i} className="bg-[#13151f] border border-[#1e2133] rounded-xl h-32 animate-pulse" />
            ))}
          </div>
        ) : (
          <>
            <TimeRangesStat
              title="Peak Listening Windows"
              subtitle="When your audience is most active. Replaces the default Accra commute peaks in scheduling analysis."
              statKey="peak_listening_window"
              value={stats['peak_listening_window']}
              saving={savingKey === 'peak_listening_window'}
              onSave={(v, notes) => saveStat('peak_listening_window', v, notes)}
              onClear={() => removeStat('peak_listening_window')}
            />

            <TimeRangesStat
              title="Low Listenership Windows"
              subtitle="Known quiet periods (e.g. Friday market 12:00–14:00). Advert-density warnings during these times are softened."
              statKey="low_listening_window"
              value={stats['low_listening_window']}
              saving={savingKey === 'low_listening_window'}
              onSave={(v, notes) => saveStat('low_listening_window', v, notes)}
              onClear={() => removeStat('low_listening_window')}
            />

            <AudienceSize
              value={stats['audience_size_by_hour']}
              saving={savingKey === 'audience_size_by_hour'}
              onSave={(v, notes) => saveStat('audience_size_by_hour', v, notes)}
              onClear={() => removeStat('audience_size_by_hour')}
            />

            <ChipsStat
              title="Preferred Languages"
              subtitle="Languages your station broadcasts in. Used to weight local-language content recommendations."
              statKey="preferred_languages"
              value={stats['preferred_languages']}
              saving={savingKey === 'preferred_languages'}
              suggestions={['Twi', 'Ga', 'Ewe', 'Dagbani', 'Hausa', 'English', 'Fante', 'Nzema']}
              onSave={(v, notes) => saveStat('preferred_languages', v, notes)}
              onClear={() => removeStat('preferred_languages')}
            />

            <FreeTextStat
              title="Top Performing Slots"
              description="Notes on which slots, days, or formats perform best for your station."
              statKey="top_programme_type"
              value={stats['top_programme_type']}
              saving={savingKey === 'top_programme_type'}
              placeholder="e.g. Saturday 14:00–16:00 family hour drives our highest social engagement"
              onSave={(v, notes) => saveStat('top_programme_type', v, notes)}
              onClear={() => removeStat('top_programme_type')}
            />

            <FreeTextStat
              title="Local Cultural Notes"
              description="Local context the engine surfaces as a tip recommendation."
              statKey="local_cultural_note"
              value={stats['local_cultural_note']}
              saving={savingKey === 'local_cultural_note'}
              placeholder="e.g. Many farmers tune in 04:30–06:30 before heading out"
              onSave={(v, notes) => saveStat('local_cultural_note', v, notes)}
              onClear={() => removeStat('local_cultural_note')}
            />

            <FreeTextStat
              title="Custom Recommendations"
              description="Persistent tips you always want shown alongside generated recommendations."
              statKey="custom_recommendation"
              value={stats['custom_recommendation']}
              saving={savingKey === 'custom_recommendation'}
              placeholder="e.g. Always mention the next community event before the close segment"
              onSave={(v, notes) => saveStat('custom_recommendation', v, notes)}
              onClear={() => removeStat('custom_recommendation')}
            />
          </>
        )}
      </main>
    </div>
  )
}

/* ── Section: Time-range picker (peak / low) ────────────────────────────── */

interface TimeRangesStatProps {
  title: string
  subtitle: string
  statKey: string
  value: UserStatistic | undefined
  saving: boolean
  onSave: (stat_value: string, notes: string) => void
  onClear: () => void
}

function TimeRangesStat({ title, subtitle, value, saving, onSave, onClear }: TimeRangesStatProps) {
  const initialRanges = parseTimeRanges(value?.stat_value)
  const [ranges, setRanges] = useState<string[]>(initialRanges)
  const [start, setStart] = useState('')
  const [end, setEnd] = useState('')
  const [notes, setNotes] = useState(value?.notes ?? '')
  const [error, setError] = useState<string | null>(null)

  function addRange() {
    setError(null)
    if (!start || !end) {
      setError('Pick both a start and end time.')
      return
    }
    if (start >= end) {
      setError('End time must be after start time.')
      return
    }
    const range = `${start}-${end}`
    if (ranges.includes(range)) {
      setError('That window is already listed.')
      return
    }
    setRanges([...ranges, range])
    setStart('')
    setEnd('')
  }

  function removeRange(idx: number) {
    setRanges(ranges.filter((_, i) => i !== idx))
  }

  return (
    <SectionCard title={title} subtitle={subtitle}>
      <p className="text-[#8891a8] text-xs italic">
        This is used to personalise your recommendations and scheduling analysis.
      </p>

      {ranges.length > 0 && (
        <div className="flex flex-wrap gap-2">
          {ranges.map((r, i) => (
            <span
              key={r + i}
              className="inline-flex items-center gap-2 bg-[#1a2a4a] border border-[#2E75B6]/40 rounded-full px-3 py-1 text-sm"
            >
              {r}
              <button
                type="button"
                onClick={() => removeRange(i)}
                className="text-[#8891a8] hover:text-[#ef4444] text-base leading-none"
                aria-label={`Remove window ${r}`}
              >
                ×
              </button>
            </span>
          ))}
        </div>
      )}

      <div className="grid grid-cols-1 sm:grid-cols-[1fr_1fr_auto] gap-3 items-end">
        <LabeledField label="Start time">
          <input
            type="time"
            value={start}
            onChange={(e) => setStart(e.target.value)}
            className={inputCls}
          />
        </LabeledField>
        <LabeledField label="End time">
          <input
            type="time"
            value={end}
            onChange={(e) => setEnd(e.target.value)}
            className={inputCls}
          />
        </LabeledField>
        <button
          type="button"
          onClick={addRange}
          className="bg-[#2E75B6] hover:bg-[#1a5ea8] text-white text-sm px-4 py-2 rounded-lg transition-colors h-fit"
        >
          Add window
        </button>
      </div>

      {error && <p className="text-[#ef4444] text-xs">{error}</p>}

      <LabeledField label="Notes (optional)">
        <textarea
          value={notes}
          onChange={(e) => setNotes(e.target.value)}
          rows={2}
          placeholder="e.g. Based on listener feedback over the last 3 months"
          className={`${inputCls} resize-none`}
        />
      </LabeledField>

      <RowActions
        saving={saving}
        hasValue={Boolean(value)}
        onSave={() => onSave(formatRanges(ranges), notes)}
        onClear={() => {
          setRanges([])
          onClear()
        }}
      />
    </SectionCard>
  )
}

/* ── Section: Audience Size by Hour ─────────────────────────────────────── */

interface AudienceSizeProps {
  value: UserStatistic | undefined
  saving: boolean
  onSave: (stat_value: string, notes: string) => void
  onClear: () => void
}

function AudienceSize({ value, saving, onSave, onClear }: AudienceSizeProps) {
  const initial = value ? parseJsonOr<AudienceMap>(value.stat_value, {}) : {}

  const [hours, setHours] = useState<AudienceMap>(initial)
  const [notes, setNotes] = useState(value?.notes ?? '')
  const [open, setOpen] = useState(Object.keys(initial).length > 0)

  function updateHour(hour: number, raw: string) {
    const n = parseInt(raw, 10)
    setHours((prev) => {
      const next = { ...prev }
      if (raw === '' || isNaN(n)) delete next[String(hour)]
      else next[String(hour)] = n
      return next
    })
  }

  return (
    <SectionCard
      title="Audience Size by Hour"
      subtitle="Optional 24-hour estimates. When provided, recommendations are weighted toward your high-traffic hours."
    >
      <p className="text-[#8891a8] text-xs italic">
        This is used to personalise your recommendations and scheduling analysis.
      </p>

      <button
        type="button"
        onClick={() => setOpen((v) => !v)}
        className="text-[#2E75B6] hover:text-[#1a5ea8] text-sm self-start"
      >
        {open ? '▾ Hide hourly table' : '▸ Show hourly table (most users skip this)'}
      </button>

      {open && (
        <>
          <div className="grid grid-cols-3 sm:grid-cols-6 gap-2">
            {Array.from({ length: 24 }, (_, h) => (
              <div key={h} className="flex flex-col">
                <span className="text-[#8891a8] text-xs">{String(h).padStart(2, '0')}:00</span>
                <input
                  type="number"
                  min={0}
                  value={hours[String(h)] ?? ''}
                  onChange={(e) => updateHour(h, e.target.value)}
                  placeholder="—"
                  className={`${inputCls} text-center px-1`}
                />
              </div>
            ))}
          </div>
          <LabeledField label="Notes (optional)">
            <textarea
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              rows={2}
              placeholder="e.g. Based on listener call-ins during the last quarter"
              className={`${inputCls} resize-none`}
            />
          </LabeledField>
        </>
      )}
      <RowActions
        saving={saving}
        hasValue={Boolean(value)}
        onSave={() => onSave(JSON.stringify(hours), notes)}
        onClear={() => {
          setHours({})
          onClear()
        }}
      />
    </SectionCard>
  )
}

/* ── Section: Chips (preferred languages) ───────────────────────────────── */

interface ChipsStatProps {
  title: string
  subtitle: string
  statKey: string
  value: UserStatistic | undefined
  saving: boolean
  suggestions: string[]
  onSave: (stat_value: string, notes: string) => void
  onClear: () => void
}

function ChipsStat({
  title,
  subtitle,
  value,
  saving,
  suggestions,
  onSave,
  onClear,
}: ChipsStatProps) {
  const initial = parseCsv(value?.stat_value)
  const [chips, setChips] = useState<string[]>(initial)
  const [input, setInput] = useState('')
  const [notes, setNotes] = useState(value?.notes ?? '')

  function add(raw: string) {
    const v = raw.trim()
    if (!v) return
    if (chips.includes(v)) return
    setChips([...chips, v])
    setInput('')
  }

  function remove(idx: number) {
    setChips(chips.filter((_, i) => i !== idx))
  }

  const available = suggestions.filter((s) => !chips.includes(s))

  return (
    <SectionCard title={title} subtitle={subtitle}>
      <p className="text-[#8891a8] text-xs italic">
        This is used to personalise your recommendations and scheduling analysis.
      </p>

      {chips.length > 0 && (
        <div className="flex flex-wrap gap-2">
          {chips.map((c, i) => (
            <span
              key={c + i}
              className="inline-flex items-center gap-2 bg-[#1a2a4a] border border-[#2E75B6]/40 rounded-full px-3 py-1 text-sm"
            >
              {c}
              <button
                type="button"
                onClick={() => remove(i)}
                className="text-[#8891a8] hover:text-[#ef4444] text-base leading-none"
                aria-label={`Remove ${c}`}
              >
                ×
              </button>
            </span>
          ))}
        </div>
      )}

      <div className="flex gap-2">
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === 'Enter') {
              e.preventDefault()
              add(input)
            }
          }}
          placeholder="Type a language and press Enter"
          className={inputCls}
        />
        <button
          type="button"
          onClick={() => add(input)}
          className="bg-[#2E75B6] hover:bg-[#1a5ea8] text-white text-sm px-4 py-1.5 rounded-lg transition-colors"
        >
          Add
        </button>
      </div>

      {available.length > 0 && (
        <div className="flex flex-wrap gap-2">
          {available.map((s) => (
            <button
              key={s}
              type="button"
              onClick={() => add(s)}
              className="text-xs px-2 py-1 rounded-full border border-[#1e2133] text-[#8891a8] hover:text-[#e8eaf0] hover:border-[#2E75B6] transition-colors"
            >
              + {s}
            </button>
          ))}
        </div>
      )}

      <LabeledField label="Notes (optional)">
        <textarea
          value={notes}
          onChange={(e) => setNotes(e.target.value)}
          rows={2}
          placeholder="e.g. Primary language for morning show is Twi"
          className={`${inputCls} resize-none`}
        />
      </LabeledField>

      <RowActions
        saving={saving}
        hasValue={Boolean(value)}
        onSave={() => onSave(chips.join(','), notes)}
        onClear={() => {
          setChips([])
          onClear()
        }}
      />
    </SectionCard>
  )
}

/* ── Section: free text stat ────────────────────────────────────────────── */

interface FreeTextStatProps {
  title: string
  description: string
  statKey: string
  value: UserStatistic | undefined
  placeholder: string
  saving: boolean
  onSave: (stat_value: string, notes: string) => void
  onClear: () => void
}

function FreeTextStat({ title, description, value, placeholder, saving, onSave, onClear }: FreeTextStatProps) {
  const [text, setText] = useState(value?.stat_value ?? '')
  const [notes, setNotes] = useState(value?.notes ?? '')

  return (
    <SectionCard title={title} subtitle={description}>
      <p className="text-[#8891a8] text-xs italic">
        This is used to personalise your recommendations and scheduling analysis.
      </p>
      <LabeledField label="Value">
        <textarea
          value={text}
          onChange={(e) => setText(e.target.value)}
          rows={3}
          placeholder={placeholder}
          className={`${inputCls} resize-none`}
        />
      </LabeledField>
      <LabeledField label="Notes (optional)">
        <textarea
          value={notes}
          onChange={(e) => setNotes(e.target.value)}
          rows={2}
          placeholder="Context or source for this note"
          className={`${inputCls} resize-none`}
        />
      </LabeledField>
      <RowActions
        saving={saving}
        hasValue={Boolean(value)}
        onSave={() => onSave(text, notes)}
        onClear={onClear}
      />
    </SectionCard>
  )
}

/* ── Shared UI ──────────────────────────────────────────────────────────── */

const inputCls =
  'w-full bg-[#0f1117] border border-[#1e2133] rounded-lg px-3 py-2 text-[#e8eaf0] text-sm focus:outline-none focus:border-[#3b82f6] transition-colors'

function SectionCard({ title, subtitle, children }: { title: string; subtitle: string; children: React.ReactNode }) {
  return (
    <section>
      <h2 className="text-[#e8eaf0] font-medium">{title}</h2>
      <p className="text-[#8891a8] text-xs mb-3">{subtitle}</p>
      <div className="bg-[#13151f] border border-[#1e2133] rounded-xl p-6 space-y-4 flex flex-col">
        {children}
      </div>
    </section>
  )
}

function LabeledField({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div>
      <label className="text-[#8891a8] text-xs block mb-1">{label}</label>
      {children}
    </div>
  )
}

interface RowActionsProps {
  saving: boolean
  hasValue: boolean
  onSave: () => void
  onClear: () => void
}

function RowActions({ saving, hasValue, onSave, onClear }: RowActionsProps) {
  return (
    <div className="flex gap-2 justify-end pt-1">
      {hasValue && (
        <button
          type="button"
          onClick={onClear}
          disabled={saving}
          className="text-[#8891a8] hover:text-[#ef4444] text-sm px-3 py-1.5 rounded-lg transition-colors disabled:opacity-50"
        >
          Remove
        </button>
      )}
      <button
        type="button"
        onClick={onSave}
        disabled={saving}
        className="bg-[#2E75B6] hover:bg-[#1a5ea8] disabled:opacity-60 text-white text-sm px-4 py-1.5 rounded-lg transition-colors"
      >
        {saving ? 'Saving…' : 'Save'}
      </button>
    </div>
  )
}
