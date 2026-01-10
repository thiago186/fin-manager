<template>
  <Dialog :open="true">
    <DialogContent class="sm:max-w-2xl">
      <DialogHeader>
        <DialogTitle>Edição em Massa</DialogTitle>
        <DialogDescription>
          Atualize {{ selectedCount }} transação(ões) selecionada(s). Deixe os campos em branco para não alterar.
        </DialogDescription>
      </DialogHeader>

      <form @submit.prevent="handleSubmit" class="space-y-6">
        <!-- Transaction Type -->
        <div class="space-y-2">
          <Label>Tipo de Transação</Label>
          <Select v-model="form.transaction_type">
            <SelectTrigger>
              <SelectValue placeholder="Manter tipo atual" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem :value="null">Manter tipo atual</SelectItem>
              <SelectItem value="INCOME">Receita</SelectItem>
              <SelectItem value="EXPENSE">Despesa</SelectItem>
              <SelectItem value="TRANSFER">Transferência</SelectItem>
            </SelectContent>
          </Select>
        </div>

        <!-- Account & Credit Card -->
        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div class="space-y-2">
            <Label>Conta</Label>
            <Select v-model="form.account_id" @update:model-value="handleAccountChange">
              <SelectTrigger>
                <SelectValue placeholder="Manter conta atual" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem :value="null">Manter conta atual</SelectItem>
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
            <Select v-model="form.credit_card_id" @update:model-value="handleCreditCardChange">
              <SelectTrigger>
                <SelectValue placeholder="Manter cartão atual" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem :value="null">Manter cartão atual</SelectItem>
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

        <!-- Subcategory -->
        <div class="space-y-2">
          <Label>Subcategoria</Label>
          <Select
            v-model="form.subcategory_id"
            :disabled="!form.transaction_type"
          >
            <SelectTrigger :class="!form.transaction_type ? 'cursor-not-allowed opacity-60' : ''">
              <SelectValue placeholder="Manter subcategoria atual" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem :value="null">Manter subcategoria atual</SelectItem>
              <SelectItem
                v-for="subcategory in availableSubcategories"
                :key="subcategory.id"
                :value="String(subcategory.id)"
              >
                {{ subcategory.name }}
              </SelectItem>
            </SelectContent>
          </Select>
          <p v-if="!form.transaction_type" class="text-sm text-muted-foreground">
            Selecione um tipo de transação para escolher uma subcategoria
          </p>
        </div>

        <!-- Error Display -->
        <Alert v-if="error" variant="destructive">
          <ExclamationTriangleIcon class="h-4 w-4" />
          <AlertTitle>Erro ao atualizar transações</AlertTitle>
          <AlertDescription>{{ error }}</AlertDescription>
        </Alert>

        <DialogFooter class="gap-2">
          <Button type="button" variant="outline" :disabled="isSubmitting" @click="$emit('close')">
            Cancelar
          </Button>
          <Button type="submit" :disabled="isSubmitting || !hasChanges">
            <span v-if="isSubmitting" class="mr-2 inline-flex h-4 w-4 animate-spin rounded-full border-b-2 border-white"></span>
            {{ isSubmitting ? 'Atualizando...' : 'Atualizar' }}
          </Button>
        </DialogFooter>
      </form>
    </DialogContent>
  </Dialog>
</template>

<script setup lang="ts">
import { ExclamationTriangleIcon } from '@heroicons/vue/24/outline'
import type { TransactionType } from '~/types/transactions'
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
  selectedTransactionIds: number[]
}

const props = defineProps<Props>()

// Emits
const emit = defineEmits<{
  close: []
  saved: []
}>()

// Composables
const { 
  bulkUpdateTransactions,
  formatCurrency,
  clearError
} = useTransactions()

const { accounts, loadAccounts } = useAccounts()
const { creditCards, loadCreditCards } = useCreditCards()
const { loadSubcategories: loadSubcategoriesApi } = useSubcategories()

// Local state
const isSubmitting = ref(false)
const error = ref<string | null>(null)

// Form state
const form = ref<{
  transaction_type: TransactionType | null
  account_id: string | number | null
  credit_card_id: string | number | null
  subcategory_id: string | number | null
}>({
  transaction_type: null,
  account_id: null,
  credit_card_id: null,
  subcategory_id: null
})

// Computed
const selectedCount = computed(() => props.selectedTransactionIds.length)

const hasChanges = computed(() => {
  return form.value.transaction_type !== null ||
    form.value.account_id !== null ||
    form.value.credit_card_id !== null ||
    form.value.subcategory_id !== null
})

const availableSubcategories = ref<SubcategoryList[]>([])

// Methods
const handleAccountChange = () => {
  // Clear credit card when account is selected
  if (form.value.account_id !== null) {
    form.value.credit_card_id = null
  }
}

const handleCreditCardChange = () => {
  // Clear account when credit card is selected
  if (form.value.credit_card_id !== null) {
    form.value.account_id = null
  }
}

const loadSubcategories = async () => {
  if (!form.value.transaction_type) {
    availableSubcategories.value = []
    return
  }

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
}

const handleSubmit = async () => {
  if (!hasChanges.value) {
    error.value = 'Selecione pelo menos um campo para atualizar'
    return
  }

  isSubmitting.value = true
  error.value = null

  try {
    // Build bulk update request
    const updates = props.selectedTransactionIds.map(id => {
      const update: any = { id }
      
      if (form.value.transaction_type !== null) {
        update.transaction_type = form.value.transaction_type
      }
      
      if (form.value.account_id !== null) {
        update.account_id = form.value.account_id === '' ? null : Number(form.value.account_id)
      }
      
      if (form.value.credit_card_id !== null) {
        update.credit_card_id = form.value.credit_card_id === '' ? null : Number(form.value.credit_card_id)
      }
      
      if (form.value.subcategory_id !== null) {
        update.subcategory_id = form.value.subcategory_id === '' ? null : Number(form.value.subcategory_id)
      }
      
      return update
    })

    const result = await bulkUpdateTransactions({ transactions: updates })
    
    if (!result.success) {
      error.value = result.error?.message || 'Erro ao atualizar transações'
      return
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
  await Promise.all([
    loadAccounts(),
    loadCreditCards()
  ])
})

// Watch for transaction type changes to load subcategories
watch(() => form.value.transaction_type, () => {
  loadSubcategories()
  // Clear subcategory if transaction type changes
  if (form.value.transaction_type === null) {
    form.value.subcategory_id = null
  }
})
</script>

