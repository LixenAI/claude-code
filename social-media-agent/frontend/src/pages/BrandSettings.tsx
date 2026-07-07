import { useEffect, useState } from 'react'
import { api } from '../api/client'
import type { Brand, Slot } from '../types'

const DAYS = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']

export default function BrandSettings({ brand, onSaved }: { brand: Brand; onSaved: () => void }) {
  const [form, setForm] = useState<Brand>(brand)
  const [slots, setSlots] = useState<Slot[]>([])
  const [saved, setSaved] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => {
    setForm(brand)
    api.slots(brand.id).then(setSlots)
  }, [brand])

  const set = <K extends keyof Brand>(key: K, value: Brand[K]) =>
    setForm((f) => ({ ...f, [key]: value }))

  const save = async () => {
    setError('')
    setSaved(false)
    try {
      await api.updateBrand(brand.id, {
        name: form.name,
        description: form.description,
        system_prompt: form.system_prompt,
        batch_prompt_template: form.batch_prompt_template,
        publisher: form.publisher,
        tts_voice: form.tts_voice,
        autonomy: form.autonomy,
        auto_generate_enabled: form.auto_generate_enabled,
        auto_generate_day: form.auto_generate_day,
        auto_generate_time: form.auto_generate_time,
        posts_per_batch: form.posts_per_batch,
        timezone: form.timezone,
      })
      setSaved(true)
      onSaved()
    } catch (e) {
      setError(String(e))
    }
  }

  const addSlot = async () => {
    const slot = await api.createSlot(brand.id, {
      platform: brand.platforms[0] ?? 'instagram',
      day_of_week: 0,
      time_local: '18:00',
      post_type: 'reel',
      pillar_hint: '',
      active: true,
    })
    setSlots((s) => [...s, slot])
  }

  const patchSlot = async (id: number, body: Partial<Slot>) => {
    const updated = await api.updateSlot(id, body)
    setSlots((s) => s.map((x) => (x.id === id ? updated : x)))
  }

  const removeSlot = async (id: number) => {
    await api.deleteSlot(id)
    setSlots((s) => s.filter((x) => x.id !== id))
  }

  const input = 'rounded-lg border border-zinc-700 bg-zinc-800 px-3 py-2 text-sm text-zinc-100'

  return (
    <div className="flex flex-col gap-6 max-w-3xl">
      <h1 className="text-2xl font-bold">Brand Settings — {brand.name}</h1>

      <section className="rounded-xl border border-zinc-800 bg-zinc-900/60 p-5 flex flex-col gap-4">
        <h2 className="font-semibold">Identity & voice</h2>
        <div className="grid grid-cols-2 gap-4">
          <label className="text-sm text-zinc-400 flex flex-col gap-1">Name
            <input className={input} value={form.name} onChange={(e) => set('name', e.target.value)} />
          </label>
          <label className="text-sm text-zinc-400 flex flex-col gap-1">Timezone
            <input className={input} value={form.timezone} onChange={(e) => set('timezone', e.target.value)} />
          </label>
        </div>
        <label className="text-sm text-zinc-400 flex flex-col gap-1">Description
          <input className={input} value={form.description} onChange={(e) => set('description', e.target.value)} />
        </label>
        <label className="text-sm text-zinc-400 flex flex-col gap-1">
          System prompt (the brand's voice — edit carefully)
          <textarea className={`${input} font-mono text-xs`} rows={12} value={form.system_prompt} onChange={(e) => set('system_prompt', e.target.value)} />
        </label>
        <label className="text-sm text-zinc-400 flex flex-col gap-1">
          Weekly batch prompt template (use {'{count}'})
          <textarea className={`${input} font-mono text-xs`} rows={6} value={form.batch_prompt_template} onChange={(e) => set('batch_prompt_template', e.target.value)} />
        </label>
      </section>

      <section className="rounded-xl border border-zinc-800 bg-zinc-900/60 p-5 flex flex-col gap-4">
        <h2 className="font-semibold">Automation</h2>
        <div className="grid grid-cols-2 gap-4">
          <label className="text-sm text-zinc-400 flex flex-col gap-1">Workflow
            <select className={input} value={form.autonomy} onChange={(e) => set('autonomy', e.target.value as Brand['autonomy'])}>
              <option value="approval">Approval queue (review before posting)</option>
              <option value="auto">Full-auto (schedule + post without review)</option>
            </select>
          </label>
          <label className="text-sm text-zinc-400 flex flex-col gap-1">Publisher
            <select className={input} value={form.publisher} onChange={(e) => set('publisher', e.target.value as Brand['publisher'])}>
              <option value="native">Native APIs (Instagram Graph + TikTok)</option>
              <option value="manual">Manual (render everything, I post by hand)</option>
              <option value="ghl">GoHighLevel (legacy)</option>
            </select>
          </label>
          <label className="text-sm text-zinc-400 flex flex-col gap-1">Voiceover voice (edge-tts)
            <input className={input} value={form.tts_voice} onChange={(e) => set('tts_voice', e.target.value)} />
          </label>
          <label className="text-sm text-zinc-400 flex flex-col gap-1">Posts per weekly batch
            <input type="number" min={1} max={20} className={input} value={form.posts_per_batch} onChange={(e) => set('posts_per_batch', Number(e.target.value))} />
          </label>
        </div>
        <div className="flex items-center gap-4">
          <label className="flex items-center gap-2 text-sm text-zinc-300">
            <input type="checkbox" checked={form.auto_generate_enabled} onChange={(e) => set('auto_generate_enabled', e.target.checked)} />
            Auto-generate a weekly batch
          </label>
          <select className={input} value={form.auto_generate_day} onChange={(e) => set('auto_generate_day', e.target.value)}>
            {['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday'].map((d) => (
              <option key={d} value={d}>{d}</option>
            ))}
          </select>
          <input type="time" className={input} value={form.auto_generate_time} onChange={(e) => set('auto_generate_time', e.target.value)} />
        </div>
        <p className="text-xs text-zinc-500">
          Native publishing needs IG_ACCESS_TOKEN / IG_USER_ID (Instagram) and TIKTOK_ACCESS_TOKEN (TikTok) in the server environment.
          Without credentials, due posts move to <span className="text-teal-300">ready</span> — you post them manually from the Queue with one tap.
        </p>
      </section>

      <section className="rounded-xl border border-zinc-800 bg-zinc-900/60 p-5 flex flex-col gap-3">
        <div className="flex items-center">
          <h2 className="font-semibold">Posting slots (recurring calendar)</h2>
          <button onClick={addSlot} className="ml-auto rounded-lg border border-zinc-700 px-3 py-1.5 text-sm hover:bg-zinc-800">+ Add slot</button>
        </div>
        <div className="flex flex-col gap-2">
          {slots.map((slot) => (
            <div key={slot.id} className="flex items-center gap-2 text-sm">
              <select className={input} value={slot.platform} onChange={(e) => patchSlot(slot.id, { platform: e.target.value })}>
                {['instagram', 'tiktok', 'facebook'].map((p) => <option key={p} value={p}>{p}</option>)}
              </select>
              <select className={input} value={slot.day_of_week} onChange={(e) => patchSlot(slot.id, { day_of_week: Number(e.target.value) })}>
                {DAYS.map((d, i) => <option key={d} value={i}>{d}</option>)}
              </select>
              <input type="time" className={input} value={slot.time_local} onChange={(e) => patchSlot(slot.id, { time_local: e.target.value })} />
              <select className={input} value={slot.pillar_hint} onChange={(e) => patchSlot(slot.id, { pillar_hint: e.target.value })}>
                <option value="">any pillar</option>
                {form.pillars.map((p) => <option key={p.key} value={p.key}>{p.name}</option>)}
              </select>
              <label className="flex items-center gap-1 text-xs text-zinc-400">
                <input type="checkbox" checked={slot.active} onChange={(e) => patchSlot(slot.id, { active: e.target.checked })} /> active
              </label>
              <button onClick={() => removeSlot(slot.id)} className="ml-auto text-red-400 hover:text-red-300">✕</button>
            </div>
          ))}
        </div>
      </section>

      {error && <div className="text-sm text-red-400">{error}</div>}
      <div className="flex items-center gap-3">
        <button onClick={save} className="rounded-lg bg-lime-500/90 px-5 py-2.5 font-semibold text-zinc-950 hover:bg-lime-400">
          Save settings
        </button>
        {saved && <span className="text-sm text-lime-400">Saved ✓</span>}
      </div>
    </div>
  )
}
