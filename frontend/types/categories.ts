/**
 * Transaction type enum for categories
 */
export type TransactionType = 'income' | 'expense'

/**
 * Base category interface with common properties
 */
export interface BaseCategory {
  id: number
  name: string
  transaction_type: TransactionType
  description?: string
  created_at: string
  updated_at: string
  is_active: boolean
  user: number
}

/**
 * Full category interface for detailed operations
 * Used for GET /api/v1/finance/categories/{id}/ and POST responses
 */
export interface Category extends BaseCategory {
  // All properties from BaseCategory are inherited
}

/**
 * Category list interface for listing operations
 * Used for GET /api/v1/finance/categories/ responses
 */
export interface CategoryList {
  id: number
  name: string
  transaction_type: TransactionType
  is_active: boolean
  created_at?: string
  updated_at?: string
}

/**
 * Category detail interface for detailed category information
 * Used for GET /api/v1/finance/categories/{id}/ responses
 */
export interface CategoryDetail extends BaseCategory {
  subcategories: Record<string, any>[] // Array of subcategory objects
}

/**
 * Patched category interface for partial updates
 * Used for PATCH /api/v1/finance/categories/{id}/ requests
 */
export interface PatchedCategory {
  id?: number
  name?: string
  transaction_type?: TransactionType
  description?: string
  created_at?: string
  updated_at?: string
  is_active?: boolean
  user?: number
}

/**
 * Category creation request interface
 * Used for POST /api/v1/finance/categories/ requests
 */
export interface CreateCategoryRequest {
  name: string
  transaction_type: TransactionType
  description?: string
  is_active?: boolean
}

/**
 * Category update request interface
 * Used for PUT /api/v1/finance/categories/{id}/ requests
 */
export interface UpdateCategoryRequest {
  name: string
  transaction_type: TransactionType
  description?: string
  is_active: boolean
}

/**
 * Category filters interface for query parameters
 * Used for filtering categories in GET requests
 */
export interface CategoryFilters {
  transaction_type?: TransactionType | null
}

/**
 * Category form interface for UI forms
 */
export interface CategoryForm {
  name: string
  transaction_type: TransactionType | ''
  description: string
  is_active: boolean
}

/**
 * Category API response wrapper
 */
export interface CategoryApiResponse {
  data: Category | CategoryList | CategoryDetail
  message?: string
}

/**
 * Categories list API response wrapper
 */
export interface CategoriesListApiResponse {
  data: CategoryList[]
  message?: string
}

/**
 * Category statistics interface
 */
export interface CategoryStats {
  total_categories: number
  income_categories: number
  expense_categories: number
  active_categories: number
  inactive_categories: number
}

/**
 * Type guards for runtime type checking
 */
export const isTransactionType = (value: any): value is TransactionType => {
  return value === 'income' || value === 'expense'
}

export const isCategory = (value: any): value is Category => {
  return (
    typeof value === 'object' &&
    value !== null &&
    typeof value.id === 'number' &&
    typeof value.name === 'string' &&
    isTransactionType(value.transaction_type) &&
    typeof value.created_at === 'string' &&
    typeof value.updated_at === 'string' &&
    typeof value.is_active === 'boolean' &&
    typeof value.user === 'number'
  )
}

export const isCategoryList = (value: any): value is CategoryList => {
  return (
    typeof value === 'object' &&
    value !== null &&
    typeof value.id === 'number' &&
    typeof value.name === 'string' &&
    isTransactionType(value.transaction_type) &&
    typeof value.is_active === 'boolean'
  )
}

export const isCategoryDetail = (value: any): value is CategoryDetail => {
  return (
    typeof value === 'object' &&
    value !== null &&
    typeof value.id === 'number' &&
    typeof value.name === 'string' &&
    isTransactionType(value.transaction_type) &&
    typeof value.created_at === 'string' &&
    typeof value.updated_at === 'string' &&
    typeof value.is_active === 'boolean' &&
    typeof value.user === 'number' &&
    Array.isArray(value.subcategories)
  )
}

/**
 * Utility types for form handling
 */
export type CategoryFormErrors = Partial<Record<keyof CategoryForm, string>>

export type CategoryFormState = {
  form: CategoryForm
  errors: CategoryFormErrors
  isSubmitting: boolean
  isValid: boolean
}

/**
 * Category API error interface
 */
export interface CategoryApiError {
  message: string
  field?: string
  code?: string
}

/**
 * Category API response with error handling
 */
export interface CategoryApiResult<T> {
  success: boolean
  data?: T
  error?: CategoryApiError
}
