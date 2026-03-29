const BASE_URL = 'http://localhost:8000'

export async function analyzeVideo(youtubeUrl) {
  const res = await fetch(`${BASE_URL}/api/stage1`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ youtube_url: youtubeUrl }),
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: 'Stage 1 failed' }))
    throw new Error(err.detail || 'Stage 1 failed')
  }
  return res.json()
}

export async function generateSummary(videoId, outputLanguage) {
  const res = await fetch(`${BASE_URL}/api/stage2`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ video_id: videoId, output_language: outputLanguage }),
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: 'Stage 2 failed' }))
    throw new Error(err.detail || 'Stage 2 failed')
  }
  return res.json()
}
