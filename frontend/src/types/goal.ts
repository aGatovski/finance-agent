export interface Goal {
  id: number
  name: string
  target_amount: number
  current_amount: number
  deadline: string | null
  progress_pct: number
}

export interface GoalCreate {
  name: string
  target_amount: number
  current_amount?: number
  deadline?: string | null
}

export interface GoalUpdate {
  name?: string
  target_amount?: number
  current_amount?: number
  deadline?: string | null
}
