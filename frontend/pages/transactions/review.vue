<template>
    <div class="py-8">
      <!-- Page Header -->
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 mb-6">
        <div class="flex justify-between items-center">
          <div>
            <h1 class="text-3xl font-bold text-gray-900">Revisar Transações</h1>
            <p class="mt-1 text-sm text-gray-500">
              Revise e ajuste as transações categorizadas pela IA
            </p>
          </div>
          <div class="flex space-x-3">
            <Button as-child variant="outline">
              <NuxtLink to="/transactions" class="inline-flex items-center">
                <ArrowLeftIcon class="h-4 w-4 mr-2" />
                Voltar para Transações
              </NuxtLink>
            </Button>
          </div>
        </div>
      </div>
  
      <!-- Transactions Table -->
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <Card>
          <CardHeader>
            <div class="flex items-center justify-between">
              <div>
                <CardTitle class="text-lg">Transações para Revisão</CardTitle>
                <CardDescription>{{ transactionsNeedingReview.length }} transações encontradas</CardDescription>
              </div>
              <Button
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
          <CardContent v-if="loadingReview">
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
                  <template v-if="sortedTransactions.length > 0">
                    <TableRow
                      v-for="transaction in sortedTransactions"
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
                    v-else-if="!loadingReview"
                    :colspan="tableColumns.length"
                  >
                    <div class="text-center py-12">
                      <CheckCircleIcon class="mx-auto h-12 w-12 text-gray-400" />
                      <h3 class="mt-2 text-sm font-medium text-gray-900">
                        Nenhuma transação precisa de revisão
                      </h3>
                      <p class="mt-1 text-sm text-gray-500">
                        Todas as transações foram revisadas.
                      </p>
                    </div>
                  </TableEmpty>
              </TableBody>
            </Table>
          </div>
          
          <!-- Pagination Controls -->
          <div v-if="!loadingReview && transactionsNeedingReview.length > 0" class="flex items-center justify-between border-t px-4 py-3">
            <div class="flex items-center text-sm text-gray-700">
              <span>
                Mostrando {{ transactionsNeedingReview.length }} de {{ paginationReview.count }} transações
              </span>
            </div>
            <div class="flex items-center space-x-2">
              <Button
                variant="outline"
                size="sm"
                @click="loadPreviousPageReview()"
                :disabled="!paginationReview.previous"
              >
                Anterior
              </Button>
              <div class="flex items-center space-x-1">
                <span class="text-sm text-gray-700">
                  Página {{ paginationReview.currentPage }} de {{ totalPagesReview || 1 }}
                </span>
              </div>
              <Button
                variant="outline"
                size="sm"
                @click="loadNextPageReview()"
                :disabled="!paginationReview.next"
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
        v-if="showEditModal"
        :transaction="editingTransaction"
        :is-edit="showEditModal"
        @close="closeModal"
        @saved="handleTransactionSaved"
      />
    </div>
  </template>
  
  <script setup lang="ts">
  import {
    DocumentTextIcon,
    ChevronUpIcon,
    ChevronDownIcon,
    PencilIcon,
    TrashIcon,
    BanknotesIcon,
    CreditCardIcon,
    CheckIcon,
    ArrowLeftIcon,
    CheckCircleIcon
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
  
  import type { Transaction, TransactionTableSort } from '~/types/transactions'
  
  // Page metadata
  definePageMeta({
    middleware: 'auth'
  })
  
  // Composables
  const { 
    transactionsNeedingReview,
    loadingReview,
    error,
    sort,
    paginationReview,
    loadTransactionsNeedingReview,
    loadNextPageReview,
    loadPreviousPageReview,
    loadPageReview,
    deleteTransaction: deleteTransactionApi,
    bulkUpdateTransactions,
    applyTableSort,
    formatCurrency,
    formatDate,
    getTransactionTypeColor,
    getTransactionTypeLabel
  } = useTransactions()
  
  const { creditCards, initialize: initializeCreditCards } = useCreditCards()
  const { accounts, initialize: initializeAccounts } = useAccounts()
  const { subcategories, loadSubcategories } = useSubcategories()
  const { categories, initialize: initializeCategories } = useCategories()
  
  // Local state
  const showEditModal = ref(false)
  const editingTransaction = ref<Transaction | null>(null)
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
  const totalPagesReview = computed(() => Math.ceil(paginationReview.value.count / 100))
  
  const sortedTransactions = computed(() => {
    const transactions = [...transactionsNeedingReview.value]
    
    transactions.sort((a, b) => {
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
  
    return transactions
  })
  
  // Methods
  const handleSort = async (key: string) => {
    const newDirection = sort.value.key === key && sort.value.direction === 'asc' ? 'desc' : 'asc'
    applyTableSort({ key: key as keyof Transaction, direction: newDirection })
    // Reload current page
    await loadPageReview(paginationReview.value.currentPage)
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
      } else {
        // Reload current page of transactions needing review after deletion
        await loadPageReview(paginationReview.value.currentPage)
      }
    }
  }
  
  const closeModal = () => {
    showEditModal.value = false
    editingTransaction.value = null
  }
  
  const handleTransactionSaved = async () => {
    closeModal()
    // Reload current page of transactions needing review after update
    await loadPageReview(paginationReview.value.currentPage)
  }
  
  // Account/Credit Card editing methods
  const getCurrentAccountCardValue = (transaction: Transaction): string => {
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
    const pendingChange = pendingChanges.value.get(transaction.id)
    
    if (pendingChange) {
      if (pendingChange.account_id !== null && pendingChange.account_id !== undefined) {
        const account = accounts.value.find(a => a.id === pendingChange.account_id)
        return account?.name || '-'
      }
      if (pendingChange.credit_card_id !== null && pendingChange.credit_card_id !== undefined) {
        const creditCard = creditCards.value.find(c => c.id === pendingChange.credit_card_id)
        return creditCard?.name || '-'
      }
    }
    
    return transaction.account?.name || transaction.credit_card?.name || '-'
  }
  
  const getDisplayCategoryName = (transaction: Transaction): string => {
    const pendingChange = pendingChanges.value.get(transaction.id)
    
    if (pendingChange?.category_id !== null && pendingChange?.category_id !== undefined) {
      const category = categories.value.find(c => c.id === pendingChange.category_id)
      return category?.name || '-'
    }
    
    return transaction.category?.name || '-'
  }
  
  const getDisplayAccountCardIcon = (transaction: Transaction) => {
    const pendingChange = pendingChanges.value.get(transaction.id)
    
    if (pendingChange) {
      if (pendingChange.account_id !== null && pendingChange.account_id !== undefined) {
        return 'account'
      }
      if (pendingChange.credit_card_id !== null && pendingChange.credit_card_id !== undefined) {
        return 'credit_card'
      }
    }
    
    if (transaction.account) return 'account'
    if (transaction.credit_card) return 'credit_card'
    return null
  }
  
  // Subcategory editing methods
  const getCurrentSubcategoryValue = (transaction: Transaction): string => {
    const pendingChange = pendingChanges.value.get(transaction.id)
    const subcategoryId = pendingChange?.subcategory_id ?? transaction.subcategory?.id ?? null
    
    if (subcategoryId !== null) {
      return `subcategory_${subcategoryId}`
    }
    return 'none'
  }
  
  const getDisplaySubcategoryName = (transaction: Transaction): string => {
    const pendingChange = pendingChanges.value.get(transaction.id)
    
    if (pendingChange?.subcategory_id !== null && pendingChange?.subcategory_id !== undefined) {
      const subcategory = subcategories.value.find(s => s.id === pendingChange.subcategory_id)
      return subcategory?.name || '-'
    }
    
    return transaction.subcategory?.name || '-'
  }
  
  const getAvailableSubcategories = (transaction: Transaction) => {
    if (!subcategories.value || subcategories.value.length === 0) {
      return []
    }
    
    const transactionTypeMap: Record<string, 'income' | 'expense' | null> = {
      'INCOME': 'income',
      'EXPENSE': 'expense',
      'TRANSFER': null
    }
    
    const subcategoryTransactionType = transactionTypeMap[transaction.transaction_type] ?? null
    
    return subcategories.value.filter(subcategory => {
      const matchesTransactionType = subcategoryTransactionType === null || subcategory.transaction_type === subcategoryTransactionType
      const isActive = subcategory.is_active
      return matchesTransactionType && isActive
    })
  }
  
  const getSubcategoriesGroupedByCategory = (transaction: Transaction) => {
    const availableSubcategories = getAvailableSubcategories(transaction)
    
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
    
    return Array.from(grouped.entries())
      .map(([categoryId, data]) => ({ categoryId, ...data }))
      .sort((a, b) => a.categoryName.localeCompare(b.categoryName))
  }
  
  const handleSubcategoryChange = (transaction: Transaction, value: string) => {
    const transactionId = transaction.id
    const pendingChange = pendingChanges.value.get(transaction.id)
    
    const originalSubcategoryId = transaction.subcategory?.id ?? null
    const originalCategoryId = transaction.category?.id ?? null
    
    let newSubcategoryId: number | null = null
    let newCategoryId: number | null = null
    
    if (value === 'none') {
      newSubcategoryId = null
      newCategoryId = null
    } else if (value.startsWith('subcategory_')) {
      newSubcategoryId = Number(value.replace('subcategory_', ''))
      
      const selectedSubcategory = subcategories.value.find(s => s.id === newSubcategoryId)
      if (selectedSubcategory) {
        newCategoryId = Number(selectedSubcategory.category)
      }
    }
    
    const existingChanges = pendingChanges.value.get(transactionId) || {}
    
    const subcategoryChanged = newSubcategoryId !== originalSubcategoryId
    const categoryChanged = newCategoryId !== originalCategoryId
    
    if (subcategoryChanged || categoryChanged) {
      const updatedChanges: { account_id?: number | null, credit_card_id?: number | null, category_id?: number | null, subcategory_id?: number | null } = {
        ...existingChanges,
        subcategory_id: newSubcategoryId,
        category_id: newCategoryId
      }
      
      pendingChanges.value.set(transactionId, updatedChanges)
    } else {
      const updatedChanges = { ...existingChanges }
      delete updatedChanges.subcategory_id
      delete updatedChanges.category_id
      
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
    const pendingChange = pendingChanges.value.get(transactionId)
    const currentAccountId = pendingChange?.account_id ?? transaction.account?.id ?? null
    const currentCreditCardId = pendingChange?.credit_card_id ?? transaction.credit_card?.id ?? null
    
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
    
    const existingChanges = pendingChanges.value.get(transactionId) || {}
    
    if (newAccountId !== originalAccountId || newCreditCardId !== originalCreditCardId) {
      pendingChanges.value.set(transactionId, {
        ...existingChanges,
        account_id: newAccountId,
        credit_card_id: newCreditCardId
      })
    } else {
      const updatedChanges = { ...existingChanges }
      delete updatedChanges.account_id
      delete updatedChanges.credit_card_id
      
      if (Object.keys(updatedChanges).length === 0) {
        pendingChanges.value.delete(transactionId)
      } else {
        pendingChanges.value.set(transactionId, updatedChanges)
      }
    }
    
    editingCellId.value = null
  }
  
  const handleSaveChanges = async () => {
    savingChanges.value = true
    
    try {
      // Collect all updates: pending changes + mark all as reviewed
      const updatesMap = new Map<number, { account_id?: number | null, credit_card_id?: number | null, category_id?: number | null, subcategory_id?: number | null, need_review?: boolean }>()
      
      // Add pending changes
      pendingChanges.value.forEach((changes, id) => {
        updatesMap.set(id, { ...changes })
      })
      
      // Mark all transactions needing review as reviewed (even if no pending changes)
      transactionsNeedingReview.value.forEach(transaction => {
        const existingUpdate = updatesMap.get(transaction.id) || {}
        updatesMap.set(transaction.id, {
          ...existingUpdate,
          need_review: false
        })
      })
      
      const updates = Array.from(updatesMap.entries()).map(([id, changes]) => ({
        id,
        ...changes
      }))
      
      const result = await bulkUpdateTransactions({ transactions: updates })
      
      if (result.success) {
        pendingChanges.value.clear()
        editingCellId.value = null
        editingSubcategoryCellId.value = null
        alert('Alterações salvas e transações marcadas como revisadas!')
        // Navigate back to transactions page
        await navigateTo('/transactions')
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
      loadTransactionsNeedingReview(),
      initializeCreditCards(),
      initializeAccounts(),
      initializeCategories(),
      loadSubcategories()
    ])
  })
  </script>
  
  