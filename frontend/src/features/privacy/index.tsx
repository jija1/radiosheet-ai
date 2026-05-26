import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'

import {
  deleteAccount,
  downloadUserExport,
  getSettings,
  updateSettings,
} from '../../api/user'
import type { UserSettings } from '../../api/user'
import { useAuthStore } from '../../store/authStore'
import { useToastStore } from '../../store/toastStore'
import { NavBar } from '../../components/layout/NavBar'

const RETENTION_OPTIONS = [
  { value: 30,  label: '30 days' },
  { value: 90,  label: '90 days' },
  { value: 180, label: '180 days' },
  { value: 365, label: '365 days' },
]

const PRIVACY_STATEMENT = `RadioSheet AI stores your data locally on this server only.
Your run-sheets, statistics, and account information are never sold,
shared with third parties, or used for advertising.
All data is associated with your account and deleted permanently
when you delete your account. You can export a full copy of your
data at any time using the button below.`

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

export default function PrivacyPage() {
  const logout   = useAuthStore(s => s.logout)
  const navigate = useNavigate()
  const toast    = useToastStore()

  const [settings, setSettings] = useState<UserSettings | null>(null)
  const [loading, setLoading]   = useState(true)
  const [exporting, setExporting] = useState(false)
  const [showDelete, setShowDelete] = useState(false)
  const [password, setPassword] = useState('')
  const [deleting, setDeleting] = useState(false)
  const [deleteError, setDeleteError] = useState<string | null>(null)

  useEffect(() => {
    getSettings()
      .then(setSettings)
      .catch(() => toast.error('Could not load privacy settings'))
      .finally(() => setLoading(false))
  }, [toast])

  async function saveSetting<K extends keyof UserSettings>(key: K, value: UserSettings[K]) {
    setSettings(prev => prev ? { ...prev, [key]: value } : prev)
    try {
      const updated = await updateSettings({ [key]: value })
      setSettings(updated)
      toast.success('Setting saved')
    } catch {
      toast.error('Could not save setting')
    }
  }

  async function handleExport() {
    setExporting(true)
    try {
      await downloadUserExport()
      toast.success('Data export downloaded')
    } catch {
      toast.error('Export failed')
    } finally {
      setExporting(false)
    }
  }

  async function handleDelete() {
    if (!password.trim()) {
      setDeleteError('Password is required')
      return
    }
    setDeleting(true)
    setDeleteError(null)
    try {
      await deleteAccount(password)
      localStorage.clear()
      logout()
      toast.success('Account deleted')
      navigate('/register', { replace: true })
    } catch (err: unknown) {
      const msg = err instanceof Error && err.message ? err.message : 'Incorrect password or server error'
      setDeleteError(msg)
    } finally {
      setDeleting(false)
    }
  }

  const navItems = [
    { label: 'Dashboard',     to: '/dashboard' },
    { label: 'Settings',      to: '/settings' },
    { label: 'New Run-sheet', to: '/' },
    { label: 'Sign out', onClick: () => { logout(); navigate('/login') }, danger: true as const },
  ]

  return (
    <div className="min-h-screen bg-[#0f1117] text-[#e8eaf0]">
      <NavBar items={navItems} />

      <main className="max-w-3xl mx-auto px-4 md:px-6 py-8 space-y-8">

        <div>
          <h1 className="text-2xl font-semibold text-[#2E75B6]">Privacy &amp; Data</h1>
          <p className="text-[#8891a8] text-sm mt-1">
            Control how your data is stored, retained, and exported.
          </p>
        </div>

        {/* Your Data */}
        <section>
          <h2 className="text-[#e8eaf0] font-medium mb-3">Your Data</h2>
          <div className="bg-[#13151f] border border-[#1e2133] rounded-xl p-6">
            <p className="text-[#8891a8] text-sm whitespace-pre-line leading-relaxed">
              {PRIVACY_STATEMENT}
            </p>
          </div>
        </section>

        {/* Export My Data */}
        <section>
          <h2 className="text-[#e8eaf0] font-medium mb-3">Export My Data</h2>
          <div className="bg-[#13151f] border border-[#1e2133] rounded-xl p-6 flex items-start justify-between gap-4 flex-wrap">
            <div>
              <p className="text-[#e8eaf0] text-sm font-medium">Download a full copy</p>
              <p className="text-[#8891a8] text-xs mt-0.5">
                Profile, settings, statistics, run-sheet summaries, and audit log as JSON.
              </p>
            </div>
            <button
              type="button"
              onClick={handleExport}
              disabled={exporting}
              className="bg-[#2E75B6] hover:bg-[#1a5ea8] disabled:opacity-60 text-white text-sm px-4 py-2 rounded-lg transition-colors"
            >
              {exporting ? 'Preparing…' : 'Export My Data'}
            </button>
          </div>
        </section>

        {/* Retention + Analytics */}
        {!loading && settings && (
          <section>
            <h2 className="text-[#e8eaf0] font-medium mb-3">Logging &amp; Retention</h2>
            <div className="bg-[#13151f] border border-[#1e2133] rounded-xl p-6 space-y-4">

              <div className="flex items-center justify-between gap-4">
                <div>
                  <p className="text-[#e8eaf0] text-sm font-medium">Audit Log Retention</p>
                  <p className="text-[#8891a8] text-xs mt-0.5">
                    Older audit entries are deleted automatically when you next view the log.
                  </p>
                </div>
                <select
                  className="bg-[#0f1117] border border-[#1e2133] rounded px-3 py-1.5 text-[#e8eaf0] text-sm"
                  value={settings.audit_log_retention_days}
                  onChange={e => saveSetting('audit_log_retention_days', parseInt(e.target.value, 10))}
                >
                  {RETENTION_OPTIONS.map(o => (
                    <option key={o.value} value={o.value}>{o.label}</option>
                  ))}
                </select>
              </div>

              <div className="flex items-center justify-between gap-4">
                <div>
                  <p className="text-[#e8eaf0] text-sm font-medium">Analytics opt-out</p>
                  <p className="text-[#8891a8] text-xs mt-0.5">
                    When enabled, your actions are no longer recorded in the audit log.
                  </p>
                </div>
                <Toggle
                  checked={settings.analytics_opted_out}
                  onChange={v => saveSetting('analytics_opted_out', v)}
                />
              </div>
            </div>
          </section>
        )}

        {/* Delete Account */}
        <section>
          <h2 className="text-[#ef4444] font-medium mb-3">Delete Account</h2>
          <div className="bg-[#13151f] border border-[#ef444433] rounded-xl p-6 space-y-3">
            <p className="text-[#8891a8] text-sm">
              Permanently delete your account, all run-sheets, statistics, and audit log.
              This cannot be undone.
            </p>
            <button
              type="button"
              onClick={() => setShowDelete(true)}
              className="bg-[#ef4444] hover:bg-[#dc2626] text-white text-sm px-4 py-2 rounded-lg transition-colors"
            >
              Delete my account
            </button>
          </div>
        </section>

        {/* Delete confirmation modal */}
        {showDelete && (
          <div className="fixed inset-0 bg-black/70 flex items-center justify-center z-50 p-4">
            <div className="bg-[#13151f] border border-[#ef444433] rounded-xl p-6 max-w-md w-full space-y-4">
              <h3 className="text-[#ef4444] font-semibold">Confirm account deletion</h3>
              <p className="text-[#8891a8] text-sm">
                Enter your password to permanently delete your account and all associated
                data. This action cannot be undone.
              </p>
              <input
                type="password"
                value={password}
                onChange={e => setPassword(e.target.value)}
                placeholder="Your password"
                className="w-full bg-[#0f1117] border border-[#1e2133] rounded-lg px-3 py-2 text-[#e8eaf0] text-sm focus:outline-none focus:border-[#ef4444]"
              />
              {deleteError && (
                <p className="text-[#ef4444] text-xs">{deleteError}</p>
              )}
              <div className="flex gap-2 justify-end">
                <button
                  type="button"
                  onClick={() => { setShowDelete(false); setPassword(''); setDeleteError(null) }}
                  disabled={deleting}
                  className="text-[#8891a8] hover:text-[#e8eaf0] text-sm px-4 py-2 rounded-lg transition-colors"
                >
                  Cancel
                </button>
                <button
                  type="button"
                  onClick={handleDelete}
                  disabled={deleting}
                  className="bg-[#ef4444] hover:bg-[#dc2626] disabled:opacity-60 text-white text-sm px-4 py-2 rounded-lg transition-colors"
                >
                  {deleting ? 'Deleting…' : 'Permanently delete'}
                </button>
              </div>
            </div>
          </div>
        )}

      </main>
    </div>
  )
}
