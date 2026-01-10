<template>
  <div class="min-h-screen bg-gray-50">
    <!-- Header -->
    <div class="bg-white shadow">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div class="flex justify-between items-center py-6">
          <div>
            <h1 class="text-3xl font-bold text-gray-900">Contas</h1>
            <p class="mt-1 text-sm text-gray-500">
              Gerencie suas contas bancárias e acompanhe seus saldos
            </p>
          </div>
        <Button @click="showCreateModal = true">
          <PlusIcon class="h-4 w-4 mr-2" />
          Nova Conta
        </Button>
        </div>
      </div>
    </div>

    <!-- Stats -->
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
      <div class="grid grid-cols-1 gap-5 sm:grid-cols-4">
        <Card>
          <CardHeader class="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle class="text-sm font-medium">Total de Contas</CardTitle>
            <BanknotesIcon class="h-5 w-5 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div class="text-lg font-semibold">{{ accountStats.total }}</div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader class="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle class="text-sm font-medium">Contas Ativas</CardTitle>
            <CheckCircleIcon class="h-5 w-5 text-green-500" />
          </CardHeader>
          <CardContent>
            <div class="text-lg font-semibold">{{ accountStats.active }}</div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader class="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle class="text-sm font-medium">Contas Inativas</CardTitle>
            <XCircleIcon class="h-5 w-5 text-red-500" />
          </CardHeader>
          <CardContent>
            <div class="text-lg font-semibold">{{ accountStats.inactive }}</div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader class="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle class="text-sm font-medium">Saldo Total</CardTitle>
            <CurrencyDollarIcon class="h-5 w-5 text-green-500" />
          </CardHeader>
          <CardContent>
            <div class="text-lg font-semibold">{{ formatCurrency(accountStats.totalBalance) }}</div>
          </CardContent>
        </Card>
      </div>
    </div>

    <!-- Filters -->
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
      <Card class="mb-6">
        <CardHeader>
          <CardTitle class="text-lg">Filtros</CardTitle>
          <CardDescription>Refine a lista de contas.</CardDescription>
        </CardHeader>
        <CardContent class="space-y-4">
          <div class="grid grid-cols-1 gap-4 sm:grid-cols-4">
            <div class="space-y-2">
              <Label>Buscar</Label>
              <Input
                v-model="localFilters.search"
                type="text"
                placeholder="Nome da conta..."
              />
            </div>

            <div class="space-y-2">
              <Label>Tipo de Conta</Label>
              <Select v-model="localFilters.account_type">
                <SelectTrigger>
                  <SelectValue placeholder="Todos os tipos" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem :value="null">Todos os tipos</SelectItem>
                  <SelectItem value="checking">Conta Corrente</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div class="space-y-2">
              <Label>Moeda</Label>
              <Select v-model="localFilters.currency">
                <SelectTrigger>
                  <SelectValue placeholder="Todas as moedas" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem :value="null">Todas as moedas</SelectItem>
                  <SelectItem value="BRL">Real Brasileiro</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div class="space-y-2">
              <Label>Status</Label>
              <Select v-model="localFilters.is_active">
                <SelectTrigger>
                  <SelectValue placeholder="Todos" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem :value="null">Todos</SelectItem>
                  <SelectItem :value="true">Ativas</SelectItem>
                  <SelectItem :value="false">Inativas</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>

          <div class="flex justify-end gap-3">
            <Button variant="outline" @click="clearFilters">
              <XMarkIcon class="h-4 w-4 mr-1" />
              Limpar
            </Button>
            <Button @click="applyFilters">
              <FunnelIcon class="h-4 w-4 mr-1" />
              Filtrar
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>

    <!-- Table -->
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
      <Card>
        <CardHeader>
          <CardTitle class="text-lg">Contas</CardTitle>
          <CardDescription>{{ filteredAccounts.length }} contas encontradas</CardDescription>
        </CardHeader>

        <CardContent v-if="loading">
          <div class="space-y-2">
            <Skeleton class="h-8 w-full" />
            <Skeleton class="h-8 w-full" />
            <Skeleton class="h-8 w-full" />
          </div>
        </CardContent>

        <CardContent v-else-if="error">
          <Alert variant="destructive">
            <AlertTitle>Erro ao carregar contas</AlertTitle>
            <AlertDescription>{{ error }}</AlertDescription>
          </Alert>
        </CardContent>

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
                  >
                    <button
                      v-if="column.sortable"
                      @click="handleSort(column.key)"
                      class="group inline-flex items-center hover:text-gray-700"
                    >
                      {{ column.label }}
                      <span class="ml-2 flex-none rounded">
                        <ChevronUpIcon
                          v-if="sort.key === column.key && sort.direction === 'asc'"
                          class="h-4 w-4 text-gray-400 group-hover:text-gray-500"
                        />
                        <ChevronDownIcon
                          v-else-if="sort.key === column.key && sort.direction === 'desc'"
                          class="h-4 w-4 text-gray-400 group-hover:text-gray-500"
                        />
                        <ChevronUpIcon
                          v-else
                          class="h-4 w-4 text-gray-300 group-hover:text-gray-400"
                        />
                      </span>
                    </button>
                    <span v-else>{{ column.label }}</span>
                  </TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                <TableRow v-for="account in filteredAccounts" :key="account.id" class="hover:bg-muted/40">
                  <TableCell class="whitespace-nowrap">
                    <div class="flex items-center">
                      <div class="flex-shrink-0 h-10 w-10">
                        <div class="h-10 w-10 rounded-full bg-indigo-100 flex items-center justify-center">
                          <BanknotesIcon class="h-6 w-6 text-indigo-600" />
                        </div>
                      </div>
                      <div class="ml-4">
                        <div class="text-sm font-medium text-gray-900">
                          {{ account.name }}
                        </div>
                        <div class="text-sm text-gray-500">
                          {{ getAccountTypeLabel(account.account_type) }}
                        </div>
                      </div>
                    </div>
                  </TableCell>
                  <TableCell class="whitespace-nowrap text-sm text-gray-900">
                    {{ formatCurrency(account.current_balance) }}
                  </TableCell>
                  <TableCell class="whitespace-nowrap text-sm text-gray-900">
                    {{ getCurrencyLabel(account.currency) }}
                  </TableCell>
                  <TableCell class="whitespace-nowrap">
                    <Badge :variant="account.is_active ? 'secondary' : 'destructive'">
                      {{ account.is_active ? 'Ativa' : 'Inativa' }}
                    </Badge>
                  </TableCell>
                  <TableCell class="whitespace-nowrap text-sm text-gray-500">
                    {{ formatDate(account.created_at) }}
                  </TableCell>
                  <TableCell class="whitespace-nowrap text-right text-sm font-medium">
                    <div class="flex justify-end space-x-2">
                      <Button variant="ghost" size="icon" @click="editAccount(account)">
                        <PencilIcon class="h-4 w-4" />
                      </Button>
                      <Button variant="ghost" size="icon" @click="deleteAccount(account.id)">
                        <TrashIcon class="h-4 w-4 text-destructive" />
                      </Button>
                    </div>
                  </TableCell>
                </TableRow>
              </TableBody>
            </Table>
          </div>

          <div v-if="filteredAccounts.length === 0" class="text-center py-12">
            <BanknotesIcon class="mx-auto h-12 w-12 text-gray-400" />
            <h3 class="mt-2 text-sm font-medium text-gray-900">
              Nenhuma conta encontrada
            </h3>
            <p class="mt-1 text-sm text-gray-500">
              Comece criando sua primeira conta.
            </p>
            <div class="mt-6">
              <Button @click="showCreateModal = true">
                <PlusIcon class="h-4 w-4 mr-2" />
                Nova Conta
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>

    <!-- Create/Edit Modal -->
    <AccountModal
      v-if="showCreateModal || showEditModal"
      :account="editingAccount"
      :is-edit="showEditModal"
      @close="closeModal"
      @saved="handleAccountSaved"
    />
  </div>
</template>

<script setup lang="ts">
import {
  PlusIcon,
  BanknotesIcon,
  CheckCircleIcon,
  XCircleIcon,
  CurrencyDollarIcon,
  FunnelIcon,
  XMarkIcon,
  ExclamationTriangleIcon,
  ChevronUpIcon,
  ChevronDownIcon,
  PencilIcon,
  TrashIcon
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
  SelectItem,
  SelectTrigger,
  SelectValue
} from '@/components/ui/select'
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert'
import { Skeleton } from '@/components/ui/skeleton'

import type { Account, AccountTableFilters, AccountTableSort } from '~/types/accounts'

// Page metadata
definePageMeta({
  middleware: 'auth'
})

// Composables
const { 
  accounts,
  loading,
  error,
  filters,
  sort,
  filteredAccounts,
  accountStats,
  loadAccounts,
  deleteAccount: deleteAccountApi,
  applyTableFilters,
  applyTableSort,
  formatCurrency,
  formatDate,
  getAccountTypeLabel,
  getCurrencyLabel,
  initialize
} = useAccounts()

// Local state
const showCreateModal = ref(false)
const showEditModal = ref(false)
const editingAccount = ref<Account | null>(null)
const localFilters = ref<AccountTableFilters>({})

// Table columns configuration
const tableColumns = [
  { key: 'name', label: 'Conta', sortable: true, width: '300px' },
  { key: 'current_balance', label: 'Saldo', sortable: true, width: '150px', align: 'right' },
  { key: 'currency', label: 'Moeda', sortable: true, width: '120px' },
  { key: 'is_active', label: 'Status', sortable: true, width: '100px' },
  { key: 'created_at', label: 'Criada em', sortable: true, width: '120px' },
  { key: 'actions', label: 'Ações', sortable: false, width: '100px', align: 'right' }
]

// Methods
const handleSort = (key: string) => {
  const newDirection = sort.value.key === key && sort.value.direction === 'asc' ? 'desc' : 'asc'
  applyTableSort({ key: key as keyof Account, direction: newDirection })
}

const applyFilters = () => {
  applyTableFilters(localFilters.value)
}

const clearFilters = () => {
  localFilters.value = {}
  applyTableFilters({})
}

const editAccount = (account: Account) => {
  editingAccount.value = account
  showEditModal.value = true
}

const deleteAccount = async (id: number) => {
  if (confirm('Tem certeza que deseja excluir esta conta?')) {
    const result = await deleteAccountApi(id)
    if (!result.success) {
      alert('Erro ao excluir conta: ' + result.error?.message)
    }
  }
}

const closeModal = () => {
  showCreateModal.value = false
  showEditModal.value = false
  editingAccount.value = null
}

const handleAccountSaved = () => {
  closeModal()
  // Accounts will be automatically refreshed by the composable
}

// Initialize data
onMounted(async () => {
  await initialize()
})
</script> 