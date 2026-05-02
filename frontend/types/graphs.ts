export interface CategoryMonthlyTotals {
  id: number
  name: string
  transaction_type: string
  monthly_totals: Record<string, string>
}

export interface MonthlyByCategoryResponse {
  year: number
  categories: CategoryMonthlyTotals[]
}

export interface MonthlyByCategoryApiResult<T> {
  success: boolean
  data?: T
  error?: { message: string; code?: string }
}
