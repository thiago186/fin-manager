/**
 * Cash Flow Views types based on the Fin Manager API
 */

/**
 * Category reference in a cash flow group
 */
export interface CashFlowGroupCategory {
  id: number
  name: string
}

/**
 * Cash Flow Group interface
 */
export interface CashFlowGroup {
  id: number
  name: string
  position: number
  categories: CashFlowGroupCategory[]
  created_at: string
  updated_at: string
}

/**
 * Cash Flow Result interface
 */
export interface CashFlowResult {
  id: number
  name: string
  position: number
  created_at: string
  updated_at: string
}

/**
 * Cash Flow View interface
 */
export interface CashFlowView {
  id: number
  name: string
  groups: CashFlowGroup[]
  results: CashFlowResult[]
  created_at: string
  updated_at: string
}

/**
 * Group creation/update request (for POST/PUT)
 */
export interface CashFlowGroupRequest {
  name: string
  position: number
  category_ids: number[]
}

/**
 * Group update request (for PATCH - can include id)
 */
export interface CashFlowGroupUpdateRequest {
  id?: number
  name?: string
  position?: number
  category_ids?: number[]
}

/**
 * Result creation/update request (for POST/PUT)
 */
export interface CashFlowResultRequest {
  name: string
  position: number
}

/**
 * Result update request (for PATCH - can include id)
 */
export interface CashFlowResultUpdateRequest {
  id?: number
  name?: string
  position?: number
}

/**
 * Create Cash Flow View request
 */
export interface CreateCashFlowViewRequest {
  name: string
  groups: CashFlowGroupRequest[]
  results: CashFlowResultRequest[]
}

/**
 * Update Cash Flow View request (PUT - full replace)
 */
export interface UpdateCashFlowViewRequest {
  name: string
  groups: CashFlowGroupRequest[]
  results: CashFlowResultRequest[]
}

/**
 * Patch Cash Flow View request (PATCH - partial update)
 */
export interface PatchCashFlowViewRequest {
  name?: string
  groups?: CashFlowGroupUpdateRequest[]
  results?: CashFlowResultUpdateRequest[]
}

/**
 * Monthly totals map (month index 1-12 to amount string)
 */
export interface MonthlyTotals {
  [key: string]: string // "1" through "12" -> "5000.00"
}

/**
 * Subcategory in a cash flow report
 */
export interface CashFlowReportSubcategory {
  id: number
  name: string
  monthly_totals: MonthlyTotals
  annual_total: string
}

/**
 * Category in a cash flow report (includes subcategories)
 */
export interface CashFlowReportCategory {
  id: number
  name: string
  monthly_totals: MonthlyTotals
  annual_total: string
  subcategories: CashFlowReportSubcategory[]
}

/**
 * Report item for a group
 */
export interface CashFlowReportGroupItem {
  type: 'group'
  name: string
  position: number
  categories: CashFlowReportCategory[]
  monthly_totals: MonthlyTotals
  annual_total: string
}

/**
 * Report item for a result
 */
export interface CashFlowReportResultItem {
  type: 'result'
  name: string
  position: number
  monthly_totals: MonthlyTotals
  annual_total: string
}

/**
 * Report item for uncategorized transactions
 */
export interface CashFlowReportUncategorizedItem {
  type: 'uncategorized'
  name: string
  monthly_totals: MonthlyTotals
  annual_total: string
}

/**
 * Union type for report items
 */
export type CashFlowReportItem = CashFlowReportGroupItem | CashFlowReportResultItem | CashFlowReportUncategorizedItem

/**
 * Cash Flow Report response
 */
export interface CashFlowReport {
  view_id: number
  view_name: string
  year: number
  items: CashFlowReportItem[]
}

/**
 * Cash Flow View form interface for UI
 */
export interface CashFlowViewForm {
  name: string
  groups: CashFlowGroupForm[]
  results: CashFlowResultForm[]
}

/**
 * Group form interface for UI
 */
export interface CashFlowGroupForm {
  id?: number // Optional for new groups
  name: string
  position: number
  category_ids: number[]
}

/**
 * Result form interface for UI
 */
export interface CashFlowResultForm {
  id?: number // Optional for new results
  name: string
  position: number
}

/**
 * API result wrapper
 */
export interface CashFlowViewApiResult<T> {
  success: boolean
  data?: T
  error?: {
    message: string
    code?: string
  }
}

/**
 * Paginated Cash Flow View List response
 */
export interface PaginatedCashFlowViewList {
  count: number
  next: string | null
  previous: string | null
  results: CashFlowView[]
}

