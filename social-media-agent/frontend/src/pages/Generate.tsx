import { useEffect, useRef, useState } from 'react'
import { Link } from 'react-router-dom'
import { api } from '../api/client'
import type { Brand, GenerationRun } from '../types'

export default function Generate({ brand }: { brand: Brand }) {
  const [count, setCount] = useState(brand.posts_per_batch)
  const [pillar, setPillar] = useState('')
  const [platform, setPlatform] = useState('')
  const [format, setFormat] = useState('')
  const [topic, setTopic] = useState('')
  const [run, setRun] = useState<GenerationRun | null>(null)
  const [history, setHistory] = useState<GenerationRun[]>([])
  const [error, setError] = useState('')
  const poll = useRef<ReturnType<typeof setInterval>>(undefined)

  const loadHistory = () => api.runs(brand.id).then(setHistory)
  useEffect(() => {
    loadHistory()
    setCount(brand.posts_per_batch)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [brand.id])

  useEffect(() => () => clearInterval(poll.current), [])

  const fire = async () => {
    setError('')
    try {
      const started = await api.generate(brand.id, {
        count,
        pillar: pillar || null,
        platform: platform || null,
        format: format || null,
        topic: topic || null,
      })
      setRun(started)
      clearInterval(poll.current)
      poll.current = setInterval(async () => {
        const latest = await api.run(started.id)
        setRun(latest)
        if (latest.status !== 'running') {
          clearInterval(poll.current)
          loadHistory()
        }
      }, 3000)
    } catch (e) {
      setError(String(e))
    }
  }

  return (
    <div className="flex flex-col gap-6 max-w-2xl">
      <div>
        <h1 className="text-2xl font-bold">Generate Content</h1>
        <p className="text-sm text-zinc-500">
          Claude writes platform-ready posts in {brand.name}'s voice. Reel scripts automatically get a rendered short video with AI voiceover.
        </p>
      </div>

      <div className="rounded-xl border border-zinc-800 bg-zinc-900/60 p-5 flex flex-col gap-4">
        <div className="grid grid-cols-2 gap-4">
          <label className="text-sm text-zinc-400 flex flex-col gap-1">
            How many posts
            <input type="number" min={1} max={20} value={count} onChange={(e) => setCount(Number(e.target.value))} className="rounded-lg border border-zinc-700 bg-zinc-800 px-3 py-2 text-zinc-100" />
          </label>
          <label className="text-sm text-zinc-400 flex flex-col gap-1">
            Pillar (optional)
            <select value={pillar} onChange={(e) => setPillar(e.target.value)} className="rounded-lg border border-zinc-700 bg-zinc-800 px-3 py-2 text-zinc-100">
              <option value="">Rotate all pillars</option>
              {brand.pillars.map((p) => (
                <option key={p.key} value={p.key}>{p.name}</option>
              ))}
            </select>
          </label>
          <label className="text-sm text-zinc-400 flex flex-col gap-1">
            Platform (optional)
            <select value={platform} onChange={(e) => setPlatform(e.target.value)} className="rounded-lg border border-zinc-700 bg-zinc-800 px-3 py-2 text-zinc-100">
              <option value="">Mix platforms</option>
              {brand.platforms.map((p) => (
                <option key={p} value={p}>{p}</option>
              ))}
            </select>
          </label>
          <label className="text-sm text-zinc-400 flex flex-col gap-1">
            Format (optional)
            <select value={format} onChange={(e) => setFormat(e.target.value)} className="rounded-lg border border-zinc-700 bg-zinc-800 px-3 py-2 text-zinc-100">
              <option value="">Mix formats</option>
              <option value="reel_script">Reel script (short video)</option>
              <option value="carousel">Carousel</option>
              <option value="caption">Caption</option>
              <option value="quote_image">Quote image</option>
              <option value="story">Story</option>
            </select>
          </label>
        </div>
        <label className="text-sm text-zinc-400 flex flex-col gap-1">
          Topic / angle (optional)
          <input value={topic} onChange={(e) => setTopic(e.target.value)} placeholder='e.g. "why motivation is unreliable" or "Claude prompt for a weekly review"' className="rounded-lg border border-zinc-700 bg-zinc-800 px-3 py-2 text-zinc-100" />
        </label>

        <button
          onClick={fire}
          disabled={run?.status === 'running'}
          className="self-start rounded-lg bg-lime-500/90 px-5 py-2.5 font-semibold text-zinc-950 hover:bg-lime-400 disabled:opacity-50"
        >
          {run?.status === 'running' ? 'Generating…' : '✦ Generate batch'}
        </button>

        {error && <div className="text-sm text-red-400">{error}</div>}

        {run && (
          <div className="rounded-lg border border-zinc-800 bg-zinc-950/60 p-4 text-sm">
            <div className="flex items-center gap-2">
              <span className={`h-2 w-2 rounded-full ${run.status === 'running' ? 'bg-amber-400 animate-pulse' : run.status === 'done' ? 'bg-lime-400' : 'bg-red-400'}`} />
              Run #{run.id}: {run.status}
              {run.status === 'done' && (
                <span className="text-zinc-400">
                  — {run.post_count} posts created.{' '}
                  <Link to="/queue" className="text-lime-300 underline">Review them in the Queue →</Link>
                </span>
              )}
            </div>
            {run.error && <div className="mt-2 text-red-400">{run.error}</div>}
          </div>
        )}
      </div>

      <section>
        <h2 className="mb-2 text-sm font-semibold uppercase tracking-wide text-zinc-400">Recent runs</h2>
        <div className="flex flex-col gap-1">
          {history.map((h) => (
            <div key={h.id} className="flex items-center gap-3 rounded-lg border border-zinc-800/60 px-3 py-1.5 text-xs text-zinc-400">
              <span>#{h.id}</span>
              <span className={h.status === 'done' ? 'text-lime-400' : h.status === 'failed' ? 'text-red-400' : 'text-amber-400'}>{h.status}</span>
              <span>{h.post_count} posts</span>
              <span className="ml-auto">{new Date(h.created_at).toLocaleString()}</span>
            </div>
          ))}
        </div>
      </section>
    </div>
  )
}
