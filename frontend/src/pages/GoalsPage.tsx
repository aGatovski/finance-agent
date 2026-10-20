import { useEffect, useState } from 'react'
import { createGoal, deleteGoal, listGoals, updateGoal, updateGoalProgress } from '../api/goals'
import type { Goal } from '../types/goal'
import { formatCurrency } from '../lib/format'

export default function GoalsPage() {
  const [goals, setGoals] = useState<Goal[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [name, setName] = useState('')
  const [target, setTarget] = useState('')
  const [current, setCurrent] = useState('')
  const [deadline, setDeadline] = useState('')
  const [saving, setSaving] = useState(false)

  const [editingId, setEditingId] = useState<number | null>(null)
  const [editName, setEditName] = useState('')
  const [editTarget, setEditTarget] = useState('')
  const [editCurrent, setEditCurrent] = useState('')
  const [editDeadline, setEditDeadline] = useState('')

  function load() {
    setLoading(true)
    listGoals()
      .then(setGoals)
      .catch((e: Error) => setError(e.message))
      .finally(() => setLoading(false))
  }

  useEffect(load, [])

  async function onCreate(e: React.FormEvent) {
    e.preventDefault()
    const tgt = parseFloat(target)
    if (!name.trim()) {
      setError('Give the goal a name.')
      return
    }
    if (!Number.isFinite(tgt) || tgt <= 0) {
      setError('Enter a target amount greater than 0.')
      return
    }
    setSaving(true)
    setError(null)
    try {
      await createGoal({
        name: name.trim(),
        target_amount: tgt,
        current_amount: current ? parseFloat(current) : 0,
        deadline: deadline || null,
      })
      setName('')
      setTarget('')
      setCurrent('')
      setDeadline('')
      load()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Could not create goal')
    } finally {
      setSaving(false)
    }
  }

  async function onAdjust(goal: Goal, delta: number) {
    const next = Math.max(0, goal.current_amount + delta)
    try {
      const updated = await updateGoalProgress(goal.id, next)
      setGoals((prev) => prev.map((g) => (g.id === goal.id ? updated : g)))
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Could not update goal')
    }
  }

  function startEdit(goal: Goal) {
    setError(null)
    setEditingId(goal.id)
    setEditName(goal.name)
    setEditTarget(String(goal.target_amount))
    setEditCurrent(String(goal.current_amount))
    setEditDeadline(goal.deadline ?? '')
  }

  function cancelEdit() {
    setEditingId(null)
  }

  async function onSave(goal: Goal) {
    const tgt = parseFloat(editTarget)
    const cur = parseFloat(editCurrent)
    if (!editName.trim()) {
      setError('Give the goal a name.')
      return
    }
    if (!Number.isFinite(tgt) || tgt <= 0) {
      setError('Enter a target amount greater than 0.')
      return
    }
    setError(null)
    try {
      const updated = await updateGoal(goal.id, {
        name: editName.trim(),
        target_amount: tgt,
        current_amount: Number.isFinite(cur) ? Math.max(0, cur) : 0,
        deadline: editDeadline || null,
      })
      setGoals((prev) => prev.map((g) => (g.id === goal.id ? updated : g)))
      setEditingId(null)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Could not update goal')
    }
  }

  async function onDelete(goal: Goal) {
    if (!window.confirm(`Delete goal “${goal.name}”?`)) return
    try {
      await deleteGoal(goal.id)
      setGoals((prev) => prev.filter((g) => g.id !== goal.id))
      if (editingId === goal.id) setEditingId(null)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Could not delete goal')
    }
  }

  return (
    <section className="page">
      <header className="page-head">
        <div>
          <h1>Goals</h1>
          <p className="page-sub">Savings targets and progress</p>
        </div>
      </header>

      {error && <div className="banner error">{error}</div>}

      <form className="inline-form card" onSubmit={onCreate}>
        <input
          type="text"
          className="text-input"
          placeholder="Goal name"
          value={name}
          onChange={(e) => setName(e.target.value)}
        />
        <input
          type="number"
          className="text-input"
          placeholder="Target (€)"
          min="0"
          step="0.01"
          value={target}
          onChange={(e) => setTarget(e.target.value)}
        />
        <input
          type="number"
          className="text-input"
          placeholder="Saved so far (optional)"
          min="0"
          step="0.01"
          value={current}
          onChange={(e) => setCurrent(e.target.value)}
        />
        <input
          type="date"
          className="text-input"
          title="Target date (optional)"
          value={deadline}
          onChange={(e) => setDeadline(e.target.value)}
        />
        <button type="submit" className="btn-primary" disabled={saving}>
          {saving ? 'Adding…' : 'Add goal'}
        </button>
      </form>
      <p className="muted-note">Only name and target are required — a date and starting amount are optional.</p>

      {loading ? (
        <div className="muted-note">Loading…</div>
      ) : goals.length === 0 ? (
        <div className="empty-card">
          <h3>No goals yet</h3>
          <p>Add a savings target above to track your progress.</p>
        </div>
      ) : (
        <div className="stack">
          {goals.map((g) => (
            <div className="card progress-card" key={g.id}>
              {editingId === g.id ? (
                <div className="goal-edit">
                  <div className="inline-form">
                    <input
                      type="text"
                      className="text-input"
                      placeholder="Goal name"
                      value={editName}
                      onChange={(e) => setEditName(e.target.value)}
                    />
                    <input
                      type="number"
                      className="text-input"
                      placeholder="Target (€)"
                      min="0"
                      step="0.01"
                      value={editTarget}
                      onChange={(e) => setEditTarget(e.target.value)}
                    />
                    <input
                      type="number"
                      className="text-input"
                      placeholder="Saved so far"
                      min="0"
                      step="0.01"
                      value={editCurrent}
                      onChange={(e) => setEditCurrent(e.target.value)}
                    />
                    <input
                      type="date"
                      className="text-input"
                      title="Target date (optional)"
                      value={editDeadline}
                      onChange={(e) => setEditDeadline(e.target.value)}
                    />
                  </div>
                  <div className="progress-foot">
                    <span className="muted-note">Target date is optional.</span>
                    <span className="adjust">
                      <button type="button" className="btn-primary" onClick={() => onSave(g)}>
                        Save
                      </button>
                      <button type="button" className="text-btn" onClick={cancelEdit}>
                        Cancel
                      </button>
                    </span>
                  </div>
                </div>
              ) : (
                <>
                  <div className="progress-head">
                    <strong>{g.name}</strong>
                    <span className="muted-note">
                      {formatCurrency(g.current_amount)} / {formatCurrency(g.target_amount)}
                    </span>
                    <span className="pct">{g.progress_pct.toFixed(0)}%</span>
                  </div>
                  <div className="bar-track">
                    <div className="bar-fill" style={{ width: `${g.progress_pct}%` }} />
                  </div>
                  <div className="progress-foot">
                    <span className="muted-note">
                      {g.deadline ? `Target date: ${g.deadline}` : 'No deadline'}
                    </span>
                    <span className="adjust">
                      <button type="button" className="text-btn" onClick={() => onAdjust(g, -50)}>
                        −50
                      </button>
                      <button type="button" className="text-btn" onClick={() => onAdjust(g, 50)}>
                        +50
                      </button>
                      <button type="button" className="text-btn" onClick={() => startEdit(g)}>
                        Edit
                      </button>
                      <button type="button" className="text-btn danger" onClick={() => onDelete(g)}>
                        Delete
                      </button>
                    </span>
                  </div>
                </>
              )}
            </div>
          ))}
        </div>
      )}
    </section>
  )
}
