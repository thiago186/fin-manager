import type {
  ImportReport,
  ImportStatus,
  CSVUploadResponse,
  ImportReportApiResult,
  PaginatedResponse
} from '~/types/importReports'

export const useImportReports = () => {
  const config = useRuntimeConfig()

  // State
  const importReports = ref<ImportReport[]>([])
  const loading = ref(false)
  const error = ref<string | null>(null)
  const uploading = ref(false)
  const pollingIntervals = ref<Map<number, NodeJS.Timeout>>(new Map())

  // Upload CSV file
  const uploadCSV = async (
    file: File,
    options?: { account_id?: number; credit_card_id?: number }
  ): Promise<ImportReportApiResult<CSVUploadResponse>> => {
    uploading.value = true
    error.value = null

    // Validate file extension
    if (!file.name.toLowerCase().endsWith('.csv')) {
      const errorMessage = 'Por favor, selecione um arquivo CSV (.csv)'
      error.value = errorMessage
      uploading.value = false
      return {
        success: false,
        error: { message: errorMessage }
      }
    }

    // Validate that either account_id or credit_card_id is provided
    if (!options?.account_id && !options?.credit_card_id) {
      const errorMessage = 'É necessário selecionar uma conta ou cartão de crédito'
      error.value = errorMessage
      uploading.value = false
      return {
        success: false,
        error: { message: errorMessage }
      }
    }

    try {
      const formData = new FormData()
      formData.append('file', file)
      
      if (options?.account_id) {
        formData.append('account_id', String(options.account_id))
      }
      
      if (options?.credit_card_id) {
        formData.append('credit_card_id', String(options.credit_card_id))
      }

      const response = await $fetch<CSVUploadResponse>('/finance/transactions/import-report/', {
        baseURL: config.public.apiBase,
        method: 'POST',
        body: formData,
        credentials: 'include'
      })

      uploading.value = false
      return { success: true, data: response }
    } catch (err: any) {
      let errorMessage = 'Falha ao fazer upload do arquivo'
      
      if (err?.data?.file && Array.isArray(err.data.file) && err.data.file.length > 0) {
        errorMessage = err.data.file[0]
      } else if (err?.data?.error) {
        errorMessage = err.data.error
      } else if (err?.message) {
        errorMessage = err.message
      }

      error.value = errorMessage
      uploading.value = false
      console.error('Error uploading CSV:', err)
      return {
        success: false,
        error: { message: errorMessage, code: err?.status?.toString() }
      }
    }
  }

  // Upload JSON file
  const uploadJSON = async (
    file: File,
    options?: { account_id?: number; credit_card_id?: number }
  ): Promise<ImportReportApiResult<CSVUploadResponse>> => {
    uploading.value = true
    error.value = null

    // Validate file extension
    if (!file.name.toLowerCase().endsWith('.json')) {
      const errorMessage = 'Por favor, selecione um arquivo JSON (.json)'
      error.value = errorMessage
      uploading.value = false
      return {
        success: false,
        error: { message: errorMessage }
      }
    }

    // Validate that either account_id or credit_card_id is provided
    if (!options?.account_id && !options?.credit_card_id) {
      const errorMessage = 'É necessário selecionar uma conta ou cartão de crédito'
      error.value = errorMessage
      uploading.value = false
      return {
        success: false,
        error: { message: errorMessage }
      }
    }

    try {
      const formData = new FormData()
      formData.append('file', file)
      
      if (options?.account_id) {
        formData.append('account_id', String(options.account_id))
      }
      
      if (options?.credit_card_id) {
        formData.append('credit_card_id', String(options.credit_card_id))
      }

      const response = await $fetch<CSVUploadResponse>('/finance/transactions/import-report/', {
        baseURL: config.public.apiBase,
        method: 'POST',
        body: formData,
        credentials: 'include'
      })

      uploading.value = false
      return { success: true, data: response }
    } catch (err: any) {
      let errorMessage = 'Falha ao fazer upload do arquivo'
      
      if (err?.data?.file && Array.isArray(err.data.file) && err.data.file.length > 0) {
        errorMessage = err.data.file[0]
      } else if (err?.data?.error) {
        errorMessage = err.data.error
      } else if (err?.message) {
        errorMessage = err.message
      }

      error.value = errorMessage
      uploading.value = false
      console.error('Error uploading JSON:', err)
      return {
        success: false,
        error: { message: errorMessage, code: err?.status?.toString() }
      }
    }
  }

  // Get single import report by ID
  const getImportReport = async (id: number): Promise<ImportReportApiResult<ImportReport>> => {
    try {
      const response = await $fetch<ImportReport>(`/finance/import-reports/${id}/`, {
        baseURL: config.public.apiBase,
        credentials: 'include'
      })

      return { success: true, data: response }
    } catch (err: any) {
      const errorMessage = err?.data?.message || err?.data?.detail || 'Falha ao carregar relatório de importação'
      console.error('Error getting import report:', err)
      return {
        success: false,
        error: { message: errorMessage, code: err?.status?.toString() }
      }
    }
  }

  // Load all import reports
  const loadImportReports = async (): Promise<ImportReportApiResult<ImportReport[]>> => {
    loading.value = true
    error.value = null

    try {
      const response = await $fetch<PaginatedResponse<ImportReport>>('/finance/import-reports/', {
        baseURL: config.public.apiBase,
        credentials: 'include'
      })

      // Extract results from paginated response
      importReports.value = response.results || []
      loading.value = false
      console.log('Import reports loaded:', importReports.value.length)
      return { success: true, data: importReports.value }
    } catch (err: any) {
      let errorMessage = 'Falha ao carregar relatórios de importação'
      
      if (err?.data?.message) {
        errorMessage = err.data.message
      } else if (err?.data?.detail) {
        errorMessage = err.data.detail
      } else if (err?.message) {
        errorMessage = err.message
      }
      
      error.value = errorMessage
      loading.value = false
      console.error('Error loading import reports:', err)
      return {
        success: false,
        error: { message: errorMessage, code: err?.status?.toString() }
      }
    }
  }

  // Poll import status
  const pollImportStatus = (
    reportId: number,
    onUpdate: (report: ImportReport) => void,
    onComplete: (report: ImportReport) => void,
    maxDuration: number = 300000 // 5 minutes
  ): (() => void) => {
    const startTime = Date.now()
    let pollInterval: NodeJS.Timeout | null = null

    const poll = async () => {
      try {
        const result = await getImportReport(reportId)
        
        if (!result.success || !result.data) {
          console.error('Failed to poll import status:', result.error)
          if (pollInterval) {
            clearInterval(pollInterval)
            pollingIntervals.value.delete(reportId)
          }
          return
        }

        const report = result.data
        onUpdate(report)

        // Check if import is complete
        if (report.status === 'IMPORTED' || report.status === 'FAILED') {
          onComplete(report)
          if (pollInterval) {
            clearInterval(pollInterval)
            pollingIntervals.value.delete(reportId)
          }
          return
        }

        // Check if max duration exceeded
        if (Date.now() - startTime > maxDuration) {
          console.warn('Polling timeout reached for report:', reportId)
          if (pollInterval) {
            clearInterval(pollInterval)
            pollingIntervals.value.delete(reportId)
          }
          return
        }
      } catch (err) {
        console.error('Error polling import status:', err)
        if (pollInterval) {
          clearInterval(pollInterval)
          pollingIntervals.value.delete(reportId)
        }
      }
    }

    // Poll immediately
    poll()

    // Then poll every 2 seconds
    pollInterval = setInterval(poll, 2000)
    pollingIntervals.value.set(reportId, pollInterval)

    // Return cleanup function
    return () => {
      if (pollInterval) {
        clearInterval(pollInterval)
        pollingIntervals.value.delete(reportId)
      }
    }
  }

  // Stop polling for a specific report
  const stopPolling = (reportId: number) => {
    const interval = pollingIntervals.value.get(reportId)
    if (interval) {
      clearInterval(interval)
      pollingIntervals.value.delete(reportId)
    }
  }

  // Stop all polling
  const stopAllPolling = () => {
    pollingIntervals.value.forEach((interval) => {
      clearInterval(interval)
    })
    pollingIntervals.value.clear()
  }

  // Format date for display
  const formatDate = (dateString: string): string => {
    return new Date(dateString).toLocaleDateString('pt-BR', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit'
    })
  }

  // Format date time for display
  const formatDateTime = (dateString: string): string => {
    return new Date(dateString).toLocaleString('pt-BR', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit'
    })
  }

  // Get status badge color
  const getStatusBadgeColor = (status: ImportStatus): string => {
    switch (status) {
      case 'SENT':
        return 'bg-gray-100 text-gray-800'
      case 'PROCESSING':
        return 'bg-yellow-100 text-yellow-800'
      case 'IMPORTED':
        return 'bg-green-100 text-green-800'
      case 'FAILED':
        return 'bg-red-100 text-red-800'
      default:
        return 'bg-gray-100 text-gray-800'
    }
  }

  // Get status label in Portuguese
  const getStatusLabel = (status: ImportStatus): string => {
    switch (status) {
      case 'SENT':
        return 'Enviado'
      case 'PROCESSING':
        return 'Processando'
      case 'IMPORTED':
        return 'Importado'
      case 'FAILED':
        return 'Falhou'
      default:
        return status
    }
  }

  // Initialize import reports data
  const initialize = async (): Promise<void> => {
    await loadImportReports()
  }

  // Cleanup on unmount
  onUnmounted(() => {
    stopAllPolling()
  })

  return {
    // State
    importReports: readonly(importReports),
    loading: readonly(loading),
    error: readonly(error),
    uploading: readonly(uploading),

    // Methods
    uploadCSV,
    uploadJSON,
    getImportReport,
    loadImportReports,
    pollImportStatus,
    stopPolling,
    stopAllPolling,
    formatDate,
    formatDateTime,
    getStatusBadgeColor,
    getStatusLabel,
    initialize,

    // Clear error
    clearError: () => { error.value = null }
  }
}

