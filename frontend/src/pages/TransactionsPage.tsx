import { useEffect, useRef, useState } from 'react'
import { getCategories } from '../api/categories'
import {
  deleteTransaction,
  importCsv,
  listTransactions,
  updateCategory,
} from '../api/transactions'
import type { ImportResult, Transaction } from '../types/transaction'
import { formatCurrency } from '../lib/format'
import TransactionFormModal from '../components/TransactionFormModal'

const PAGE = 50

type ModalState = { mode: 'add' } | { mode: 'edit'; tx: Transaction } | null

export default function TransactionsPage() {
  const [items, setItems] = useState<Transaction[]>([])
  const [total, setTotal] = useState(0)
  const [offset, setOffset] = useState(0)
  const [month, setMonth] = useState('')
  const [category, setCategory] = useState('')
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [uploading, setUploading] = useState(false)
  const [result, setResult] = useState<ImportResult | null>(null)
  const [categories, setCategories] = useState<string[]>([])
  const [savingId, setSavingId] = useState<number | null>(null)
  const [modal, setModal] = useState<ModalState>(null)
  const fileRef = useRef<HTMLInputElement>(null)

  // Fixed category vocabulary for the inline dropdowns (fetched once).
  useEffect(() => {
    getCategories()
      .then(setCategories)
      .catch(() => setCategories([]))
  }, [])

  function load() {
    setLoading(true)
    setError(null)
    listTransactions({ month: month || undefined, category: category || undefined, limit: PAGE, offset })
      .then((res) => {
        setItems(res.items)
        setTotal(res.total)
      })
      .catch((e: Error) => setError(e.message))
      .finally(() => setLoading(false))
  }

  // eslint-disable-next-line react-hooks/exhaustive-deps
  useEffect(load, [month, category, offset])

  async function onUpload(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0]
    if (!file) return
    setUploading(true)
    setError(null)
    setResult(null)
    try {
      const res = await importCsv(file)
      setResult(res)
      setOffset(0)
      load()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Import failed')
    } finally {
      setUploading(false)
      if (fileRef.current) fileRef.current.value = ''
    }
  }

  async function onCategoryChange(t: Transaction, next: string) {
    if (next === t.category) return
    let applyToMerchant = false
    if (t.merchant) {
      applyToMerchant = window.confirm(
        `Also apply to other "${t.merchant}" transactions?\n\nOK = update all from this merchant · Cancel = just this one`,
      )
    }
    const prev = t.category
    setSavingId(t.id)
    setError(null)
    setItems((rows) => rows.map((r) => (r.id === t.id ? { ...r, category: next } : r)))
    try {
      await updateCategory(t.id, next, applyToMerchant)
      if (applyToMerchant) load() // refresh so sibling rows reflect the change
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Could not update category')
      setItems((rows) => rows.map((r) => (r.id === t.id ? { ...r, category: prev } : r)))
    } finally {
      setSavingId(null)
    }
  }

  async function onDelete(t: Transaction) {
    const label = t.merchant || t.description || `transaction #${t.id}`
    if (!window.confirm(`Delete ${label}?`)) return
    setError(null)
    const prev = items
    setItems((rows) => rows.filter((r) => r.id !== t.id))
    setTotal((n) => Math.max(0, n - 1))
    try {
      await deleteTransaction(t.id)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Could not delete transaction')
      setItems(prev)
      setTotal(prev.length)
    }
  }

  const pages = Math.ceil(total / PAGE)
  const page = Math.floor(offset / PAGE) + 1

  return (
    <section className="page">
      <header className="page-head">
        <div>
          <h1>Transactions</h1>
          <p className="page-sub">{total} transactions</p>
        </div>
        <div className="head-actions">
          <button type="button" className="btn-ghost" onClick={() => setModal({ mode: 'add' })}>
            + Add transaction
          </button>
          <div className="upload">
            <input
              ref={fileRef}
              type="file"
              accept=".csv"
              id="csv"
              hidden
              onChange={onUpload}
              disabled={uploading}
            />
            <label htmlFor="csv" className={`btn-primary${uploading ? ' disabled' : ''}`}>
              {uploading ? 'Importing…' : 'Import CSV'}
            </label>
          </div>
        </div>
      </header>

      {error && <div className="banner error">{error}</div>}
      {result && (
        <div className="banner ok">
          Imported <strong>{result.inserted}</strong> rows · {result.categorized} categorized ·{' '}
          {result.uncategorized} uncategorized · {result.skipped_internal} internal transfers
          {result.format_cached ? ' · format cached' : ''}
        </div>
      )}

      <div className="filters">
        <input
          type="month"
          className="month-input"
          value={month}
          onChange={(e) => {
            setMonth(e.target.value)
            setOffset(0)
          }}
        />
        <select
          className="text-input"
          value={category}
          onChange={(e) => {
            setCategory(e.target.value)
            setOffset(0)
          }}
        >
          <option value="">All categories</option>
          {categories.map((c) => (
            <option key={c} value={c}>
              {c}
            </option>
          ))}
        </select>
        {(month || category) && (
          <button
            type="button"
            className="text-btn"
            onClick={() => {
              setMonth('')
              setCategory('')
              setOffset(0)
            }}
          >
            Clear
          </button>
        )}
      </div>

      {loading ? (
        <div className="muted-note">Loading…</div>
      ) : items.length === 0 ? (
        <div className="empty-card">
          <h3>No transactions</h3>
          <p>Import a bank CSV to get started.</p>
        </div>
      ) : (
        <>
          <div className="table-wrap">
            <table className="table">
              <thead>
                <tr>
                  <th>Date</th>
                  <th>Description</th>
                  <th>Category</th>
                  <th className="num">Amount</th>
                  <th className="num">Actions</th>
                </tr>
              </thead>
              <tbody>
                {items.map((t) => (
                  <tr key={t.id} className={t.is_internal ? 'internal' : ''}>
                    <td className="nowrap">{t.date.slice(0, 10)}</td>
                    <td>
                      {t.merchant || t.description || '—'}
                      {t.is_internal && <span className="tag">internal</span>}
                    </td>
                    <td>
                      {(() => {
                        const current = t.category || 'Uncategorized'
                        const options = categories.includes(current)
                          ? categories
                          : [current, ...categories]
                        return (
                          <select
                            className="cat-select"
                            value={current}
                            disabled={savingId === t.id || categories.length === 0}
                            onChange={(e) => onCategoryChange(t, e.target.value)}
                          >
                            {options.map((c) => (
                              <option key={c} value={c}>
                                {c}
                              </option>
                            ))}
                          </select>
                        )
                      })()}
                    </td>
                    <td className={`num ${t.amount < 0 ? 'neg' : 'pos'}`}>
                      {formatCurrency(t.amount)}
                    </td>
                    <td className="num">
                      <span className="row-actions">
                        <button
                          type="button"
                          className="text-btn"
                          onClick={() => setModal({ mode: 'edit', tx: t })}
                        >
                          Edit
                        </button>
                        <button
                          type="button"
                          className="icon-btn danger"
                          title="Delete"
                          onClick={() => void onDelete(t)}
                        >
                          ✕
                        </button>
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {pages > 1 && (
            <div className="pager">
              <button
                type="button"
                className="text-btn"
                disabled={offset === 0}
                onClick={() => setOffset(Math.max(0, offset - PAGE))}
              >
                ← Prev
              </button>
              <span className="muted-note">
                Page {page} of {pages}
              </span>
              <button
                type="button"
                className="text-btn"
                disabled={page >= pages}
                onClick={() => setOffset(offset + PAGE)}
              >
                Next →
              </button>
            </div>
          )}
        </>
      )}

      {modal && (
        <TransactionFormModal
          mode={modal.mode}
          initial={modal.mode === 'edit' ? modal.tx : undefined}
          onSaved={() => {
            setModal(null)
            load()
          }}
          onClose={() => setModal(null)}
        />
      )}
    </section>
  )
}
