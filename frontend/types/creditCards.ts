/**
 * Credit Card types based on the Fin Manager API
 */

/**
 * Credit Card interface
 */
export interface CreditCard {
  id: number
  name: string
  created_at: string
  updated_at: string
  is_active: boolean
}

/**
 * Credit Card form interface for creating/editing
 */
export interface CreditCardForm {
  name: string
  is_active: boolean
}

/**
 * Credit Card filters for API requests
 */
export interface CreditCardFilters {
  is_active?: boolean
}

/**
 * Create credit card request interface
 */
export interface CreateCreditCardRequest {
  name: string
  is_active: boolean
}

/**
 * Update credit card request interface
 */
export interface UpdateCreditCardRequest {
  name?: string
  is_active?: boolean
}

/**
 * API result wrapper
 */
export interface CreditCardApiResult<T> {
  success: boolean
  data?: T
  error?: {
    message: string
    code?: string
  }
}

/**
 * Credit Card table filters for frontend
 */
export interface CreditCardTableFilters {
  search?: string
  is_active?: boolean
}

/**
 * Credit Card table sort configuration
 */
export interface CreditCardTableSort {
  key: keyof CreditCard
  direction: 'asc' | 'desc'
} 