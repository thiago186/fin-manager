/**
 * Account types based on the Fin Manager API
 */

/**
 * Account interface
 */
export interface Account {
  id: number
  name: string
  current_balance: string
  account_type: 'checking'
  currency: 'BRL'
  created_at: string
  updated_at: string
  is_active: boolean
}

/**
 * Account form interface for creating/editing
 */
export interface AccountForm {
  name: string
  current_balance: string
  account_type: 'checking'
  currency: 'BRL'
  is_active: boolean
}

/**
 * Account filters for API requests
 */
export interface AccountFilters {
  account_type?: string
  currency?: string
  is_active?: boolean
}

/**
 * Create account request interface
 */
export interface CreateAccountRequest {
  name: string
  current_balance: string
  account_type: 'checking'
  currency: 'BRL'
  is_active: boolean
}

/**
 * Update account request interface
 */
export interface UpdateAccountRequest {
  name?: string
  current_balance?: string
  account_type?: 'checking'
  currency?: 'BRL'
  is_active?: boolean
}

/**
 * API result wrapper
 */
export interface AccountApiResult<T> {
  success: boolean
  data?: T
  error?: {
    message: string
    code?: string
  }
}

/**
 * Account table filters for frontend
 */
export interface AccountTableFilters {
  search?: string
  account_type?: string
  currency?: string
  is_active?: boolean
}

/**
 * Account table sort configuration
 */
export interface AccountTableSort {
  key: keyof Account
  direction: 'asc' | 'desc'
} 