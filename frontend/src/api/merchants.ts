import { request } from './client'
import type { Merchant, MerchantUpdateResult } from '../types/merchant'

export function listMerchants(
  params: { search?: string; category?: string } = {},
): Promise<Merchant[]> {
  const q = new URLSearchParams()
  if (params.search) q.set('search', params.search)
  if (params.category) q.set('category', params.category)
  const qs = q.toString()
  return request<Merchant[]>(`/merchants${qs ? `?${qs}` : ''}`)
}

export interface MerchantPatch {
  category?: string
  is_internal?: boolean
  apply_to_existing?: boolean
}

export function updateMerchant(id: number, patch: MerchantPatch): Promise<MerchantUpdateResult> {
  return request<MerchantUpdateResult>(`/merchants/${id}`, {
    method: 'PATCH',
    body: JSON.stringify(patch),
  })
}

export function deleteMerchant(id: number): Promise<void> {
  return request<void>(`/merchants/${id}`, { method: 'DELETE' })
}
