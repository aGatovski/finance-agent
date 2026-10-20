export interface Merchant {
  id: number
  merchant_name: string
  category: string
  is_internal: boolean
  tx_count: number
}

export interface MerchantUpdateResult {
  merchant: Merchant
  updated_transactions: number
}
