import { postForm, request } from './client'
import type {
  ImportResult,
  Transaction,
  TransactionCreate,
  TransactionList,
  TransactionUpdate,
} from '../types/transaction'

interface ListParams {
  month?: string
  category?: string
  limit?: number
  offset?: number
}

export function listTransactions(params: ListParams = {}): Promise<TransactionList> {
  const q = new URLSearchParams()
  if (params.month) q.set('month', params.month)
  if (params.category) q.set('category', params.category)
  q.set('limit', String(params.limit ?? 50))
  q.set('offset', String(params.offset ?? 0))
  return request<TransactionList>(`/transactions?${q.toString()}`)
}

export function importCsv(file: File): Promise<ImportResult> {
  const form = new FormData()
  form.append('file', file)
  return postForm<ImportResult>('/transactions/import', form)
}

export function updateCategory(
  id: number,
  category: string,
  applyToMerchant = false,
): Promise<Transaction> {
  const q = applyToMerchant ? '?apply_to_merchant=true' : ''
  return request<Transaction>(`/transactions/${id}${q}`, {
    method: 'PATCH',
    body: JSON.stringify({ category }),
  })
}

export function createTransaction(body: TransactionCreate): Promise<Transaction> {
  return request<Transaction>('/transactions', {
    method: 'POST',
    body: JSON.stringify(body),
  })
}

export function updateTransaction(id: number, body: TransactionUpdate): Promise<Transaction> {
  return request<Transaction>(`/transactions/${id}`, {
    method: 'PATCH',
    body: JSON.stringify(body),
  })
}

export function deleteTransaction(id: number): Promise<void> {
  return request<void>(`/transactions/${id}`, { method: 'DELETE' })
}
