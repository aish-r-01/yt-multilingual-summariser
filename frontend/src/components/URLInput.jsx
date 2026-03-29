import { useState } from 'react'

function Spinner() {
  return (
    <svg className="animate-spin h-4 w-4 shrink-0" viewBox="0 0 24 24" fill="none">
      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8z" />
    </svg>
  )
}

export default function URLInput({ onAnalyze, loading, error }) {
  const [url, setUrl] = useState('')

  function handleSubmit(e) {
    e.preventDefault()
    const trimmed = url.trim()
    if (trimmed) onAnalyze(trimmed)
  }

  return (
    <div className="max-w-2xl mx-auto">
      <form onSubmit={handleSubmit} className="flex gap-3">
        <input
          type="text"
          value={url}
          onChange={e => setUrl(e.target.value)}
          placeholder="Paste a YouTube URL — e.g. https://youtube.com/watch?v=..."
          className="flex-1 min-w-0 bg-slate-800 border border-slate-700 rounded-xl px-4 py-3 text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-violet-500 focus:border-transparent transition"
          disabled={loading}
        />
        <button
          type="submit"
          disabled={loading || !url.trim()}
          className="bg-violet-600 hover:bg-violet-500 disabled:bg-slate-700 disabled:cursor-not-allowed text-white font-semibold px-6 py-3 rounded-xl transition-colors flex items-center gap-2 whitespace-nowrap shrink-0"
        >
          {loading ? <><Spinner /> Analyzing…</> : 'Analyze'}
        </button>
      </form>

      {loading && (
        <p className="mt-3 text-center text-slate-400 text-sm animate-pulse">
          Extracting audio and detecting languages…
        </p>
      )}

      {error && (
        <p className="mt-3 text-center text-red-400 text-sm bg-red-900/20 border border-red-800/40 rounded-lg px-4 py-2">
          {error}
        </p>
      )}
    </div>
  )
}
