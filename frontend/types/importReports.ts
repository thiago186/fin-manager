/**
 * Import status type
 */
export type ImportStatus = 'SENT' | 'PROCESSING' | 'IMPORTED' | 'FAILED'

/**
 * Import report interface matching backend API
 */
export interface ImportReport {
  id: number
  status: ImportStatus
  file_name: string
  file_path: string
  handler_type: string | null
  failed_reason: string | null
  success_count: number
  error_count: number
  errors: string[]
  created_at: string
  updated_at: string
  processed_at: string | null
}

/**
 * CSV upload response interface
 */
export interface CSVUploadResponse {
  report_id: number
  status: string
  status_url: string
}

/**
 * Import report API error interface
 */
export interface ImportReportApiError {
  message: string
  field?: string
  code?: string
}

/**
 * Import report API result with error handling
 */
export interface ImportReportApiResult<T> {
  success: boolean
  data?: T
  error?: ImportReportApiError
}

/**
 * Paginated API response
 */
export interface PaginatedResponse<T> {
  count: number
  next: string | null
  previous: string | null
  results: T[]
}

