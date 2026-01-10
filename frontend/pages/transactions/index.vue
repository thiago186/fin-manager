<template>
  <div class="py-8">
    <!-- Page Header -->
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 mb-6">
      <div class="flex justify-between items-center">
        <div>
          <h1 class="text-3xl font-bold text-gray-900">Transações</h1>
          <p class="mt-1 text-sm text-gray-500">
            Gerencie todas as suas transações financeiras
          </p>
        </div>
        <div class="flex space-x-3">
          <Button as-child variant="outline">
            <NuxtLink to="/imports" class="inline-flex items-center">
              <ClockIcon class="h-4 w-4 mr-2" />
              Histórico de Importações
            </NuxtLink>
          </Button>
          <Button variant="outline" @click="showImportModal = true">
            <ArrowUpTrayIcon class="h-4 w-4 mr-2" />
            Importar CSV/JSON
          </Button>
          <Button 
            variant="outline" 
            @click="handleClassifyTransactions"
            :disabled="classifying"
          >
            <SparklesIcon v-if="!classifying" class="h-4 w-4 mr-2" />
            <svg v-else class="animate-spin h-4 w-4 mr-2" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
              <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
              <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
            </svg>
            {{ classifying ? 'Categorizando...' : 'Categorizar' }}
          </Button>
          <Button as-child variant="outline">
            <NuxtLink to="/transactions/review" class="inline-flex items-center">
              <ClipboardDocumentCheckIcon class="h-4 w-4 mr-2" />
              Revisar Transações
            </NuxtLink>
          </Button>
          <ButtonGroup>
            <Button @click="openCreateTransactionModal('INCOME')">
              Receita
            </Button>
            <ButtonGroupSeparator />
            <Button @click="openCreateTransactionModal('EXPENSE')">
              Despesa
            </Button>
          </ButtonGroup>
        </div>
      </div>
    </div>

    <!-- Statistics Cards -->
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
      <div class="grid grid-cols-1 md:grid-cols-4 gap-6 mb-6">
        <Card>
          <CardHeader class="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle class="text-sm font-medium">Total de Transações</CardTitle>
            <DocumentTextIcon class="h-5 w-5 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div class="text-lg font-semibold text-gray-900">{{ transactionStats.total_transactions }}</div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader class="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle class="text-sm font-medium">Total Receitas</CardTitle>
            <ArrowUpIcon class="h-5 w-5 text-green-500" />
          </CardHeader>
          <CardContent>
            <div class="text-lg font-semibold text-green-600">{{ formatCurrency(transactionStats.total_income) }}</div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader class="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle class="text-sm font-medium">Total Despesas</CardTitle>
            <ArrowDownIcon class="h-5 w-5 text-red-500" />
          </CardHeader>
          <CardContent>
            <div class="text-lg font-semibold text-red-600">{{ formatCurrency(transactionStats.total_expenses) }}</div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader class="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle class="text-sm font-medium">Total Transferências</CardTitle>
            <ArrowsRightLeftIcon class="h-5 w-5 text-blue-500" />
          </CardHeader>
          <CardContent>
            <div class="text-lg font-semibold text-blue-600">{{ formatCurrency(transactionStats.total_transfers) }}</div>
          </CardContent>
        </Card>
      </div>

      <!-- Filters -->
      <Card class="mb-6">
        <CardHeader>
          <CardTitle class="text-lg">Filtros</CardTitle>
          <CardDescription>Refine os resultados de transações.</CardDescription>
        </CardHeader>
        <CardContent class="space-y-4">
          <div class="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-8 gap-4">
            <div class="space-y-2">
              <Label>Buscar</Label>
              <Input
                v-model="localFilters.search"
                type="text"
                placeholder="Descrição, categoria..."
              />
            </div>

            <div class="space-y-2">
              <Label>Tipo</Label>
              <Select v-model="localFilters.transaction_type">
                <SelectTrigger>
                  <SelectValue placeholder="Todos" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem :value="null">Todos</SelectItem>
                  <SelectItem value="INCOME">Receita</SelectItem>
                  <SelectItem value="EXPENSE">Despesa</SelectItem>
                  <SelectItem value="TRANSFER">Transferência</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div class="space-y-2">
              <Label>Cartão de Crédito</Label>
              <Select v-model="localFilters.credit_card_id">
                <SelectTrigger>
                  <SelectValue placeholder="Todos" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem :value="null">Todos</SelectItem>
                  <SelectItem
                    v-for="creditCard in creditCards"
                    :key="creditCard.id"
                    :value="creditCard.id"
                  >
                    {{ creditCard.name }}
                  </SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div class="space-y-2">
              <Label>Subcategoria</Label>
              <Select v-model="localFilters.subcategory_id">
                <SelectTrigger>
                  <SelectValue placeholder="Todas" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem :value="null">Todas</SelectItem>
                  <SelectItem
                    v-for="subcategory in subcategories"
                    :key="subcategory.id"
                    :value="subcategory.id"
                  >
                    {{ subcategory.name }}
                  </SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div class="space-y-2">
              <Label>Data Início</Label>
              <Input v-model="localFilters.date_from" type="date" />
            </div>

            <div class="space-y-2">
              <Label>Data Fim</Label>
              <Input v-model="localFilters.date_to" type="date" />
            </div>

            <div class="space-y-2">
              <Label>Valor Mín</Label>
              <Input
                v-model="localFilters.amount_min"
                type="number"
                step="0.01"
                placeholder="0.00"
              />
            </div>

            <div class="space-y-2">
              <Label>Valor Máx</Label>
              <Input
                v-model="localFilters.amount_max"
                type="number"
                step="0.01"
                placeholder="0.00"
              />
            </div>
          </div>

          <div class="flex justify-between">
            <Button variant="outline" @click="clearFilters">
              <XMarkIcon class="h-4 w-4 mr-2" />
              Limpar Filtros
            </Button>
            <Button @click="applyFilters">
              <FunnelIcon class="h-4 w-4 mr-2" />
              Aplicar Filtros
            </Button>
          </div>
        </CardContent>
      </Card>

      <!-- Transactions Table -->
      <Card>
        <CardHeader>
          <div class="flex items-center justify-between">
            <div>
              <CardTitle class="text-lg">Lista de Transações</CardTitle>
              <CardDescription>{{ filteredTransactions.length }} transações encontradas</CardDescription>
            </div>
            <Button
              v-if="hasPendingChanges"
              @click="handleSaveChanges"
              :disabled="savingChanges"
            >
              <CheckIcon v-if="!savingChanges" class="h-4 w-4 mr-2" />
              <svg v-else class="animate-spin h-4 w-4 mr-2" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
              </svg>
              {{ savingChanges ? 'Salvando...' : 'Salvar Alterações' }}
            </Button>
          </div>
        </CardHeader>

        <!-- Loading State -->
        <CardContent v-if="loading">
          <div class="space-y-2">
            <Skeleton class="h-8 w-full" />
            <Skeleton class="h-8 w-full" />
            <Skeleton class="h-8 w-full" />
          </div>
        </CardContent>

        <!-- Error State -->
        <CardContent v-else-if="error">
          <Alert variant="destructive">
            <AlertTitle>Erro ao carregar transações</AlertTitle>
            <AlertDescription>{{ error }}</AlertDescription>
          </Alert>
        </CardContent>

        <!-- Table -->
        <CardContent v-else class="p-0">
          <div class="overflow-x-auto">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead
                    v-for="column in tableColumns"
                    :key="column.key"
                    :class="[
                      column.align === 'right' ? 'text-right' : '',
                      column.align === 'center' ? 'text-center' : ''
                    ]"
                    @click="column.sortable ? handleSort(column.key) : null"
                  >
                    <div class="flex items-center space-x-1 cursor-pointer" v-if="column.sortable">
                      <span>{{ column.label }}</span>
                      <div class="flex flex-col">
                        <ChevronUpIcon
                          :class="[
                            'h-3 w-3',
                            sort.key === column.key && sort.direction === 'asc'
                              ? 'text-indigo-600'
                              : 'text-gray-400'
                          ]"
                        />
                        <ChevronDownIcon
                          :class="[
                            'h-3 w-3 -mt-1',
                            sort.key === column.key && sort.direction === 'desc'
                              ? 'text-indigo-600'
                              : 'text-gray-400'
                          ]"
                        />
                      </div>
                    </div>
                    <span v-else>{{ column.label }}</span>
                  </TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                <template v-if="filteredTransactions.length > 0">
                  <TableRow
                    v-for="transaction in filteredTransactions"
                    :key="transaction.id"
                    class="hover:bg-muted/40"
                  >
                    <TableCell class="whitespace-nowrap text-sm text-gray-900">
                      {{ formatDate(transaction.occurred_at) }}
                    </TableCell>
                    <TableCell class="whitespace-nowrap">
                      <Badge :variant="transaction.transaction_type === 'INCOME' ? 'secondary' : transaction.transaction_type === 'EXPENSE' ? 'destructive' : 'outline'">
                        {{ getTransactionTypeLabel(transaction.transaction_type) }}
                      </Badge>
                    </TableCell>
                    <TableCell class="text-sm text-gray-900">
                      <div class="max-w-xs truncate">
                        {{ transaction.description || 'Sem descrição' }}
                      </div>
                    </TableCell>
                    <TableCell class="whitespace-nowrap text-sm text-gray-900">
                      {{ getDisplayCategoryName(transaction) }}
                    </TableCell>
                    <TableCell class="whitespace-nowrap text-sm text-gray-900">
                      <Select 
                        :model-value="getCurrentSubcategoryValue(transaction)"
                        @update:model-value="(value) => handleSubcategoryChange(transaction, value as string)"
                        @open-change="(open: boolean) => { 
                          if (open) {
                            editingSubcategoryCellId = transaction.id
                          } else {
                            editingSubcategoryCellId = null
                          }
                        }"
                      >
                        <SelectTrigger 
                          class="w-full border-none shadow-none hover:bg-muted/50 p-1 h-auto data-[state=open]:bg-muted/50 focus-visible:ring-0 focus-visible:ring-offset-0 justify-start"
                        >
                          <SelectValue class="text-sm text-gray-900">
                            {{ getDisplaySubcategoryName(transaction) }}
                          </SelectValue>
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="none">Nenhum</SelectItem>
                          <template v-for="group in getSubcategoriesGroupedByCategory(transaction)" :key="group.categoryId">
                            <SelectGroup>
                              <SelectLabel>{{ group.categoryName }}</SelectLabel>
                              <SelectItem
                                v-for="subcategory in group.subcategories"
                                :key="subcategory.id"
                                :value="`subcategory_${subcategory.id}`"
                              >
                                {{ subcategory.name }}
                              </SelectItem>
                            </SelectGroup>
                          </template>
                        </SelectContent>
                      </Select>
                    </TableCell>
                    <TableCell class="whitespace-nowrap text-sm text-gray-900">
                      <Select 
                        :model-value="getCurrentAccountCardValue(transaction)"
                        @update:model-value="(value) => handleAccountCardChange(transaction, value as string)"
                        @open-change="(open: boolean) => { 
                          if (open) {
                            editingCellId = transaction.id
                          } else {
                            editingCellId = null
                          }
                        }"
                      >
                        <SelectTrigger 
                          class="w-full border-none shadow-none hover:bg-muted/50 p-1 h-auto data-[state=open]:bg-muted/50 focus-visible:ring-0 focus-visible:ring-offset-0 justify-start"
                        >
                          <div class="flex items-center w-full cursor-pointer">
                            <div class="flex-shrink-0 mr-2">
                              <BanknotesIcon 
                                v-if="getDisplayAccountCardIcon(transaction) === 'account'" 
                                class="h-4 w-4 text-indigo-600" 
                              />
                              <CreditCardIcon 
                                v-else-if="getDisplayAccountCardIcon(transaction) === 'credit_card'" 
                                class="h-4 w-4 text-blue-600" 
                              />
                            </div>
                            <SelectValue class="flex-1 text-left text-sm text-gray-900">
                              {{ getDisplayAccountCardName(transaction) }}
                            </SelectValue>
                          </div>
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="none">Nenhum</SelectItem>
                          <SelectGroup v-if="accounts.length > 0">
                            <SelectLabel>Contas</SelectLabel>
                            <SelectItem
                              v-for="account in accounts"
                              :key="`account_${account.id}`"
                              :value="`account_${account.id}`"
                            >
                              <div class="flex items-center">
                                <BanknotesIcon class="h-4 w-4 mr-2 text-indigo-600" />
                                {{ account.name }}
                              </div>
                            </SelectItem>
                          </SelectGroup>
                          <SelectGroup v-if="creditCards.length > 0">
                            <SelectLabel>Cartões de Crédito</SelectLabel>
                            <SelectItem
                              v-for="creditCard in creditCards"
                              :key="`credit_card_${creditCard.id}`"
                              :value="`credit_card_${creditCard.id}`"
                            >
                              <div class="flex items-center">
                                <CreditCardIcon class="h-4 w-4 mr-2 text-blue-600" />
                                {{ creditCard.name }}
                              </div>
                            </SelectItem>
                          </SelectGroup>
                        </SelectContent>
                      </Select>
                    </TableCell>
                    <TableCell class="whitespace-nowrap text-sm font-medium text-right">
                      <span :class="[getTransactionTypeColor(transaction.transaction_type)]">
                        {{ formatCurrency(transaction.amount) }}
                      </span>
                    </TableCell>
                    <TableCell class="whitespace-nowrap text-sm text-gray-900 text-center">
                      <span v-if="transaction.installments_total > 1">
                        {{ transaction.installment_number }}/{{ transaction.installments_total }}
                      </span>
                      <span v-else>-</span>
                    </TableCell>
                    <TableCell class="whitespace-nowrap text-right text-sm font-medium">
                      <div class="flex items-center justify-end space-x-2">
                        <Button variant="ghost" size="icon" @click="editTransaction(transaction)">
                          <PencilIcon class="h-4 w-4" />
                        </Button>
                        <Button variant="ghost" size="icon" @click="deleteTransaction(transaction.id)">
                          <TrashIcon class="h-4 w-4 text-destructive" />
                        </Button>
                      </div>
                    </TableCell>
                  </TableRow>
                </template>
                <TableEmpty
                  v-else-if="!loading"
                  :colspan="tableColumns.length"
                >
                  <div class="text-center py-12">
                    <DocumentTextIcon class="mx-auto h-12 w-12 text-gray-400" />
                    <h3 class="mt-2 text-sm font-medium text-gray-900">
                      Nenhuma transação encontrada
                    </h3>
                    <p class="mt-1 text-sm text-gray-500">
                      Comece criando sua primeira transação.
                    </p>
                    <div class="mt-6">
                      <ButtonGroup>
                        <Button @click="openCreateTransactionModal('INCOME')">
                          Receita
                        </Button>
                        <ButtonGroupSeparator />
                        <Button @click="openCreateTransactionModal('EXPENSE')">
                          Despesa
                        </Button>
                      </ButtonGroup>
                    </div>
                  </div>
                </TableEmpty>
              </TableBody>
            </Table>
          </div>
          
          <!-- Pagination Controls -->
          <div v-if="!loading && transactions.length > 0" class="flex items-center justify-between border-t px-4 py-3">
            <div class="flex items-center text-sm text-gray-700">
              <span>
                Mostrando {{ transactions.length }} de {{ pagination.count }} transações
              </span>
            </div>
            <div class="flex items-center space-x-2">
              <Button
                variant="outline"
                size="sm"
                @click="loadPreviousPage(getApiFilters())"
                :disabled="!pagination.previous"
              >
                Anterior
              </Button>
              <div class="flex items-center space-x-1">
                <span class="text-sm text-gray-700">
                  Página {{ pagination.currentPage }} de {{ totalPages || 1 }}
                </span>
              </div>
              <Button
                variant="outline"
                size="sm"
                @click="loadNextPage(getApiFilters())"
                :disabled="!pagination.next"
              >
                Próxima
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>

    <!-- Create/Edit Modal -->
    <TransactionModal
      v-if="showCreateModal || showEditModal"
      :transaction="editingTransaction"
      :is-edit="showEditModal"
      @close="closeModal"
      @saved="handleTransactionSaved"
    />

    <!-- CSV Import Modal -->
    <CsvImportModal
      v-if="showImportModal"
      @close="showImportModal = false"
      @imported="handleImportComplete"
    />
  </div>
</template>

<script setup lang="ts">
import {
  PlusIcon,
  DocumentTextIcon,
  ArrowUpIcon,
  ArrowDownIcon,
  ArrowsRightLeftIcon,
  FunnelIcon,
  XMarkIcon,
  ExclamationTriangleIcon,
  ChevronUpIcon,
  ChevronDownIcon,
  PencilIcon,
  TrashIcon,
  BanknotesIcon,
  CreditCardIcon,
  ArrowUpTrayIcon,
  ClockIcon,
  CheckIcon,
  SparklesIcon,
  ClipboardDocumentCheckIcon
} from '@heroicons/vue/24/outline'
import { Button } from '@/components/ui/button'
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle
} from '@/components/ui/card'
import {
  Table,
  TableBody,
  TableCell,
  TableEmpty,
  TableHead,
  TableHeader,
  TableRow
} from '@/components/ui/table'
import { Badge } from '@/components/ui/badge'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import {
  Select,
  SelectContent,
  SelectGroup,
  SelectItem,
  SelectLabel,
  SelectTrigger,
  SelectValue
} from '@/components/ui/select'
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert'
import { Skeleton } from '@/components/ui/skeleton'
import { ButtonGroup, ButtonGroupSeparator } from '@/components/ui/button-group'

import type { Transaction, TransactionTableFilters, TransactionTableSort, TransactionFilters } from '~/types/transactions'

// Page metadata
definePageMeta({
  middleware: 'auth'
})

// Composables
const { 
  transactions,
  loading,
  error,
  classifying,
  filters,
  sort,
  pagination,
  filteredTransactions,
  transactionStats,
  loadTransactions,
  loadNextPage,
  loadPreviousPage,
  loadPage,
  deleteTransaction: deleteTransactionApi,
  bulkUpdateTransactions,
  classifyTransactions,
  applyTableFilters,
  applyTableSort,
  formatCurrency,
  formatDate,
  getTransactionTypeColor,
  getTransactionTypeLabel,
  initialize
} = useTransactions()

const { creditCards, initialize: initializeCreditCards } = useCreditCards()
const { accounts, initialize: initializeAccounts } = useAccounts()
const { subcategories, loadSubcategories } = useSubcategories()
const { categories, initialize: initializeCategories } = useCategories()

// Local state
const showCreateModal = ref(false)
const showEditModal = ref(false)
const showImportModal = ref(false)
const editingTransaction = ref<Transaction | null>(null)
const localFilters = ref<TransactionTableFilters>({})
const pendingChanges = ref<Map<number, { account_id?: number | null, credit_card_id?: number | null, category_id?: number | null, subcategory_id?: number | null }>>(new Map())
const editingCellId = ref<number | null>(null)
const editingSubcategoryCellId = ref<number | null>(null)
const savingChanges = ref(false)

// Table columns configuration
const tableColumns = [
  { key: 'occurred_at', label: 'Data', sortable: true, width: '120px' },
  { key: 'transaction_type', label: 'Tipo', sortable: true, width: '100px' },
  { key: 'description', label: 'Descrição', sortable: false, width: '200px' },
  { key: 'category', label: 'Categoria', sortable: false, width: '120px' },
  { key: 'subcategory', label: 'Subcategoria', sortable: false, width: '120px' },
  { key: 'account', label: 'Conta/Cartão', sortable: false, width: '150px' },
  { key: 'amount', label: 'Valor', sortable: true, width: '120px', align: 'right' },
  { key: 'installments', label: 'Parcelas', sortable: false, width: '80px', align: 'center' },
  { key: 'actions', label: 'Ações', sortable: false, width: '100px', align: 'right' }
]

// Computed
const hasPendingChanges = computed(() => pendingChanges.value.size > 0)
const totalPages = computed(() => Math.ceil(pagination.value.count / 100))

// Methods
const openCreateTransactionModal = (transactionType: 'INCOME' | 'EXPENSE') => {
  editingTransaction.value = {
    id: 0,
    user: 0,
    transaction_type: transactionType,
    amount: '0',
    description: '',
    occurred_at: new Date().toISOString().split('T')[0],
    installments_total: 1,
    installment_number: 1,
    installment_group_id: null,
    account: null,
    credit_card: null,
    category: null,
    subcategory: null,
    tags: [],
    created_at: '',
    updated_at: ''
  } as Transaction
  showCreateModal.value = true
}

const handleSort = (key: string) => {
  const newDirection = sort.value.key === key && sort.value.direction === 'asc' ? 'desc' : 'asc'
  applyTableSort({ key: key as keyof Transaction, direction: newDirection })

  // No API call needed - filteredTransactions computed property will handle sorting locally
}

const getApiFilters = (): TransactionFilters => {
  const apiFilters: TransactionFilters = {}
  if (filters.value.transaction_type && filters.value.transaction_type !== '') {
    apiFilters.transaction_type = filters.value.transaction_type as 'INCOME' | 'EXPENSE' | 'TRANSFER'
  }
  if (filters.value.account_id) {
    apiFilters.account_id = filters.value.account_id
  }
  if (filters.value.category_id) {
    apiFilters.category_id = filters.value.category_id
  }
  if (filters.value.subcategory_id) {
    apiFilters.subcategory_id = filters.value.subcategory_id
  }
  if (filters.value.credit_card_id) {
    apiFilters.credit_card_id = filters.value.credit_card_id
  }
  return apiFilters
}

const applyFilters = async () => {
  let creditCardId: number | null = null
  const creditCardIdValue = localFilters.value.credit_card_id
  
  if (creditCardIdValue !== null && creditCardIdValue !== undefined) {
    const numValue = typeof creditCardIdValue === 'string' 
      ? (creditCardIdValue === '' ? null : Number(creditCardIdValue))
      : creditCardIdValue
    
    if (numValue !== null && !isNaN(numValue) && numValue > 0) {
      creditCardId = numValue
    }
  }
  
  const filtersToApply: TransactionTableFilters = {
    ...localFilters.value,
    credit_card_id: creditCardId
  }
  
  console.log('Applying filters:', filtersToApply)
  applyTableFilters(filtersToApply)
  
  // Convert UI filters to API filters and reload with page 1
  await loadPage(1, getApiFilters())
}

const clearFilters = async () => {
  localFilters.value = {}
  applyTableFilters({})
  await loadPage(1)
}

const editTransaction = (transaction: Transaction) => {
  editingTransaction.value = transaction
  showEditModal.value = true
}

const deleteTransaction = async (id: number) => {
  if (confirm('Tem certeza que deseja excluir esta transação?')) {
    const result = await deleteTransactionApi(id)
    if (!result.success) {
      alert('Erro ao excluir transação: ' + result.error?.message)
    }
  }
}

const closeModal = () => {
  showCreateModal.value = false
  showEditModal.value = false
  editingTransaction.value = null
}

const handleTransactionSaved = () => {
  closeModal()
  // Transactions will be automatically refreshed by the composable
}

const handleImportComplete = async () => {
  showImportModal.value = false
  // Refresh transactions after successful import
  await loadTransactions()
}

const handleClassifyTransactions = async () => {
  const result = await classifyTransactions()
  if (result.success) {
    alert('Transações categorizadas com sucesso!')
  } else {
    alert('Erro ao categorizar transações: ' + (result.error?.message || 'Erro desconhecido'))
  }
}

// Account/Credit Card editing methods
const getCurrentAccountCardValue = (transaction: Transaction): string => {
  // Get effective current values (pending change or original)
  const pendingChange = pendingChanges.value.get(transaction.id)
  const accountId = pendingChange?.account_id ?? transaction.account?.id ?? null
  const creditCardId = pendingChange?.credit_card_id ?? transaction.credit_card?.id ?? null
  
  if (accountId !== null) {
    return `account_${accountId}`
  }
  if (creditCardId !== null) {
    return `credit_card_${creditCardId}`
  }
  return 'none'
}

const getDisplayAccountCardName = (transaction: Transaction): string => {
  // Get effective current values (pending change or original)
  const pendingChange = pendingChanges.value.get(transaction.id)
  
  // Check if there's a pending change for account/credit card
  if (pendingChange) {
    if (pendingChange.account_id !== null && pendingChange.account_id !== undefined) {
      const account = accounts.value.find(a => a.id === pendingChange.account_id)
      return account?.name || '-'
    }
    if (pendingChange.credit_card_id !== null && pendingChange.credit_card_id !== undefined) {
      const creditCard = creditCards.value.find(c => c.id === pendingChange.credit_card_id)
      return creditCard?.name || '-'
    }
    // If pending change exists but doesn't have account/credit card changes, fall back to original
  }
  
  // Show original value
  return transaction.account?.name || transaction.credit_card?.name || '-'
}

const getDisplayCategoryName = (transaction: Transaction): string => {
  // Get effective current values (pending change or original)
  const pendingChange = pendingChanges.value.get(transaction.id)
  
  // Check if there's a pending change for category
  if (pendingChange?.category_id !== null && pendingChange?.category_id !== undefined) {
    const category = categories.value.find(c => c.id === pendingChange.category_id)
    return category?.name || '-'
  }
  
  // Show original value
  return transaction.category?.name || '-'
}

const getDisplayAccountCardIcon = (transaction: Transaction) => {
  // Get effective current values (pending change or original)
  const pendingChange = pendingChanges.value.get(transaction.id)
  
  // Check if there's a pending change for account/credit card
  if (pendingChange) {
    if (pendingChange.account_id !== null && pendingChange.account_id !== undefined) {
      return 'account'
    }
    if (pendingChange.credit_card_id !== null && pendingChange.credit_card_id !== undefined) {
      return 'credit_card'
    }
    // If pending change exists but doesn't have account/credit card changes, fall back to original
  }
  
  // Show original value
  if (transaction.account) return 'account'
  if (transaction.credit_card) return 'credit_card'
  return null
}

// Subcategory editing methods
const getCurrentSubcategoryValue = (transaction: Transaction): string => {
  // Get effective current values (pending change or original)
  const pendingChange = pendingChanges.value.get(transaction.id)
  const subcategoryId = pendingChange?.subcategory_id ?? transaction.subcategory?.id ?? null
  
  if (subcategoryId !== null) {
    return `subcategory_${subcategoryId}`
  }
  return 'none'
}

const getDisplaySubcategoryName = (transaction: Transaction): string => {
  // Get effective current values (pending change or original)
  const pendingChange = pendingChanges.value.get(transaction.id)
  
  if (pendingChange?.subcategory_id !== null && pendingChange?.subcategory_id !== undefined) {
    const subcategory = subcategories.value.find(s => s.id === pendingChange.subcategory_id)
    return subcategory?.name || '-'
  }
  
  // Show original value
  return transaction.subcategory?.name || '-'
}

const getAvailableSubcategories = (transaction: Transaction) => {
  if (!subcategories.value || subcategories.value.length === 0) {
    return []
  }
  
  // Map transaction type to subcategory transaction type
  // Transaction: 'INCOME' | 'EXPENSE' | 'TRANSFER'
  // Subcategory: 'income' | 'expense'
  const transactionTypeMap: Record<string, 'income' | 'expense' | null> = {
    'INCOME': 'income',
    'EXPENSE': 'expense',
    'TRANSFER': null // Transfers might not have subcategories
  }
  
  const subcategoryTransactionType = transactionTypeMap[transaction.transaction_type] ?? null
  
  // Filter subcategories by transaction type and active status only
  return subcategories.value.filter(subcategory => {
    const matchesTransactionType = subcategoryTransactionType === null || subcategory.transaction_type === subcategoryTransactionType
    const isActive = subcategory.is_active
    return matchesTransactionType && isActive
  })
}

const getSubcategoriesGroupedByCategory = (transaction: Transaction) => {
  const availableSubcategories = getAvailableSubcategories(transaction)
  
  // Group subcategories by their parent category
  const grouped = new Map<number, { categoryName: string, subcategories: typeof availableSubcategories }>()
  
  availableSubcategories.forEach(subcategory => {
    const categoryId = Number(subcategory.category)
    const category = categories.value.find(c => c.id === categoryId)
    
    if (!grouped.has(categoryId)) {
      grouped.set(categoryId, {
        categoryName: category?.name || 'Sem categoria',
        subcategories: []
      })
    }
    
    grouped.get(categoryId)!.subcategories.push(subcategory)
  })
  
  // Convert map to array sorted by category name
  return Array.from(grouped.entries())
    .map(([categoryId, data]) => ({ categoryId, ...data }))
    .sort((a, b) => a.categoryName.localeCompare(b.categoryName))
}

const handleSubcategoryChange = (transaction: Transaction, value: string) => {
  const transactionId = transaction.id
  
  // Get effective current values (pending change or original)
  const pendingChange = pendingChanges.value.get(transaction.id)
  
  // Get original values from transaction
  const originalSubcategoryId = transaction.subcategory?.id ?? null
  const originalCategoryId = transaction.category?.id ?? null
  
  let newSubcategoryId: number | null = null
  let newCategoryId: number | null = null
  
  if (value === 'none') {
    newSubcategoryId = null
    newCategoryId = null
  } else if (value.startsWith('subcategory_')) {
    newSubcategoryId = Number(value.replace('subcategory_', ''))
    
    // Find the selected subcategory to get its parent category
    const selectedSubcategory = subcategories.value.find(s => s.id === newSubcategoryId)
    if (selectedSubcategory) {
      newCategoryId = Number(selectedSubcategory.category)
    }
  }
  
  // Get existing pending changes or create new
  const existingChanges = pendingChanges.value.get(transactionId) || {}
  
  // Check if values actually changed from original
  const subcategoryChanged = newSubcategoryId !== originalSubcategoryId
  const categoryChanged = newCategoryId !== originalCategoryId
  
  if (subcategoryChanged || categoryChanged) {
    // Update both subcategory_id and category_id
    const updatedChanges: { account_id?: number | null, credit_card_id?: number | null, category_id?: number | null, subcategory_id?: number | null } = {
      ...existingChanges,
      subcategory_id: newSubcategoryId,
      category_id: newCategoryId
    }
    
    pendingChanges.value.set(transactionId, updatedChanges)
  } else {
    // Remove subcategory_id and category_id from pending changes if reverted to original
    const updatedChanges = { ...existingChanges }
    delete updatedChanges.subcategory_id
    delete updatedChanges.category_id
    
    // If there are no other changes, remove the entry entirely
    if (Object.keys(updatedChanges).length === 0) {
      pendingChanges.value.delete(transactionId)
    } else {
      pendingChanges.value.set(transactionId, updatedChanges)
    }
  }
  
  editingSubcategoryCellId.value = null
}

const handleAccountCardChange = (transaction: Transaction, value: string) => {
  const transactionId = transaction.id
  
  // Get effective current values (pending change or original)
  const pendingChange = pendingChanges.value.get(transactionId)
  const currentAccountId = pendingChange?.account_id ?? transaction.account?.id ?? null
  const currentCreditCardId = pendingChange?.credit_card_id ?? transaction.credit_card?.id ?? null
  
  // Get original values from transaction
  const originalAccountId = transaction.account?.id ?? null
  const originalCreditCardId = transaction.credit_card?.id ?? null
  
  let newAccountId: number | null = null
  let newCreditCardId: number | null = null
  
  if (value === 'none') {
    newAccountId = null
    newCreditCardId = null
  } else if (value.startsWith('account_')) {
    newAccountId = Number(value.replace('account_', ''))
    newCreditCardId = null
  } else if (value.startsWith('credit_card_')) {
    newAccountId = null
    newCreditCardId = Number(value.replace('credit_card_', ''))
  }
  
  // Get existing pending changes or create new
  const existingChanges = pendingChanges.value.get(transactionId) || {}
  
  // Only track if value actually changed from original
  if (newAccountId !== originalAccountId || newCreditCardId !== originalCreditCardId) {
    pendingChanges.value.set(transactionId, {
      ...existingChanges,
      account_id: newAccountId,
      credit_card_id: newCreditCardId
    })
  } else {
    // Remove account_id and credit_card_id from pending changes if reverted to original
    const updatedChanges = { ...existingChanges }
    delete updatedChanges.account_id
    delete updatedChanges.credit_card_id
    
    // If there are no other changes, remove the entry entirely
    if (Object.keys(updatedChanges).length === 0) {
      pendingChanges.value.delete(transactionId)
    } else {
      pendingChanges.value.set(transactionId, updatedChanges)
    }
  }
  
  editingCellId.value = null
}

const handleSaveChanges = async () => {
  if (pendingChanges.value.size === 0) return
  
  savingChanges.value = true
  
  try {
    const updates = Array.from(pendingChanges.value.entries()).map(([id, changes]) => ({
      id,
      ...changes
    }))
    
    const result = await bulkUpdateTransactions({ transactions: updates })
    
    if (result.success) {
      pendingChanges.value.clear()
      editingCellId.value = null
      editingSubcategoryCellId.value = null
      // Transactions will be automatically refreshed by the composable
    } else {
      alert('Erro ao salvar alterações: ' + (result.error?.message || 'Erro desconhecido'))
    }
  } catch (err: any) {
    alert('Erro ao salvar alterações: ' + (err?.message || 'Erro desconhecido'))
  } finally {
    savingChanges.value = false
  }
}

// Initialize data
onMounted(async () => {
  await Promise.all([
    initialize(),
    initializeCreditCards(),
    initializeAccounts(),
    initializeCategories(),
    loadSubcategories()
  ])
})
</script> 