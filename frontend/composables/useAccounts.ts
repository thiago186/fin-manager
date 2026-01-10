import type { 
  Account, 
  AccountForm, 
  AccountFilters, 
  CreateAccountRequest, 
  UpdateAccountRequest,
  AccountApiResult,
  AccountTableFilters,
  AccountTableSort
} from '~/types/accounts'

export const useAccounts = () => {
  const config = useRuntimeConfig()
  
  // State
  const accounts = ref<Account[]>([])
  const loading = ref(false)
  const error = ref<string | null>(null)
  const filters = ref<AccountTableFilters>({})
  const sort = ref<AccountTableSort>({ key: 'name', direction: 'asc' })

  // Load accounts with optional filters
  const loadAccounts = async (apiFilters?: AccountFilters): Promise<AccountApiResult<Account[]>> => {
    loading.value = true
    error.value = null
    
    try {
      const params = new URLSearchParams()
      
      // Add API filters
      if (apiFilters?.account_type) {
        params.append('account_type', apiFilters.account_type)
      }
      if (apiFilters?.currency) {
        params.append('currency', apiFilters.currency)
      }
      if (apiFilters?.is_active !== undefined) {
        params.append('is_active', String(apiFilters.is_active))
      }

      const response = await $fetch<Account[]>(`/finance/accounts/?${params}`, {
        baseURL: config.public.apiBase,
        credentials: 'include'
      })
      
      accounts.value = response
      return { success: true, data: response }
    } catch (err: any) {
      const errorMessage = err?.data?.message || 'Failed to load accounts'
      error.value = errorMessage
      console.error('Error loading accounts:', err)
      return { 
        success: false, 
        error: { message: errorMessage, code: err?.status?.toString() } 
      }
    } finally {
      loading.value = false
    }
  }

  // Create a new account
  const createAccount = async (accountData: CreateAccountRequest): Promise<AccountApiResult<Account>> => {
    loading.value = true
    error.value = null
    
    try {
      const response = await $fetch<Account>('/finance/accounts/', {
        baseURL: config.public.apiBase,
        method: 'POST',
        body: accountData,
        credentials: 'include'
      })

      // Refresh accounts after creation
      await loadAccounts()
      
      return { success: true, data: response }
    } catch (err: any) {
      const errorMessage = err?.data?.message || 'Failed to create account'
      error.value = errorMessage
      console.error('Error creating account:', err)
      return { 
        success: false, 
        error: { message: errorMessage, code: err?.status?.toString() } 
      }
    } finally {
      loading.value = false
    }
  }

  // Update an existing account
  const updateAccount = async (id: number, accountData: UpdateAccountRequest): Promise<AccountApiResult<Account>> => {
    loading.value = true
    error.value = null
    
    try {
      const response = await $fetch<Account>(`/finance/accounts/${id}/`, {
        baseURL: config.public.apiBase,
        method: 'PUT',
        body: accountData,
        credentials: 'include'
      })

      // Refresh accounts after update
      await loadAccounts()
      
      return { success: true, data: response }
    } catch (err: any) {
      const errorMessage = err?.data?.message || 'Failed to update account'
      error.value = errorMessage
      console.error('Error updating account:', err)
      return { 
        success: false, 
        error: { message: errorMessage, code: err?.status?.toString() } 
      }
    } finally {
      loading.value = false
    }
  }

  // Delete an account
  const deleteAccount = async (id: number): Promise<AccountApiResult<void>> => {
    loading.value = true
    error.value = null
    
    try {
      await $fetch(`/finance/accounts/${id}/`, {
        baseURL: config.public.apiBase,
        method: 'DELETE',
        credentials: 'include'
      })

      // Refresh accounts after deletion
      await loadAccounts()
      
      return { success: true }
    } catch (err: any) {
      const errorMessage = err?.data?.message || 'Failed to delete account'
      error.value = errorMessage
      console.error('Error deleting account:', err)
      return { 
        success: false, 
        error: { message: errorMessage, code: err?.status?.toString() } 
      }
    } finally {
      loading.value = false
    }
  }

  // Get account by ID
  const getAccount = async (id: number): Promise<AccountApiResult<Account>> => {
    try {
      const response = await $fetch<Account>(`/finance/accounts/${id}/`, {
        baseURL: config.public.apiBase,
        credentials: 'include'
      })
      
      return { success: true, data: response }
    } catch (err: any) {
      const errorMessage = err?.data?.message || 'Failed to get account'
      error.value = errorMessage
      console.error('Error getting account:', err)
      return { 
        success: false, 
        error: { message: errorMessage, code: err?.status?.toString() } 
      }
    }
  }

  // Format account form data for API
  const formatAccountData = (form: AccountForm): CreateAccountRequest | UpdateAccountRequest => {
    return {
      name: form.name,
      current_balance: form.current_balance,
      account_type: form.account_type,
      currency: form.currency,
      is_active: form.is_active
    }
  }

  // Apply table filters and sorting
  const applyTableFilters = (newFilters: AccountTableFilters) => {
    filters.value = { ...filters.value, ...newFilters }
  }

  const applyTableSort = (newSort: AccountTableSort) => {
    sort.value = newSort
  }

  // Get filtered and sorted accounts
  const getFilteredAccounts = computed(() => {
    let filtered = [...accounts.value]

    // Apply search filter
    if (filters.value.search) {
      const searchTerm = filters.value.search.toLowerCase()
      filtered = filtered.filter(account => 
        account.name.toLowerCase().includes(searchTerm)
      )
    }

    // Apply account type filter
    if (filters.value.account_type) {
      filtered = filtered.filter(account => 
        account.account_type === filters.value.account_type
      )
    }

    // Apply currency filter
    if (filters.value.currency) {
      filtered = filtered.filter(account => 
        account.currency === filters.value.currency
      )
    }

    // Apply active status filter
    if (filters.value.is_active !== undefined) {
      filtered = filtered.filter(account => 
        account.is_active === filters.value.is_active
      )
    }

    // Apply sorting
    filtered.sort((a, b) => {
      const aValue = a[sort.value.key]
      const bValue = b[sort.value.key]
      
      if (typeof aValue === 'string' && typeof bValue === 'string') {
        return sort.value.direction === 'asc' 
          ? aValue.localeCompare(bValue)
          : bValue.localeCompare(aValue)
      }
      
      if (typeof aValue === 'number' && typeof bValue === 'number') {
        return sort.value.direction === 'asc' 
          ? aValue - bValue
          : bValue - aValue
      }
      
      return 0
    })

    return filtered
  })

  // Get account statistics
  const getAccountStats = computed(() => {
    const total = accounts.value.length
    const active = accounts.value.filter(account => account.is_active).length
    const totalBalance = accounts.value
      .filter(account => account.is_active)
      .reduce((sum, account) => sum + parseFloat(account.current_balance), 0)
    
    return {
      total,
      active,
      inactive: total - active,
      totalBalance: totalBalance.toFixed(2)
    }
  })

  // Utility functions
  const formatCurrency = (amount: string): string => {
    return new Intl.NumberFormat('pt-BR', {
      style: 'currency',
      currency: 'BRL'
    }).format(parseFloat(amount))
  }

  const formatDate = (dateString: string): string => {
    return new Date(dateString).toLocaleDateString('pt-BR')
  }

  const getAccountTypeLabel = (type: string): string => {
    const labels: Record<string, string> = {
      checking: 'Conta Corrente'
    }
    return labels[type] || type
  }

  const getCurrencyLabel = (currency: string): string => {
    const labels: Record<string, string> = {
      BRL: 'Real Brasileiro'
    }
    return labels[currency] || currency
  }

  // Initialize accounts data
  const initialize = async (): Promise<void> => {
    await loadAccounts()
  }

  return {
    // State
    accounts: readonly(accounts),
    loading: readonly(loading),
    error: readonly(error),
    filters: readonly(filters),
    sort: readonly(sort),
    
    // Computed
    filteredAccounts: getFilteredAccounts,
    accountStats: getAccountStats,
    
    // Methods
    loadAccounts,
    createAccount,
    updateAccount,
    deleteAccount,
    getAccount,
    formatAccountData,
    applyTableFilters,
    applyTableSort,
    formatCurrency,
    formatDate,
    getAccountTypeLabel,
    getCurrencyLabel,
    initialize,
    
    // Clear error
    clearError: () => { error.value = null }
  }
} 