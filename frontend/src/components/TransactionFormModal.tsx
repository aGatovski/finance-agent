import { useEffect, useState } from 'react'
import { getCategories } from '../api/categories'
import { createTransaction, updateTransaction } from '../api/transactions'
import type { Transaction, TransactionCreate } from '../types/transaction'

interface Props {
  mode: 'add' | 'edit'
  initial?: Transaction
  onSaved: () => void
  onClose: () => void
}

function toDateInput(iso: string | undefined): string {
  return iso ? iso.slice(0, 10) : new Date().toISOString().slice(0, 10)
}

/** Overlay form reused for adding and editing a single transaction. */
export default function TransactionFormModal({ mode, initial, onSaved, onClose }: Props) {
  const [categories, setCategories] = useState<string[]>([])
  const [date, setDate] = useState(toDateInput(initial?.date))
  const [amount, setAmount] = useState(initial ? String(initial.amount) : '')
  const [description, setDescription] = useState(initial?.description ?? '')
  const [merchant, setMerchant] = useState(initial?.merchant ?? '')
  const [category, setCategory] = useState(initial?.category ?? 'Uncategorized')
  const [type, setType] = useState(initial?.type ?? '')
  const [isInternal, setIsInternal] = useState(initial?.is_internal ?? false)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    getCategories()
      .then((cats) => {
        setCategories(cats)
        // Make sure the current value is selectable even if not in the list.
        if (initial?.category && !cats.includes(initial.category)) {
          setCategories([initial.category, ...cats])
        }
      })
      .catch(() => setCategories([]))
  }, [initial?.category])

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault()
    const amt = parseFloat(amount)
    if (!date || !Number.isFinite(amt)) {
      setError('Date and a numeric amount are required.')
      return
    }
    const body: TransactionCreate = {
      date,
      amount: amt,
      description: description.trim() || null,
      merchant: merchant.trim() || null,
      category,
      type: type.trim() || null,
      is_internal: isInternal,
    }
    setSaving(true)
    setError(null)
    try {
      if (mode === 'add') await createTransaction(body)
      else if (initial) await updateTransaction(initial.id, body)
      onSaved()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Could not save transaction')
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-card" onClick={(e) => e.stopPropagation()}>
        <h2>{mode === 'add' ? 'Add transaction' : 'Edit transaction'}</h2>
        {error && <div className="banner error">{error}</div>}
        <form className="modal-form" onSubmit={onSubmit}>
          <label>
            Date
            <input type="date" value={date} onChange={(e) => setDate(e.target.value)} required />
          </label>
          <label>
            Amount (€) <span className="hint">negative = expense</span>
            <input
              type="number"
              step="0.01"
              value={amount}
              onChange={(e) => setAmount(e.target.value)}
              placeholder="-12.50"
              required
            />
          </label>
          <label>
            Description
            <input value={description} onChange={(e) => setDescription(e.target.value)} />
          </label>
          <label>
            Merchant
            <input value={merchant} onChange={(e) => setMerchant(e.target.value)} />
          </label>
          <label>
            Category
            <select value={category} onChange={(e) => setCategory(e.target.value)}>
              {categories.map((c) => (
                <option key={c} value={c}>
                  {c}
                </option>
              ))}
            </select>
          </label>
          <label>
            Type
            <input value={type} onChange={(e) => setType(e.target.value)} placeholder="Card Payment" />
          </label>
          <label className="checkbox">
            <input
              type="checkbox"
              checked={isInternal}
              onChange={(e) => setIsInternal(e.target.checked)}
            />
            Internal transfer (excluded from analytics)
          </label>
          <div className="modal-actions">
            <button type="button" className="text-btn" onClick={onClose}>
              Cancel
            </button>
            <button type="submit" className="btn-primary" disabled={saving}>
              {saving ? 'Saving…' : mode === 'add' ? 'Add' : 'Save'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}
