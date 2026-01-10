<template>
  <Dialog :open="true" @update:open="(open) => !open && $emit('close')">
    <DialogContent class="sm:max-w-lg">
      <DialogHeader>
        <DialogTitle>{{ isEdit ? 'Editar Conta' : 'Nova Conta' }}</DialogTitle>
        <DialogDescription>
          Informe os dados da conta bancária.
        </DialogDescription>
      </DialogHeader>

      <form @submit.prevent="handleSubmit" class="space-y-5">
        <div class="space-y-2">
          <Label>Nome da Conta *</Label>
          <Input
            v-model="form.name"
            type="text"
            required
            placeholder="Ex: Conta Corrente Banco X"
          />
        </div>

        <div class="space-y-2">
          <Label>Saldo Atual *</Label>T
          <div class="relative">
            <span class="absolute inset-y-0 left-3 flex items-center text-sm text-muted-foreground">R$</span>
            <Input
              v-model="form.current_balance"
              type="number"
              step="0.01"
              required
              placeholder="0,00"
              class="pl-10"
            />
          </div>
        </div>

        <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div class="space-y-2">
            <Label>Tipo de Conta *</Label>
            <Select v-model="form.account_type" required>
              <SelectTrigger>
                <SelectValue placeholder="Selecione o tipo" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="checking">Conta Corrente</SelectItem>
              </SelectContent>
            </Select>
          </div>

          <div class="space-y-2">
            <Label>Moeda *</Label>
            <Select v-model="form.currency" required>
              <SelectTrigger>
                <SelectValue placeholder="Selecione a moeda" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="BRL">Real Brasileiro (BRL)</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </div>

        <div class="flex items-center gap-2">
          <Checkbox v-model:checked="form.is_active" />
          <Label class="text-sm">Conta ativa</Label>
        </div>

        <Alert v-if="error" variant="destructive">
          <ExclamationTriangleIcon class="h-4 w-4" />
          <AlertTitle>Erro ao salvar conta</AlertTitle>
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
import type { Account, AccountForm } from '~/types/accounts'
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
import { Checkbox } from '@/components/ui/checkbox'
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert'

// Props
interface Props {
  account?: Account | null
  isEdit?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  account: null,
  isEdit: false
})

// Emits
const emit = defineEmits<{
  close: []
  saved: []
}>()

// Composables
const { 
  createAccount, 
  updateAccount, 
  formatAccountData,
  clearError
} = useAccounts()

// Local state
const isSubmitting = ref(false)
const error = ref<string | null>(null)

// Form state
const form = ref<AccountForm>({
  name: '',
  current_balance: '',
  account_type: 'checking',
  currency: 'BRL',
  is_active: true
})

// Methods
const initializeForm = () => {
  if (props.account && props.isEdit) {
    form.value = {
      name: props.account.name,
      current_balance: props.account.current_balance,
      account_type: props.account.account_type,
      currency: props.account.currency,
      is_active: props.account.is_active
    }
  } else {
    form.value = {
      name: '',
      current_balance: '',
      account_type: 'checking',
      currency: 'BRL',
      is_active: true
    }
  }
}

const handleSubmit = async () => {
  isSubmitting.value = true
  error.value = null

  try {
    const accountData = formatAccountData(form.value)
    
    if (props.isEdit && props.account) {
      const result = await updateAccount(props.account.id, accountData)
      if (!result.success) {
        error.value = result.error?.message || 'Erro ao atualizar conta'
        return
      }
    } else {
      const result = await createAccount(accountData)
      if (!result.success) {
        error.value = result.error?.message || 'Erro ao criar conta'
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
onMounted(() => {
  initializeForm()
})
</script> 