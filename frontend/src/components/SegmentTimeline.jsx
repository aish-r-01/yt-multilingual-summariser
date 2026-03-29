import { useState } from 'react'

const PALETTE = [
  '#7c3aed', '#2563eb', '#059669', '#d97706', '#dc2626',
  '#0891b2', '#65a30d', '#9333ea', '#c2410c', '#0f766e',
]

function colorFor(language, allLanguages) {
  const idx = [...allLanguages].sort().indexOf(language)
  return PALETTE[Math.max(0, idx) % PALETTE.length]
}

function fmt(seconds) {
  const m = Math.floor(seconds / 60)
  const s = Math.floor(seconds % 60)
  return `${m}:${String(s).padStart(2, '0')}`
}

export default function SegmentTimeline({ segments, totalDuration }) {
  const [tooltip, setTooltip] = useState(null)

  const duration = totalDuration || segments.reduce((mx, s) => Math.max(mx, s.end), 0)
  const allLanguages = [...new Set(segments.map(s => s.language))]

  return (
    <div className="bg-slate-800/60 border border-slate-700/50 rounded-2xl p-5 flex flex-col gap-4">
      <h2 className="text-lg font-semibold text-white">Language Timeline</h2>

      {/* Bar + tooltip anchor */}
      <div
        className="relative"
        onMouseLeave={() => setTooltip(null)}
      >
        <div className="flex rounded-lg overflow-hidden h-10">
          {segments.map((seg, i) => {
            const widthPct = duration > 0 ? ((seg.end - seg.start) / duration) * 100 : 0
            const color = colorFor(seg.language, allLanguages)
            const leftPct = duration > 0 ? (seg.start / duration) * 100 : 0
            return (
              <div
                key={i}
                style={{ width: `${widthPct}%`, backgroundColor: color, flexShrink: 0 }}
                className="cursor-pointer hover:brightness-125 transition-all"
                onMouseEnter={e => {
                  const bar = e.currentTarget.parentElement
                  const barRect = bar.getBoundingClientRect()
                  const segRect = e.currentTarget.getBoundingClientRect()
                  setTooltip({
                    x: segRect.left - barRect.left + segRect.width / 2,
                    language: seg.language,
                    start: seg.start,
                    end: seg.end,
                    confidence: seg.confidence,
                  })
                }}
              />
            )
          })}
        </div>

        {/* Floating tooltip */}
        {tooltip && (
          <div
            className="absolute bottom-[calc(100%+8px)] z-20 bg-slate-900 border border-slate-600 rounded-lg px-3 py-2 text-xs shadow-2xl pointer-events-none -translate-x-1/2 whitespace-nowrap"
            style={{ left: tooltip.x }}
          >
            <p className="font-semibold text-white mb-0.5">{tooltip.language}</p>
            <p className="text-slate-400">{fmt(tooltip.start)} – {fmt(tooltip.end)}</p>
            <p className="text-slate-400">Confidence: {Math.round(tooltip.confidence * 100)}%</p>
          </div>
        )}
      </div>

      {/* Time axis labels */}
      <div className="flex justify-between text-xs text-slate-500 -mt-2 px-0.5">
        <span>0:00</span>
        <span>{fmt(duration / 2)}</span>
        <span>{fmt(duration)}</span>
      </div>

      {/* Language legend */}
      <div className="flex flex-wrap gap-x-4 gap-y-1.5">
        {allLanguages.map(lang => (
          <div key={lang} className="flex items-center gap-1.5 text-xs text-slate-400">
            <span
              className="w-2.5 h-2.5 rounded-sm shrink-0"
              style={{ backgroundColor: colorFor(lang, allLanguages) }}
            />
            {lang}
          </div>
        ))}
      </div>
    </div>
  )
}
