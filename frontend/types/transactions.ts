/**
 * Transaction type enum
 */
export type TransactionType = 'INCOME' | 'EXPENSE' | 'TRANSFER'

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
 * Credit card interface
 */
export interface CreditCard {
  id: number
  name: string
  created_at: string
  updated_at: string
  is_active: boolean
}

/**
 * Category list interface
 */
export interface CategoryList {
  id: number
  name: string
  transaction_type: 'income' | 'expense'
  parent?: number | null
  is_active: boolean
}

/**
 * Tag interface
 */
export interface Tag {
  id: number
  name: string
  created_at: string
}

/**
 * Transaction interface
 */
export interface Transaction {
  id: number
  user: number
  transaction_type: TransactionType
  amount: string
  description?: string | null
  occurred_at: string
  installments_total: number
  installment_number: number
  installment_group_id: string | null
  created_at: string
  updated_at: string
  account: Account | null
  account_id?: number | null
  credit_card: CreditCard | null
  credit_card_id?: number | null
  category: CategoryList | null
  category_id?: number | null
  subcategory: CategoryList | null
  subcategory_id?: number | null
  tags: Tag[]
  tag_ids?: number[]
  need_review?: boolean
}

/**
 * Patched transaction interface for partial updates
 */
export interface PatchedTransaction {
  id?: number
  user?: number
  transaction_type?: TransactionType
  amount?: string
  description?: string | null
  occurred_at?: string
  installments_total?: number
  installment_number?: number
  installment_group_id?: string | null
  created_at?: string
  updated_at?: string
  account?: Account | null
  account_id?: number | null
  credit_card?: CreditCard | null
  credit_card_id?: number | null
  category?: CategoryList | null
  category_id?: number | null
  subcategory?: CategoryList | null
  subcategory_id?: number | null
  tags?: Tag[]
  tag_ids?: number[]
}

/**
 * Transaction creation request interface
 */
export interface CreateTransactionRequest {
  transaction_type: TransactionType
  amount: string
  description?: string
  occurred_at: string
  installments_total?: number
  installment_number?: number
  account_id?: number | null
  credit_card_id?: number | null
  category_id?: number | null
  subcategory_id?: number | null
  tag_ids?: number[]
}

/**
 * Transaction update request interface
 */
export interface UpdateTransactionRequest {
  transaction_type: TransactionType
  amount: string
  description?: string
  occurred_at: string
  installments_total?: number
  installment_number?: number
  account_id?: number | null
  credit_card_id?: number | null
  category_id?: number | null
  subcategory_id?: number | null
  tag_ids?: number[]
}

/**
 * Transaction filters interface for query parameters
 */
export interface TransactionFilters {
  account_id?: number | null
  category_id?: number | null
  subcategory_id?: number | null
  credit_card_id?: number | null
  occurred_at?: string | null
  transaction_type?: TransactionType | null
}

/**
 * Transaction form interface for UI forms
 */
export interface TransactionForm {
  transaction_type: TransactionType | ''
  amount: string
  description: string
  occurred_at: string
  installments_total: string
  installment_number: string
  account_id: string | number | null
  credit_card_id: string | number | null
  category_id: string | number | null
  subcategory_id: string | number | null
  tag_ids: number[]
}

/**
 * Transaction API response wrapper
 */
export interface TransactionApiResponse {
  data: Transaction
  message?: string
}

/**
 * Transactions list API response wrapper
 */
export interface TransactionsListApiResponse {
  data: Transaction[]
  message?: string
}

/**
 * Transaction statistics interface
 */
export interface TransactionStats {
  total_transactions: number
  total_income: string
  total_expenses: string
  total_transfers: string
  income_count: number
  expense_count: number
  transfer_count: number
}

/**
 * Transaction API error interface
 */
export interface TransactionApiError {
  message: string
  field?: string
  code?: string
}

/**
 * Transaction API result with error handling
 */
export interface TransactionApiResult<T> {
  success: boolean
  data?: T
  error?: TransactionApiError
}

/**
 * Type guards for runtime type checking
 */
export const isTransactionType = (value: any): value is TransactionType => {
  return value === 'INCOME' || value === 'EXPENSE' || value === 'TRANSFER'
}

export const isTransaction = (value: any): value is Transaction => {
  return (
    typeof value === 'object' &&
    value !== null &&
    typeof value.id === 'number' &&
    typeof value.user === 'number' &&
    isTransactionType(value.transaction_type) &&
    typeof value.amount === 'string' &&
    typeof value.occurred_at === 'string' &&
    typeof value.installments_total === 'number' &&
    typeof value.installment_number === 'number' &&
    typeof value.created_at === 'string' &&
    typeof value.updated_at === 'string' &&
    (value.account === null || typeof value.account === 'object') &&
    (value.credit_card === null || typeof value.credit_card === 'object') &&
    (value.category === null || typeof value.category === 'object') &&
    (value.subcategory === null || typeof value.subcategory === 'object') &&
    Array.isArray(value.tags)
  )
}

/**
 * Utility types for form handling
 */
export type TransactionFormErrors = Partial<Record<keyof TransactionForm, string>>

export type TransactionFormState = {
  form: TransactionForm
  errors: TransactionFormErrors
  isSubmitting: boolean
  isValid: boolean
}

/**
 * Transaction table column interface
 */
export interface TransactionTableColumn {
  key: keyof Transaction | 'actions'
  label: string
  sortable?: boolean
  width?: string
  align?: 'left' | 'center' | 'right'
}

/**
 * Transaction table sort interface
 */
export interface TransactionTableSort {
  key: keyof Transaction
  direction: 'asc' | 'desc'
}

/**
 * Transaction table filters interface
 */
export interface TransactionTableFilters {
  search?: string
  transaction_type?: TransactionType | ''
  account_id?: number | null
  category_id?: number | null
  subcategory_id?: number | null
  credit_card_id?: number | null
  date_from?: string
  date_to?: string
  amount_min?: string
  amount_max?: string
}

/**
 * Bulk transaction update interface for individual transaction updates
 */
export interface BulkTransactionUpdate {
  id: number
  account_id?: number | null
  credit_card_id?: number | null
  transaction_type?: TransactionType
  amount?: string
  description?: string | null
  occurred_at?: string
  category_id?: number | null
  subcategory_id?: number | null
  tag_ids?: number[]
  installments_total?: number
  installment_number?: number
  need_review?: boolean
}

/**
 * Bulk transaction update request interface
 */
export interface BulkTransactionUpdateRequest {
  transactions: BulkTransactionUpdate[]
}

/**
 * Paginated transaction response interface
 */
export interface PaginatedTransactionResponse {
  count: number
  next: string | null
  previous: string | null
  results: Transaction[]
} 