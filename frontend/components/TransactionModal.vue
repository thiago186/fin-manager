<template>
  <Dialog :open="true" @update:open="(open) => !open && $emit('close')">
    <DialogContent class="sm:max-w-2xl">
      <DialogHeader>
        <DialogTitle>{{ isEdit ? 'Editar Transação' : 'Nova Transação' }}</DialogTitle>
        <DialogDescription>
          Preencha os detalhes da transação.
        </DialogDescription>
      </DialogHeader>

      <form @submit.prevent="handleSubmit" class="space-y-6">
        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
          <!-- Transaction Type -->
          <div class="space-y-2">
            <Label>Tipo de Transação *</Label>
            <Select v-model="form.transaction_type" required>
              <SelectTrigger>
                <SelectValue placeholder="Selecione o tipo" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="INCOME">Receita</SelectItem>
                <SelectItem value="EXPENSE">Despesa</SelectItem>
                <SelectItem value="TRANSFER">Transferência</SelectItem>
              </SelectContent>
            </Select>
          </div>

          <!-- Amount -->
          <div class="space-y-2">
            <Label>Valor *</Label>
            <div class="relative">
              <span class="absolute inset-y-0 left-3 flex items-center text-sm text-muted-foreground">R$</span>
              <Input
                v-model="form.amount"
                type="number"
                step="0.01"
                min="0"
                required
                placeholder="0,00"
                class="pl-10"
              />
            </div>
          </div>
        </div>

        <!-- Description -->
        <div class="space-y-2">
          <Label>Descrição</Label>
          <Input
            v-model="form.description"
            type="text"
            placeholder="Descrição da transação"
          />
        </div>

        <!-- Date -->
        <div class="space-y-2">
          <Label>Data da Transação *</Label>
          <Input v-model="form.occurred_at" type="date" required />
        </div>

        <!-- Account & Credit Card -->
        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div class="space-y-2">
            <Label>Conta</Label>
            <Select v-model="form.account_id">
              <SelectTrigger>
                <SelectValue placeholder="Selecione uma conta" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem :value="null">Nenhuma</SelectItem>
                <SelectItem
                  v-for="account in accounts.filter(a => a.is_active)"
                  :key="account.id"
                  :value="String(account.id)"
                >
                  {{ account.name }} - {{ formatCurrency(account.current_balance) }}
                </SelectItem>
              </SelectContent>
            </Select>
          </div>
          <div class="space-y-2">
            <Label>Cartão de Crédito</Label>
            <Select v-model="form.credit_card_id">
              <SelectTrigger>
                <SelectValue placeholder="Selecione um cartão" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem :value="null">Nenhum</SelectItem>
                <SelectItem
                  v-for="card in creditCards.filter(c => c.is_active)"
                  :key="card.id"
                  :value="String(card.id)"
                >
                  {{ card.name }}
                </SelectItem>
              </SelectContent>
            </Select>
          </div>
        </div>

        <!-- Category -->
        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div class="space-y-2">
            <Label>Categoria</Label>
            <Select v-model="form.category_id" :disabled="isEdit" @update:model-value="loadSubcategories">
              <SelectTrigger :class="isEdit ? 'cursor-not-allowed opacity-60' : ''">
                <SelectValue placeholder="Selecione uma categoria" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem :value="null">Selecione</SelectItem>
                <SelectItem
                  v-for="category in availableCategories"
                  :key="category.id"
                  :value="String(category.id)"
                >
                  {{ category.name }}
                </SelectItem>
              </SelectContent>
            </Select>
          </div>

          <!-- Subcategory -->
          <div class="space-y-2">
            <Label>Subcategoria</Label>
            <Select
              v-model="form.subcategory_id"
              :disabled="isEdit ? false : !form.category_id"
              @update:model-value="handleSubcategoryChange"
            >
              <SelectTrigger :class="(!form.category_id && !isEdit) ? 'cursor-not-allowed opacity-60' : ''">
                <SelectValue placeholder="Selecione uma subcategoria" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem :value="null">Selecione</SelectItem>
                <SelectItem
                  v-for="subcategory in availableSubcategories"
                  :key="subcategory.id"
                  :value="String(subcategory.id)"
                >
                  {{ subcategory.name }}
                </SelectItem>
              </SelectContent>
            </Select>
          </div>
        </div>

        <!-- Installments -->
        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div class="space-y-2">
            <Label>Total de Parcelas</Label>
            <Input
              v-model="form.installments_total"
              type="number"
              min="1"
              placeholder="1"
            />
          </div>
          <div class="space-y-2">
            <Label>Parcela Atual</Label>
            <Input
              v-model="form.installment_number"
              type="number"
              min="1"
              placeholder="1"
            />
          </div>
        </div>

        <!-- Error Display -->
        <Alert v-if="error" variant="destructive">
          <ExclamationTriangleIcon class="h-4 w-4" />
          <AlertTitle>Erro ao salvar transação</AlertTitle>
          <AlertDescription>{{ error }}</AlertDescription>
        </Alert>

        <DialogFooter class="gap-2">
          <Button type="button" variant="outline" :disabled="isSubmitting" @click="$emit('close')">
            Cancelar
          </Button>
          <Button type="submit" :disabled="isSubmitting">
            <span v-if="isSubmitting" class="mr-2 inline-flex h-4 w-4 animate-spin rounded-full border-b-2 border-white"></span>
            {{ isSubmitting ? 'Salvando...' : (isEdit ? 'Atualizar' : 'Criar') }}
          </Button>
        </DialogFooter>
      </form>
    </DialogContent>
  </Dialog>
</template>

<script setup lang="ts">
import { ExclamationTriangleIcon } from '@heroicons/vue/24/outline'
import type { Transaction, TransactionForm } from '~/types/transactions'
import type { CategoryList } from '~/types/categories'
import type { SubcategoryList } from '~/types/subcategories'
import { Button } from '@/components/ui/button'
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
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue
} from '@/components/ui/select'
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert'

// Props
interface Props {
  transaction?: Transaction | null
  isEdit?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  transaction: null,
  isEdit: false
})

// Emits
const emit = defineEmits<{
  close: []
  saved: []
}>()

// Composables
const { 
  createTransaction, 
  updateTransaction, 
  formatTransactionData,
  formatCurrency,
  clearError
} = useTransactions()

const { categories, loadCategories } = useCategories()
const { loadSubcategories: loadSubcategoriesApi } = useSubcategories()

// Local state
const isSubmitting = ref(false)
const error = ref<string | null>(null)

// Get accounts from the accounts composable
const { accounts, loadAccounts } = useAccounts()

// Get credit cards from the credit cards composable
const { creditCards, loadCreditCards } = useCreditCards()

// Form state
const form = ref<TransactionForm>({
  transaction_type: '',
  amount: '',
  description: '',
  occurred_at: new Date().toISOString().split('T')[0],
  installments_total: '1',
  installment_number: '1',
  account_id: null,
  credit_card_id: null,
  category_id: null,
  subcategory_id: null,
  tag_ids: []
})

// Available categories and subcategories
const availableCategories = computed(() => {
  if (!form.value.transaction_type) return []
  return categories.value.filter(cat => 
    cat.transaction_type === (form.value.transaction_type === 'INCOME' ? 'income' : 'expense') &&
    cat.is_active
  )
})

const availableSubcategories = ref<SubcategoryList[]>([])

// Methods
const loadSubcategories = async () => {
  // When editing, load all subcategories filtered by transaction type
  // When creating, load subcategories filtered by category
  if (props.isEdit) {
    // Load all subcategories for the current transaction type
    try {
      const result = await loadSubcategoriesApi()
      
      if (result.success && result.data) {
        // Filter by transaction type and active status
        const transactionType = form.value.transaction_type === 'INCOME' ? 'income' : 'expense'
        availableSubcategories.value = result.data.filter(sub => 
          sub.transaction_type === transactionType && sub.is_active
        )
      } else {
        availableSubcategories.value = []
      }
    } catch (err) {
      console.error('Error loading subcategories:', err)
      availableSubcategories.value = []
    }
  } else {
    // Original behavior for creating transactions
    if (!form.value.category_id) {
      availableSubcategories.value = []
      form.value.subcategory_id = null
      return
    }

    try {
      const result = await loadSubcategoriesApi({
        category: Number(form.value.category_id)
      })
      
      if (result.success && result.data) {
        // Filter to only show active subcategories
        availableSubcategories.value = result.data.filter(sub => sub.is_active)
      } else {
        availableSubcategories.value = []
      }
    } catch (err) {
      console.error('Error loading subcategories:', err)
      availableSubcategories.value = []
    }
  }
}

const handleSubcategoryChange = () => {
  // When editing, automatically set category_id from the selected subcategory
  if (props.isEdit && form.value.subcategory_id) {
    const selectedSubcategory = availableSubcategories.value.find(
      sub => sub.id === Number(form.value.subcategory_id)
    )
    if (selectedSubcategory) {
      form.value.category_id = String(selectedSubcategory.category)
    }
  }
}

const initializeForm = async () => {
  if (props.transaction && props.isEdit) {
    form.value = {
      transaction_type: props.transaction.transaction_type,
      amount: props.transaction.amount,
      description: props.transaction.description || '',
      occurred_at: props.transaction.occurred_at,
      installments_total: String(props.transaction.installments_total),
      installment_number: String(props.transaction.installment_number),
      account_id: props.transaction.account_id ? String(props.transaction.account_id) : null,
      credit_card_id: props.transaction.credit_card_id ? String(props.transaction.credit_card_id) : null,
      category_id: props.transaction.category_id ? String(props.transaction.category_id) : null,
      subcategory_id: props.transaction.subcategory_id ? String(props.transaction.subcategory_id) : null,
      tag_ids: props.transaction.tag_ids || []
    }
    
    // When editing, ensure category_id is synced from subcategory if subcategory exists
    if (props.isEdit && form.value.subcategory_id && form.value.transaction_type) {
      // Load subcategories first to get the category from the subcategory
      await loadSubcategories()
      // Sync category from subcategory
      handleSubcategoryChange()
    }
  } else {
    form.value = {
      transaction_type: props.transaction?.transaction_type || '',
      amount: '',
      description: '',
      occurred_at: new Date().toISOString().split('T')[0],
      installments_total: '1',
      installment_number: '1',
      account_id: null,
      credit_card_id: null,
      category_id: null,
      subcategory_id: null,
      tag_ids: []
    }
  }
}

const handleSubmit = async () => {
  isSubmitting.value = true
  error.value = null

  try {
    const transactionData = formatTransactionData(form.value)
    
    if (props.isEdit && props.transaction) {
      const result = await updateTransaction(props.transaction.id, transactionData)
      if (!result.success) {
        error.value = result.error?.message || 'Erro ao atualizar transação'
        return
      }
    } else {
      const result = await createTransaction(transactionData)
      if (!result.success) {
        error.value = result.error?.message || 'Erro ao criar transação'
        return
      }
    }

    emit('saved')
  } catch (err: any) {
    error.value = err?.message || 'Erro desconhecido'
  } finally {
    isSubmitting.value = false
  }
}

// Initialize
onMounted(async () => {
  await Promise.all([loadCategories(), loadAccounts(), loadCreditCards()])
  // Only initialize form if not editing (for new transactions)
  if (!props.isEdit) {
    initializeForm()
  }
})

// Watch for transaction type changes to reset category selection
watch(() => form.value.transaction_type, () => {
  form.value.category_id = null
  form.value.subcategory_id = null
  availableSubcategories.value = []
  // Reload subcategories when transaction type changes (especially important for edit mode)
  if (form.value.transaction_type) {
    loadSubcategories()
  }
})

// Watch for category changes to load subcategories (only for create mode)
watch(() => form.value.category_id, () => {
  if (!props.isEdit) {
    loadSubcategories()
  }
})

// Watch for subcategory changes to update category (only for edit mode)
watch(() => form.value.subcategory_id, () => {
  if (props.isEdit && form.value.subcategory_id) {
    handleSubcategoryChange()
  }
})

// Watch for transaction prop changes to re-initialize form when editing
watch(() => props.transaction, async () => {
  if (props.transaction && props.isEdit) {
    await initializeForm()
  }
}, { immediate: true })

// Watch for isEdit prop changes to re-initialize form
watch(() => props.isEdit, async () => {
  if (props.isEdit && props.transaction) {
    await initializeForm()
  }
})
</script> 