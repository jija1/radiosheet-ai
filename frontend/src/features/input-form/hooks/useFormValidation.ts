import type { FormErrors, FormState } from '../types'

const HHMM = /^\d{2}:\d{2}$/

export function useFormValidation(form: FormState): FormErrors {
  const errors: FormErrors = {}

  if (!form.station_name.trim()) {
    errors.station_name = 'Station name is required'
  } else if (form.station_name.length > 100) {
    errors.station_name = 'Station name must be 100 characters or fewer'
  }

  if (!form.presenter_name.trim()) {
    errors.presenter_name = 'Presenter name is required'
  } else if (form.presenter_name.length > 100) {
    errors.presenter_name = 'Presenter name must be 100 characters or fewer'
  }

  if (!form.total_duration_minutes) {
    errors.total_duration_minutes = 'Duration is required'
  } else if (form.total_duration_minutes < 15 || form.total_duration_minutes > 240) {
    errors.total_duration_minutes = 'Duration must be between 15 and 240 minutes'
  }

  if (!form.start_time) {
    errors.start_time = 'Start time is required'
  } else if (!HHMM.test(form.start_time)) {
    errors.start_time = 'Start time must be in HH:MM format'
  }

  if (!form.broadcast_date) {
    errors.broadcast_date = 'Broadcast date is required'
  } else if (isNaN(Date.parse(form.broadcast_date))) {
    errors.broadcast_date = 'Invalid broadcast date'
  }

  if (!form.max_advert_blocks_per_hour) {
    errors.max_advert_blocks_per_hour = 'Advert blocks per hour is required'
  } else if (form.max_advert_blocks_per_hour < 1 || form.max_advert_blocks_per_hour > 6) {
    errors.max_advert_blocks_per_hour = 'Must be between 1 and 6'
  }

  return errors
}
