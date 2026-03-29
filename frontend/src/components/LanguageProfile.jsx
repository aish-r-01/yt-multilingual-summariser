// Deterministic color palette — assigned by sorted language name index
const PALETTE = [
  '#7c3aed', // violet   (primary accent)
  '#2563eb', // blue
  '#059669', // emerald
  '#d97706', // amber
  '#dc2626', // red
  '#0891b2', // cyan
  '#65a30d', // lime
  '#9333ea', // purple
  '#c2410c', // orange
  '#0f766e', // teal
]

function colorFor(language, allLanguages) {
  const idx = [...allLanguages].sort().indexOf(language)
  return PALETTE[Math.max(0, idx) % PALETTE.length]
}

const TYPE_BADGE = {
  Monolingual:    'bg-emerald-900/40 text-emerald-400 border-emerald-700/40',
  'Code-mixed':   'bg-amber-900/40  text-amber-400  border-amber-700/40',
  'Heavily Mixed':'bg-red-900/40    text-red-400    border-red-700/40',
}

export default function LanguageProfile({ languageProfile }) {
  const { mix, dominant_language, type, detected_languages } = languageProfile
  const sortedLangs = Object.keys(mix).sort()
  const badgeClass = TYPE_BADGE[type] ?? 'bg-slate-800 text-slate-400 border-slate-700'

  return (
    <div className="bg-slate-800/60 border border-slate-700/50 rounded-2xl p-5 flex flex-col gap-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold text-white">Language Mix</h2>
        <span className={`text-xs font-medium px-2.5 py-1 rounded-full border ${badgeClass}`}>
          {type}
        </span>
      </div>

      {/* Stacked bar */}
      <div className="flex rounded-lg overflow-hidden h-6">
        {sortedLangs.map(lang => (
          <div
            key={lang}
            style={{ width: `${mix[lang]}%`, backgroundColor: colorFor(lang, sortedLangs) }}
            title={`${lang}: ${mix[lang]}%`}
          />
        ))}
      </div>

      {/* Legend rows */}
      <div className="space-y-2">
        {sortedLangs.map(lang => (
          <div key={lang} className="flex items-center justify-between text-sm">
            <div className="flex items-center gap-2">
              <span
                className="w-3 h-3 rounded-full shrink-0"
                style={{ backgroundColor: colorFor(lang, sortedLangs) }}
              />
              <span className="text-slate-300">{lang}</span>
              {lang === dominant_language && (
                <span className="text-xs text-slate-500">(dominant)</span>
              )}
            </div>
            <span className="text-slate-400 font-mono tabular-nums">{mix[lang]}%</span>
          </div>
        ))}
      </div>
    </div>
  )
}
