export interface Pillar {
  key: string
  name: string
  description: string
  example_hooks: string[]
}

export interface Slot {
  id: number
  brand_id: number
  platform: string
  day_of_week: number
  time_local: string
  post_type: string
  pillar_hint: string
  active: boolean
}

export interface Brand {
  id: number
  slug: string
  name: string
  description: string
  system_prompt: string
  batch_prompt_template: string
  pillars: Pillar[]
  platforms: string[]
  ghl_account_ids: Record<string, string>
  publisher: 'native' | 'manual' | 'ghl'
  tts_voice: string
  autonomy: 'approval' | 'auto'
  auto_generate_enabled: boolean
  auto_generate_day: string
  auto_generate_time: string
  posts_per_batch: number
  timezone: string
}

export interface Post {
  id: number
  brand_id: number
  generation_run_id: number | null
  platform: string
  post_type: string
  format: string
  pillar: string
  hook: string
  caption: string
  raw_generated: string
  hashtags: string
  media_urls: string[]
  status: string
  video_status: 'none' | 'queued' | 'rendering' | 'ready' | 'failed'
  video_path: string
  video_error: string
  scheduled_at: string | null
  posted_at: string | null
  ghl_post_id: string
  error_message: string
  created_at: string
  updated_at: string
}

export interface GenerationRun {
  id: number
  brand_id: number
  trigger: string
  params: Record<string, unknown>
  model: string
  status: 'running' | 'done' | 'failed'
  error: string
  post_count: number
  created_at: string
}

export interface DashboardData {
  brand_id: number
  counts: Record<string, number>
  upcoming: Post[]
  recent_failures: Post[]
}
