import { useCallback, useEffect, useState } from 'react'
import { api } from '../api/client'
import type { Brand, Post } from '../types'
import { PlatformBadge } from '../components/StatusBadge'
import PostEditorModal from '../components/PostEditorModal'

const STATUS_DOT: Record<string, string> = {
  scheduled: 'bg-indigo-400',
  publishing: 'bg-purple-400',
  posted: 'bg-lime-400',
  ready: 'bg-teal-400',
  failed: 'bg-red-400',
}

function startOfWeek(d: Date): Date {
  const copy = new Date(d)
  copy.setDate(copy.getDate() - ((copy.getDay() + 6) % 7)) // Monday
  copy.setHours(0, 0, 0, 0)
  return copy
}

export default function Calendar({ brand }: { brand: Brand }) {
  const [posts, setPosts] = useState<Post[]>([])
  const [weekStart, setWeekStart] = useState(() => startOfWeek(new Date()))
  const [editing, setEditing] = useState<Post | null>(null)

  const load = useCallback(() => {
    api
      .posts({
        brand_id: String(brand.id),
        status: 'scheduled,publishing,posted,ready,failed',
      })
      .then(setPosts)
  }, [brand.id])

  useEffect(load, [load])

  const days = Array.from({ length: 14 }, (_, i) => {
    const d = new Date(weekStart)
    d.setDate(d.getDate() + i)
    return d
  })

  const postsOn = (day: Date) =>
    posts
      .filter((p) => {
        if (!p.scheduled_at) return false
        const t = new Date(p.scheduled_at)
        return t.toDateString() === day.toDateString()
      })
      .sort((a, b) => (a.scheduled_at! < b.scheduled_at! ? -1 : 1))

  const shift = (weeks: number) => {
    const d = new Date(weekStart)
    d.setDate(d.getDate() + weeks * 7)
    setWeekStart(d)
  }

  return (
    <div className="flex flex-col gap-4">
      <div className="flex items-center gap-3">
        <h1 className="text-2xl font-bold">Calendar</h1>
        <div className="ml-auto flex gap-2">
          <button onClick={() => shift(-1)} className="rounded-lg border border-zinc-700 px-3 py-1.5 text-sm hover:bg-zinc-800">← Prev</button>
          <button onClick={() => setWeekStart(startOfWeek(new Date()))} className="rounded-lg border border-zinc-700 px-3 py-1.5 text-sm hover:bg-zinc-800">Today</button>
          <button onClick={() => shift(1)} className="rounded-lg border border-zinc-700 px-3 py-1.5 text-sm hover:bg-zinc-800">Next →</button>
        </div>
      </div>

      <div className="grid grid-cols-7 gap-2">
        {days.map((day) => {
          const isToday = day.toDateString() === new Date().toDateString()
          return (
            <div
              key={day.toISOString()}
              className={`min-h-28 rounded-xl border p-2 ${isToday ? 'border-lime-500/50 bg-lime-500/5' : 'border-zinc-800 bg-zinc-900/40'}`}
            >
              <div className={`text-xs mb-2 ${isToday ? 'text-lime-300 font-semibold' : 'text-zinc-500'}`}>
                {day.toLocaleDateString(undefined, { weekday: 'short', day: 'numeric' })}
              </div>
              <div className="flex flex-col gap-1">
                {postsOn(day).map((p) => (
                  <button
                    key={p.id}
                    onClick={() => setEditing(p)}
                    className="flex items-center gap-1.5 rounded-md bg-zinc-800/80 px-1.5 py-1 text-left text-xs hover:bg-zinc-700"
                    title={p.hook || p.caption}
                  >
                    <span className={`h-2 w-2 shrink-0 rounded-full ${STATUS_DOT[p.status] ?? 'bg-zinc-500'}`} />
                    <span className="text-zinc-400">
                      {new Date(p.scheduled_at!).toLocaleTimeString(undefined, { hour: '2-digit', minute: '2-digit' })}
                    </span>
                    <span className="truncate text-zinc-300">{p.platform === 'instagram' ? 'IG' : p.platform === 'tiktok' ? 'TT' : 'FB'}</span>
                  </button>
                ))}
              </div>
            </div>
          )
        })}
      </div>

      <div className="flex gap-4 text-xs text-zinc-500">
        {Object.entries(STATUS_DOT).map(([status, cls]) => (
          <span key={status} className="flex items-center gap-1.5">
            <span className={`h-2 w-2 rounded-full ${cls}`} /> {status}
          </span>
        ))}
      </div>

      <section>
        <h2 className="mb-2 text-sm font-semibold uppercase tracking-wide text-zinc-400">Selected post</h2>
        {editing ? (
          <div className="rounded-xl border border-zinc-800 bg-zinc-900/60 p-4 text-sm flex flex-col gap-2">
            <div className="flex items-center gap-2">
              <PlatformBadge platform={editing.platform} />
              <span className="text-zinc-400">{editing.scheduled_at && new Date(editing.scheduled_at).toLocaleString()}</span>
            </div>
            <div className="font-medium">{editing.hook}</div>
            <div className="text-zinc-400 line-clamp-3 whitespace-pre-line">{editing.caption}</div>
          </div>
        ) : (
          <div className="text-xs text-zinc-600">Click a calendar entry to open the editor.</div>
        )}
      </section>

      {editing && (
        <PostEditorModal
          post={editing}
          onClose={() => setEditing(null)}
          onSaved={() => {
            setEditing(null)
            load()
          }}
        />
      )}
    </div>
  )
}
