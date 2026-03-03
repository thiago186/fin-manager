<template>
  <div class="py-8">
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
      <!-- Section Header -->
      <div class="flex justify-between items-center mb-6">
        <div>
          <h1 class="text-3xl font-bold text-gray-900">Orçamentos</h1>
          <p class="mt-1 text-sm text-gray-500">Gerencie seus limites mensais por categoria</p>
        </div>
        <Button @click="openCreateModal">
          <svg class="h-5 w-5 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4"></path>
          </svg>
          Novo Orçamento
        </Button>
      </div>

      <!-- Filters -->
      <Card class="mb-6">
        <CardHeader>
          <CardTitle class="text-base">Filters</CardTitle>
          <CardDescription>Refine the budgets list.</CardDescription>
        </CardHeader>
        <CardContent class="grid gap-4 md:grid-cols-[1fr_auto]">
          <div class="space-y-2">
            <Label>Transaction Type</Label>
            <Select v-model="filters.transaction_type" @update:model-value="handleLoadBudgets">
              <SelectTrigger>
                <SelectValue placeholder="All Types" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem :value="null">All Types</SelectItem>
                <SelectItem value="income">Income</SelectItem>
                <SelectItem value="expense">Expense</SelectItem>
              </SelectContent>
            </Select>
          </div>
          <div class="flex items-end justify-start md:justify-end">
            <Button variant="outline" @click="handleLoadBudgets">
              Refresh
            </Button>
          </div>
        </CardContent>
      </Card>

      <Alert v-if="budgetsError" variant="destructive" class="mb-4">
        <AlertTitle>Erro ao carregar orçamentos</AlertTitle>
        <AlertDescription>{{ budgetsError }}</AlertDescription>
      </Alert>

      <!-- Loading State -->
      <div v-if="budgetsLoading" class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        <Skeleton v-for="n in 3" :key="`budget-skel-${n}`" class="h-32 w-full" />
      </div>

      <!-- Budgets Grid -->
      <div v-else-if="budgets.length > 0" class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        <Card
          v-for="budget in budgets"
          :key="budget.id"
          class="hover:shadow-md transition-shadow"
        >
          <CardHeader class="pb-3 flex flex-row items-start justify-between gap-2">
            <div>
              <CardTitle class="text-lg">{{ budget.category.name }}</CardTitle>
              <CardDescription class="flex items-center gap-2 mt-2">
                <Badge :variant="budget.category.transaction_type === 'income' ? 'secondary' : 'destructive'">
                  {{ budget.category.transaction_type }}
                </Badge>
                <Badge v-if="!budget.is_active" variant="outline">Inactive</Badge>
              </CardDescription>
            </div>
            <div class="flex gap-2">
              <Button variant="ghost" size="icon" @click="editBudget(budget)" title="Edit budget">
                <svg class="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z"></path>
                </svg>
              </Button>
              <Button variant="ghost" size="icon" @click="handleDeleteBudget(budget)" title="Delete budget">
                <svg class="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"></path>
                </svg>
              </Button>
            </div>
          </CardHeader>
          <CardContent>
            <p class="text-2xl font-semibold text-gray-900">
              {{ formatCurrency(budget.amount) }}
            </p>
            <p class="text-sm text-gray-500 mt-1">por mês</p>
          </CardContent>
        </Card>
      </div>

      <!-- Empty State -->
      <div v-else class="text-center py-12">
        <div class="mx-auto h-12 w-12 text-gray-400">
          <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path>
          </svg>
        </div>
        <h3 class="mt-2 text-sm font-medium text-gray-900">Nenhum orçamento encontrado</h3>
        <p class="mt-1 text-sm text-gray-500">Comece criando um novo orçamento.</p>
        <div class="mt-6">
          <Button @click="openCreateModal">
            Novo Orçamento
          </Button>
        </div>
      </div>
    </div>

    <!-- Create/Edit Modal -->
    <Dialog v-if="showCreateModal || showEditModal" :open="true" @update:open="(open) => !open && closeModal()">
      <DialogContent class="sm:max-w-md">
        <DialogHeader>
          <DialogTitle>{{ showEditModal ? 'Editar Orçamento' : 'Criar Orçamento' }}</DialogTitle>
          <DialogDescription>
            Defina a categoria e o limite mensal.
          </DialogDescription>
        </DialogHeader>

        <form @submit.prevent="showEditModal ? handleUpdateBudget() : handleCreateBudget()" class="space-y-4">
          <div class="space-y-2">
            <Label>Categoria</Label>
            <Select v-model="budgetForm.category_id" required>
              <SelectTrigger>
                <SelectValue placeholder="Selecione a categoria" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem v-for="category in categories" :key="category.id" :value="String(category.id)">
                  {{ category.name }} ({{ category.transaction_type }})
                </SelectItem>
              </SelectContent>
            </Select>
          </div>

          <div class="space-y-2">
            <Label>Valor Mensal</Label>
            <Input
              v-model="budgetForm.amount"
              type="number"
              step="0.01"
              min="0"
              required
              placeholder="0.00"
            />
          </div>

          <div class="flex items-center gap-2">
            <Checkbox v-model:checked="budgetForm.is_active" id="budget_is_active" />
            <Label for="budget_is_active" class="text-sm">Ativo</Label>
          </div>

          <DialogFooter class="gap-2">
            <Button type="button" variant="outline" @click="closeModal" :disabled="submitting">
              Cancelar
            </Button>
            <Button type="submit" :disabled="submitting">
              <span v-if="submitting" class="mr-2 inline-flex h-4 w-4 animate-spin rounded-full border-b-2 border-white"></span>
              {{ submitting ? 'Salvando...' : (showEditModal ? 'Atualizar' : 'Criar') }}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  </div>
</template>

<script setup>
import { Button } from '@/components/ui/button'
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle
} from '@/components/ui/card'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle
} from '@/components/ui/dialog'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Checkbox } from '@/components/ui/checkbox'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue
} from '@/components/ui/select'
import { Badge } from '@/components/ui/badge'
import { Skeleton } from '@/components/ui/skeleton'
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert'

definePageMeta({
  middleware: 'auth'
})

const {
  budgets,
  loading: budgetsLoading,
  error: budgetsError,
  loadBudgets,
  createBudget: createBudgetApi,
  updateBudget: updateBudgetApi,
  deleteBudget: deleteBudgetApi,
  formatBudgetData,
  initialize: initializeBudgets,
  clearError
} = useBudgets()

const {
  categories,
  initialize: initializeCategories
} = useCategories()

const submitting = ref(false)
const showCreateModal = ref(false)
const showEditModal = ref(false)
const editingBudget = ref(null)

const filters = ref({
  transaction_type: ''
})

const budgetForm = ref({
  category_id: '',
  amount: '',
  is_active: true
})

const handleLoadBudgets = async () => {
  const filtersData = {
    transaction_type: filters.value.transaction_type || null
  }
  await loadBudgets(filtersData)
}

const openCreateModal = () => {
  budgetForm.value = {
    category_id: '',
    amount: '',
    is_active: true
  }
  showCreateModal.value = true
}

const handleCreateBudget = async () => {
  submitting.value = true
  try {
    const data = formatBudgetData(budgetForm.value)
    const result = await createBudgetApi(data)
    if (result.success) {
      closeModal()
    }
  } catch (error) {
    console.error('Error creating budget:', error)
  } finally {
    submitting.value = false
  }
}

const editBudget = (budget) => {
  editingBudget.value = budget
  budgetForm.value = {
    category_id: String(budget.category.id),
    amount: budget.amount,
    is_active: budget.is_active
  }
  showEditModal.value = true
}

const handleUpdateBudget = async () => {
  submitting.value = true
  try {
    const data = formatBudgetData(budgetForm.value)
    const result = await updateBudgetApi(editingBudget.value.id, data)
    if (result.success) {
      closeModal()
    }
  } catch (error) {
    console.error('Error updating budget:', error)
  } finally {
    submitting.value = false
  }
}

const handleDeleteBudget = async (budget) => {
  if (!confirm(`Tem certeza que deseja excluir o orçamento de "${budget.category.name}"?`)) {
    return
  }
  await deleteBudgetApi(budget.id)
}

const closeModal = () => {
  showCreateModal.value = false
  showEditModal.value = false
  editingBudget.value = null
  budgetForm.value = {
    category_id: '',
    amount: '',
    is_active: true
  }
  clearError()
}

const formatCurrency = (value) => {
  return new Intl.NumberFormat('pt-BR', {
    style: 'currency',
    currency: 'BRL'
  }).format(Number(value))
}

onMounted(async () => {
  await Promise.all([initializeBudgets(), initializeCategories()])
})
</script>
