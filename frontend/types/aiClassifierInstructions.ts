/**
 * AI Classifier Instruction interface
 * Matches the API schema from /api/v1/ai/classifier-instructions/
 */
export interface AIClassifierInstruction {
  id: number
  instructions: string
  created_at: string
  updated_at: string
}

/**
 * Paginated response for AI Classifier Instructions list
 */
export interface PaginatedAIClassifierInstructionList {
  count: number
  next: string | null
  previous: string | null
  results: AIClassifierInstruction[]
}

/**
 * Create AI Classifier Instruction request
 * Used for POST /api/v1/ai/classifier-instructions/
 */
export interface CreateAIClassifierInstructionRequest {
  instructions: string
}

/**
 * Update AI Classifier Instruction request
 * Used for PUT /api/v1/ai/classifier-instructions/{id}/
 */
export interface UpdateAIClassifierInstructionRequest {
  instructions: string
}

/**
 * Patched AI Classifier Instruction request
 * Used for PATCH /api/v1/ai/classifier-instructions/{id}/
 */
export interface PatchedAIClassifierInstruction {
  instructions?: string
}

/**
 * AI Classifier Instruction API error interface
 */
export interface AIClassifierInstructionApiError {
  message: string
  code?: string
}

/**
 * AI Classifier Instruction API response with error handling
 */
export interface AIClassifierInstructionApiResult<T> {
  success: boolean
  data?: T
  error?: AIClassifierInstructionApiError
}

