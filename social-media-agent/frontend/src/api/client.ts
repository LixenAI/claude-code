import type { Brand, DashboardData, GenerationRun, Post, Slot } from '../types'

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(path, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  })
  if (!res.ok) {
    const body = await res.text()
    let detail = body
    try {
      detail = JSON.parse(body).detail ?? body
    } catch {
      /* raw body */
    }
    throw new Error(`${res.status}: ${detail}`)
  }
  if (res.status === 204) return undefined as T
  return res.json()
}

export const api = {
  brands: () => request<Brand[]>('/api/brands'),
  brand: (id: number) => request<Brand>(`/api/brands/${id}`),
  updateBrand: (id: number, body: Partial<Brand>) =>
    request<Brand>(`/api/brands/${id}`, { method: 'PATCH', body: JSON.stringify(body) }),

  slots: (brandId: number) => request<Slot[]>(`/api/brands/${brandId}/slots`),
  createSlot: (brandId: number, body: Omit<Slot, 'id' | 'brand_id'>) =>
    request<Slot>(`/api/brands/${brandId}/slots`, { method: 'POST', body: JSON.stringify(body) }),
  updateSlot: (id: number, body: Partial<Slot>) =>
    request<Slot>(`/api/slots/${id}`, { method: 'PATCH', body: JSON.stringify(body) }),
  deleteSlot: (id: number) => request<void>(`/api/slots/${id}`, { method: 'DELETE' }),

  posts: (params: Record<string, string>) =>
    request<Post[]>(`/api/posts?${new URLSearchParams(params)}`),
  updatePost: (id: number, body: Partial<Post>) =>
    request<Post>(`/api/posts/${id}`, { method: 'PATCH', body: JSON.stringify(body) }),
  deletePost: (id: number) => request<void>(`/api/posts/${id}`, { method: 'DELETE' }),
  approve: (id: number, scheduledAt?: string) =>
    request<Post>(`/api/posts/${id}/approve`, {
      method: 'POST',
      body: JSON.stringify(scheduledAt ? { scheduled_at: scheduledAt } : {}),
    }),
  reject: (id: number) => request<Post>(`/api/posts/${id}/reject`, { method: 'POST' }),
  regenerate: (id: number) => request<GenerationRun>(`/api/posts/${id}/regenerate`, { method: 'POST' }),
  publishNow: (id: number) => request<Post>(`/api/posts/${id}/publish-now`, { method: 'POST' }),
  retry: (id: number) => request<Post>(`/api/posts/${id}/retry`, { method: 'POST' }),
  markPosted: (id: number) => request<Post>(`/api/posts/${id}/mark-posted`, { method: 'POST' }),
  renderVideo: (id: number) => request<Post>(`/api/posts/${id}/render-video`, { method: 'POST' }),

  generate: (brandId: number, body: Record<string, unknown>) =>
    request<GenerationRun>(`/api/brands/${brandId}/generate`, { method: 'POST', body: JSON.stringify(body) }),
  run: (id: number) => request<GenerationRun>(`/api/generation-runs/${id}`),
  runs: (brandId: number) => request<GenerationRun[]>(`/api/brands/${brandId}/generation-runs`),

  dashboard: (brandId: number) => request<DashboardData>(`/api/dashboard?brand_id=${brandId}`),
}
