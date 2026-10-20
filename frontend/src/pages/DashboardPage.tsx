import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import {
  Bar,
  BarChart,
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'
import { getByCategory, getBalance, getSummary, getTrend } from '../api/analytics'
import { listGoals } from '../api/goals'
import type { CategoryAmount, MonthlySummary, TrendPoint } from '../types/analytics'
import { currentMonth, formatCurrency, monthLabel } from '../lib/format'

// Validated with the dataviz palette script (CVD ΔE 10.1 protan, contrast ≥3:1).
const INCOME = '#059669' // emerald — brand accent
const EXPENSE = '#ea580c' // orange — CVD-safe partner
const GRID = '#e5e7eb'

export default function DashboardPage() {
  const [month, setMonth] = useState(currentMonth())
  const [summary, setSummary] = useState<MonthlySummary | null>(null)
  const [categories, setCategories] = useState<CategoryAmount[]>([])
  const [trend, setTrend] = useState<TrendPoint[]>([])
  const [balance, setBalance] = useState(0)
  const [savings, setSavings] = useState(0)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    let cancelled = false
    setLoading(true)
    setError(null)
    Promise.all([getSummary(month), getByCategory(month), getTrend(6), getBalance(), listGoals()])
      .then(([s, c, t, b, goals]) => {
        if (cancelled) return
        setSummary(s)
        setCategories(c.items)
        setTrend(t.items)
        setBalance(b.total_balance)
        setSavings(goals.reduce((sum, g) => sum + g.current_amount, 0))
      })
      .catch((e: Error) => !cancelled && setError(e.message))
      .finally(() => !cancelled && setLoading(false))
    return () => {
      cancelled = true
    }
  }, [month])

  const hasData =
    !!summary && (summary.income !== 0 || summary.expenses !== 0 || categories.length > 0)

  return (
    <section className="page">
      <header className="page-head">
        <div>
          <h1>Dashboard</h1>
          <p className="page-sub">Spending overview for {monthLabel(month)}</p>
        </div>
        <input
          type="month"
          className="month-input"
          value={month}
          onChange={(e) => setMonth(e.target.value)}
        />
      </header>

      {error && <div className="banner error">{error}</div>}
      {loading && <div className="muted-note">Loading…</div>}

      {!loading && !error && (
        <div className="kpi-row">
          <Kpi
            label="Total balance"
            value={formatCurrency(balance)}
            tone={balance >= 0 ? 'pos' : 'neg'}
          />
          <Kpi label="In savings" value={formatCurrency(savings)} />
        </div>
      )}

      {!loading && !error && !hasData && (
        <div className="empty-card">
          <h3>No data for {monthLabel(month)}</h3>
          <p>Import a bank CSV to populate your dashboard.</p>
          <Link to="/transactions" className="btn-primary">
            Import a CSV →
          </Link>
        </div>
      )}

      {!loading && !error && hasData && summary && (
        <>
          <div className="kpi-row">
            <Kpi label="Income" value={formatCurrency(summary.income)} tone="pos" />
            <Kpi label="Expenses" value={formatCurrency(summary.expenses)} tone="neg" />
            <Kpi
              label="Net"
              value={formatCurrency(summary.net)}
              tone={summary.net >= 0 ? 'pos' : 'neg'}
            />
            <Kpi label="Savings rate" value={`${summary.savings_rate.toFixed(1)}%`} />
          </div>

          <div className="chart-grid">
            <div className="card">
              <h3 className="card-title">Spending by category</h3>
              {categories.length === 0 ? (
                <p className="muted-note">No expenses this month.</p>
              ) : (
                <ResponsiveContainer width="100%" height={Math.max(160, categories.length * 36)}>
                  <BarChart
                    layout="vertical"
                    data={categories}
                    margin={{ top: 4, right: 24, bottom: 4, left: 8 }}
                  >
                    <CartesianGrid horizontal={false} stroke={GRID} />
                    <XAxis
                      type="number"
                      tickFormatter={(v) => formatCurrency(v)}
                      stroke="#94a3b8"
                      fontSize={12}
                    />
                    <YAxis
                      type="category"
                      dataKey="category"
                      width={110}
                      stroke="#94a3b8"
                      fontSize={12}
                    />
                    <Tooltip formatter={(v) => formatCurrency(Number(v))} />
                    <Bar dataKey="amount" fill={INCOME} radius={[0, 4, 4, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              )}
            </div>

            <div className="card">
              <h3 className="card-title">Income vs expenses</h3>
              <ResponsiveContainer width="100%" height={260}>
                <LineChart data={trend} margin={{ top: 8, right: 24, bottom: 4, left: 8 }}>
                  <CartesianGrid stroke={GRID} />
                  <XAxis
                    dataKey="month"
                    tickFormatter={monthLabel}
                    stroke="#94a3b8"
                    fontSize={12}
                  />
                  <YAxis tickFormatter={(v) => formatCurrency(v)} stroke="#94a3b8" fontSize={12} />
                  <Tooltip
                    formatter={(v) => formatCurrency(Number(v))}
                    labelFormatter={(l) => monthLabel(String(l))}
                  />
                  <Legend />
                  <Line
                    type="monotone"
                    dataKey="income"
                    name="Income"
                    stroke={INCOME}
                    strokeWidth={2}
                    dot={{ r: 3 }}
                    activeDot={{ r: 5 }}
                  />
                  <Line
                    type="monotone"
                    dataKey="expenses"
                    name="Expenses"
                    stroke={EXPENSE}
                    strokeWidth={2}
                    dot={{ r: 3 }}
                    activeDot={{ r: 5 }}
                  />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </div>
        </>
      )}
    </section>
  )
}

function Kpi({ label, value, tone }: { label: string; value: string; tone?: 'pos' | 'neg' }) {
  return (
    <div className="kpi">
      <span className="kpi-label">{label}</span>
      <span className={`kpi-value${tone ? ` ${tone}` : ''}`}>{value}</span>
    </div>
  )
}
