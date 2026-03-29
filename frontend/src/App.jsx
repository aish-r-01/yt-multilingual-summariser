import { useState } from 'react'
import URLInput from './components/URLInput'
import LanguageProfile from './components/LanguageProfile'
import SegmentTimeline from './components/SegmentTimeline'
import LanguageSelector from './components/LanguageSelector'
import SummaryOutput from './components/SummaryOutput'
import { analyzeVideo, generateSummary } from './services/api'

// app states: idle | loading-stage1 | stage1-done | loading-stage2 | done
const SHOW_STAGE1 = new Set(['stage1-done', 'loading-stage2', 'done'])

export default function App() {
  const [appState, setAppState]         = useState('idle')
  const [stage1Data, setStage1Data]     = useState(null)
  const [stage2Data, setStage2Data]     = useState(null)
  const [selectedLang, setSelectedLang] = useState('')
  const [urlError, setUrlError]         = useState('')
  const [summaryError, setSummaryError] = useState('')

  async function handleAnalyze(url) {
    setUrlError('')
    setAppState('loading-stage1')
    try {
      const data = await analyzeVideo(url)
      setStage1Data(data)
      setSelectedLang(data.language_profile.dominant_language)
      setAppState('stage1-done')
    } catch (err) {
      setUrlError(err.message)
      setAppState('idle')
    }
  }

  async function handleGenerateSummary() {
    if (!stage1Data) return
    setSummaryError('')
    setAppState('loading-stage2')
    try {
      const data = await generateSummary(stage1Data.video_id, selectedLang)
      setStage2Data(data)
      setAppState('done')
    } catch (err) {
      setSummaryError(err.message)
      setAppState('stage1-done')
    }
  }

  function handleReset() {
    setAppState('idle')
    setStage1Data(null)
    setStage2Data(null)
    setSelectedLang('')
    setUrlError('')
    setSummaryError('')
  }

  const totalDuration = stage1Data
    ? Math.max(...stage1Data.segments.map(s => s.end), 0)
    : 0

  return (
    <div className="min-h-screen bg-[#0f172a] text-slate-100">
      <div className="max-w-6xl mx-auto px-4 py-12">

        {/* Header */}
        <div className="text-center mb-12">
          <h1 className="text-4xl font-bold text-white mb-3 tracking-tight">
            YouTube <span className="text-violet-400">Regional</span> Summarizer
          </h1>
          <p className="text-slate-400 text-lg">
            Detect languages, analyze code-switching, and summarize in any language
          </p>
        </div>

        {/* Stage 1 — URL input */}
        <URLInput
          onAnalyze={handleAnalyze}
          loading={appState === 'loading-stage1'}
          error={urlError}
        />

        {/* Stage 1 — Results */}
        {SHOW_STAGE1.has(appState) && stage1Data && (
          <div className="mt-10 grid grid-cols-1 lg:grid-cols-3 gap-6">
            <LanguageProfile languageProfile={stage1Data.language_profile} />
            <SegmentTimeline
              segments={stage1Data.segments}
              totalDuration={totalDuration}
            />
            <LanguageSelector
              availableLanguages={stage1Data.available_languages}
              selectedLanguage={selectedLang}
              onLanguageChange={setSelectedLang}
              onGenerate={handleGenerateSummary}
              loading={appState === 'loading-stage2'}
              error={summaryError}
            />
          </div>
        )}

        {/* Stage 2 — Summary */}
        {appState === 'done' && stage2Data && (
          <SummaryOutput
            summary={stage2Data.summary}
            outputLanguage={stage2Data.output_language}
            processingTime={stage2Data.processing_time_seconds}
            onReset={handleReset}
          />
        )}

      </div>
    </div>
  )
}
