import type {
  MonthlyByCategoryResponse,
  MonthlyByCategoryApiResult
} from '~/types/graphs'

export const useGraphs = () => {
  const config = useRuntimeConfig()

  const data = ref<MonthlyByCategoryResponse | null>(null)
  const loading = ref(false)
  const error = ref<string | null>(null)

  const loadMonthlyByCategory = async (
    year: number
  ): Promise<MonthlyByCategoryApiResult<MonthlyByCategoryResponse>> => {
    loading.value = true
    error.value = null

    try {
      const params = new URLSearchParams()
      params.append('year', String(year))

      const response = await $fetch<MonthlyByCategoryResponse>(
        `/finance/transactions/monthly-by-category/?${params}`,
        {
          baseURL: config.public.apiBase,
          credentials: 'include'
        }
      )

      data.value = response
      return { success: true, data: response }
    } catch (err: any) {
      const errorMessage =
        err?.data?.message || err?.data?.detail || 'Failed to load monthly data by category'
      error.value = errorMessage
      console.error('Error loading monthly by category:', err)
      return {
        success: false,
        error: { message: errorMessage, code: err?.status?.toString() }
      }
    } finally {
      loading.value = false
    }
  }

  const clearError = () => {
    error.value = null
  }

  return {
    data: readonly(data),
    loading: readonly(loading),
    error: readonly(error),
    loadMonthlyByCategory,
    clearError
  }
}
