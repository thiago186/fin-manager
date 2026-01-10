import type { 
  CategoryList, 
  CategoryForm, 
  CategoryFilters, 
  CreateCategoryRequest, 
  UpdateCategoryRequest,
  CategoryApiResult 
} from '~/types/categories'

export const useCategories = () => {
  const config = useRuntimeConfig()
  
  // State
  const categories = ref<CategoryList[]>([])
  const loading = ref(false)
  const error = ref<string | null>(null)

  // Load categories with optional filters
  const loadCategories = async (filters?: CategoryFilters): Promise<CategoryApiResult<CategoryList[]>> => {
    loading.value = true
    error.value = null
    
    try {
      const params = new URLSearchParams()
      if (filters?.transaction_type) {
        params.append('transaction_type', filters.transaction_type)
      }

      const response = await $fetch<CategoryList[]>(`/finance/categories/?${params}`, {
        baseURL: config.public.apiBase,
        credentials: 'include'
      })
      
      categories.value = response
      return { success: true, data: response }
    } catch (err: any) {
      const errorMessage = err?.data?.message || 'Failed to load categories'
      error.value = errorMessage
      console.error('Error loading categories:', err)
      return { 
        success: false, 
        error: { message: errorMessage, code: err?.status?.toString() } 
      }
    } finally {
      loading.value = false
    }
  }

  // Create a new category
  const createCategory = async (categoryData: CreateCategoryRequest): Promise<CategoryApiResult<CategoryList>> => {
    loading.value = true
    error.value = null
    
    try {
      const response = await $fetch<CategoryList>('/finance/categories/', {
        baseURL: config.public.apiBase,
        method: 'POST',
        body: categoryData,
        credentials: 'include'
      })

      // Refresh categories after creation
      await loadCategories()
      
      return { success: true, data: response }
    } catch (err: any) {
      const errorMessage = err?.data?.message || 'Failed to create category'
      error.value = errorMessage
      console.error('Error creating category:', err)
      return { 
        success: false, 
        error: { message: errorMessage, code: err?.status?.toString() } 
      }
    } finally {
      loading.value = false
    }
  }

  // Update an existing category
  const updateCategory = async (id: number, categoryData: UpdateCategoryRequest): Promise<CategoryApiResult<CategoryList>> => {
    loading.value = true
    error.value = null
    
    try {
      const response = await $fetch<CategoryList>(`/finance/categories/${id}/`, {
        baseURL: config.public.apiBase,
        method: 'PUT',
        body: categoryData,
        credentials: 'include'
      })

      // Refresh categories after update
      await loadCategories()
      
      return { success: true, data: response }
    } catch (err: any) {
      const errorMessage = err?.data?.message || 'Failed to update category'
      error.value = errorMessage
      console.error('Error updating category:', err)
      return { 
        success: false, 
        error: { message: errorMessage, code: err?.status?.toString() } 
      }
    } finally {
      loading.value = false
    }
  }

  // Delete a category
  const deleteCategory = async (id: number): Promise<CategoryApiResult<void>> => {
    loading.value = true
    error.value = null
    
    try {
      await $fetch(`/finance/categories/${id}/`, {
        baseURL: config.public.apiBase,
        method: 'DELETE',
        credentials: 'include'
      })

      // Refresh categories after deletion
      await loadCategories()
      
      return { success: true }
    } catch (err: any) {
      const errorMessage = err?.data?.message || 'Failed to delete category'
      error.value = errorMessage
      console.error('Error deleting category:', err)
      return { 
        success: false, 
        error: { message: errorMessage, code: err?.status?.toString() } 
      }
    } finally {
      loading.value = false
    }
  }

  // Get category by ID
  const getCategory = async (id: number): Promise<CategoryApiResult<CategoryList>> => {
    try {
      const response = await $fetch<CategoryList>(`/finance/categories/${id}/`, {
        baseURL: config.public.apiBase,
        credentials: 'include'
      })
      
      return { success: true, data: response }
    } catch (err: any) {
      const errorMessage = err?.data?.message || 'Failed to get category'
      error.value = errorMessage
      console.error('Error getting category:', err)
      return { 
        success: false, 
        error: { message: errorMessage, code: err?.status?.toString() } 
      }
    }
  }

  // Format category form data for API
  const formatCategoryData = (form: CategoryForm): CreateCategoryRequest | UpdateCategoryRequest => {
    return {
      name: form.name,
      transaction_type: form.transaction_type as 'income' | 'expense',
      description: form.description || '',
      is_active: form.is_active
    }
  }

  // Initialize categories data
  const initialize = async (): Promise<void> => {
    await loadCategories()
  }

  return {
    // State
    categories: readonly(categories),
    loading: readonly(loading),
    error: readonly(error),
    
    // Methods
    loadCategories,
    createCategory,
    updateCategory,
    deleteCategory,
    getCategory,
    formatCategoryData,
    initialize,
    
    // Clear error
    clearError: () => { error.value = null }
  }
}