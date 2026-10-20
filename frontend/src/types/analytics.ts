export interface MonthlySummary {
  month: string
  income: number
  expenses: number
  net: number
  savings_rate: number
}

export interface CategoryAmount {
  category: string
  amount: number
}

export interface CategoryBreakdown {
  month: string
  items: CategoryAmount[]
}

export interface TrendPoint {
  month: string
  income: number
  expenses: number
  net: number
}

export interface Trend {
  items: TrendPoint[]
}

export interface Balance {
  total_balance: number
}
