import { request } from './client'
import type { Budget, BudgetCreate } from '../types/budget'

export function listBudgets(): Promise<Budget[]> {
  return request<Budget[]>('/budgets')
}

export function createBudget(body: BudgetCreate): Promise<Budget> {
  return request<Budget>('/budgets', { method: 'POST', body: JSON.stringify(body) })
}

export function deleteBudget(id: number): Promise<void> {
  return request<void>(`/budgets/${id}`, { method: 'DELETE' })
}
