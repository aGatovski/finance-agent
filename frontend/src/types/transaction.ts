export interface Transaction {
  id: number
  date: string
  amount: number
  description: string | null
  merchant: string | null
  category: string | null
  category_src: string | null
  is_internal: boolean
  type: string | null
}

export interface TransactionList {
  items: Transaction[]
  total: number
}

export interface ImportResult {
  inserted: number
  skipped_internal: number
  categorized: number
  uncategorized: number
  format_cached: boolean
  detected_mapping: Record<string, unknown>
}

export interface TransactionCreate {
  date: string
  amount: number
  description?: string | null
  merchant?: string | null
  category?: string | null
  type?: string | null
  is_internal?: boolean
}

export type TransactionUpdate = Partial<TransactionCreate>
