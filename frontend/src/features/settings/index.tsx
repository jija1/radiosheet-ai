import { useEffect, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'

import { getAuditLog, getMe, getSettings, updateSettings } from '../../api/user'
import type { AuditLogEntry, UserInfo, UserSettings } from '../../api/user'
import { useAuthStore } from '../../store/authStore'
import { useToastStore } from '../../store/toastStore'
import { NavBar } from '../../components/layout/NavBar'

/* ── Helpers ────────────────────────────────────────────────────────────── */

const ACTION_LABELS: Record<string, string> = {
  runsheet_generated:   'Run-sheet Generated',
  fix_applied:          'Conflict Fix Applied',
  segments_updated:     'Segments Updated',
  compliance_validated: 'Compliance Validated',
  export_viewed:        'Export Viewed',
}

function labelFor(action: string): string {
  return ACTION_LABELS[action] ?? action.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase())
}

function fmtDateTime(iso: string): string {
  const d = new Date(iso)
  if (isNaN(d.getTime())) return iso
  return d.toLocaleString('en-GB', {
    day: '2-digit', month: 'short', year: 'numeric',
    hour: '2-digit', minute: '2-digit', second: '2-digit',
  })
}

function fmtDate(iso: string): string {
  if (!iso) return '—'
  const d = new Date(iso)
  if (isNaN(d.getTime())) return iso
  return d.toLocaleDateString('en-GB', { day: '2-digit', month: 'long', year: 'numeric' })
}

/* ── Setting toggle ─────────────────────────────────────────────────────── */

function Toggle({ checked, onChange }: { checked: boolean; onChange: (v: boolean) => void }) {
  return (
    <button
      type="button"
      onClick={() => onChange(!checked)}
      className={`relative w-10 h-5 rounded-full transition-colors ${checked ? 'bg-[#2563eb]' : 'bg-[#1e2133]'}`}
    >
      <span className={`absolute top-0.5 left-0.5 w-4 h-4 bg-white rounded-full transition-transform ${checked ? 'translate-x-5' : ''}`} />
    </button>
  )
}

/* ── Page ───────────────────────────────────────────────────────────────── */

export default function SettingsPage() {
  const logout   = useAuthStore(s => s.logout)
  const navigate = useNavigate()
  const toast    = useToastStore()

  const [userInfo, setUserInfo]     = useState<UserInfo | null>(null)
  const [auditLog, setAuditLog]     = useState<AuditLogEntry[]>([])
  const [settings, setSettings]     = useState<UserSettings | null>(null)
  const [isLoading, setIsLoading]   = useState(true)
  const [isSaving, setIsSaving]     = useState(false)
  const [error, setError]           = useState<string | null>(null)

  useEffect(() => {
    Promise.all([getMe(), getAuditLog(), getSettings()])
      .then(([info, log, prefs]) => {
        setUserInfo(info)
        setAuditLog(log)
        setSettings(prefs)
      })
      .catch(() => setError('Could not load settings data.'))
      .finally(() => setIsLoading(false))
  }, [])

  async function saveSetting<K extends keyof UserSettings>(key: K, value: UserSettings[K]) {
    if (!settings) return
    setSettings(prev => prev ? { ...prev, [key]: value } : prev)
    setIsSaving(true)
    try {
      const updated = await updateSettings({ [key]: value })
      setSettings(updated)
      toast.success('Setting saved')
    } catch {
      toast.error('Failed to save setting')
    } finally {
      setIsSaving(false)
    }
  }

  const navItems = [
    { label: 'Dashboard',     to: '/dashboard' },
    { label: 'New Run-sheet', to: '/' },
    { label: 'Validate',      to: '/validate' },
    { label: 'My Station Stats', to: '/statistics' },
    { label: 'Privacy & Data', to: '/privacy' },
    { label: 'Sign out', onClick: () => { logout(); navigate('/login') }, danger: true as const },
  ]

  const inputCls = 'w-full bg-[#0f1117] border border-[#1e2133] rounded-lg px-3 py-2 text-[#e8eaf0] text-sm focus:outline-none focus:border-[#3b82f6] transition-colors'
  const selectCls = inputCls

  return (
    <div className="min-h-screen bg-[#0f1117] text-[#e8eaf0]">
      <NavBar items={navItems} />

      <main className="max-w-4xl mx-auto px-4 md:px-6 py-8 space-y-8">

        <div>
          <h1 className="text-2xl font-semibold text-[#2E75B6]">Settings</h1>
          <p className="text-[#8891a8] text-sm mt-1">Account details, preferences, and activity history.</p>
        </div>

        {error && (
          <p className="text-[#ef4444] text-sm bg-[#ef444411] border border-[#ef444433] rounded px-4 py-3">
            {error}
          </p>
        )}

        {/* ── Account ─────────────────────────────────────────────────── */}
        <section>
          <h2 className="text-[#e8eaf0] font-medium mb-3">Account</h2>
          <div className="bg-[#13151f] border border-[#1e2133] rounded-xl p-6">
            {isLoading ? (
              <div className="space-y-3">{[1, 2].map(i => (
                <div key={i} className="h-5 bg-[#1e2133] rounded animate-pulse w-48" />
              ))}</div>
            ) : userInfo ? (
              <dl className="space-y-3">
                <div className="flex gap-4">
                  <dt className="text-[#8891a8] text-sm w-32 shrink-0">Email</dt>
                  <dd className="text-[#e8eaf0] text-sm font-medium">{userInfo.email}</dd>
                </div>
                <div className="flex gap-4">
                  <dt className="text-[#8891a8] text-sm w-32 shrink-0">Member since</dt>
                  <dd className="text-[#e8eaf0] text-sm">{fmtDate(userInfo.created_at)}</dd>
                </div>
              </dl>
            ) : null}
          </div>
        </section>

        {/* ── Preferences ─────────────────────────────────────────────── */}
        {settings && (
          <>
            {/* Defaults */}
            <section>
              <h2 className="text-[#e8eaf0] font-medium mb-1">Defaults</h2>
              <p className="text-[#8891a8] text-xs mb-3">Pre-fill the run-sheet form with these values.</p>
              <div className="bg-[#13151f] border border-[#1e2133] rounded-xl p-6 grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                  <label className="text-[#8891a8] text-xs block mb-1">Station Name</label>
                  <input
                    className={inputCls}
                    defaultValue={settings.default_station_name ?? ''}
                    onBlur={e => saveSetting('default_station_name', e.target.value || null)}
                    placeholder="e.g. Gold FM"
                  />
                </div>
                <div>
                  <label className="text-[#8891a8] text-xs block mb-1">Presenter Name</label>
                  <input
                    className={inputCls}
                    defaultValue={settings.default_presenter_name ?? ''}
                    onBlur={e => saveSetting('default_presenter_name', e.target.value || null)}
                    placeholder="e.g. Kofi Mensah"
                  />
                </div>
                <div>
                  <label className="text-[#8891a8] text-xs block mb-1">Programme Type</label>
                  <select
                    className={selectCls}
                    value={settings.default_programme_type ?? ''}
                    onChange={e => saveSetting('default_programme_type', e.target.value || null)}
                  >
                    <option value="">— none —</option>
                    <option value="morning_show">Morning Show</option>
                    <option value="drive_time">Drive-time</option>
                    <option value="news_hour">News Hour</option>
                    <option value="music_only">Music Only</option>
                    <option value="sports_show">Sports Show</option>
                    <option value="talk_show">Talk Show</option>
                    <option value="religious_show">Religious Show</option>
                    <option value="farmer_show">Farmer Show</option>
                  </select>
                </div>
                <div>
                  <label className="text-[#8891a8] text-xs block mb-1">Duration (minutes)</label>
                  <input
                    type="number"
                    className={inputCls}
                    defaultValue={settings.default_duration_minutes ?? ''}
                    onBlur={e => {
                      const v = parseInt(e.target.value, 10)
                      saveSetting('default_duration_minutes', isNaN(v) ? null : v)
                    }}
                    min={15}
                    max={240}
                    placeholder="e.g. 60"
                  />
                </div>
                <div>
                  <label className="text-[#8891a8] text-xs block mb-1">Talk / Music Preference</label>
                  <select
                    className={selectCls}
                    value={settings.default_talk_music_preference ?? ''}
                    onChange={e => saveSetting('default_talk_music_preference', e.target.value || null)}
                  >
                    <option value="">— none —</option>
                    <option value="heavy_music">Heavy Music</option>
                    <option value="balanced">Balanced</option>
                    <option value="talk_heavy">Talk Heavy</option>
                  </select>
                </div>
                <div>
                  <label className="text-[#8891a8] text-xs block mb-1">Max Adverts / Hour</label>
                  <input
                    type="number"
                    className={inputCls}
                    defaultValue={settings.default_max_adverts_per_hour ?? ''}
                    onBlur={e => {
                      const v = parseInt(e.target.value, 10)
                      saveSetting('default_max_adverts_per_hour', isNaN(v) ? null : v)
                    }}
                    min={1}
                    max={6}
                    placeholder="e.g. 3"
                  />
                </div>
              </div>
            </section>

            {/* Display */}
            <section>
              <h2 className="text-[#e8eaf0] font-medium mb-3">Display</h2>
              <div className="bg-[#13151f] border border-[#1e2133] rounded-xl p-6 space-y-4">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-[#e8eaf0] text-sm font-medium">Time Format</p>
                    <p className="text-[#8891a8] text-xs">24-hour or 12-hour clock display</p>
                  </div>
                  <select
                    className="bg-[#0f1117] border border-[#1e2133] rounded px-3 py-1.5 text-[#e8eaf0] text-sm"
                    value={settings.time_format}
                    onChange={e => saveSetting('time_format', e.target.value)}
                  >
                    <option value="24h">24-hour</option>
                    <option value="12h">12-hour</option>
                  </select>
                </div>
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-[#e8eaf0] text-sm font-medium">Recommendation Depth</p>
                    <p className="text-[#8891a8] text-xs">How many recommendations to show</p>
                  </div>
                  <select
                    className="bg-[#0f1117] border border-[#1e2133] rounded px-3 py-1.5 text-[#e8eaf0] text-sm"
                    value={settings.recommendation_depth}
                    onChange={e => saveSetting('recommendation_depth', e.target.value)}
                  >
                    <option value="light">Light</option>
                    <option value="standard">Standard</option>
                    <option value="detailed">Detailed</option>
                  </select>
                </div>
              </div>
            </section>

            {/* Behaviour */}
            <section>
              <h2 className="text-[#e8eaf0] font-medium mb-3">Behaviour</h2>
              <div className="bg-[#13151f] border border-[#1e2133] rounded-xl p-6 space-y-4">
                {(
                  [
                    ['cultural_calendar_enabled', 'Cultural Calendar', 'Enable Ghana public holidays and Sunday/Friday recommendations'],
                    ['strict_mode',               'Strict Mode',       'Treat warnings as blocking errors'],
                    ['auto_apply_fixes',           'Auto-Apply Fixes',  'Automatically apply conflict fixes without confirmation'],
                    ['notifications_enabled',      'Notifications',     'Show toast notifications for actions'],
                  ] as [keyof UserSettings, string, string][]
                ).map(([key, label, desc]) => (
                  <div key={key} className="flex items-center justify-between">
                    <div>
                      <p className="text-[#e8eaf0] text-sm font-medium">{label}</p>
                      <p className="text-[#8891a8] text-xs">{desc}</p>
                    </div>
                    <Toggle
                      checked={Boolean(settings[key])}
                      onChange={v => saveSetting(key, v as UserSettings[typeof key])}
                    />
                  </div>
                ))}
              </div>
            </section>

            {/* Station Profile */}
            <section>
              <h2 className="text-[#e8eaf0] font-medium mb-3">Station Profile</h2>
              <div className="bg-[#13151f] border border-[#1e2133] rounded-xl p-6 grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                  <label className="text-[#8891a8] text-xs block mb-1">Region</label>
                  <select
                    className={selectCls}
                    value={settings.default_region ?? ''}
                    onChange={e => saveSetting('default_region', e.target.value || null)}
                  >
                    <option value="">— not set —</option>
                    {['greater_accra','ashanti','northern','western','volta','eastern','central','upper_east','upper_west','bono','other'].map(r => (
                      <option key={r} value={r}>{r.replace('_', ' ').replace(/\b\w/g, c => c.toUpperCase())}</option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="text-[#8891a8] text-xs block mb-1">Audience Type</label>
                  <select
                    className={selectCls}
                    value={settings.station_audience ?? ''}
                    onChange={e => saveSetting('station_audience', e.target.value || null)}
                  >
                    <option value="">— not set —</option>
                    <option value="urban">Urban</option>
                    <option value="rural">Rural</option>
                    <option value="mixed">Mixed</option>
                  </select>
                </div>
              </div>
            </section>
          </>
        )}

        {/* ── Privacy & Data ──────────────────────────────────────────── */}
        <section>
          <h2 className="text-[#e8eaf0] font-medium mb-3">Privacy &amp; Data</h2>
          <div className="bg-[#13151f] border border-[#1e2133] rounded-xl p-6 flex items-center justify-between gap-4 flex-wrap">
            <div>
              <p className="text-[#e8eaf0] text-sm font-medium">Manage your data</p>
              <p className="text-[#8891a8] text-xs mt-0.5">
                Export your data, change audit log retention, opt out of analytics, or delete your account.
              </p>
            </div>
            <Link
              to="/privacy"
              className="bg-[#0f1117] hover:bg-[#1e2133] border border-[#1e2133] text-[#e8eaf0] text-sm px-4 py-2 rounded-lg transition-colors"
            >
              Open Privacy &amp; Data
            </Link>
          </div>
        </section>

        {/* ── Audit Log ───────────────────────────────────────────────── */}
        <section>
          <h2 className="text-[#e8eaf0] font-medium mb-3">
            Audit Log
            {auditLog.length > 0 && (
              <span className="ml-2 text-[#8891a8] text-sm font-normal">({auditLog.length} entries)</span>
            )}
          </h2>
          <div className="bg-[#13151f] border border-[#1e2133] rounded-xl overflow-hidden">
            {isLoading ? (
              <div className="p-6 space-y-3">
                {[1, 2, 3, 4].map(i => (
                  <div key={i} className="h-4 bg-[#1e2133] rounded animate-pulse" />
                ))}
              </div>
            ) : auditLog.length === 0 ? (
              <p className="text-[#8891a8] text-sm text-center py-10">No activity yet</p>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-sm min-w-[480px]">
                  <thead>
                    <tr className="border-b border-[#1e2133]">
                      <th className="text-left px-4 py-3 text-[#8891a8] text-xs uppercase tracking-wide font-medium w-44">Timestamp</th>
                      <th className="text-left px-4 py-3 text-[#8891a8] text-xs uppercase tracking-wide font-medium w-48">Action</th>
                      <th className="text-left px-4 py-3 text-[#8891a8] text-xs uppercase tracking-wide font-medium">Detail</th>
                    </tr>
                  </thead>
                  <tbody>
                    {auditLog.map((entry, idx) => (
                      <tr key={idx} className={`border-b border-[#1e2133] last:border-0 ${idx % 2 === 1 ? 'bg-[#0f1117]' : ''}`}>
                        <td className="px-4 py-3 text-[#8891a8] text-xs font-mono whitespace-nowrap">{fmtDateTime(entry.created_at)}</td>
                        <td className="px-4 py-3">
                          <span className="text-[#e8eaf0] font-medium">{labelFor(entry.action)}</span>
                        </td>
                        <td className="px-4 py-3 text-[#8891a8] text-xs font-mono">{entry.detail || '—'}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </section>

      </main>
    </div>
  )
}
