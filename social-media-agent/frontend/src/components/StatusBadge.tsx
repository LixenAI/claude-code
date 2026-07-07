const COLORS: Record<string, string> = {
  draft: 'bg-zinc-700 text-zinc-300',
  pending_approval: 'bg-amber-500/15 text-amber-300',
  approved: 'bg-sky-500/15 text-sky-300',
  scheduled: 'bg-indigo-500/15 text-indigo-300',
  publishing: 'bg-purple-500/15 text-purple-300',
  posted: 'bg-lime-500/15 text-lime-300',
  ready: 'bg-teal-500/15 text-teal-300',
  failed: 'bg-red-500/15 text-red-300',
  rejected: 'bg-zinc-800 text-zinc-500',
}

export default function StatusBadge({ status }: { status: string }) {
  return (
    <span className={`rounded-full px-2 py-0.5 text-xs font-medium ${COLORS[status] ?? 'bg-zinc-700'}`}>
      {status.replace('_', ' ')}
    </span>
  )
}

export function PlatformBadge({ platform }: { platform: string }) {
  const style =
    platform === 'instagram'
      ? 'bg-pink-500/15 text-pink-300'
      : platform === 'tiktok'
        ? 'bg-cyan-500/15 text-cyan-300'
        : 'bg-blue-500/15 text-blue-300'
  return <span className={`rounded-full px-2 py-0.5 text-xs font-medium ${style}`}>{platform}</span>
}

export function VideoBadge({ status }: { status: string }) {
  if (status === 'none') return null
  const map: Record<string, string> = {
    queued: 'bg-zinc-700 text-zinc-300',
    rendering: 'bg-purple-500/15 text-purple-300 animate-pulse',
    ready: 'bg-lime-500/15 text-lime-300',
    failed: 'bg-red-500/15 text-red-300',
  }
  return (
    <span className={`rounded-full px-2 py-0.5 text-xs font-medium ${map[status]}`}>
      🎬 {status}
    </span>
  )
}
