<template>
  <div class="py-8">
    <!-- Page Header -->
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 mb-6">
      <div class="flex justify-between items-center">
        <div>
          <h1 class="text-3xl font-bold text-gray-900">Transações Duplicadas</h1>
          <p class="mt-1 text-sm text-gray-500">
            Visualize e gerencie transações com possível duplicidade
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

    <!-- Duplicate Groups -->
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
      <!-- Save Changes Button -->
      <div v-if="hasSelectedHashes" class="mb-4 flex justify-end">
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

      <!-- Loading State -->
      <Card v-if="loadingDuplicates">
        <CardContent class="space-y-2 py-6">
          <Skeleton class="h-8 w-full" />
          <Skeleton class="h-8 w-full" />
          <Skeleton class="h-8 w-full" />
        </CardContent>
      </Card>

      <!-- Error State -->
      <Card v-else-if="error">
        <CardContent class="py-6">
          <Alert variant="destructive">
            <AlertTitle>Erro ao carregar transações</AlertTitle>
            <AlertDescription>{{ error }}</AlertDescription>
          </Alert>
        </CardContent>
      </Card>

      <!-- Empty State -->
      <Card v-else-if="groupedDuplicates.length === 0">
        <CardContent class="py-12">
          <div class="text-center">
            <CheckCircleIcon class="mx-auto h-12 w-12 text-gray-400" />
            <h3 class="mt-2 text-sm font-medium text-gray-900">
              Nenhuma transação duplicada encontrada
            </h3>
            <p class="mt-1 text-sm text-gray-500">
              Todas as transações parecem únicas.
            </p>
          </div>
        </CardContent>
      </Card>

      <!-- Duplicate Groups List -->
      <template v-else>
        <div
          v-for="(group, index) in groupedDuplicates"
          :key="group.hash"
          class="mb-6"
        >
          <Card>
            <CardHeader class="pb-3">
              <div class="flex items-center justify-between">
                <div class="flex items-center space-x-3">
                  <ExclamationTriangleIcon class="h-5 w-5 text-amber-500" />
                  <div>
                    <CardTitle class="text-base">Grupo Duplicado #{{ index + 1 }}</CardTitle>
                    <CardDescription class="text-xs font-mono mt-0.5">
                      Hash: {{ group.hash }}
                    </CardDescription>
                  </div>
                </div>
                <div class="flex items-center space-x-4">
                  <div class="flex items-center space-x-2">
                    <Checkbox
                      :id="`ignore-${group.hash}`"
                      v-model="selectedHashes[group.hash]"
                    />
                    <Label :for="`ignore-${group.hash}`" class="text-sm cursor-pointer">
                      Não é duplicada
                    </Label>
                  </div>
                  <Badge variant="destructive">
                    {{ group.transactions.length }} ocorrências
                  </Badge>
                </div>
              </div>
            </CardHeader>

            <CardContent class="p-0">
              <div class="overflow-x-auto">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead class="w-[120px]">Data</TableHead>
                      <TableHead class="w-[100px]">Tipo</TableHead>
                      <TableHead>Descrição</TableHead>
                      <TableHead class="w-[120px]">Categoria</TableHead>
                      <TableHead class="w-[150px]">Conta/Cartão</TableHead>
                      <TableHead class="w-[120px] text-right">Valor</TableHead>
                      <TableHead class="w-[80px] text-center">Parcelas</TableHead>
                      <TableHead class="w-[100px] text-right">Ações</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    <TableRow
                      v-for="transaction in group.transactions"
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
                        {{ transaction.category?.name || '-' }}
                      </TableCell>
                      <TableCell class="whitespace-nowrap text-sm text-gray-900">
                        <div class="flex items-center">
                          <BanknotesIcon
                            v-if="transaction.account"
                            class="h-4 w-4 mr-1.5 text-indigo-600"
                          />
                          <CreditCardIcon
                            v-else-if="transaction.credit_card"
                            class="h-4 w-4 mr-1.5 text-blue-600"
                          />
                          <span>
                            {{ transaction.account?.name || transaction.credit_card?.name || '-' }}
                          </span>
                        </div>
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
                  </TableBody>
                </Table>
              </div>
            </CardContent>
          </Card>
        </div>

        <!-- Pagination Controls -->
        <div class="flex items-center justify-between border-t bg-white rounded-lg px-4 py-3 shadow-sm">
          <div class="flex items-center text-sm text-gray-700">
            <span>
              Mostrando {{ transactionsDuplicates.length }} de {{ paginationDuplicates.count }} transações
            </span>
          </div>
          <div class="flex items-center space-x-2">
            <Button
              variant="outline"
              size="sm"
              @click="loadPreviousPageDuplicates()"
              :disabled="!paginationDuplicates.previous"
            >
              Anterior
            </Button>
            <div class="flex items-center space-x-1">
              <span class="text-sm text-gray-700">
                Página {{ paginationDuplicates.currentPage }} de {{ totalPages || 1 }}
              </span>
            </div>
            <Button
              variant="outline"
              size="sm"
              @click="loadNextPageDuplicates()"
              :disabled="!paginationDuplicates.next"
            >
              Próxima
            </Button>
          </div>
        </div>
      </template>
    </div>

    <!-- Edit Modal -->
    <TransactionModal
      v-if="showEditModal"
      :transaction="editingTransaction"
      :is-edit="true"
      @close="closeModal"
      @saved="handleTransactionSaved"
    />
  </div>
</template>

<script setup lang="ts">
import {
  ArrowLeftIcon,
  ExclamationTriangleIcon,
  CheckCircleIcon,
  PencilIcon,
  TrashIcon,
  BanknotesIcon,
  CreditCardIcon,
  CheckIcon
} from '@heroicons/vue/24/outline'
import { Button } from '@/components/ui/button'
import { Checkbox } from '@/components/ui/checkbox'
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
  TableHead,
  TableHeader,
  TableRow
} from '@/components/ui/table'
import { Badge } from '@/components/ui/badge'
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert'
import { Skeleton } from '@/components/ui/skeleton'
import { Label } from '@/components/ui/label'

import type { Transaction } from '~/types/transactions'

interface DuplicateGroup {
  hash: string
  transactions: Transaction[]
}

// Page metadata
definePageMeta({
  middleware: 'auth'
})

// Composables
const {
  transactionsDuplicates,
  loadingDuplicates,
  error,
  paginationDuplicates,
  loadTransactionsDuplicates,
  loadNextPageDuplicates,
  loadPreviousPageDuplicates,
  loadPageDuplicates,
  deleteTransaction: deleteTransactionApi,
  bulkUpdateTransactions,
  formatCurrency,
  formatDate,
  getTransactionTypeColor,
  getTransactionTypeLabel
} = useTransactions()

// Local state
const showEditModal = ref(false)
const editingTransaction = ref<Transaction | null>(null)
const selectedHashes = ref<Record<string, boolean>>({})
const savingChanges = ref(false)

// Computed
const totalPages = computed(() => Math.ceil(paginationDuplicates.value.count / 100))
const hasSelectedHashes = computed(() => Object.values(selectedHashes.value).some(Boolean))

const groupedDuplicates = computed<DuplicateGroup[]>(() => {
  const groups = new Map<string, Transaction[]>()

  transactionsDuplicates.value.forEach((transaction) => {
    const hash = transaction.hash || 'unknown'
    if (!groups.has(hash)) {
      groups.set(hash, [])
    }
    groups.get(hash)!.push(transaction as Transaction)
  })

  return Array.from(groups.entries()).map(([hash, transactions]) => ({
    hash,
    transactions
  }))
})

// Methods
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
      await loadPageDuplicates(paginationDuplicates.value.currentPage)
    }
  }
}

const closeModal = () => {
  showEditModal.value = false
  editingTransaction.value = null
}

const handleTransactionSaved = async () => {
  closeModal()
  await loadPageDuplicates(paginationDuplicates.value.currentPage)
}

const handleSaveChanges = async () => {
  if (!hasSelectedHashes.value) return

  savingChanges.value = true

  try {
    const updates: { id: number; ignore_duplicates: boolean }[] = []

    groupedDuplicates.value.forEach((group) => {
      if (selectedHashes.value[group.hash]) {
        group.transactions.forEach((transaction) => {
          updates.push({
            id: transaction.id,
            ignore_duplicates: true
          })
        })
      }
    })

    const result = await bulkUpdateTransactions({ transactions: updates })

    if (result.success) {
      selectedHashes.value = {}
      alert('Grupos marcados como não duplicados com sucesso!')
      await loadPageDuplicates(paginationDuplicates.value.currentPage)
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
  await loadTransactionsDuplicates()
})
</script>
