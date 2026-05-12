import type { RunSheetStats } from '../../../types/runsheet'

interface StatItemProps {
  label: string
  value: string
  valueClass?: string
}

function StatItem({ label, value, valueClass = 'text-[#e8eaf0]' }: StatItemProps) {
  return (
    <div className="flex flex-col gap-0.5">
      <span className="text-[#8891a8] text-xs uppercase tracking-wider">{label}</span>
      <span className={`text-lg font-medium ${valueClass}`}>{value}</span>
    </div>
  )
}

interface StatsBarProps {
  stats: RunSheetStats
  conflictCount: number
  recommendationCount: number
}

export function StatsBar({ stats, conflictCount, recommendationCount }: StatsBarProps) {
  return (
    <div className="bg-[#13151f] border-b border-[#1e2133] px-6 py-4 flex gap-10">
      <StatItem label="Total Duration" value={`${stats.total_duration_minutes} min`} />
      <StatItem label="Segments" value={String(stats.total_segments)} />
      <StatItem label="Advert %" value={`${stats.advert_percentage}%`} />
      <StatItem
        label="Conflicts"
        value={String(conflictCount)}
        valueClass={conflictCount > 0 ? 'text-[#ef4444]' : 'text-[#22c55e]'}
      />
      <StatItem
        label="Recommendations"
        value={String(recommendationCount)}
        valueClass="text-[#3b82f6]"
      />
      <StatItem
        label="Score"
        value={`${Math.round(stats.score * 100)}%`}
        valueClass="text-[#8891a8]"
      />
    </div>
  )
}
