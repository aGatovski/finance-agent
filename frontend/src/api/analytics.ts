import { request } from './client'
import type { Balance, CategoryBreakdown, MonthlySummary, Trend } from '../types/analytics'

export function getSummary(month: string): Promise<MonthlySummary> {
  return request<MonthlySummary>(`/analytics/summary?month=${month}`)
}

export function getByCategory(month: string): Promise<CategoryBreakdown> {
  return request<CategoryBreakdown>(`/analytics/by-category?month=${month}`)
}

export function getTrend(months = 6): Promise<Trend> {
  return request<Trend>(`/analytics/trend?months=${months}`)
}

export function getBalance(): Promise<Balance> {
  return request<Balance>('/analytics/balance')
}
