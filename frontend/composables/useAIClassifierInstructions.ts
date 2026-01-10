import type {
  AIClassifierInstruction,
  CreateAIClassifierInstructionRequest,
  UpdateAIClassifierInstructionRequest,
  AIClassifierInstructionApiResult
} from '~/types/aiClassifierInstructions'

export const useAIClassifierInstructions = () => {
  const config = useRuntimeConfig()
  
  // State
  const instruction = ref<AIClassifierInstruction | null>(null)
  const loading = ref(false)
  const error = ref<string | null>(null)

  // Load the user's instruction (assumes only one per user)
  const loadInstruction = async (): Promise<AIClassifierInstructionApiResult<AIClassifierInstruction | null>> => {
    loading.value = true
    error.value = null
    
    try {
      const response = await $fetch<AIClassifierInstruction>('/ai/classifier-instructions/', {
        baseURL: config.public.apiBase,
        credentials: 'include'
      })

      instruction.value = response
      return { success: true, data: response }
    } catch (err: any) {
      // Handle 404 gracefully - user can still create new instruction
      const status = err?.status || err?.statusCode
      if (status === 404) {
        // 404 means no instruction exists, which is fine
        instruction.value = null
        return { success: true, data: null }
      }
      
      const errorMessage = err?.data?.message || err?.message || 'Failed to load AI classifier instruction'
      error.value = errorMessage
      console.error('Error loading AI classifier instruction:', err)
      return { 
        success: false, 
        error: { message: errorMessage, code: status?.toString() } 
      }
    } finally {
      loading.value = false
    }
  }

  // Create a new instruction
  const createInstruction = async (instructions: string): Promise<AIClassifierInstructionApiResult<AIClassifierInstruction>> => {
    loading.value = true
    error.value = null
    
    try {
      const requestData: CreateAIClassifierInstructionRequest = { instructions }
      const response = await $fetch<AIClassifierInstruction>('/ai/classifier-instructions/', {
        baseURL: config.public.apiBase,
        method: 'POST',
        body: requestData,
        credentials: 'include'
      })

      instruction.value = response
      
      return { success: true, data: response }
    } catch (err: any) {
      const errorMessage = err?.data?.message || 'Failed to create AI classifier instruction'
      error.value = errorMessage
      console.error('Error creating AI classifier instruction:', err)
      return { 
        success: false, 
        error: { message: errorMessage, code: err?.status?.toString() } 
      }
    } finally {
      loading.value = false
    }
  }

  // Update an existing instruction
  const updateInstruction = async (id: number, instructions: string): Promise<AIClassifierInstructionApiResult<AIClassifierInstruction>> => {
    loading.value = true
    error.value = null
    
    try {
      const requestData: UpdateAIClassifierInstructionRequest = { instructions }
      const response = await $fetch<AIClassifierInstruction>(`/ai/classifier-instructions/${id}/`, {
        baseURL: config.public.apiBase,
        method: 'PUT',
        body: requestData,
        credentials: 'include'
      })

      instruction.value = response
      
      return { success: true, data: response }
    } catch (err: any) {
      const errorMessage = err?.data?.message || 'Failed to update AI classifier instruction'
      error.value = errorMessage
      console.error('Error updating AI classifier instruction:', err)
      return { 
        success: false, 
        error: { message: errorMessage, code: err?.status?.toString() } 
      }
    } finally {
      loading.value = false
    }
  }

  // Save instruction - creates if no ID exists, updates otherwise
  const saveInstruction = async (instructions: string): Promise<AIClassifierInstructionApiResult<AIClassifierInstruction>> => {
    if (instruction.value?.id) {
      return await updateInstruction(instruction.value.id, instructions)
    } else {
      return await createInstruction(instructions)
    }
  }

  return {
    // State
    instruction: readonly(instruction),
    loading: readonly(loading),
    error: readonly(error),
    
    // Methods
    loadInstruction,
    createInstruction,
    updateInstruction,
    saveInstruction,
    
    // Clear error
    clearError: () => { error.value = null }
  }
}

