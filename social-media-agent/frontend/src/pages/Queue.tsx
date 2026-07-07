import { useCallback, useEffect, useState } from 'react'
import { api } from '../api/client'
import type { Brand, Post } from '../types'
import PostCard from '../components/PostCard'

const FILTERS = [
  { key: 'pending_approval', label: 'Awaiting approval' },
  { key: 'scheduled', label: 'Scheduled' },
  { key: 'ready', label: 'Ready to post' },
  { key: 'posted', label: 'Posted' },
  { key: 'failed', label: 'Failed' },
  { key: 'rejected', label: 'Rejected' },
  { key: '', label: 'All' },
]

export default function Queue({ brand }: { brand: Brand }) {
  const [posts, setPosts] = useState<Post[]>([])
  const [status, setStatus] = useState('pending_approval')
  const [platform, setPlatform] = useState('')

  const load = useCallback(() => {
    const params: Record<string, string> = { brand_id: String(brand.id) }
    if (status) params.status = status
    if (platform) params.platform = platform
    api.posts(params).then(setPosts)
  }, [brand.id, status, platform])

  useEffect(() => {
    load()
    const t = setInterval(load, 10000)
    return () => clearInterval(t)
  }, [load])

  return (
    <div className="flex flex-col gap-4">
      <h1 className="text-2xl font-bold">Content Queue</h1>

      <div className="flex items-center gap-2 flex-wrap">
        {FILTERS.map((f) => (
          <button
            key={f.key}
            onClick={() => setStatus(f.key)}
            className={`rounded-full px-3 py-1 text-sm ${
              status === f.key ? 'bg-lime-400/15 text-lime-300 font-medium' : 'text-zinc-400 hover:bg-zinc-800'
            }`}
          >
            {f.label}
          </button>
        ))}
        <select
          value={platform}
          onChange={(e) => setPlatform(e.target.value)}
          className="ml-auto rounded-lg border border-zinc-700 bg-zinc-800 px-3 py-1.5 text-sm"
        >
          <option value="">All platforms</option>
          {brand.platforms.map((p) => (
            <option key={p} value={p}>{p}</option>
          ))}
        </select>
      </div>

      {posts.length === 0 ? (
        <div className="rounded-xl border border-dashed border-zinc-800 p-10 text-center text-sm text-zinc-500">
          No posts here. Head to <span className="text-lime-300">Generate</span> to create a batch.
        </div>
      ) : (
        <div className="grid gap-4 md:grid-cols-2">
          {posts.map((post) => (
            <PostCard key={post.id} post={post} onChanged={load} />
          ))}
        </div>
      )}
    </div>
  )
}
