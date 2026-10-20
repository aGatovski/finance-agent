export interface Budget {
  id: number
  category: string
  limit: number
  spent: number
  remaining: number
}

export interface BudgetCreate {
  category: string
  limit: number
}
