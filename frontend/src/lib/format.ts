/** Small formatting helpers shared across pages. */

const EUR = new Intl.NumberFormat('en-IE', {
  style: 'currency',
  currency: 'EUR',
  maximumFractionDigits: 2,
})

export function formatCurrency(n: number): string {
  return EUR.format(n)
}

/** Current month as 'YYYY-MM'. */
export function currentMonth(): string {
  const d = new Date()
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}`
}

/** 'YYYY-MM' → 'Mon YYYY' for display. */
export function monthLabel(month: string): string {
  const [y, m] = month.split('-').map(Number)
  return new Date(y, m - 1, 1).toLocaleString('en', { month: 'short', year: 'numeric' })
}
