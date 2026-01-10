<template>
  <div class="min-h-screen bg-gray-50">
    <!-- Header -->
    <div class="bg-white shadow">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div class="flex justify-between items-center py-6">
          <div>
            <h1 class="text-3xl font-bold text-gray-900">Cartões de Crédito</h1>
            <p class="mt-1 text-sm text-gray-500">
              Gerencie seus cartões de crédito
            </p>
          </div>
        <Button @click="showCreateModal = true">
          <PlusIcon class="h-4 w-4 mr-2" />
          Novo Cartão
        </Button>
        </div>
      </div>
    </div>

    <!-- Stats -->
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
      <div class="grid grid-cols-1 gap-5 sm:grid-cols-4">
        <Card>
          <CardHeader class="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle class="text-sm font-medium">Total de Cartões</CardTitle>
            <CreditCardIcon class="h-5 w-5 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div class="text-lg font-semibold">{{ creditCardStats.total }}</div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader class="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle class="text-sm font-medium">Cartões Ativos</CardTitle>
            <CheckCircleIcon class="h-5 w-5 text-green-500" />
          </CardHeader>
          <CardContent>
            <div class="text-lg font-semibold">{{ creditCardStats.active }}</div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader class="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle class="text-sm font-medium">Cartões Inativos</CardTitle>
            <XCircleIcon class="h-5 w-5 text-red-500" />
          </CardHeader>
          <CardContent>
            <div class="text-lg font-semibold">{{ creditCardStats.inactive }}</div>
          </CardContent>
        </Card>
      </div>
    </div>

    <!-- Filters -->
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
      <Card class="mb-6">
        <CardHeader>
          <CardTitle class="text-lg">Filtros</CardTitle>
          <CardDescription>Refine a lista de cartões.</CardDescription>
        </CardHeader>
        <CardContent class="space-y-4">
          <div class="grid grid-cols-1 gap-4 sm:grid-cols-2">
            <div class="space-y-2">
              <Label>Buscar</Label>
              <Input
                v-model="localFilters.search"
                type="text"
                placeholder="Nome do cartão..."
              />
            </div>

            <div class="space-y-2">
              <Label>Status</Label>
              <Select v-model="localFilters.is_active">
                <SelectTrigger>
                  <SelectValue placeholder="Todos" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem :value="null">Todos</SelectItem>
                  <SelectItem :value="true">Ativos</SelectItem>
                  <SelectItem :value="false">Inativos</SelectItem>
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
          <CardTitle class="text-lg">Cartões</CardTitle>
          <CardDescription>{{ filteredCreditCards.length }} cartões encontrados</CardDescription>
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
            <AlertTitle>Erro ao carregar cartões</AlertTitle>
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
                <TableRow v-for="creditCard in filteredCreditCards" :key="creditCard.id" class="hover:bg-muted/40">
                  <TableCell class="whitespace-nowrap">
                    <div class="flex items-center">
                      <div class="flex-shrink-0 h-10 w-10">
                        <div class="h-10 w-10 rounded-full bg-blue-100 flex items-center justify-center">
                          <CreditCardIcon class="h-6 w-6 text-blue-600" />
                        </div>
                      </div>
                      <div class="ml-4">
                        <div class="text-sm font-medium text-gray-900">
                          {{ creditCard.name }}
                        </div>
                        <div class="text-sm text-gray-500">
                          Cartão de Crédito
                        </div>
                      </div>
                    </div>
                  </TableCell>
                  <TableCell class="whitespace-nowrap">
                    <Badge :variant="creditCard.is_active ? 'secondary' : 'destructive'">
                      {{ creditCard.is_active ? 'Ativo' : 'Inativo' }}
                    </Badge>
                  </TableCell>
                  <TableCell class="whitespace-nowrap text-sm text-gray-500">
                    {{ formatDate(creditCard.created_at) }}
                  </TableCell>
                  <TableCell class="whitespace-nowrap text-right text-sm font-medium">
                    <div class="flex justify-end space-x-2">
                      <Button variant="ghost" size="icon" @click="editCreditCard(creditCard)">
                        <PencilIcon class="h-4 w-4" />
                      </Button>
                      <Button variant="ghost" size="icon" @click="deleteCreditCard(creditCard.id)">
                        <TrashIcon class="h-4 w-4 text-destructive" />
                      </Button>
                    </div>
                  </TableCell>
                </TableRow>
              </TableBody>
            </Table>
          </div>

          <div v-if="filteredCreditCards.length === 0" class="text-center py-12">
            <CreditCardIcon class="mx-auto h-12 w-12 text-gray-400" />
            <h3 class="mt-2 text-sm font-medium text-gray-900">
              Nenhum cartão encontrado
            </h3>
            <p class="mt-1 text-sm text-gray-500">
              Comece criando seu primeiro cartão de crédito.
            </p>
            <div class="mt-6">
              <Button @click="showCreateModal = true">
                <PlusIcon class="h-4 w-4 mr-2" />
                Novo Cartão
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>

    <!-- Create/Edit Modal -->
    <CreditCardModal
      v-if="showCreateModal || showEditModal"
      :credit-card="editingCreditCard"
      :is-edit="showEditModal"
      @close="closeModal"
      @saved="handleCreditCardSaved"
    />
  </div>
</template>

<script setup lang="ts">
import {
  PlusIcon,
  CreditCardIcon,
  CheckCircleIcon,
  XCircleIcon,
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

import type { CreditCard, CreditCardTableFilters, CreditCardTableSort } from '~/types/creditCards'

// Page metadata
definePageMeta({
  middleware: 'auth'
})

// Composables
const { 
  creditCards,
  loading,
  error,
  filters,
  sort,
  filteredCreditCards,
  creditCardStats,
  loadCreditCards,
  deleteCreditCard: deleteCreditCardApi,
  applyTableFilters,
  applyTableSort,
  formatDate,
  initialize
} = useCreditCards()

// Local state
const showCreateModal = ref(false)
const showEditModal = ref(false)
const editingCreditCard = ref<CreditCard | null>(null)
const localFilters = ref<CreditCardTableFilters>({})

// Table columns configuration
const tableColumns = [
  { key: 'name', label: 'Cartão', sortable: true, width: '300px' },
  { key: 'is_active', label: 'Status', sortable: true, width: '100px' },
  { key: 'created_at', label: 'Criado em', sortable: true, width: '120px' },
  { key: 'actions', label: 'Ações', sortable: false, width: '100px', align: 'right' }
]

// Methods
const handleSort = (key: string) => {
  const newDirection = sort.value.key === key && sort.value.direction === 'asc' ? 'desc' : 'asc'
  applyTableSort({ key: key as keyof CreditCard, direction: newDirection })
}

const applyFilters = () => {
  applyTableFilters(localFilters.value)
}

const clearFilters = () => {
  localFilters.value = {}
  applyTableFilters({})
}

const editCreditCard = (creditCard: CreditCard) => {
  editingCreditCard.value = creditCard
  showEditModal.value = true
}

const deleteCreditCard = async (id: number) => {
  if (confirm('Tem certeza que deseja excluir este cartão?')) {
    const result = await deleteCreditCardApi(id)
    if (!result.success) {
      alert('Erro ao excluir cartão: ' + result.error?.message)
    }
  }
}

const closeModal = () => {
  showCreateModal.value = false
  showEditModal.value = false
  editingCreditCard.value = null
}

const handleCreditCardSaved = () => {
  closeModal()
  // Credit cards will be automatically refreshed by the composable
}

// Initialize data
onMounted(async () => {
  await initialize()
})
</script> 