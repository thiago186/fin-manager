import type { 
  Transaction, 
  TransactionForm, 
  TransactionFilters, 
  CreateTransactionRequest, 
  UpdateTransactionRequest,
  TransactionApiResult,
  TransactionTableFilters,
  TransactionTableSort,
  BulkTransactionUpdateRequest,
  PaginatedTransactionResponse
} from '~/types/transactions'

export const useTransactions = () => {
  const config = useRuntimeConfig()
  
  // State
  const transactions = ref<Transaction[]>([])
  const transactionsNeedingReview = ref<Transaction[]>([])
  const loading = ref(false)
  const loadingReview = ref(false)
  const error = ref<string | null>(null)
  const classifying = ref(false)
  const filters = ref<TransactionTableFilters>({})
  const sort = ref<TransactionTableSort>({ key: 'occurred_at', direction: 'desc' })
  
  // Pagination state
  const pagination = ref<{ count: number; next: string | null; previous: string | null; currentPage: number }>({
    count: 0,
    next: null,
    previous: null,
    currentPage: 1
  })
  const paginationReview = ref<{ count: number; next: string | null; previous: string | null; currentPage: number }>({
    count: 0,
    next: null,
    previous: null,
    currentPage: 1
  })
  const pageSize = 100

  // Helper function to extract page number from URL
  const extractPageFromUrl = (url: string | null): number => {
    if (!url) return 1
    const match = url.match(/[?&]page=(\d+)/)
    return match ? parseInt(match[1], 10) : 1
  }

  // Load transactions with optional filters and pagination
  const loadTransactions = async (apiFilters?: TransactionFilters, page: number = 1): Promise<TransactionApiResult<Transaction[]>> => {
    loading.value = true
    error.value = null
    
    try {
      const params = new URLSearchParams()
      
      // Add pagination
      params.append('page', String(page))
      params.append('page_size', String(pageSize))
      
      // Add API filters
      if (apiFilters?.account_id) {
        params.append('account_id', String(apiFilters.account_id))
      }
      if (apiFilters?.category_id) {
        params.append('category_id', String(apiFilters.category_id))
      }
      if (apiFilters?.subcategory_id) {
        params.append('subcategory_id', String(apiFilters.subcategory_id))
      }
      if (apiFilters?.credit_card_id) {
        params.append('credit_card_id', String(apiFilters.credit_card_id))
      }
      if (apiFilters?.occurred_at) {
        params.append('occurred_at', apiFilters.occurred_at)
      }
      if (apiFilters?.transaction_type) {
        params.append('transaction_type', apiFilters.transaction_type)
      }

      const response = await $fetch<PaginatedTransactionResponse>(`/finance/transactions/?${params}`, {
        baseURL: config.public.apiBase,
        credentials: 'include'
      })
      
      transactions.value = response.results
      pagination.value = {
        count: response.count,
        next: response.next,
        previous: response.previous,
        currentPage: page
      }
      console.log('Transactions loaded:', response.results.length, 'of', response.count)
      return { success: true, data: response.results }
    } catch (err: any) {
      const errorMessage = err?.data?.message || 'Failed to load transactions'
      error.value = errorMessage
      console.error('Error loading transactions:', err)
      return { 
        success: false, 
        error: { message: errorMessage, code: err?.status?.toString() } 
      }
    } finally {
      loading.value = false
    }
  }

  // Load transactions needing review with pagination
  const loadTransactionsNeedingReview = async (page: number = 1): Promise<TransactionApiResult<Transaction[]>> => {
    loadingReview.value = true
    error.value = null
    
    try {
      const params = new URLSearchParams()
      params.append('page', String(page))
      params.append('page_size', String(pageSize))
      
      const response = await $fetch<PaginatedTransactionResponse>('/finance/transactions/needing-review/?' + params.toString(), {
        baseURL: config.public.apiBase,
        credentials: 'include'
      })
      
      transactionsNeedingReview.value = response.results
      paginationReview.value = {
        count: response.count,
        next: response.next,
        previous: response.previous,
        currentPage: page
      }
      console.log('Transactions needing review loaded:', response.results.length, 'of', response.count)
      return { success: true, data: response.results }
    } catch (err: any) {
      const errorMessage = err?.data?.message || 'Falha ao carregar transações para revisão'
      error.value = errorMessage
      console.error('Error loading transactions needing review:', err)
      return { 
        success: false, 
        error: { message: errorMessage, code: err?.status?.toString() } 
      }
    } finally {
      loadingReview.value = false
    }
  }

  // Create a new transaction
  const createTransaction = async (transactionData: CreateTransactionRequest): Promise<TransactionApiResult<Transaction>> => {
    loading.value = true
    error.value = null
    
    try {
      const response = await $fetch<Transaction>('/finance/transactions/', {
        baseURL: config.public.apiBase,
        method: 'POST',
        body: transactionData,
        credentials: 'include'
      })

      // Refresh transactions after creation
      await loadTransactions()
      
      return { success: true, data: response }
    } catch (err: any) {
      const errorMessage = err?.data?.message || 'Failed to create transaction'
      error.value = errorMessage
      console.error('Error creating transaction:', err)
      return { 
        success: false, 
        error: { message: errorMessage, code: err?.status?.toString() } 
      }
    } finally {
      loading.value = false
    }
  }

  // Update an existing transaction
  const updateTransaction = async (id: number, transactionData: UpdateTransactionRequest): Promise<TransactionApiResult<Transaction>> => {
    loading.value = true
    error.value = null
    
    try {
      const response = await $fetch<Transaction>(`/finance/transactions/${id}/`, {
        baseURL: config.public.apiBase,
        method: 'PUT',
        body: transactionData,
        credentials: 'include'
      })

      // Refresh transactions after update
      await loadTransactions()
      
      return { success: true, data: response }
    } catch (err: any) {
      const errorMessage = err?.data?.message || 'Failed to update transaction'
      error.value = errorMessage
      console.error('Error updating transaction:', err)
      return { 
        success: false, 
        error: { message: errorMessage, code: err?.status?.toString() } 
      }
    } finally {
      loading.value = false
    }
  }

  // Delete a transaction
  const deleteTransaction = async (id: number): Promise<TransactionApiResult<void>> => {
    loading.value = true
    error.value = null
    
    try {
      await $fetch(`/finance/transactions/${id}/`, {
        baseURL: config.public.apiBase,
        method: 'DELETE',
        credentials: 'include'
      })

      // Refresh transactions after deletion
      await loadTransactions()
      
      return { success: true }
    } catch (err: any) {
      const errorMessage = err?.data?.message || 'Failed to delete transaction'
      error.value = errorMessage
      console.error('Error deleting transaction:', err)
      return { 
        success: false, 
        error: { message: errorMessage, code: err?.status?.toString() } 
      }
    } finally {
      loading.value = false
    }
  }

  // Bulk update transactions
  const bulkUpdateTransactions = async (updateRequest: BulkTransactionUpdateRequest): Promise<TransactionApiResult<Transaction[]>> => {
    loading.value = true
    error.value = null
    
    try {
      const response = await $fetch<{ results: Transaction[] }>('/finance/transactions/bulk-update/', {
        baseURL: config.public.apiBase,
        method: 'PATCH',
        body: updateRequest,
        credentials: 'include'
      })

      // Refresh transactions after bulk update
      await loadTransactions()
      
      return { success: true, data: response.results }
    } catch (err: any) {
      const errorMessage = err?.data?.message || err?.data?.detail || 'Failed to bulk update transactions'
      error.value = errorMessage
      console.error('Error bulk updating transactions:', err)
      return { 
        success: false, 
        error: { message: errorMessage, code: err?.status?.toString() } 
      }
    } finally {
      loading.value = false
    }
  }

  // Classify transactions using AI
  const classifyTransactions = async (): Promise<TransactionApiResult<void>> => {
    classifying.value = true
    error.value = null
    
    try {
      await $fetch('/ai/classify-transactions/', {
        baseURL: config.public.apiBase,
        method: 'POST',
        credentials: 'include'
      })

      // Refresh transactions after successful classification
      await loadTransactions()
      
      return { success: true }
    } catch (err: any) {
      const errorMessage = err?.data?.message || err?.data?.detail || 'Falha ao categorizar transações'
      error.value = errorMessage
      console.error('Error classifying transactions:', err)
      return { 
        success: false, 
        error: { message: errorMessage, code: err?.status?.toString() } 
      }
    } finally {
      classifying.value = false
    }
  }

  // Get transaction by ID
  const getTransaction = async (id: number): Promise<TransactionApiResult<Transaction>> => {
    try {
      const response = await $fetch<Transaction>(`/finance/transactions/${id}/`, {
        baseURL: config.public.apiBase,
        credentials: 'include'
      })
      
      return { success: true, data: response }
    } catch (err: any) {
      const errorMessage = err?.data?.message || 'Failed to get transaction'
      error.value = errorMessage
      console.error('Error getting transaction:', err)
      return { 
        success: false, 
        error: { message: errorMessage, code: err?.status?.toString() } 
      }
    }
  }

  // Format transaction form data for API
  const formatTransactionData = (form: TransactionForm): CreateTransactionRequest | UpdateTransactionRequest => {
    return {
      transaction_type: form.transaction_type as 'INCOME' | 'EXPENSE' | 'TRANSFER',
      amount: form.amount,
      description: form.description || undefined,
      occurred_at: form.occurred_at,
      installments_total: form.installments_total ? Number(form.installments_total) : undefined,
      installment_number: form.installment_number ? Number(form.installment_number) : undefined,
      account_id: form.account_id === '' || form.account_id === null ? null : Number(form.account_id),
      credit_card_id: form.credit_card_id === '' || form.credit_card_id === null ? null : Number(form.credit_card_id),
      category_id: form.category_id === '' || form.category_id === null ? null : Number(form.category_id),
      subcategory_id: form.subcategory_id === '' || form.subcategory_id === null ? null : Number(form.subcategory_id),
      tag_ids: form.tag_ids
    }
  }

  // Apply table filters and sorting
  const applyTableFilters = (newFilters: TransactionTableFilters) => {
    filters.value = { ...filters.value, ...newFilters }
  }

  const applyTableSort = (newSort: TransactionTableSort) => {
    sort.value = newSort
  }

  // Get filtered and sorted transactions
  const getFilteredTransactions = computed(() => {
    console.log('Computing filtered transactions, total:', transactions.value.length)
    let filtered = [...transactions.value]

    // Apply search filter
    if (filters.value.search) {
      const searchTerm = filters.value.search.toLowerCase()
      filtered = filtered.filter(transaction => 
        transaction.description?.toLowerCase().includes(searchTerm) ||
        transaction.category?.name.toLowerCase().includes(searchTerm) ||
        transaction.subcategory?.name.toLowerCase().includes(searchTerm) ||
        transaction.account?.name.toLowerCase().includes(searchTerm) ||
        transaction.credit_card?.name.toLowerCase().includes(searchTerm)
      )
    }

    // Apply transaction type filter
    if (filters.value.transaction_type) {
      filtered = filtered.filter(transaction => 
        transaction.transaction_type === filters.value.transaction_type
      )
    }

    // Apply account filter
    if (filters.value.account_id) {
      filtered = filtered.filter(transaction => 
        transaction.account_id === filters.value.account_id
      )
    }

    // Apply credit card filter
    if (filters.value.credit_card_id !== null && filters.value.credit_card_id !== undefined) {
      const filterCreditCardId = filters.value.credit_card_id
      filtered = filtered.filter(transaction => {
        const transactionCreditCardId = transaction.credit_card_id ?? transaction.credit_card?.id
        const matches = transactionCreditCardId === filterCreditCardId
        return matches
      })
    }

    // Apply category filter
    if (filters.value.category_id) {
      filtered = filtered.filter(transaction => 
        transaction.category_id === filters.value.category_id
      )
    }

    // Apply subcategory filter
    if (filters.value.subcategory_id) {
      filtered = filtered.filter(transaction => {
        const transactionSubcategoryId = transaction.subcategory_id ?? transaction.subcategory?.id
        return transactionSubcategoryId === filters.value.subcategory_id
      })
    }

    // Apply date range filter
    if (filters.value.date_from) {
      filtered = filtered.filter(transaction => 
        transaction.occurred_at >= filters.value.date_from!
      )
    }

    if (filters.value.date_to) {
      filtered = filtered.filter(transaction => 
        transaction.occurred_at <= filters.value.date_to!
      )
    }

    // Apply amount range filter
    if (filters.value.amount_min) {
      filtered = filtered.filter(transaction => 
        parseFloat(transaction.amount) >= parseFloat(filters.value.amount_min!)
      )
    }

    if (filters.value.amount_max) {
      filtered = filtered.filter(transaction => 
        parseFloat(transaction.amount) <= parseFloat(filters.value.amount_max!)
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
        return sort.value.direction === 'asc' ? aValue - bValue : bValue - aValue
      }

      if (aValue instanceof Date && bValue instanceof Date) {
        return sort.value.direction === 'asc' 
          ? aValue.getTime() - bValue.getTime()
          : bValue.getTime() - aValue.getTime()
      }

      return 0
    })

    return filtered
  })

  // Calculate transaction statistics
  const getTransactionStats = computed(() => {
    const filtered = getFilteredTransactions.value
    const stats = {
      total_transactions: filtered.length,
      total_income: '0.00',
      total_expenses: '0.00',
      total_transfers: '0.00',
      income_count: 0,
      expense_count: 0,
      transfer_count: 0
    }

    filtered.forEach(transaction => {
      const amount = parseFloat(transaction.amount)
      
      switch (transaction.transaction_type) {
        case 'INCOME':
          stats.income_count++
          stats.total_income = (parseFloat(stats.total_income) + amount).toFixed(2)
          break
        case 'EXPENSE':
          stats.expense_count++
          stats.total_expenses = (parseFloat(stats.total_expenses) + amount).toFixed(2)
          break
        case 'TRANSFER':
          stats.transfer_count++
          stats.total_transfers = (parseFloat(stats.total_transfers) + amount).toFixed(2)
          break
      }
    })

    return stats
  })

  // Format currency for display
  const formatCurrency = (amount: string): string => {
    return new Intl.NumberFormat('pt-BR', {
      style: 'currency',
      currency: 'BRL'
    }).format(parseFloat(amount))
  }

  // Format date for display
  const formatDate = (dateString: string): string => {
    return new Date(dateString).toLocaleDateString('pt-BR')
  }

  // Get transaction type color
  const getTransactionTypeColor = (type: string): string => {
    switch (type) {
      case 'INCOME':
        return 'text-green-600'
      case 'EXPENSE':
        return 'text-red-600'
      case 'TRANSFER':
        return 'text-blue-600'
      default:
        return 'text-gray-600'
    }
  }

  // Get transaction type label
  const getTransactionTypeLabel = (type: string): string => {
    switch (type) {
      case 'INCOME':
        return 'Receita'
      case 'EXPENSE':
        return 'Despesa'
      case 'TRANSFER':
        return 'Transferência'
      default:
        return type
    }
  }

  // Pagination navigation methods for transactions
  const loadNextPage = async (apiFilters?: TransactionFilters): Promise<void> => {
    if (pagination.value.next) {
      const nextPage = pagination.value.currentPage + 1
      await loadTransactions(apiFilters, nextPage)
    }
  }

  const loadPreviousPage = async (apiFilters?: TransactionFilters): Promise<void> => {
    if (pagination.value.previous && pagination.value.currentPage > 1) {
      const prevPage = pagination.value.currentPage - 1
      await loadTransactions(apiFilters, prevPage)
    }
  }

  const loadPage = async (page: number, apiFilters?: TransactionFilters): Promise<void> => {
    if (page >= 1) {
      await loadTransactions(apiFilters, page)
    }
  }

  // Pagination navigation methods for review transactions
  const loadNextPageReview = async (): Promise<void> => {
    if (paginationReview.value.next) {
      const nextPage = paginationReview.value.currentPage + 1
      await loadTransactionsNeedingReview(nextPage)
    }
  }

  const loadPreviousPageReview = async (): Promise<void> => {
    if (paginationReview.value.previous && paginationReview.value.currentPage > 1) {
      const prevPage = paginationReview.value.currentPage - 1
      await loadTransactionsNeedingReview(prevPage)
    }
  }

  const loadPageReview = async (page: number): Promise<void> => {
    if (page >= 1) {
      await loadTransactionsNeedingReview(page)
    }
  }

  // Initialize transactions data
  const initialize = async (): Promise<void> => {
    console.log('Initializing transactions...')
    await loadTransactions()
    console.log('Initialization complete, loading:', loading.value)
  }

  return {
    // State
    transactions: readonly(transactions),
    transactionsNeedingReview: readonly(transactionsNeedingReview),
    loading: readonly(loading),
    loadingReview: readonly(loadingReview),
    error: readonly(error),
    classifying: readonly(classifying),
    filters: readonly(filters),
    sort: readonly(sort),
    pagination: readonly(pagination),
    paginationReview: readonly(paginationReview),
    
    // Computed
    filteredTransactions: getFilteredTransactions,
    transactionStats: getTransactionStats,
    
    // Methods
    loadTransactions,
    loadTransactionsNeedingReview,
    loadNextPage,
    loadPreviousPage,
    loadPage,
    loadNextPageReview,
    loadPreviousPageReview,
    loadPageReview,
    createTransaction,
    updateTransaction,
    deleteTransaction,
    bulkUpdateTransactions,
    classifyTransactions,
    getTransaction,
    formatTransactionData,
    applyTableFilters,
    applyTableSort,
    formatCurrency,
    formatDate,
    getTransactionTypeColor,
    getTransactionTypeLabel,
    initialize,
    
    // Clear error
    clearError: () => { error.value = null }
  }
} 