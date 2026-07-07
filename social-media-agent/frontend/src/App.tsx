import { useCallback, useEffect, useState } from 'react'
import { NavLink, Navigate, Route, Routes } from 'react-router-dom'
import { api } from './api/client'
import type { Brand } from './types'
import Dashboard from './pages/Dashboard'
import Queue from './pages/Queue'
import Calendar from './pages/Calendar'
import Generate from './pages/Generate'
import BrandSettings from './pages/BrandSettings'

const NAV = [
  { to: '/', label: 'Dashboard', icon: '▦' },
  { to: '/queue', label: 'Queue', icon: '☰' },
  { to: '/calendar', label: 'Calendar', icon: '▤' },
  { to: '/generate', label: 'Generate', icon: '✦' },
  { to: '/settings', label: 'Brand Settings', icon: '⚙' },
]

export default function App() {
  const [brands, setBrands] = useState<Brand[]>([])
  const [brandId, setBrandId] = useState<number>(() =>
    Number(localStorage.getItem('brandId') || 0),
  )

  const reload = useCallback(() => {
    api.brands().then((list) => {
      setBrands(list)
      if (list.length && !list.some((b) => b.id === brandId)) {
        setBrandId(list[list.length - 1].id)
      }
    })
  }, [brandId])

  useEffect(reload, [reload])
  useEffect(() => {
    if (brandId) localStorage.setItem('brandId', String(brandId))
  }, [brandId])

  const brand = brands.find((b) => b.id === brandId)

  return (
    <div className="flex min-h-screen">
      <aside className="w-56 shrink-0 border-r border-zinc-800 bg-zinc-900/60 p-4 flex flex-col gap-6">
        <div>
          <div className="text-lg font-bold tracking-tight">Content<span className="text-lime-400">OS</span></div>
          <div className="text-xs text-zinc-500">Social Media Manager</div>
        </div>

        <select
          className="w-full rounded-lg border border-zinc-700 bg-zinc-800 px-3 py-2 text-sm"
          value={brandId || ''}
          onChange={(e) => setBrandId(Number(e.target.value))}
        >
          {brands.map((b) => (
            <option key={b.id} value={b.id}>{b.name}</option>
          ))}
        </select>

        <nav className="flex flex-col gap-1">
          {NAV.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.to === '/'}
              className={({ isActive }) =>
                `rounded-lg px-3 py-2 text-sm transition ${
                  isActive ? 'bg-lime-400/10 text-lime-300 font-medium' : 'text-zinc-400 hover:bg-zinc-800 hover:text-zinc-100'
                }`
              }
            >
              <span className="mr-2 opacity-70">{item.icon}</span>
              {item.label}
            </NavLink>
          ))}
        </nav>

        {brand && (
          <div className="mt-auto rounded-lg border border-zinc-800 bg-zinc-900 p-3 text-xs text-zinc-500">
            <div className="font-medium text-zinc-300">{brand.name}</div>
            <div>{brand.platforms.join(' · ')}</div>
            <div className="mt-1">
              {brand.autonomy === 'approval' ? '✋ approval queue' : '⚡ full-auto'} · {brand.publisher}
            </div>
          </div>
        )}
      </aside>

      <main className="flex-1 p-6 max-w-6xl">
        {brand ? (
          <Routes>
            <Route path="/" element={<Dashboard brand={brand} />} />
            <Route path="/queue" element={<Queue brand={brand} />} />
            <Route path="/calendar" element={<Calendar brand={brand} />} />
            <Route path="/generate" element={<Generate brand={brand} />} />
            <Route path="/settings" element={<BrandSettings brand={brand} onSaved={reload} />} />
            <Route path="*" element={<Navigate to="/" />} />
          </Routes>
        ) : (
          <div className="text-zinc-500">Loading brands…</div>
        )}
      </main>
    </div>
  )
}
