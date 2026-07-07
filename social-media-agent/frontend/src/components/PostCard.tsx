import { useState } from 'react'
import { api } from '../api/client'
import type { Post } from '../types'
import StatusBadge, { PlatformBadge, VideoBadge } from './StatusBadge'
import PostEditorModal from './PostEditorModal'

export default function PostCard({ post, onChanged }: { post: Post; onChanged: () => void }) {
  const [editing, setEditing] = useState(false)
  const [busy, setBusy] = useState<string | null>(null)
  const [error, setError] = useState('')
  const [showVideo, setShowVideo] = useState(false)

  const act = async (name: string, fn: () => Promise<unknown>) => {
    setBusy(name)
    setError('')
    try {
      await fn()
      onChanged()
    } catch (e) {
      setError(String(e))
    } finally {
      setBusy(null)
    }
  }

  const canApprove = ['draft', 'pending_approval', 'approved', 'failed'].includes(post.status)

  return (
    <div className="rounded-xl border border-zinc-800 bg-zinc-900/60 p-4 flex flex-col gap-3">
      <div className="flex items-center gap-2 flex-wrap">
        <PlatformBadge platform={post.platform} />
        <StatusBadge status={post.status} />
        <VideoBadge status={post.video_status} />
        <span className="text-xs text-zinc-500">{post.format.replace('_', ' ')} · {post.pillar}</span>
        <span className="ml-auto text-xs text-zinc-600">#{post.id}</span>
      </div>

      {post.hook && <div className="font-semibold leading-snug">{post.hook}</div>}
      <div className="text-sm text-zinc-400 whitespace-pre-line line-clamp-4">{post.caption}</div>
      {post.hashtags && <div className="text-xs text-sky-400/70 line-clamp-1">{post.hashtags}</div>}

      {post.scheduled_at && (
        <div className="text-xs text-zinc-500">
          🗓 {new Date(post.scheduled_at).toLocaleString()}
        </div>
      )}
      {post.error_message && (
        <div className="text-xs text-amber-400/90">{post.error_message}</div>
      )}
      {post.video_error && <div className="text-xs text-red-400">{post.video_error}</div>}
      {error && <div className="text-xs text-red-400">{error}</div>}

      {showVideo && post.video_path && (
        <video controls className="max-h-96 rounded-lg self-start" src={`/${post.video_path}`} />
      )}

      <div className="flex gap-2 flex-wrap text-sm">
        {canApprove && (
          <button
            onClick={() => act('approve', () => api.approve(post.id))}
            disabled={!!busy}
            className="rounded-lg bg-lime-500/90 px-3 py-1.5 font-medium text-zinc-950 hover:bg-lime-400 disabled:opacity-50"
          >
            {busy === 'approve' ? '…' : 'Approve'}
          </button>
        )}
        <button onClick={() => setEditing(true)} className="rounded-lg border border-zinc-700 px-3 py-1.5 hover:bg-zinc-800">
          Edit
        </button>
        {post.video_path && (
          <button onClick={() => setShowVideo(!showVideo)} className="rounded-lg border border-zinc-700 px-3 py-1.5 hover:bg-zinc-800">
            {showVideo ? 'Hide video' : '▶ Video'}
          </button>
        )}
        {['none', 'failed'].includes(post.video_status) && post.format === 'reel_script' && (
          <button
            onClick={() => act('render', () => api.renderVideo(post.id))}
            disabled={!!busy}
            className="rounded-lg border border-zinc-700 px-3 py-1.5 hover:bg-zinc-800 disabled:opacity-50"
          >
            Render video
          </button>
        )}
        {['scheduled', 'ready', 'approved', 'failed'].includes(post.status) && (
          <button
            onClick={() => act('publish', () => api.publishNow(post.id))}
            disabled={!!busy}
            className="rounded-lg border border-indigo-500/50 text-indigo-300 px-3 py-1.5 hover:bg-indigo-500/10 disabled:opacity-50"
          >
            {busy === 'publish' ? '…' : 'Publish now'}
          </button>
        )}
        {post.status === 'ready' && (
          <button
            onClick={() => act('mark', () => api.markPosted(post.id))}
            disabled={!!busy}
            className="rounded-lg border border-teal-500/50 text-teal-300 px-3 py-1.5 hover:bg-teal-500/10 disabled:opacity-50"
          >
            Mark posted
          </button>
        )}
        {post.status !== 'posted' && post.status !== 'rejected' && (
          <>
            <button
              onClick={() => act('regen', () => api.regenerate(post.id))}
              disabled={!!busy}
              className="rounded-lg border border-zinc-700 px-3 py-1.5 hover:bg-zinc-800 disabled:opacity-50"
            >
              Regenerate
            </button>
            <button
              onClick={() => act('reject', () => api.reject(post.id))}
              disabled={!!busy}
              className="rounded-lg border border-red-500/40 text-red-300 px-3 py-1.5 hover:bg-red-500/10 disabled:opacity-50"
            >
              Reject
            </button>
          </>
        )}
      </div>

      {editing && (
        <PostEditorModal
          post={post}
          onClose={() => setEditing(false)}
          onSaved={() => {
            setEditing(false)
            onChanged()
          }}
        />
      )}
    </div>
  )
}
