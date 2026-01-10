import type { 
  SubcategoryList, 
  SubcategoryForm, 
  SubcategoryFilters, 
  CreateSubcategoryRequest, 
  UpdateSubcategoryRequest,
  SubcategoryApiResult,
  PaginatedSubcategoryList
} from '~/types/subcategories'

export const useSubcategories = () => {
  const config = useRuntimeConfig()
  
  // State
  const subcategories = ref<SubcategoryList[]>([])
  const loading = ref(false)
  const error = ref<string | null>(null)

  // Load subcategories with optional filters
  const loadSubcategories = async (filters?: SubcategoryFilters): Promise<SubcategoryApiResult<SubcategoryList[]>> => {
    loading.value = true
    error.value = null
    
    try {
      const params = new URLSearchParams()
      if (filters?.category) {
        params.append('category', String(filters.category))
      }

      const response = await $fetch<PaginatedSubcategoryList | SubcategoryList[]>(`/finance/subcategories/?${params}`, {
        baseURL: config.public.apiBase,
        credentials: 'include'
      })
      
      // Handle paginated response or direct array
      const subcategoriesList = Array.isArray(response) 
        ? response 
        : (response as PaginatedSubcategoryList).results
      
      subcategories.value = subcategoriesList
      return { success: true, data: subcategoriesList }
    } catch (err: any) {
      const errorMessage = err?.data?.message || 'Failed to load subcategories'
      error.value = errorMessage
      console.error('Error loading subcategories:', err)
      return { 
        success: false, 
        error: { message: errorMessage, code: err?.status?.toString() } 
      }
    } finally {
      loading.value = false
    }
  }

  // Create a new subcategory
  const createSubcategory = async (subcategoryData: CreateSubcategoryRequest): Promise<SubcategoryApiResult<SubcategoryList>> => {
    loading.value = true
    error.value = null
    
    try {
      const response = await $fetch<SubcategoryList>('/finance/subcategories/', {
        baseURL: config.public.apiBase,
        method: 'POST',
        body: subcategoryData,
        credentials: 'include'
      })

      // Refresh subcategories after creation
      await loadSubcategories()
      
      return { success: true, data: response }
    } catch (err: any) {
      const errorMessage = err?.data?.message || 'Failed to create subcategory'
      error.value = errorMessage
      console.error('Error creating subcategory:', err)
      return { 
        success: false, 
        error: { message: errorMessage, code: err?.status?.toString() } 
      }
    } finally {
      loading.value = false
    }
  }

  // Update an existing subcategory
  const updateSubcategory = async (id: number, subcategoryData: UpdateSubcategoryRequest): Promise<SubcategoryApiResult<SubcategoryList>> => {
    loading.value = true
    error.value = null
    
    try {
      const response = await $fetch<SubcategoryList>(`/finance/subcategories/${id}/`, {
        baseURL: config.public.apiBase,
        method: 'PUT',
        body: subcategoryData,
        credentials: 'include'
      })

      // Refresh subcategories after update
      await loadSubcategories()
      
      return { success: true, data: response }
    } catch (err: any) {
      const errorMessage = err?.data?.message || 'Failed to update subcategory'
      error.value = errorMessage
      console.error('Error updating subcategory:', err)
      return { 
        success: false, 
        error: { message: errorMessage, code: err?.status?.toString() } 
      }
    } finally {
      loading.value = false
    }
  }

  // Delete a subcategory (soft delete)
  const deleteSubcategory = async (id: number): Promise<SubcategoryApiResult<void>> => {
    loading.value = true
    error.value = null
    
    try {
      await $fetch(`/finance/subcategories/${id}/`, {
        baseURL: config.public.apiBase,
        method: 'DELETE',
        credentials: 'include'
      })

      // Refresh subcategories after deletion
      await loadSubcategories()
      
      return { success: true }
    } catch (err: any) {
      const errorMessage = err?.data?.message || 'Failed to delete subcategory'
      error.value = errorMessage
      console.error('Error deleting subcategory:', err)
      return { 
        success: false, 
        error: { message: errorMessage, code: err?.status?.toString() } 
      }
    } finally {
      loading.value = false
    }
  }

  // Get subcategory by ID
  const getSubcategory = async (id: number): Promise<SubcategoryApiResult<SubcategoryList>> => {
    try {
      const response = await $fetch<SubcategoryList>(`/finance/subcategories/${id}/`, {
        baseURL: config.public.apiBase,
        credentials: 'include'
      })
      
      return { success: true, data: response }
    } catch (err: any) {
      const errorMessage = err?.data?.message || 'Failed to get subcategory'
      error.value = errorMessage
      console.error('Error getting subcategory:', err)
      return { 
        success: false, 
        error: { message: errorMessage, code: err?.status?.toString() } 
      }
    }
  }

  // Format subcategory form data for API
  const formatSubcategoryData = (form: SubcategoryForm): CreateSubcategoryRequest | UpdateSubcategoryRequest => {
    return {
      name: form.name,
      category: Number(form.category),
      description: form.description || '',
      is_active: form.is_active
    }
  }

  // Initialize subcategories data
  const initialize = async (): Promise<void> => {
    await loadSubcategories()
  }

  return {
    // State
    subcategories: readonly(subcategories),
    loading: readonly(loading),
    error: readonly(error),
    
    // Methods
    loadSubcategories,
    createSubcategory,
    updateSubcategory,
    deleteSubcategory,
    getSubcategory,
    formatSubcategoryData,
    initialize,
    
    // Clear error
    clearError: () => { error.value = null }
  }
}

