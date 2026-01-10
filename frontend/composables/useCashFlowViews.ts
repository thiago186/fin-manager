import type {
  CashFlowView,
  CashFlowViewForm,
  CashFlowGroupForm,
  CashFlowResultForm,
  CreateCashFlowViewRequest,
  UpdateCashFlowViewRequest,
  CashFlowViewApiResult,
  CashFlowReport,
  PaginatedCashFlowViewList
} from '~/types/cashFlowViews'

export const useCashFlowViews = () => {
  const config = useRuntimeConfig()

  // State
  const views = ref<CashFlowView[]>([])
  const loading = ref(false)
  const error = ref<string | null>(null)
  const currentReport = ref<CashFlowReport | null>(null)
  const reportLoading = ref(false)
  const reportError = ref<string | null>(null)

  // Load cash flow views
  const loadCashFlowViews = async (): Promise<CashFlowViewApiResult<CashFlowView[]>> => {
    loading.value = true
    error.value = null

    try {
      const response = await $fetch<PaginatedCashFlowViewList>('/finance/cash-flow-views/', {
        baseURL: config.public.apiBase,
        credentials: 'include'
      })

      views.value = response.results || []
      return { success: true, data: views.value }
    } catch (err: any) {
      const errorMessage = err?.data?.message || err?.data?.detail || 'Failed to load cash flow views'
      error.value = errorMessage
      console.error('Error loading cash flow views:', err)
      return {
        success: false,
        error: { message: errorMessage, code: err?.status?.toString() }
      }
    } finally {
      loading.value = false
    }
  }

  // Get cash flow view by ID
  const getCashFlowView = async (id: number): Promise<CashFlowViewApiResult<CashFlowView>> => {
    loading.value = true
    error.value = null

    try {
      const response = await $fetch<CashFlowView>(`/finance/cash-flow-views/${id}/`, {
        baseURL: config.public.apiBase,
        credentials: 'include'
      })

      return { success: true, data: response }
    } catch (err: any) {
      const errorMessage = err?.data?.message || 'Failed to get cash flow view'
      error.value = errorMessage
      console.error('Error getting cash flow view:', err)
      return {
        success: false,
        error: { message: errorMessage, code: err?.status?.toString() }
      }
    } finally {
      loading.value = false
    }
  }

  // Get cash flow report for a view and year
  const getCashFlowReport = async (viewId: number, year: number): Promise<CashFlowViewApiResult<CashFlowReport>> => {
    reportLoading.value = true
    reportError.value = null

    try {
      const params = new URLSearchParams()
      params.append('year', String(year))

      const response = await $fetch<CashFlowReport>(`/finance/cash-flow-views/${viewId}/report/?${params}`, {
        baseURL: config.public.apiBase,
        credentials: 'include'
      })

      currentReport.value = response
      return { success: true, data: response }
    } catch (err: any) {
      const errorMessage = err?.data?.message || err?.data?.detail || 'Failed to load cash flow report'
      reportError.value = errorMessage
      console.error('Error loading cash flow report:', err)
      return {
        success: false,
        error: { message: errorMessage, code: err?.status?.toString() }
      }
    } finally {
      reportLoading.value = false
    }
  }

  // Create a new cash flow view
  const createCashFlowView = async (viewData: CreateCashFlowViewRequest): Promise<CashFlowViewApiResult<CashFlowView>> => {
    loading.value = true
    error.value = null

    try {
      console.log('Creating cash flow view - Payload:', JSON.stringify(viewData, null, 2))
      const response = await $fetch<CashFlowView>('/finance/cash-flow-views/', {
        baseURL: config.public.apiBase,
        method: 'POST',
        body: viewData,
        credentials: 'include'
      })

      // Refresh views after creation
      await loadCashFlowViews()

      return { success: true, data: response }
    } catch (err: any) {
      const errorMessage = err?.data?.message || err?.data?.detail || 'Failed to create cash flow view'
      error.value = errorMessage
      console.error('Error creating cash flow view:', err)
      return {
        success: false,
        error: { message: errorMessage, code: err?.status?.toString() }
      }
    } finally {
      loading.value = false
    }
  }

  // Update an existing cash flow view (full replace)
  const updateCashFlowView = async (
    id: number,
    viewData: UpdateCashFlowViewRequest
  ): Promise<CashFlowViewApiResult<CashFlowView>> => {
    loading.value = true
    error.value = null

    try {
      console.log('Updating cash flow view - ID:', id, 'Payload:', JSON.stringify(viewData, null, 2))
      const response = await $fetch<CashFlowView>(`/finance/cash-flow-views/${id}/`, {
        baseURL: config.public.apiBase,
        method: 'PUT',
        body: viewData,
        credentials: 'include'
      })

      // Refresh views after update
      await loadCashFlowViews()

      return { success: true, data: response }
    } catch (err: any) {
      const errorMessage = err?.data?.message || err?.data?.detail || 'Failed to update cash flow view'
      error.value = errorMessage
      console.error('Error updating cash flow view:', err)
      return {
        success: false,
        error: { message: errorMessage, code: err?.status?.toString() }
      }
    } finally {
      loading.value = false
    }
  }

  // Convert API response to form format
  const cashFlowViewToForm = (view: CashFlowView): CashFlowViewForm => {
    console.log('Converting cash flow view to form:', view)
    const form = {
      name: view.name,
      groups: view.groups.map(g => {
        // Ensure category IDs are numbers
        const categoryIds = (g.categories || []).map(c => Number(c.id))
        return {
          id: g.id,
          name: g.name,
          position: g.position,
          category_ids: categoryIds
        }
      }),
      results: view.results.map(r => ({
        id: r.id,
        name: r.name,
        position: r.position
      }))
    }
    console.log('Form after conversion:', form)
    return form
  }

  // Convert form to update request format
  const formToUpdateData = (form: CashFlowViewForm): UpdateCashFlowViewRequest => {
    return {
      name: form.name,
      groups: form.groups.map(g => ({
        name: g.name,
        position: g.position,
        category_ids: g.category_ids
      })),
      results: form.results.map(r => ({
        name: r.name,
        position: r.position
      }))
    }
  }

  // Format view form data for API
  const formatViewData = (form: CashFlowViewForm): CreateCashFlowViewRequest => {
    return {
      name: form.name,
      groups: form.groups.map(group => ({
        name: group.name,
        position: group.position,
        category_ids: group.category_ids || []
      })),
      results: form.results.map(result => ({
        name: result.name,
        position: result.position
      }))
    }
  }

  // Format currency for display
  const formatCurrency = (amount: string): string => {
    return new Intl.NumberFormat('pt-BR', {
      style: 'currency',
      currency: 'BRL'
    }).format(parseFloat(amount))
  }

  // Format month name
  const formatMonthName = (monthNumber: string): string => {
    const months = [
      'Janeiro', 'Fevereiro', 'Março', 'Abril', 'Maio', 'Junho',
      'Julho', 'Agosto', 'Setembro', 'Outubro', 'Novembro', 'Dezembro'
    ]
    const monthIndex = parseInt(monthNumber) - 1
    return months[monthIndex] || monthNumber
  }

  // Clear errors
  const clearError = () => { error.value = null }
  const clearReportError = () => { reportError.value = null }

  return {
    // State
    views: readonly(views),
    loading: readonly(loading),
    error: readonly(error),
    currentReport: readonly(currentReport),
    reportLoading: readonly(reportLoading),
    reportError: readonly(reportError),

    // Methods
    loadCashFlowViews,
    getCashFlowView,
    getCashFlowReport,
    createCashFlowView,
    updateCashFlowView,
    cashFlowViewToForm,
    formToUpdateData,
    formatViewData,
    formatCurrency,
    formatMonthName,
    clearError,
    clearReportError
  }
}
