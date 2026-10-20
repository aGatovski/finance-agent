import { useEffect, useState } from 'react'
import { getCategories } from '../api/categories'
import { deleteMerchant, listMerchants, updateMerchant } from '../api/merchants'
import type { Merchant } from '../types/merchant'

export default function MerchantsPage() {
  const [merchants, setMerchants] = useState<Merchant[]>([])
  const [categories, setCategories] = useState<string[]>([])
  const [search, setSearch] = useState('')
  const [category, setCategory] = useState('')
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [savingId, setSavingId] = useState<number | null>(null)

  useEffect(() => {
    getCategories()
      .then(setCategories)
      .catch(() => setCategories([]))
  }, [])

  function load(term = search, cat = category) {
    setLoading(true)
    setError(null)
    listMerchants({ search: term || undefined, category: cat || undefined })
      .then(setMerchants)
      .catch((e: Error) => setError(e.message))
      .finally(() => setLoading(false))
  }

  // eslint-disable-next-line react-hooks/exhaustive-deps
  useEffect(() => load(), [])

  async function onCategoryChange(m: Merchant, next: string) {
    if (next === m.category) return
    let applyToExisting = false
    if (m.tx_count > 0) {
      applyToExisting = window.confirm(
        `Also update ${m.tx_count} existing transaction(s) from "${m.merchant_name}" to ${next}?\n\nOK = update them too · Cancel = future imports only`,
      )
    }
    setSavingId(m.id)
    setError(null)
    const prev = m.category
    setMerchants((rows) => rows.map((r) => (r.id === m.id ? { ...r, category: next } : r)))
    try {
      await updateMerchant(m.id, { category: next, apply_to_existing: applyToExisting })
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Could not update merchant')
      setMerchants((rows) => rows.map((r) => (r.id === m.id ? { ...r, category: prev } : r)))
    } finally {
      setSavingId(null)
    }
  }

  async function onInternalToggle(m: Merchant, checked: boolean) {
    if (
      m.tx_count > 0 &&
      !window.confirm(
        checked
          ? `Mark "${m.merchant_name}" as internal and exclude its ${m.tx_count} transaction(s) from analytics?`
          : `Unmark "${m.merchant_name}" as internal and include its ${m.tx_count} transaction(s) in analytics again?`,
      )
    ) {
      return
    }
    setSavingId(m.id)
    setError(null)
    setMerchants((rows) => rows.map((r) => (r.id === m.id ? { ...r, is_internal: checked } : r)))
    try {
      await updateMerchant(m.id, { is_internal: checked, apply_to_existing: true })
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Could not update merchant')
      setMerchants((rows) => rows.map((r) => (r.id === m.id ? { ...r, is_internal: !checked } : r)))
    } finally {
      setSavingId(null)
    }
  }

  async function onDelete(m: Merchant) {
    if (!window.confirm(`Forget the mapping "${m.merchant_name}" → ${m.category}?`)) return
    setError(null)
    const prev = merchants
    setMerchants((rows) => rows.filter((r) => r.id !== m.id))
    try {
      await deleteMerchant(m.id)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Could not delete merchant')
      setMerchants(prev)
    }
  }

  return (
    <section className="page">
      <header className="page-head">
        <div>
          <h1>Merchants</h1>
          <p className="page-sub">Learned merchant → category mappings used to auto-categorize imports</p>
        </div>
      </header>

      {error && <div className="banner error">{error}</div>}

      <div className="filters">
        <input
          type="text"
          className="text-input"
          placeholder="Search merchants…"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && load()}
        />
        <button type="button" className="text-btn" onClick={() => load()}>
          Search
        </button>
        <select
          className="text-input"
          value={category}
          onChange={(e) => {
            setCategory(e.target.value)
            load(search, e.target.value)
          }}
        >
          <option value="">All categories</option>
          {categories.map((c) => (
            <option key={c} value={c}>
              {c}
            </option>
          ))}
        </select>
        {(search || category) && (
          <button
            type="button"
            className="text-btn"
            onClick={() => {
              setSearch('')
              setCategory('')
              load('', '')
            }}
          >
            Clear
          </button>
        )}
      </div>

      {loading ? (
        <div className="muted-note">Loading…</div>
      ) : merchants.length === 0 ? (
        <div className="empty-card">
          <h3>No merchants learned yet</h3>
          <p>Import a CSV or recategorize a transaction — the merchant → category it resolves to is remembered here.</p>
        </div>
      ) : (
        <div className="table-wrap">
          <table className="table">
            <thead>
              <tr>
                <th>Merchant</th>
                <th>Category</th>
                <th className="num">Internal</th>
                <th className="num">Transactions</th>
                <th className="num">Actions</th>
              </tr>
            </thead>
            <tbody>
              {merchants.map((m) => {
                const options = categories.includes(m.category) ? categories : [m.category, ...categories]
                return (
                  <tr key={m.id}>
                    <td>{m.merchant_name}</td>
                    <td>
                      <select
                        className="cat-select"
                        value={m.category}
                        disabled={savingId === m.id || categories.length === 0}
                        onChange={(e) => onCategoryChange(m, e.target.value)}
                      >
                        {options.map((c) => (
                          <option key={c} value={c}>
                            {c}
                          </option>
                        ))}
                      </select>
                    </td>
                    <td className="num">
                      <input
                        type="checkbox"
                        checked={m.is_internal}
                        disabled={savingId === m.id}
                        title="Internal transfer — exclude this merchant from analytics"
                        onChange={(e) => void onInternalToggle(m, e.target.checked)}
                      />
                    </td>
                    <td className="num">{m.tx_count}</td>
                    <td className="num">
                      <button
                        type="button"
                        className="icon-btn danger"
                        title="Forget mapping"
                        onClick={() => void onDelete(m)}
                      >
                        ✕
                      </button>
                    </td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        </div>
      )}
    </section>
  )
}
