<template>
  <div class="py-8">
    <!-- Page Header -->
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 mb-6">
      <div class="flex justify-between items-center">
        <div>
          <h1 class="text-3xl font-bold text-gray-900">
            {{ selectedViewId && currentReport ? currentReport.view_name : 'Fluxo de Caixa' }}
          </h1>
          <p v-if="!selectedViewId" class="mt-1 text-sm text-gray-500">
            Visualize seus relatórios financeiros personalizados
          </p>
          <p v-else-if="currentReport" class="mt-1 text-sm text-gray-500">
            Relatório anual para {{ selectedYear }}
          </p>
        </div>
        <div v-if="!selectedViewId" class="flex space-x-3">
          <NuxtLink to="/cash-flow/create">
            <button
              class="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-indigo-600 hover:bg-indigo-700 transition-colors"
            >
              <PlusIcon class="h-4 w-4 mr-2" />
              Nova Visualização
            </button>
          </NuxtLink>
        </div>
      </div>
    </div>

    <!-- Loading State -->
    <div v-if="loading" class="flex justify-center items-center py-12">
      <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600"></div>
      <span class="ml-2">Carregando visualizações...</span>
    </div>

    <!-- Error State -->
    <div v-else-if="error" class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
      <div class="bg-red-50 border border-red-200 rounded-md p-4">
        <div class="flex">
          <ExclamationTriangleIcon class="h-5 w-5 text-red-400" />
          <div class="ml-3">
            <h3 class="text-sm font-medium text-red-800">
              Erro ao carregar dados
            </h3>
            <div class="mt-2 text-sm text-red-700">
              {{ error }}
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Views List or Dashboard -->
    <div v-else class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
      <!-- Show views list if no view is selected -->
      <div v-if="!selectedViewId" class="space-y-4">
        <div v-if="views.length === 0" class="text-center py-12">
          <ChartBarIcon class="mx-auto h-12 w-12 text-gray-400" />
          <h3 class="mt-2 text-sm font-medium text-gray-900">
            Nenhuma visualização encontrada
          </h3>
          <p class="mt-1 text-sm text-gray-500">
            Crie sua primeira visualização de fluxo de caixa para começar.
          </p>
          <div class="mt-6">
            <NuxtLink to="/cash-flow/create">
              <button
                class="inline-flex items-center px-4 py-2 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-indigo-600 hover:bg-indigo-700 transition-colors"
              >
                <PlusIcon class="h-4 w-4 mr-2" />
                Criar Visualização
              </button>
            </NuxtLink>
          </div>
        </div>

        <!-- Views Grid -->
        <div v-else class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          <div
            v-for="view in views"
            :key="view.id"
            class="bg-white overflow-hidden shadow rounded-lg hover:shadow-lg transition-shadow border-2 border-transparent hover:border-indigo-500"
          >
            <!-- Card Header - Clickable to select view -->
            <div 
              @click="selectView(view.id)"
              class="p-6 cursor-pointer"
            >
              <div class="flex items-center justify-between">
                <div class="flex-1">
                  <h3 class="text-lg font-medium text-gray-900 mb-2">
                    {{ view.name }}
                  </h3>
                  <div class="flex items-center space-x-4 text-sm text-gray-500">
                    <div class="flex items-center">
                      <FolderIcon class="h-4 w-4 mr-1" />
                      {{ view.groups.length }} grupo{{ view.groups.length !== 1 ? 's' : '' }}
                    </div>
                    <div class="flex items-center">
                      <CalculatorIcon class="h-4 w-4 mr-1" />
                      {{ view.results.length }} resultado{{ view.results.length !== 1 ? 's' : '' }}
                    </div>
                  </div>
                </div>
                <ChevronRightIcon class="h-5 w-5 text-gray-400" />
              </div>
              <div class="mt-4 text-xs text-gray-400">
                Criado em {{ formatDate(view.created_at) }}
              </div>
            </div>
            
            <!-- Card Actions - Edit button -->
            <div class="px-6 py-3 bg-gray-50 border-t border-gray-200 flex justify-end space-x-2">
              <NuxtLink
                :to="`/cash-flow/edit/${view.id}`"
                class="inline-flex items-center px-3 py-1.5 border border-gray-300 shadow-sm text-xs font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50"
              >
                <PencilIcon class="h-3.5 w-3.5 mr-1.5" />
                Editar
              </NuxtLink>
            </div>
          </div>
        </div>
      </div>

      <!-- Show dashboard for selected view -->
      <div v-else class="space-y-6">
        <!-- Back Button and View Info -->
        <div class="flex items-center justify-between">
          <button
            @click="selectedViewId = null; currentReport = null"
            class="inline-flex items-center text-sm font-medium text-gray-700 hover:text-gray-900"
          >
            <ArrowLeftIcon class="h-4 w-4 mr-2" />
            Voltar para lista
          </button>
          <div class="flex items-center space-x-4">
            <div class="text-sm text-gray-500">
              Visualização: <span class="font-medium text-gray-900">{{ selectedViewName }}</span>
            </div>
            <div class="flex items-center space-x-2">
              <label class="text-sm font-medium text-gray-700">Ano:</label>
              <select
                v-model="selectedYear"
                @change="loadReport"
                class="border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
              >
                <option v-for="year in availableYears" :key="year" :value="year">
                  {{ year }}
                </option>
              </select>
            </div>
          </div>
        </div>

        <!-- Report Loading State -->
        <div v-if="reportLoading" class="flex justify-center items-center py-12">
          <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600"></div>
          <span class="ml-2">Carregando relatório...</span>
        </div>

        <!-- Report Error State -->
        <div v-else-if="reportError" class="bg-red-50 border border-red-200 rounded-md p-4">
          <div class="flex">
            <ExclamationTriangleIcon class="h-5 w-5 text-red-400" />
            <div class="ml-3">
              <h3 class="text-sm font-medium text-red-800">
                Erro ao carregar relatório
              </h3>
              <div class="mt-2 text-sm text-red-700">
                {{ reportError }}
              </div>
            </div>
          </div>
        </div>

        <!-- Report Dashboard -->
        <div v-else-if="currentReport" class="space-y-6">
          <!-- Report Table -->
          <div class="bg-white shadow rounded-lg overflow-hidden">
            <div class="overflow-x-auto">
              <table class="min-w-full divide-y divide-gray-200">
                <thead class="bg-gray-50">
                  <tr>
                    <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Item
                    </th>
                    <th
                      v-for="month in 12"
                      :key="month"
                      class="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider"
                    >
                      {{ formatMonthName(String(month)) }}
                    </th>
                    <th class="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Total Anual
                    </th>
                  </tr>
                </thead>
                <tbody class="bg-white divide-y divide-gray-200">
                  <tr
                    v-for="row in tableRows"
                    :key="row.id"
                    :class="[
                      row.type === 'result' ? 'bg-gray-50 font-semibold' : '',
                      row.type === 'group' && row.position % 2 === 0 ? 'bg-gray-25' : '',
                      row.type === 'group' && row.isExpandable ? 'hover:bg-gray-50 cursor-pointer' : '',
                      row.type === 'category' ? 'hover:bg-gray-50' : '',
                      row.type === 'subcategory' ? 'bg-gray-25' : ''
                    ]"
                  >
                    <td 
                      class="px-6 py-4 whitespace-nowrap"
                      :class="[
                        row.type === 'category' ? 'pl-8' : '',
                        row.type === 'subcategory' ? 'pl-16' : ''
                      ]"
                    >
                      <div class="flex items-center">
                        <!-- Group expand/collapse button -->
                        <button
                          v-if="row.type === 'group' && row.isExpandable"
                          @click.stop="toggleGroup(row.position)"
                          class="mr-2 flex-shrink-0 text-gray-400 hover:text-gray-600 focus:outline-none transition-colors"
                          type="button"
                        >
                          <ChevronDownIcon
                            v-if="row.isExpanded"
                            class="h-4 w-4"
                          />
                          <ChevronRightIcon
                            v-else
                            class="h-4 w-4"
                          />
                        </button>
                        <div 
                          v-else-if="row.type === 'group' && !row.isExpandable"
                          class="mr-6 w-4"
                        ></div>
                        <!-- Category expand/collapse button -->
                        <button
                          v-if="row.type === 'category' && row.isExpandable"
                          @click.stop="toggleCategory(row.categoryId!)"
                          class="mr-2 flex-shrink-0 text-gray-400 hover:text-gray-600 focus:outline-none transition-colors"
                          type="button"
                        >
                          <ChevronDownIcon
                            v-if="row.isExpanded"
                            class="h-4 w-4"
                          />
                          <ChevronRightIcon
                            v-else
                            class="h-4 w-4"
                          />
                        </button>
                        <div 
                          v-else-if="row.type === 'category' && !row.isExpandable"
                          class="mr-6 w-4"
                        ></div>
                        <div 
                          :class="[
                            'text-sm',
                            row.type === 'group' || row.type === 'result' ? 'font-medium text-gray-900' : '',
                            row.type === 'category' ? 'font-medium text-gray-900' : '',
                            row.type === 'subcategory' ? 'text-gray-700' : ''
                          ]"
                        >
                          {{ row.name }}
                        </div>
                      </div>
                    </td>
                    <td
                      v-for="month in 12"
                      :key="month"
                      class="px-4 py-4 whitespace-nowrap text-right text-sm"
                      :class="[
                        row.type === 'result' ? 'font-semibold' : '',
                        isZeroValue(row.monthly_totals[String(month)] || '0') ? 'text-gray-400' : 
                        row.type === 'group' 
                          ? (parseFloat(row.monthly_totals[String(month)] || '0') >= 0 ? 'text-green-500' : 'text-red-400')
                          : row.type === 'result'
                          ? (parseFloat(row.monthly_totals[String(month)] || '0') >= 0 ? 'text-green-600' : 'text-red-600')
                          : (parseFloat(row.monthly_totals[String(month)] || '0') >= 0 ? 'text-gray-900' : 'text-red-600')
                      ]"
                    >
                      {{ formatValue(row.monthly_totals[String(month)] || '0') }}
                    </td>
                    <td
                      class="px-6 py-4 whitespace-nowrap text-right text-sm font-medium"
                      :class="[
                        isZeroValue(row.annual_total || '0') ? 'text-gray-400' : 
                        row.type === 'group' 
                          ? (parseFloat(row.annual_total || '0') >= 0 ? 'text-green-500' : 'text-red-400')
                          : row.type === 'result'
                          ? (parseFloat(row.annual_total || '0') >= 0 ? 'text-green-600' : 'text-red-600')
                          : (parseFloat(row.annual_total || '0') >= 0 ? 'text-gray-900' : 'text-red-600')
                      ]"
                    >
                      {{ formatValue(row.annual_total || '0.00') }}
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>

          <!-- Uncategorized Section -->
          <div v-if="uncategorizedRow" class="mt-6 bg-white shadow rounded-lg overflow-hidden">
            <div class="overflow-x-auto">
              <table class="min-w-full divide-y divide-gray-200">
                <thead class="bg-gray-100">
                  <tr>
                    <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Item
                    </th>
                    <th
                      v-for="month in 12"
                      :key="month"
                      class="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider"
                    >
                      {{ formatMonthName(String(month)) }}
                    </th>
                    <th class="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Total Anual
                    </th>
                  </tr>
                </thead>
                <tbody class="bg-white divide-y divide-gray-200">
                  <tr class="bg-gray-100">
                    <td class="px-6 py-4 whitespace-nowrap">
                      <div class="text-sm font-medium text-gray-700">
                        {{ uncategorizedRow.name }}
                      </div>
                    </td>
                    <td
                      v-for="month in 12"
                      :key="month"
                      class="px-4 py-4 whitespace-nowrap text-right text-sm"
                      :class="[
                        isZeroValue(uncategorizedRow.monthly_totals[String(month)] || '0') ? 'text-gray-400' : 
                        parseFloat(uncategorizedRow.monthly_totals[String(month)] || '0') >= 0 ? 'text-gray-900' : 'text-red-600'
                      ]"
                    >
                      {{ formatValue(uncategorizedRow.monthly_totals[String(month)] || '0') }}
                    </td>
                    <td
                      class="px-6 py-4 whitespace-nowrap text-right text-sm font-medium"
                      :class="[
                        isZeroValue(uncategorizedRow.annual_total || '0') ? 'text-gray-400' : 
                        parseFloat(uncategorizedRow.annual_total || '0') >= 0 ? 'text-gray-900' : 'text-red-600'
                      ]"
                    >
                      {{ formatValue(uncategorizedRow.annual_total || '0.00') }}
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import {
  ArrowLeftIcon,
  ArrowPathIcon,
  ExclamationTriangleIcon,
  ChevronRightIcon,
  ChevronDownIcon,
  ChevronUpIcon,
  PlusIcon,
  ChartBarIcon,
  FolderIcon,
  CalculatorIcon,
  PencilIcon
} from '@heroicons/vue/24/outline'
import type { CashFlowReportItem, CashFlowReportGroupItem } from '~/types/cashFlowViews'

// Page metadata
definePageMeta({
  middleware: 'auth'
})

// Composables
const {
  views,
  loading,
  error,
  currentReport,
  reportLoading,
  reportError,
  loadCashFlowViews,
  getCashFlowReport,
  formatCurrency,
  formatMonthName
} = useCashFlowViews()

// Local state
const selectedViewId = ref<number | null>(null)
const selectedViewName = ref<string>('')
const selectedYear = ref(new Date().getFullYear())
const expandedGroups = ref<Set<number>>(new Set())
const expandedCategories = ref<Set<number>>(new Set())

// Computed
const availableYears = computed(() => {
  const currentYear = new Date().getFullYear()
  const years = []
  for (let i = currentYear; i >= currentYear - 5; i--) {
    years.push(i)
  }
  return years
})

// Flattened table rows including categories and subcategories
interface TableRow {
  type: 'group' | 'category' | 'subcategory' | 'result' | 'uncategorized'
  id: string
  name: string
  monthly_totals: { [key: string]: string }
  annual_total: string
  position: number
  groupPosition?: number
  categoryId?: number
  isExpandable?: boolean
  isExpanded?: boolean
}

const tableRows = computed<TableRow[]>(() => {
  if (!currentReport.value) return []
  
  const rows: TableRow[] = []
  const items = [...currentReport.value.items]
  
  // Filter out uncategorized items - they'll be shown separately
  const regularItems = items.filter(item => item.type !== 'uncategorized')
  
  // Sort regular items by position
  const sortedItems = regularItems.sort((a, b) => a.position - b.position)
  
  for (const item of sortedItems) {
    if (item.type === 'group') {
      const groupItem = item as CashFlowReportGroupItem
      const isGroupExpanded = expandedGroups.value.has(item.position)
      const hasCategories = groupItem.categories && groupItem.categories.length > 0
      
      // Add group row
      rows.push({
        type: 'group',
        id: `group-${item.position}`,
        name: item.name,
        monthly_totals: { ...item.monthly_totals },
        annual_total: item.annual_total,
        position: item.position,
        isExpandable: hasCategories,
        isExpanded: isGroupExpanded
      })
      
      // Add category rows for this group only if group is expanded
      if (isGroupExpanded && hasCategories) {
        for (const category of groupItem.categories) {
          const hasSubcategories = category.subcategories && category.subcategories.length > 0
          const isCategoryExpanded = expandedCategories.value.has(category.id)
          
          rows.push({
            type: 'category',
            id: `category-${category.id}`,
            name: category.name,
            monthly_totals: { ...category.monthly_totals },
            annual_total: category.annual_total,
            position: item.position,
            groupPosition: item.position,
            categoryId: category.id,
            isExpandable: hasSubcategories,
            isExpanded: isCategoryExpanded
          })
          
          // Add subcategory rows if category is expanded
          if (isCategoryExpanded && hasSubcategories) {
            for (const subcategory of category.subcategories) {
              rows.push({
                type: 'subcategory',
                id: `subcategory-${category.id}-${subcategory.id}`,
                name: subcategory.name,
                monthly_totals: { ...subcategory.monthly_totals },
                annual_total: subcategory.annual_total,
                position: item.position,
                groupPosition: item.position,
                categoryId: category.id
              })
            }
          }
        }
      }
    } else if (item.type === 'result') {
      // Add result row
      rows.push({
        type: 'result',
        id: `result-${item.position}`,
        name: item.name,
        monthly_totals: { ...item.monthly_totals },
        annual_total: item.annual_total,
        position: item.position
      })
    }
  }
  
  return rows
})

// Separate computed property for uncategorized row
const uncategorizedRow = computed<TableRow | null>(() => {
  if (!currentReport.value) return null
  
  const uncategorizedItem = currentReport.value.items.find(item => item.type === 'uncategorized')
  
  if (!uncategorizedItem) return null
  
  return {
    type: 'uncategorized',
    id: 'uncategorized',
    name: uncategorizedItem.name,
    monthly_totals: { ...uncategorizedItem.monthly_totals },
    annual_total: uncategorizedItem.annual_total,
    position: 9999
  }
})

// Methods
const formatDate = (dateString: string): string => {
  return new Date(dateString).toLocaleDateString('pt-BR')
}

const isZeroValue = (value: string): boolean => {
  const numValue = parseFloat(value)
  return isNaN(numValue) || numValue === 0
}

const formatValue = (value: string): string => {
  if (isZeroValue(value)) {
    return '-'
  }
  return formatCurrency(value)
}

const selectView = async (viewId: number) => {
  selectedViewId.value = viewId
  const view = views.value.find(v => v.id === viewId)
  if (view) {
    selectedViewName.value = view.name
    await loadReport()
  }
}

const loadReport = async () => {
  if (selectedViewId.value) {
    // Clear expanded groups and categories when loading a new report
    expandedGroups.value.clear()
    expandedCategories.value.clear()
    await getCashFlowReport(selectedViewId.value, selectedYear.value)
  }
}

const toggleGroup = (groupPosition: number) => {
  if (expandedGroups.value.has(groupPosition)) {
    expandedGroups.value.delete(groupPosition)
  } else {
    expandedGroups.value.add(groupPosition)
  }
}

const toggleCategory = (categoryId: number) => {
  if (expandedCategories.value.has(categoryId)) {
    expandedCategories.value.delete(categoryId)
  } else {
    expandedCategories.value.add(categoryId)
  }
}

// Initialize data
onMounted(async () => {
  await loadCashFlowViews()
})
</script>
