<template>
  <div class="py-8">
    <!-- Page Header -->
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 mb-6">
      <div class="flex justify-between items-center">
        <div>
          <h1 class="text-3xl font-bold text-gray-900">Importações CSV</h1>
          <p class="mt-1 text-sm text-gray-500">
            Histórico de importações de transações via CSV
          </p>
        </div>
        <button
          @click="showImportModal = true"
          class="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
        >
          <ArrowUpTrayIcon class="h-4 w-4 mr-2" />
          Importar CSV
        </button>
      </div>
    </div>

    <!-- Import Reports Table -->
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
      <div class="bg-white shadow overflow-hidden sm:rounded-md">
        <div class="px-4 py-5 sm:px-6">
          <h3 class="text-lg leading-6 font-medium text-gray-900">
            Histórico de Importações
          </h3>
          <p class="mt-1 max-w-2xl text-sm text-gray-500">
            {{ importReports.length }} importações encontradas
          </p>
        </div>

        <!-- Loading State -->
        <div v-if="loading" class="flex justify-center items-center py-12">
          <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600"></div>
          <span class="ml-2">Carregando importações...</span>
        </div>

        <!-- Error State -->
        <div v-else-if="error" class="px-4 py-5 sm:px-6">
          <div class="bg-red-50 border border-red-200 rounded-md p-4">
            <div class="flex">
              <ExclamationTriangleIcon class="h-5 w-5 text-red-400" />
              <div class="ml-3">
                <h3 class="text-sm font-medium text-red-800">
                  Erro ao carregar importações
                </h3>
                <div class="mt-2 text-sm text-red-700">
                  {{ error }}
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Empty State -->
        <div
          v-else-if="importReports.length === 0"
          class="text-center py-12"
        >
          <DocumentArrowUpIcon class="mx-auto h-12 w-12 text-gray-400" />
          <h3 class="mt-2 text-sm font-medium text-gray-900">
            Nenhuma importação encontrada
          </h3>
          <p class="mt-1 text-sm text-gray-500">
            Comece importando seu primeiro arquivo CSV.
          </p>
          <div class="mt-6">
            <button
              @click="showImportModal = true"
              class="inline-flex items-center px-4 py-2 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
            >
              <ArrowUpTrayIcon class="h-4 w-4 mr-2" />
              Importar CSV
            </button>
          </div>
        </div>

        <!-- Table -->
        <div v-else class="overflow-x-auto">
          <table class="min-w-full divide-y divide-gray-200">
            <thead class="bg-gray-50">
              <tr>
                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Arquivo
                </th>
                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Status
                </th>
                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Resultado
                </th>
                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Handler
                </th>
                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Criado em
                </th>
                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Processado em
                </th>
                <th class="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Ações
                </th>
              </tr>
            </thead>
            <tbody class="bg-white divide-y divide-gray-200">
              <tr
                v-for="report in importReports"
                :key="report.id"
                class="hover:bg-gray-50 cursor-pointer"
                @click="selectedReport = { ...report, errors: [...report.errors] }"
              >
                <!-- File Name -->
                <td class="px-6 py-4 whitespace-nowrap">
                  <div class="flex items-center">
                    <DocumentIcon class="h-5 w-5 text-gray-400 mr-2" />
                    <div class="text-sm font-medium text-gray-900">
                      {{ report.file_name }}
                    </div>
                  </div>
                </td>

                <!-- Status -->
                <td class="px-6 py-4 whitespace-nowrap">
                  <span
                    :class="[
                      'inline-flex items-center px-2 py-1 text-xs font-semibold rounded-full',
                      getStatusBadgeColor(report.status)
                    ]"
                  >
                    <div
                      v-if="report.status === 'PROCESSING'"
                      class="animate-spin rounded-full h-3 w-3 border-b-2 border-yellow-600 mr-1"
                    ></div>
                    {{ getStatusLabel(report.status) }}
                  </span>
                </td>

                <!-- Result -->
                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                  <div v-if="report.status === 'IMPORTED'">
                    <span class="text-green-600 font-medium">{{ report.success_count }} sucesso</span>
                    <span v-if="report.error_count > 0" class="text-red-600 ml-2">
                      / {{ report.error_count }} erro{{ report.error_count > 1 ? 's' : '' }}
                    </span>
                  </div>
                  <span v-else-if="report.status === 'FAILED'" class="text-red-600">
                    Falhou
                  </span>
                  <span v-else class="text-gray-500">
                    -
                  </span>
                </td>

                <!-- Handler Type -->
                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                  {{ report.handler_type || '-' }}
                </td>

                <!-- Created At -->
                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                  {{ formatDateTime(report.created_at) }}
                </td>

                <!-- Processed At -->
                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                  {{ report.processed_at ? formatDateTime(report.processed_at) : '-' }}
                </td>

                <!-- Actions -->
                <td class="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                  <button
                    @click.stop="selectedReport = { ...report, errors: [...report.errors] }"
                    class="text-indigo-600 hover:text-indigo-900"
                  >
                    Ver detalhes
                  </button>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>

    <!-- Import Modal -->
    <CsvImportModal
      v-if="showImportModal"
      @close="showImportModal = false"
      @imported="handleImportComplete"
    />

    <!-- Report Details Modal -->
    <div
      v-if="selectedReport"
      class="fixed inset-0 z-50 overflow-y-auto"
      @click="selectedReport = null"
    >
      <div class="flex items-end justify-center min-h-screen pt-4 px-4 pb-20 text-center sm:block sm:p-0">
        <!-- Background overlay -->
        <div class="fixed inset-0 bg-gray-500 bg-opacity-75 transition-opacity"></div>

        <!-- Modal panel -->
        <div
          class="inline-block align-bottom bg-white rounded-lg text-left overflow-hidden shadow-xl transform transition-all sm:my-8 sm:align-middle sm:max-w-3xl sm:w-full"
          @click.stop
        >
          <div class="bg-white px-4 pt-5 pb-4 sm:p-6 sm:pb-4">
            <div class="sm:flex sm:items-start">
              <div class="mt-3 text-center sm:mt-0 sm:text-left w-full">
                <div class="flex justify-between items-center mb-4">
                  <h3 class="text-lg leading-6 font-medium text-gray-900">
                    Detalhes da Importação
                  </h3>
                  <button
                    @click="selectedReport = null"
                    class="text-gray-400 hover:text-gray-600"
                  >
                    <XMarkIcon class="h-6 w-6" />
                  </button>
                </div>

                <!-- Report Details -->
                <div class="space-y-4">
                  <!-- File Info -->
                  <div>
                    <h4 class="text-sm font-medium text-gray-700 mb-2">Arquivo</h4>
                    <div class="bg-gray-50 rounded-lg p-3">
                      <div class="flex items-center">
                        <DocumentIcon class="h-5 w-5 text-gray-400 mr-2" />
                        <span class="text-sm text-gray-900">{{ selectedReport.file_name }}</span>
                      </div>
                    </div>
                  </div>

                  <!-- Status -->
                  <div>
                    <h4 class="text-sm font-medium text-gray-700 mb-2">Status</h4>
                    <span
                      :class="[
                        'inline-flex items-center px-3 py-1 text-sm font-semibold rounded-full',
                        getStatusBadgeColor(selectedReport.status)
                      ]"
                    >
                      {{ getStatusLabel(selectedReport.status) }}
                    </span>
                  </div>

                  <!-- Results -->
                  <div v-if="selectedReport.status === 'IMPORTED'">
                    <h4 class="text-sm font-medium text-gray-700 mb-2">Resultados</h4>
                    <div class="grid grid-cols-2 gap-4">
                      <div class="bg-green-50 rounded-lg p-3">
                        <p class="text-xs text-gray-500">Sucesso</p>
                        <p class="text-lg font-semibold text-green-600">
                          {{ selectedReport.success_count }}
                        </p>
                      </div>
                      <div class="bg-red-50 rounded-lg p-3">
                        <p class="text-xs text-gray-500">Erros</p>
                        <p class="text-lg font-semibold text-red-600">
                          {{ selectedReport.error_count }}
                        </p>
                      </div>
                    </div>
                  </div>

                  <!-- Failed Reason -->
                  <div v-if="selectedReport.failed_reason">
                    <h4 class="text-sm font-medium text-gray-700 mb-2">Motivo da Falha</h4>
                    <div class="bg-red-50 border border-red-200 rounded-lg p-3">
                      <p class="text-sm text-red-800">{{ selectedReport.failed_reason }}</p>
                    </div>
                  </div>

                  <!-- Errors List -->
                  <div v-if="selectedReport.errors && selectedReport.errors.length > 0">
                    <h4 class="text-sm font-medium text-gray-700 mb-2">
                      Erros ({{ selectedReport.errors.length }})
                    </h4>
                    <div class="bg-gray-50 rounded-lg border border-gray-200 p-3 max-h-64 overflow-y-auto">
                      <ul class="space-y-2">
                        <li
                          v-for="(error, index) in selectedReport.errors"
                          :key="index"
                          class="flex items-start text-sm text-gray-700"
                        >
                          <ExclamationCircleIcon class="h-4 w-4 text-red-400 mr-2 mt-0.5 flex-shrink-0" />
                          <span>{{ error }}</span>
                        </li>
                      </ul>
                    </div>
                  </div>

                  <!-- Handler Type -->
                  <div v-if="selectedReport.handler_type">
                    <h4 class="text-sm font-medium text-gray-700 mb-2">Handler</h4>
                    <p class="text-sm text-gray-600">{{ selectedReport.handler_type }}</p>
                  </div>

                  <!-- Timestamps -->
                  <div>
                    <h4 class="text-sm font-medium text-gray-700 mb-2">Datas</h4>
                    <div class="space-y-1 text-sm text-gray-600">
                      <p><span class="font-medium">Criado em:</span> {{ formatDateTime(selectedReport.created_at) }}</p>
                      <p><span class="font-medium">Atualizado em:</span> {{ formatDateTime(selectedReport.updated_at) }}</p>
                      <p v-if="selectedReport.processed_at">
                        <span class="font-medium">Processado em:</span> {{ formatDateTime(selectedReport.processed_at) }}
                      </p>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- Modal Actions -->
          <div class="bg-gray-50 px-4 py-3 sm:px-6 sm:flex sm:flex-row-reverse">
            <button
              type="button"
              @click="selectedReport = null"
              class="w-full inline-flex justify-center rounded-md border border-gray-300 shadow-sm px-4 py-2 bg-white text-base font-medium text-gray-700 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 sm:ml-3 sm:w-auto sm:text-sm"
            >
              Fechar
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import {
  ArrowUpTrayIcon,
  DocumentIcon,
  DocumentArrowUpIcon,
  ExclamationTriangleIcon,
  ExclamationCircleIcon,
  XMarkIcon
} from '@heroicons/vue/24/outline'
import type { ImportReport } from '~/types/importReports'

// Page metadata
definePageMeta({
  middleware: 'auth'
})

// Composables
const {
  importReports,
  loading,
  error,
  loadImportReports,
  formatDateTime,
  getStatusBadgeColor,
  getStatusLabel,
  initialize
} = useImportReports()

// Local state
const showImportModal = ref(false)
const selectedReport = ref<ImportReport | null>(null)

// Methods
const handleImportComplete = async () => {
  showImportModal.value = false
  // Refresh import reports list
  await loadImportReports()
}

// Initialize data
onMounted(async () => {
  await initialize()
})
</script>

