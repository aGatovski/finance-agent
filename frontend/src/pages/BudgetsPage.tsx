import { useEffect, useState } from 'react'
import { getCategories } from '../api/categories'
import { createBudget, deleteBudget, listBudgets } from '../api/budgets'
import type { Budget } from '../types/budget'
import { formatCurrency } from '../lib/format'

export default function BudgetsPage() {
  const [budgets, setBudgets] = useState<Budget[]>([])
  const [categories, setCategories] = useState<string[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [category, setCategory] = useState('')
  const [limit, setLimit] = useState('')
  const [saving, setSaving] = useState(false)

  useEffect(() => {
    getCategories()
      .then(setCategories)
      .catch(() => setCategories([]))
  }, [])

  function load() {
    setLoading(true)
    listBudgets()
      .then(setBudgets)
      .catch((e: Error) => setError(e.message))
      .finally(() => setLoading(false))
  }

  useEffect(load, [])

  async function onCreate(e: React.FormEvent) {
    e.preventDefault()
    const value = parseFloat(limit)
    if (!category.trim() || !Number.isFinite(value) || value <= 0) return
    setSaving(true)
    setError(null)
    try {
      await createBudget({ category: category.trim(), limit: value })
      setCategory('')
      setLimit('')
      load()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Could not create budget')
    } finally {
      setSaving(false)
    }
  }

  async function onDelete(id: number) {
    try {
      await deleteBudget(id)
      setBudgets((prev) => prev.filter((b) => b.id !== id))
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Could not delete budget')
    }
  }

  return (
    <section className="page">
      <header className="page-head">
        <div>
          <h1>Budgets</h1>
          <p className="page-sub">Monthly spending limits by category</p>
        </div>
      </header>

      {error && <div className="banner error">{error}</div>}

      <form className="inline-form card" onSubmit={onCreate}>
        <select
          className="text-input"
          value={category}
          onChange={(e) => setCategory(e.target.value)}
        >
          <option value="">Select category…</option>
          {categories.map((c) => (
            <option key={c} value={c}>
              {c}
            </option>
          ))}
        </select>
        <input
          type="number"
          className="text-input"
          placeholder="Limit (€)"
          min="0"
          step="0.01"
          value={limit}
          onChange={(e) => setLimit(e.target.value)}
        />
        <button type="submit" className="btn-primary" disabled={saving}>
          {saving ? 'Adding…' : 'Add budget'}
        </button>
      </form>

      {loading ? (
        <div className="muted-note">Loading…</div>
      ) : budgets.length === 0 ? (
        <div className="empty-card">
          <h3>No budgets yet</h3>
          <p>Add a category limit above to start tracking.</p>
        </div>
      ) : (
        <div className="stack">
          {budgets.map((b) => {
            const pct = b.limit > 0 ? Math.min((b.spent / b.limit) * 100, 100) : 0
            const over = b.remaining < 0
            return (
              <div className="card progress-card" key={b.id}>
                <div className="progress-head">
                  <strong>{b.category}</strong>
                  <span className={over ? 'neg' : 'muted-note'}>
                    {formatCurrency(b.spent)} / {formatCurrency(b.limit)}
                  </span>
                  <button
                    type="button"
                    className="icon-btn"
                    title="Delete"
                    onClick={() => onDelete(b.id)}
                  >
                    ✕
                  </button>
                </div>
                <div className="bar-track">
                  <div
                    className={`bar-fill${over ? ' over' : ''}`}
                    style={{ width: `${pct}%` }}
                  />
                </div>
                <div className="progress-foot muted-note">
                  {over
                    ? `${formatCurrency(-b.remaining)} over budget`
                    : `${formatCurrency(b.remaining)} remaining`}
                </div>
              </div>
            )
          })}
        </div>
      )}
    </section>
  )
}
