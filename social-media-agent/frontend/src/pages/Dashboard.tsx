import { useEffect, useState } from 'react'
import { api } from '../api/client'
import type { Brand, DashboardData } from '../types'
import StatusBadge, { PlatformBadge } from '../components/StatusBadge'

const TILES = [
  { key: 'pending_approval', label: 'Awaiting approval' },
  { key: 'scheduled', label: 'Scheduled' },
  { key: 'ready', label: 'Ready to post' },
  { key: 'posted', label: 'Posted' },
  { key: 'failed', label: 'Failed' },
]

export default function Dashboard({ brand }: { brand: Brand }) {
  const [data, setData] = useState<DashboardData | null>(null)

  const load = () => api.dashboard(brand.id).then(setData)
  useEffect(() => {
    load()
    const t = setInterval(load, 15000)
    return () => clearInterval(t)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [brand.id])

  if (!data) return <div className="text-zinc-500">Loading…</div>

  return (
    <div className="flex flex-col gap-6">
      <div>
        <h1 className="text-2xl font-bold">{brand.name}</h1>
        <p className="text-sm text-zinc-500">{brand.description}</p>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
        {TILES.map((tile) => (
          <div key={tile.key} className="rounded-xl border border-zinc-800 bg-zinc-900/60 p-4">
            <div className="text-3xl font-bold">{data.counts[tile.key] ?? 0}</div>
            <div className="text-xs text-zinc-500 mt-1">{tile.label}</div>
          </div>
        ))}
      </div>

      <section>
        <h2 className="mb-3 text-sm font-semibold uppercase tracking-wide text-zinc-400">Next 7 days</h2>
        {data.upcoming.length === 0 ? (
          <div className="rounded-xl border border-dashed border-zinc-800 p-6 text-sm text-zinc-500">
            Nothing scheduled. Generate a batch and approve posts to fill the calendar.
          </div>
        ) : (
          <div className="flex flex-col gap-2">
            {data.upcoming.map((post) => (
              <div key={post.id} className="flex items-center gap-3 rounded-lg border border-zinc-800 bg-zinc-900/60 px-4 py-2 text-sm">
                <span className="w-40 shrink-0 text-zinc-400">
                  {post.scheduled_at ? new Date(post.scheduled_at).toLocaleString(undefined, { weekday: 'short', month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' }) : '—'}
                </span>
                <PlatformBadge platform={post.platform} />
                <span className="truncate text-zinc-300">{post.hook || post.caption.slice(0, 80)}</span>
                <span className="ml-auto"><StatusBadge status={post.status} /></span>
              </div>
            ))}
          </div>
        )}
      </section>

      {data.recent_failures.length > 0 && (
        <section>
          <h2 className="mb-3 text-sm font-semibold uppercase tracking-wide text-red-400">Recent failures</h2>
          <div className="flex flex-col gap-2">
            {data.recent_failures.map((post) => (
              <div key={post.id} className="rounded-lg border border-red-500/20 bg-red-500/5 px-4 py-2 text-sm">
                <div className="flex items-center gap-3">
                  <PlatformBadge platform={post.platform} />
                  <span className="truncate">{post.hook || post.caption.slice(0, 60)}</span>
                  <button
                    onClick={() => api.retry(post.id).then(load)}
                    className="ml-auto rounded border border-zinc-700 px-2 py-1 text-xs hover:bg-zinc-800"
                  >
                    Retry
                  </button>
                </div>
                <div className="mt-1 text-xs text-red-300/80">{post.error_message}</div>
              </div>
            ))}
          </div>
        </section>
      )}
    </div>
  )
}
