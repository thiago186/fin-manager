import type {
  BudgetList,
  BudgetForm,
  BudgetFilters,
  CreateBudgetRequest,
  UpdateBudgetRequest,
  BudgetApiResult,
  Budget,
} from '~/types/budgets'

export const useBudgets = () => {
  const config = useRuntimeConfig()

  const budgets = ref<BudgetList[]>([])
  const loading = ref(false)
  const error = ref<string | null>(null)

  const loadBudgets = async (filters?: BudgetFilters): Promise<BudgetApiResult<BudgetList[]>> => {
    loading.value = true
    error.value = null

    try {
      const params = new URLSearchParams()
      if (filters?.transaction_type) {
        params.append('transaction_type', filters.transaction_type)
      }
      if (filters?.is_active !== undefined && filters?.is_active !== null) {
        params.append('is_active', String(filters.is_active))
      }

      const response = await $fetch<BudgetList[]>(`/finance/budgets/?${params}`, {
        baseURL: config.public.apiBase,
        credentials: 'include',
      })

      budgets.value = response
      return { success: true, data: response }
    } catch (err: any) {
      const errorMessage = err?.data?.message || 'Failed to load budgets'
      error.value = errorMessage
      console.error('Error loading budgets:', err)
      return {
        success: false,
        error: { message: errorMessage, code: err?.status?.toString() },
      }
    } finally {
      loading.value = false
    }
  }

  const createBudget = async (budgetData: CreateBudgetRequest): Promise<BudgetApiResult<Budget>> => {
    loading.value = true
    error.value = null

    try {
      const response = await $fetch<Budget>('/finance/budgets/', {
        baseURL: config.public.apiBase,
        method: 'POST',
        body: budgetData,
        credentials: 'include',
      })

      await loadBudgets()
      return { success: true, data: response }
    } catch (err: any) {
      const errorMessage = err?.data?.message || 'Failed to create budget'
      error.value = errorMessage
      console.error('Error creating budget:', err)
      return {
        success: false,
        error: { message: errorMessage, code: err?.status?.toString() },
      }
    } finally {
      loading.value = false
    }
  }

  const updateBudget = async (id: number, budgetData: UpdateBudgetRequest): Promise<BudgetApiResult<Budget>> => {
    loading.value = true
    error.value = null

    try {
      const response = await $fetch<Budget>(`/finance/budgets/${id}/`, {
        baseURL: config.public.apiBase,
        method: 'PUT',
        body: budgetData,
        credentials: 'include',
      })

      await loadBudgets()
      return { success: true, data: response }
    } catch (err: any) {
      const errorMessage = err?.data?.message || 'Failed to update budget'
      error.value = errorMessage
      console.error('Error updating budget:', err)
      return {
        success: false,
        error: { message: errorMessage, code: err?.status?.toString() },
      }
    } finally {
      loading.value = false
    }
  }

  const deleteBudget = async (id: number): Promise<BudgetApiResult<void>> => {
    loading.value = true
    error.value = null

    try {
      await $fetch(`/finance/budgets/${id}/`, {
        baseURL: config.public.apiBase,
        method: 'DELETE',
        credentials: 'include',
      })

      await loadBudgets()
      return { success: true }
    } catch (err: any) {
      const errorMessage = err?.data?.message || 'Failed to delete budget'
      error.value = errorMessage
      console.error('Error deleting budget:', err)
      return {
        success: false,
        error: { message: errorMessage, code: err?.status?.toString() },
      }
    } finally {
      loading.value = false
    }
  }

  const formatBudgetData = (form: BudgetForm): CreateBudgetRequest | UpdateBudgetRequest => {
    return {
      category_id: Number(form.category_id),
      amount: Number(form.amount),
      is_active: form.is_active,
    }
  }

  const initialize = async (): Promise<void> => {
    await loadBudgets()
  }

  return {
    budgets: readonly(budgets),
    loading: readonly(loading),
    error: readonly(error),

    loadBudgets,
    createBudget,
    updateBudget,
    deleteBudget,
    formatBudgetData,
    initialize,

    clearError: () => { error.value = null },
  }
}
