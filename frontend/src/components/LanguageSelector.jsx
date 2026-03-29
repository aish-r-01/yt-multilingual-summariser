function Spinner() {
  return (
    <svg className="animate-spin h-4 w-4 shrink-0" viewBox="0 0 24 24" fill="none">
      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8z" />
    </svg>
  )
}

export default function LanguageSelector({
  availableLanguages,
  selectedLanguage,
  onLanguageChange,
  onGenerate,
  loading,
  error,
}) {
  return (
    <div className="bg-slate-800/60 border border-slate-700/50 rounded-2xl p-5 flex flex-col gap-4">
      <h2 className="text-lg font-semibold text-white">Summarize In</h2>

      <select
        value={selectedLanguage}
        onChange={e => onLanguageChange(e.target.value)}
        disabled={loading}
        className="w-full bg-slate-700 border border-slate-600 rounded-xl px-4 py-3 text-white focus:outline-none focus:ring-2 focus:ring-violet-500 focus:border-transparent transition appearance-none cursor-pointer"
      >
        {availableLanguages.map(lang => (
          <option key={lang} value={lang}>{lang}</option>
        ))}
      </select>

      <button
        onClick={onGenerate}
        disabled={loading || !selectedLanguage}
        className="w-full bg-violet-600 hover:bg-violet-500 disabled:bg-slate-700 disabled:cursor-not-allowed text-white font-semibold py-3 rounded-xl transition-colors flex items-center justify-center gap-2"
      >
        {loading
          ? <><Spinner />Summarizing in {selectedLanguage}…</>
          : 'Generate Summary'
        }
      </button>

      {loading && (
        <p className="text-center text-slate-500 text-xs animate-pulse">
          This may take 15–30 seconds…
        </p>
      )}

      {error && (
        <p className="text-red-400 text-sm bg-red-900/20 border border-red-800/40 rounded-lg px-3 py-2">
          {error}
        </p>
      )}
    </div>
  )
}
