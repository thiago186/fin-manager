import type { TransactionType } from '~/types/categories'

export interface BudgetCategory {
  id: number
  name: string
  transaction_type: TransactionType
}

export interface BudgetList {
  id: number
  category: BudgetCategory
  amount: string
  is_active: boolean
  created_at: string
  updated_at: string
}

export interface Budget extends BudgetList {
  // Full budget detail, same fields as list for now
}

export interface CreateBudgetRequest {
  category_id: number
  amount: number
  is_active: boolean
}

export interface UpdateBudgetRequest {
  category_id: number
  amount: number
  is_active: boolean
}

export interface BudgetFilters {
  transaction_type?: TransactionType | null
  is_active?: boolean | null
}

export interface BudgetForm {
  category_id: string
  amount: string
  is_active: boolean
}

export interface BudgetApiResult<T> {
  success: boolean
  data?: T
  error?: { message: string; code?: string }
}
