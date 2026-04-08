import type {
  InstallmentPlan,
  InstallmentPlanForm,
  CreateInstallmentPlanRequest,
} from '~/types/transactions'

interface PaginatedInstallmentPlansResponse {
  count: number
  next: string | null
  previous: string | null
  results: InstallmentPlan[]
}

export const useInstallmentPlans = () => {
  const config = useRuntimeConfig()

  const installmentPlans = ref<InstallmentPlan[]>([])
  const loading = ref(false)
  const error = ref<string | null>(null)

  const loadInstallmentPlans = async () => {
    loading.value = true
    error.value = null

    try {
      const response = await $fetch<PaginatedInstallmentPlansResponse | InstallmentPlan[]>('/finance/installment-plans/', {
        baseURL: config.public.apiBase,
        credentials: 'include',
      })
      const plans = Array.isArray(response) ? response : (response.results || [])
      installmentPlans.value = plans
      return { success: true, data: plans }
    } catch (err: any) {
      const errorMessage = err?.data?.message || 'Failed to load installment plans'
      error.value = errorMessage
      console.error('Error loading installment plans:', err)
      return { success: false, error: { message: errorMessage, code: err?.status?.toString() } }
    } finally {
      loading.value = false
    }
  }

  const createInstallmentPlan = async (data: CreateInstallmentPlanRequest) => {
    loading.value = true
    error.value = null

    try {
      const response = await $fetch<InstallmentPlan>('/finance/installment-plans/', {
        baseURL: config.public.apiBase,
        method: 'POST',
        body: data,
        credentials: 'include',
      })
      await loadInstallmentPlans()
      return { success: true, data: response }
    } catch (err: any) {
      const errorMessage = err?.data?.message || 'Failed to create installment plan'
      error.value = errorMessage
      console.error('Error creating installment plan:', err)
      return { success: false, error: { message: errorMessage, code: err?.status?.toString() } }
    } finally {
      loading.value = false
    }
  }

  const deleteInstallmentPlan = async (id: number) => {
    loading.value = true
    error.value = null

    try {
      await $fetch(`/finance/installment-plans/${id}/`, {
        baseURL: config.public.apiBase,
        method: 'DELETE',
        credentials: 'include',
      })
      await loadInstallmentPlans()
      return { success: true }
    } catch (err: any) {
      const errorMessage = err?.data?.message || 'Failed to delete installment plan'
      error.value = errorMessage
      console.error('Error deleting installment plan:', err)
      return { success: false, error: { message: errorMessage, code: err?.status?.toString() } }
    } finally {
      loading.value = false
    }
  }

  const loadPlanTransactions = async (planId: number) => {
    try {
      const response = await $fetch(`/finance/installment-plans/${planId}/transactions/`, {
        baseURL: config.public.apiBase,
        credentials: 'include',
      })
      return { success: true, data: response }
    } catch (err: any) {
      const errorMessage = err?.data?.message || 'Failed to load plan transactions'
      console.error('Error loading plan transactions:', err)
      return { success: false, error: { message: errorMessage } }
    }
  }

  const formatInstallmentPlanData = (form: InstallmentPlanForm): CreateInstallmentPlanRequest => {
    const base: CreateInstallmentPlanRequest = {
      transaction_type: form.transaction_type as any,
      description: form.description || null,
      input_mode: form.input_mode,
      installments_count: Number(form.installments_count),
      first_due_date: form.first_due_date,
      account_id: form.account_id ? Number(form.account_id) : null,
      credit_card_id: form.credit_card_id ? Number(form.credit_card_id) : null,
      category_id: form.category_id ? Number(form.category_id) : null,
      subcategory_id: form.subcategory_id ? Number(form.subcategory_id) : null,
    }

    if (form.input_mode === 'total_and_count') {
      base.total_amount = form.total_amount || null
    } else {
      base.installment_amount = form.installment_amount || null
    }

    return base
  }

  return {
    installmentPlans: readonly(installmentPlans),
    loading: readonly(loading),
    error: readonly(error),

    loadInstallmentPlans,
    createInstallmentPlan,
    deleteInstallmentPlan,
    loadPlanTransactions,
    formatInstallmentPlanData,

    clearError: () => { error.value = null },
  }
}
