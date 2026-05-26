import { useState } from 'react'
import type { ChangeEvent, FormEvent } from 'react'
import { useNavigate } from 'react-router-dom'

import { useAuthStore } from '../../store/authStore'
import { generateRunsheet } from '../../api/runsheet'
import { useRunsheetStore } from '../../store/runsheetStore'
import { useToastStore } from '../../store/toastStore'
import { NavBar } from '../../components/layout/NavBar'
import { Spinner } from '../../components/ui/Spinner'
import type { ProgrammeType, TalkMusicPreference } from '../../types/runsheet'
import { FormField, inputError, inputNormal } from './components/FormField'
import { useFormValidation } from './hooks/useFormValidation'
import { DEFAULT_FORM_VALUES } from './types'
import type { FormState } from './types'

const PROGRAMME_OPTIONS: { value: ProgrammeType; label: string }[] = [
  { value: 'morning_show',   label: 'Morning Show' },
  { value: 'drive_time',     label: 'Drive-time' },
  { value: 'news_hour',      label: 'News Hour' },
  { value: 'music_only',     label: 'Music Only' },
  { value: 'sports_show',    label: 'Sports Show' },
  { value: 'talk_show',      label: 'Talk Show' },
  { value: 'religious_show', label: 'Religious Show' },
  { value: 'farmer_show',    label: 'Farmer Show' },
]

const PREFERENCE_OPTIONS: { value: TalkMusicPreference; label: string }[] = [
  { value: 'heavy_music', label: 'Heavy Music' },
  { value: 'balanced',    label: 'Balanced' },
  { value: 'talk_heavy',  label: 'Talk Heavy' },
]

export default function InputFormPage() {
  const [form, setForm] = useState<FormState>(DEFAULT_FORM_VALUES)
  const [touched, setTouched] = useState<Partial<Record<keyof FormState, boolean>>>({})
  const [submitAttempted, setSubmitAttempted] = useState(false)
  const [submitError, setSubmitError] = useState<string | null>(null)

  const isLoading = useRunsheetStore(s => s.isLoading)
  const setLoading = useRunsheetStore(s => s.setLoading)
  const setRunsheet = useRunsheetStore(s => s.setRunsheet)
  const setStoreError = useRunsheetStore(s => s.setError)
  const logout = useAuthStore(s => s.logout)
  const toast = useToastStore()

  const navigate = useNavigate()
  const errors = useFormValidation(form)
  const hasErrors = Object.keys(errors).length > 0

  function updateField(field: keyof FormState, value: FormState[keyof FormState]) {
    setForm(prev => ({ ...prev, [field]: value } as FormState))
    setTouched(prev => ({ ...prev, [field]: true }))
  }

  function showError(field: keyof FormState): string | undefined {
    return touched[field] === true || submitAttempted ? errors[field as keyof typeof errors] : undefined
  }

  function handleTextInput(field: keyof FormState) {
    return (e: ChangeEvent<HTMLInputElement>) => updateField(field, e.target.value)
  }

  function handleSelect(field: keyof FormState) {
    return (e: ChangeEvent<HTMLSelectElement>) => updateField(field, e.target.value)
  }

  function handleNumber(field: keyof FormState) {
    return (e: ChangeEvent<HTMLInputElement>) => {
      const v = parseInt(e.target.value, 10)
      updateField(field, isNaN(v) ? 0 : v)
    }
  }

  async function handleSubmit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault()
    setSubmitAttempted(true)
    if (hasErrors) return

    setLoading(true)
    setStoreError(null)
    setSubmitError(null)

    try {
      const payload = {
        ...form,
        station_name: form.station_name.trim(),
        presenter_name: form.presenter_name.trim(),
        fixed_segments: [],
      }
      const result = await generateRunsheet(payload)
      setRunsheet(result)
      toast.success('Run-sheet generated successfully')
      navigate('/timeline')
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to generate run-sheet. Is the backend running?'
      setSubmitError(message)
      toast.error(message)
    } finally {
      setLoading(false)
    }
  }

  const navItems = [
    { label: 'Dashboard', to: '/dashboard' },
    { label: 'Validate',  to: '/validate' },
    { label: 'Sign out', onClick: () => { logout(); navigate('/login', { replace: true }) }, danger: true as const },
  ]

  return (
    <div className="min-h-screen bg-[#0f1117]">
      <NavBar items={navItems} />

      <div className="py-10 px-4">
        <div className="max-w-2xl mx-auto">

          {/* Header */}
          <div className="mb-8">
            <h1 className="text-2xl font-semibold text-[#2E75B6] mb-1">Generate Run-Sheet</h1>
            <p className="text-[#8891a8] text-sm">
              Fill in the programme details to generate an AI-optimised, conflict-free broadcast schedule.
            </p>
          </div>

          {/* Form card */}
          <form
            onSubmit={handleSubmit}
            className="bg-[#13151f] border border-[#1e2133] rounded-xl p-6 md:p-8 space-y-5"
          >

            {/* Programme type */}
            <FormField label="Programme Type" error={showError('programme_type')}>
              <select
                value={form.programme_type}
                onChange={handleSelect('programme_type')}
                className={showError('programme_type') ? inputError : inputNormal}
              >
                {PROGRAMME_OPTIONS.map(o => (
                  <option key={o.value} value={o.value}>{o.label}</option>
                ))}
              </select>
            </FormField>

            {/* Station name */}
            <FormField label="Station Name" error={showError('station_name')}>
              <input
                type="text"
                value={form.station_name}
                onChange={handleTextInput('station_name')}
                placeholder="e.g. Gold FM"
                maxLength={100}
                className={showError('station_name') ? inputError : inputNormal}
              />
            </FormField>

            {/* Presenter name */}
            <FormField label="Presenter Name" error={showError('presenter_name')}>
              <input
                type="text"
                value={form.presenter_name}
                onChange={handleTextInput('presenter_name')}
                placeholder="e.g. Kofi Mensah"
                maxLength={100}
                className={showError('presenter_name') ? inputError : inputNormal}
              />
            </FormField>

            {/* Broadcast date + start time */}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <FormField label="Broadcast Date" error={showError('broadcast_date')}>
                <input
                  type="date"
                  value={form.broadcast_date}
                  onChange={handleTextInput('broadcast_date')}
                  className={showError('broadcast_date') ? inputError : inputNormal}
                />
              </FormField>

              <FormField label="Start Time (HH:MM)" error={showError('start_time')}>
                <input
                  type="time"
                  value={form.start_time}
                  onChange={handleTextInput('start_time')}
                  className={showError('start_time') ? inputError : inputNormal}
                />
              </FormField>
            </div>

            {/* Duration + advert blocks */}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <FormField label="Total Duration (minutes)" error={showError('total_duration_minutes')}>
                <input
                  type="number"
                  value={form.total_duration_minutes}
                  onChange={handleNumber('total_duration_minutes')}
                  min={15}
                  max={240}
                  className={showError('total_duration_minutes') ? inputError : inputNormal}
                />
              </FormField>

              <FormField label="Max Advert Blocks / Hour" error={showError('max_advert_blocks_per_hour')}>
                <input
                  type="number"
                  value={form.max_advert_blocks_per_hour}
                  onChange={handleNumber('max_advert_blocks_per_hour')}
                  min={1}
                  max={6}
                  className={showError('max_advert_blocks_per_hour') ? inputError : inputNormal}
                />
              </FormField>
            </div>

            {/* Talk / Music preference */}
            <FormField label="Talk / Music Preference">
              <div className="flex gap-2 mt-1">
                {PREFERENCE_OPTIONS.map(({ value, label }) => (
                  <button
                    key={value}
                    type="button"
                    onClick={() => updateField('talk_music_preference', value)}
                    className={
                      'flex-1 py-2 rounded-lg text-sm border font-medium transition-colors ' +
                      (form.talk_music_preference === value
                        ? 'bg-[#2563eb] border-[#2563eb] text-white'
                        : 'bg-transparent border-[#1e2133] text-[#8891a8] hover:border-[#3b82f6] hover:text-[#e8eaf0]')
                    }
                  >
                    {label}
                  </button>
                ))}
              </div>
            </FormField>

            {/* API / submit error */}
            {submitError && (
              <p className="text-[#ef4444] text-sm rounded-lg bg-[#ef444411] border border-[#ef444433] px-3 py-2">
                {submitError}
              </p>
            )}

            {/* Submit */}
            <button
              type="submit"
              disabled={isLoading}
              className="bg-[#2563eb] hover:bg-[#1d4ed8] disabled:opacity-60 disabled:cursor-not-allowed text-white w-full py-3 rounded-lg font-medium transition-colors mt-2 flex items-center justify-center gap-2"
            >
              {isLoading ? (
                <>
                  <Spinner size={18} />
                  Generating…
                </>
              ) : (
                'Generate run-sheet with AI'
              )}
            </button>
          </form>
        </div>
      </div>
    </div>
  )
}
