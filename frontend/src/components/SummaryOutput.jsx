import { useState } from 'react'

function fmt(seconds) {
  const m = Math.floor(seconds / 60)
  const s = Math.floor(seconds % 60)
  return `${m}:${String(s).padStart(2, '0')}`
}

function CheckIcon() {
  return (
    <svg className="w-3 h-3 text-violet-400 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2.5">
      <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
    </svg>
  )
}

export default function SummaryOutput({ summary, outputLanguage, processingTime, onReset }) {
  const [copied, setCopied] = useState(false)

  function handleCopy() {
    const lines = [
      summary.title,
      '',
      summary.overview,
      '',
      'Key Points:',
      ...summary.key_points.map(p => `• ${p}`),
    ]

    if (summary.timestamps?.length > 0) {
      lines.push('', 'Timestamps:')
      summary.timestamps.forEach(t => lines.push(`[${fmt(t.time)}] ${t.label}`))
    }

    lines.push('', summary.conclusion)

    navigator.clipboard.writeText(lines.join('\n')).then(() => {
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    })
  }

  return (
    <div className="mt-10 animate-fade-in">
      <div className="bg-slate-800/60 border border-slate-700/50 rounded-2xl p-8 space-y-7">

        {/* Header row */}
        <div className="flex flex-col sm:flex-row sm:items-start sm:justify-between gap-4">
          <div>
            <h2 className="text-2xl font-bold text-white leading-snug">{summary.title}</h2>
            <p className="text-slate-500 text-sm mt-1.5">
              Summarized in {outputLanguage}
              <span className="mx-2 text-slate-700">·</span>
              {processingTime}s
            </p>
          </div>
          <div className="flex gap-2 shrink-0">
            <button
              onClick={handleCopy}
              className="text-sm bg-slate-700 hover:bg-slate-600 text-slate-200 px-4 py-2 rounded-lg transition-colors"
            >
              {copied ? 'Copied!' : 'Copy Summary'}
            </button>
            <button
              onClick={onReset}
              className="text-sm bg-violet-600/20 hover:bg-violet-600/40 text-violet-400 border border-violet-700/40 px-4 py-2 rounded-lg transition-colors"
            >
              Analyze Another
            </button>
          </div>
        </div>

        {/* Overview */}
        <section>
          <h3 className="text-xs uppercase tracking-widest text-slate-500 mb-2">Overview</h3>
          <p className="text-slate-300 leading-relaxed">{summary.overview}</p>
        </section>

        {/* Key Points */}
        <section>
          <h3 className="text-xs uppercase tracking-widest text-slate-500 mb-3">Key Points</h3>
          <ul className="space-y-2.5">
            {summary.key_points.map((point, i) => (
              <li key={i} className="flex items-start gap-3 text-slate-300">
                <span className="mt-0.5 w-5 h-5 rounded-full bg-violet-600/20 border border-violet-500/30 flex items-center justify-center shrink-0">
                  <CheckIcon />
                </span>
                <span className="leading-relaxed">{point}</span>
              </li>
            ))}
          </ul>
        </section>

        {/* Timestamps */}
        {summary.timestamps?.length > 0 && (
          <section>
            <h3 className="text-xs uppercase tracking-widest text-slate-500 mb-3">Timestamps</h3>
            <div className="flex flex-wrap gap-2">
              {summary.timestamps.map((ts, i) => (
                <span
                  key={i}
                  className="bg-slate-700/60 border border-slate-600/50 text-slate-300 text-sm px-3 py-1.5 rounded-full flex items-center gap-2"
                >
                  <span className="text-violet-400 font-mono text-xs tabular-nums">{fmt(ts.time)}</span>
                  <span>{ts.label}</span>
                </span>
              ))}
            </div>
          </section>
        )}

        {/* Conclusion */}
        <section>
          <h3 className="text-xs uppercase tracking-widest text-slate-500 mb-2">Conclusion</h3>
          <p className="text-slate-300 leading-relaxed italic">{summary.conclusion}</p>
        </section>

      </div>
    </div>
  )
}
