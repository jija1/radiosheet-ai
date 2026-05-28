import {
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'

import type { PatternsData } from '../../api/user'

function formatProgrammeType(raw: string): string {
  return raw.replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase())
}

function formatPreference(raw: string): string {
  return raw.replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase())
}

function formatChartDate(iso: string): string {
  const d = new Date(iso)
  if (isNaN(d.getTime())) return iso
  return d.toLocaleDateString('en-GB', { day: '2-digit', month: 'short' })
}

function formatMinutes(value: number | null): string {
  if (value === null || value === undefined) return '—'
  return `${Math.round(value)} min`
}

interface PatternStatProps {
  label: string
  value: string
  hint?: string
}

function PatternStat({ label, value, hint }: PatternStatProps) {
  return (
    <div className="bg-[#13151f] border border-[#1e2133] rounded-xl p-5 flex flex-col gap-1">
      <span className="text-[#8891a8] text-xs uppercase tracking-wide">{label}</span>
      <span className="text-[#e8eaf0] text-2xl font-semibold">{value}</span>
      {hint && <span className="text-[#8891a8] text-xs">{hint}</span>}
    </div>
  )
}

interface SetupRowProps {
  label: string
  value: string
}

function SetupRow({ label, value }: SetupRowProps) {
  return (
    <div className="flex items-center justify-between py-2 border-b border-[#1e2133] last:border-0">
      <span className="text-[#8891a8] text-sm">{label}</span>
      <span className="text-[#e8eaf0] text-sm font-medium text-right">{value}</span>
    </div>
  )
}

interface PatternsTabProps {
  data: PatternsData
}

export function PatternsTab({ data }: PatternsTabProps) {
  if (data.runsheet_count < 5) {
    return (
      <div className="bg-[#13151f] border border-[#1e2133] rounded-xl p-8 text-center">
        <div className="text-3xl mb-3">📊</div>
        <p className="text-[#e8eaf0] text-sm">
          Generate at least 5 run-sheets to unlock pattern insights.
        </p>
        <p className="text-[#8891a8] text-sm mt-1">
          You have {data.runsheet_count} so far.
        </p>
      </div>
    )
  }

  const chartData = data.score_trend.map((p) => ({
    date: formatChartDate(p.date),
    score: Math.round(p.score * 100),
  }))

  const setup = data.usual_setup

  return (
    <div className="space-y-8">
      {/* Score trend chart */}
      <div className="bg-[#13151f] border border-[#1e2133] rounded-xl p-5">
        <h3 className="text-[#e8eaf0] font-medium mb-1">Score Trend</h3>
        <p className="text-[#8891a8] text-xs mb-4">
          Last {chartData.length} run-sheet{chartData.length === 1 ? '' : 's'}
        </p>
        <div className="h-64 w-full">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={chartData} margin={{ top: 8, right: 12, bottom: 4, left: -12 }}>
              <CartesianGrid stroke="#1e2133" strokeDasharray="3 3" />
              <XAxis
                dataKey="date"
                stroke="#8891a8"
                tick={{ fill: '#8891a8', fontSize: 11 }}
                tickLine={false}
                axisLine={{ stroke: '#1e2133' }}
              />
              <YAxis
                domain={[0, 100]}
                stroke="#8891a8"
                tick={{ fill: '#8891a8', fontSize: 11 }}
                tickLine={false}
                axisLine={{ stroke: '#1e2133' }}
              />
              <Tooltip
                contentStyle={{
                  backgroundColor: '#13151f',
                  border: '1px solid #1e2133',
                  borderRadius: 8,
                  color: '#e8eaf0',
                }}
                labelStyle={{ color: '#8891a8' }}
                formatter={(value: number) => [`${value}%`, 'Score']}
              />
              <Line
                type="monotone"
                dataKey="score"
                stroke="#2E75B6"
                strokeWidth={2}
                dot={{ fill: '#2E75B6', r: 3 }}
                activeDot={{ r: 5 }}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Pattern stat cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
        <PatternStat
          label="Most Used Programme Type"
          value={data.most_used_programme_type ? formatProgrammeType(data.most_used_programme_type) : '—'}
        />
        <PatternStat
          label="Typical News Placement"
          value={formatMinutes(data.typical_news_placement_minute)}
          hint="after programme start"
        />
        <PatternStat
          label="Typical First Advert"
          value={formatMinutes(data.typical_first_advert_minute)}
          hint="after programme start"
        />
        <PatternStat
          label="Avg Talk Segment"
          value={formatMinutes(data.average_talk_duration)}
        />
        <PatternStat
          label="Best Performing Day"
          value={data.best_performing_day ?? '—'}
          hint="highest average score"
        />
      </div>

      {/* Your usual setup */}
      <div>
        <h3 className="text-[#e8eaf0] font-medium mb-3">Your Usual Setup</h3>
        <div className="bg-[#13151f] border border-[#1e2133] rounded-xl px-5 py-2">
          <SetupRow label="Station" value={setup?.station_name ?? '—'} />
          <SetupRow label="Presenter" value={setup?.presenter_name ?? '—'} />
          <SetupRow
            label="Programme Type"
            value={setup?.programme_type ? formatProgrammeType(setup.programme_type) : '—'}
          />
          <SetupRow
            label="Duration"
            value={setup?.duration_minutes != null ? `${setup.duration_minutes} min` : '—'}
          />
          <SetupRow
            label="Talk / Music"
            value={setup?.talk_music_preference ? formatPreference(setup.talk_music_preference) : '—'}
          />
        </div>
      </div>
    </div>
  )
}
