import { request } from './client'
import type { Goal, GoalCreate, GoalUpdate } from '../types/goal'

export function listGoals(): Promise<Goal[]> {
  return request<Goal[]>('/goals')
}

export function createGoal(body: GoalCreate): Promise<Goal> {
  return request<Goal>('/goals', { method: 'POST', body: JSON.stringify(body) })
}

export function updateGoal(id: number, body: GoalUpdate): Promise<Goal> {
  return request<Goal>(`/goals/${id}`, { method: 'PATCH', body: JSON.stringify(body) })
}

export function updateGoalProgress(id: number, current_amount: number): Promise<Goal> {
  return updateGoal(id, { current_amount })
}

export function deleteGoal(id: number): Promise<void> {
  return request<void>(`/goals/${id}`, { method: 'DELETE' })
}
