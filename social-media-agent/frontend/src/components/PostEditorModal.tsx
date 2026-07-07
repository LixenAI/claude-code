import { useState } from 'react'
import { api } from '../api/client'
import type { Post } from '../types'

export default function PostEditorModal({
  post,
  onClose,
  onSaved,
}: {
  post: Post
  onClose: () => void
  onSaved: () => void
}) {
  const [caption, setCaption] = useState(post.caption)
  const [hook, setHook] = useState(post.hook)
  const [hashtags, setHashtags] = useState(post.hashtags)
  const [platform, setPlatform] = useState(post.platform)
  const [scheduledAt, setScheduledAt] = useState(
    post.scheduled_at ? post.scheduled_at.slice(0, 16) : '',
  )
  const [mediaUrl, setMediaUrl] = useState(post.media_urls[0] ?? '')
  const [error, setError] = useState('')
  const [saving, setSaving] = useState(false)

  const save = async () => {
    setSaving(true)
    setError('')
    try {
      await api.updatePost(post.id, {
        caption,
        hook,
        hashtags,
        platform,
        media_urls: mediaUrl ? [mediaUrl] : [],
        ...(scheduledAt ? { scheduled_at: new Date(scheduledAt).toISOString() } : {}),
      })
      onSaved()
    } catch (e) {
      setError(String(e))
      setSaving(false)
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 p-4" onClick={onClose}>
      <div
        className="w-full max-w-2xl rounded-2xl border border-zinc-700 bg-zinc-900 p-6 flex flex-col gap-4 max-h-[90vh] overflow-y-auto"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="text-lg font-semibold">Edit post #{post.id}</div>

        <label className="text-sm text-zinc-400 flex flex-col gap-1">
          Hook
          <input value={hook} onChange={(e) => setHook(e.target.value)} className="rounded-lg border border-zinc-700 bg-zinc-800 px-3 py-2 text-zinc-100" />
        </label>

        <label className="text-sm text-zinc-400 flex flex-col gap-1">
          Caption
          <textarea value={caption} onChange={(e) => setCaption(e.target.value)} rows={8} className="rounded-lg border border-zinc-700 bg-zinc-800 px-3 py-2 text-zinc-100" />
        </label>

        <label className="text-sm text-zinc-400 flex flex-col gap-1">
          Hashtags
          <textarea value={hashtags} onChange={(e) => setHashtags(e.target.value)} rows={2} className="rounded-lg border border-zinc-700 bg-zinc-800 px-3 py-2 text-zinc-100" />
        </label>

        <div className="grid grid-cols-2 gap-4">
          <label className="text-sm text-zinc-400 flex flex-col gap-1">
            Platform
            <select value={platform} onChange={(e) => setPlatform(e.target.value)} className="rounded-lg border border-zinc-700 bg-zinc-800 px-3 py-2 text-zinc-100">
              <option value="instagram">instagram</option>
              <option value="tiktok">tiktok</option>
              <option value="facebook">facebook</option>
            </select>
          </label>
          <label className="text-sm text-zinc-400 flex flex-col gap-1">
            Scheduled at
            <input type="datetime-local" value={scheduledAt} onChange={(e) => setScheduledAt(e.target.value)} className="rounded-lg border border-zinc-700 bg-zinc-800 px-3 py-2 text-zinc-100" />
          </label>
        </div>

        <label className="text-sm text-zinc-400 flex flex-col gap-1">
          Image URL (optional, used when no video)
          <input value={mediaUrl} onChange={(e) => setMediaUrl(e.target.value)} className="rounded-lg border border-zinc-700 bg-zinc-800 px-3 py-2 text-zinc-100" />
        </label>

        {error && <div className="text-sm text-red-400">{error}</div>}

        <div className="flex justify-end gap-2">
          <button onClick={onClose} className="rounded-lg border border-zinc-700 px-4 py-2 hover:bg-zinc-800">Cancel</button>
          <button onClick={save} disabled={saving} className="rounded-lg bg-lime-500/90 px-4 py-2 font-medium text-zinc-950 hover:bg-lime-400 disabled:opacity-50">
            {saving ? 'Saving…' : 'Save'}
          </button>
        </div>
      </div>
    </div>
  )
}
