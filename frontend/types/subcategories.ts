/**
 * Transaction type enum for subcategories (inherited from parent category)
 */
export type TransactionType = 'income' | 'expense'

/**
 * Subcategory list interface for listing operations
 * Used for GET /api/v1/finance/subcategories/ responses
 */
export interface SubcategoryList {
  id: number
  name: string
  category: number // Parent category ID (readOnly in API)
  transaction_type: TransactionType // Inherited from parent category (readOnly)
  is_active: boolean
}

/**
 * Base subcategory interface with common properties
 */
export interface BaseSubcategory {
  id: number
  name: string
  description?: string
  created_at: string
  updated_at: string
  is_active: boolean
  user: number
  category: number // Parent category ID
}

/**
 * Full subcategory interface for detailed operations
 * Used for GET /api/v1/finance/subcategories/{id}/ and POST responses
 */
export interface Subcategory extends BaseSubcategory {
  // All properties from BaseSubcategory are inherited
}

/**
 * Subcategory detail interface for detailed subcategory information
 * Used for GET /api/v1/finance/subcategories/{id}/ responses
 */
export interface SubcategoryDetail extends Omit<BaseSubcategory, 'category'> {
  category: Record<string, any> // Category object (readOnly)
}

/**
 * Patched subcategory interface for partial updates
 * Used for PATCH /api/v1/finance/subcategories/{id}/ requests
 */
export interface PatchedSubcategory {
  id?: number
  name?: string
  description?: string
  created_at?: string
  updated_at?: string
  is_active?: boolean
  user?: number
  category?: number // Still required for updates
}

/**
 * Subcategory creation request interface
 * Used for POST /api/v1/finance/subcategories/ requests
 */
export interface CreateSubcategoryRequest {
  name: string
  category: number // Required parent category ID
  description?: string
  is_active?: boolean
}

/**
 * Subcategory update request interface
 * Used for PUT /api/v1/finance/subcategories/{id}/ requests
 */
export interface UpdateSubcategoryRequest {
  name: string
  category: number // Required parent category ID
  description?: string
  is_active: boolean
}

/**
 * Subcategory filters interface for query parameters
 * Used for filtering subcategories in GET requests
 */
export interface SubcategoryFilters {
  category?: number | null // Filter by category ID
}

/**
 * Subcategory form interface for UI forms
 */
export interface SubcategoryForm {
  name: string
  category: string | number | null
  description: string
  is_active: boolean
}

/**
 * Subcategory API response wrapper
 */
export interface SubcategoryApiResponse {
  data: Subcategory | SubcategoryList | SubcategoryDetail
  message?: string
}

/**
 * Subcategories list API response wrapper
 */
export interface SubcategoriesListApiResponse {
  data: SubcategoryList[]
  message?: string
}

/**
 * Subcategory API error interface
 */
export interface SubcategoryApiError {
  message: string
  field?: string
  code?: string
}

/**
 * Subcategory API response with error handling
 */
export interface SubcategoryApiResult<T> {
  success: boolean
  data?: T
  error?: SubcategoryApiError
}

/**
 * Paginated subcategory list response
 */
export interface PaginatedSubcategoryList {
  count: number
  next: string | null
  previous: string | null
  results: SubcategoryList[]
}

/**
 * Type guards for runtime type checking
 */
export const isSubcategory = (value: any): value is Subcategory => {
  return (
    typeof value === 'object' &&
    value !== null &&
    typeof value.id === 'number' &&
    typeof value.name === 'string' &&
    typeof value.category === 'number' &&
    typeof value.created_at === 'string' &&
    typeof value.updated_at === 'string' &&
    typeof value.is_active === 'boolean' &&
    typeof value.user === 'number'
  )
}

export const isSubcategoryList = (value: any): value is SubcategoryList => {
  return (
    typeof value === 'object' &&
    value !== null &&
    typeof value.id === 'number' &&
    typeof value.name === 'string' &&
    typeof value.category === 'number' &&
    typeof value.is_active === 'boolean' &&
    (value.transaction_type === 'income' || value.transaction_type === 'expense')
  )
}

export const isSubcategoryDetail = (value: any): value is SubcategoryDetail => {
  return (
    typeof value === 'object' &&
    value !== null &&
    typeof value.id === 'number' &&
    typeof value.name === 'string' &&
    typeof value.category === 'object' &&
    typeof value.created_at === 'string' &&
    typeof value.updated_at === 'string' &&
    typeof value.is_active === 'boolean' &&
    typeof value.user === 'number'
  )
}

/**
 * Utility types for form handling
 */
export type SubcategoryFormErrors = Partial<Record<keyof SubcategoryForm, string>>

export type SubcategoryFormState = {
  form: SubcategoryForm
  errors: SubcategoryFormErrors
  isSubmitting: boolean
  isValid: boolean
}

