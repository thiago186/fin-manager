<template>
  <div class="py-8">
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
      <!-- Header -->
      <div class="flex justify-between items-center mb-6">
        <div>
          <h1 class="text-3xl font-bold text-gray-900">Parcelamentos</h1>
          <p class="mt-1 text-sm text-gray-500">Acompanhe seus parcelamentos e parcelas geradas</p>
        </div>
      </div>

      <Alert v-if="error" variant="destructive" class="mb-4">
        <AlertTitle>Erro</AlertTitle>
        <AlertDescription>{{ error }}</AlertDescription>
      </Alert>

      <!-- Loading -->
      <div v-if="loading" class="space-y-4">
        <Skeleton v-for="n in 4" :key="n" class="h-20 w-full" />
      </div>

      <!-- Empty state -->
      <div v-else-if="installmentPlans.length === 0" class="text-center py-12">
        <div class="mx-auto h-12 w-12 text-gray-400">
          <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 10h18M7 15h1m4 0h1m-7 4h12a3 3 0 003-3V8a3 3 0 00-3-3H6a3 3 0 00-3 3v8a3 3 0 003 3z"></path>
          </svg>
        </div>
        <h3 class="mt-2 text-sm font-medium text-gray-900">Nenhum parcelamento encontrado</h3>
        <p class="mt-1 text-sm text-gray-500">Crie um parcelamento ao adicionar uma transação.</p>
      </div>

      <!-- Plans table -->
      <div v-else class="space-y-4">
        <Card
          v-for="plan in installmentPlans"
          :key="plan.id"
          class="hover:shadow-md transition-shadow"
        >
          <CardHeader class="pb-2">
            <div class="flex items-start justify-between gap-4">
              <div class="flex-1 min-w-0">
                <CardTitle class="text-base truncate">{{ plan.description || 'Sem descrição' }}</CardTitle>
                <div class="flex flex-wrap items-center gap-2 mt-1">
                  <Badge :variant="plan.transaction_type === 'INCOME' ? 'secondary' : 'destructive'">
                    {{ plan.transaction_type === 'INCOME' ? 'Receita' : plan.transaction_type === 'EXPENSE' ? 'Despesa' : 'Transferência' }}
                  </Badge>
                  <span class="text-sm text-gray-500">
                    {{ plan.installments_count }}x de {{ formatCurrency(plan.installment_amount) }}
                  </span>
                  <span class="text-sm text-gray-500">= {{ formatCurrency(plan.total_amount) }}</span>
                  <span class="text-sm text-gray-400">a partir de {{ formatDate(plan.first_due_date) }}</span>
                </div>
                <div class="flex flex-wrap gap-2 mt-1 text-xs text-gray-500">
                  <span v-if="plan.account">Conta: {{ plan.account.name }}</span>
                  <span v-if="plan.credit_card">Cartão: {{ plan.credit_card.name }}</span>
                  <span v-if="plan.category">Categoria: {{ plan.category.name }}</span>
                </div>
              </div>
              <div class="flex gap-2 shrink-0">
                <Button
                  variant="ghost"
                  size="sm"
                  @click="togglePlanTransactions(plan.id)"
                >
                  {{ expandedPlanId === plan.id ? 'Ocultar parcelas' : `Ver ${plan.transactions_count} parcelas` }}
                </Button>
                <Button
                  variant="ghost"
                  size="icon"
                  @click="handleDelete(plan)"
                  title="Excluir parcelamento"
                >
                  <svg class="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"></path>
                  </svg>
                </Button>
              </div>
            </div>
          </CardHeader>

          <!-- Transactions list for expanded plan -->
          <CardContent v-if="expandedPlanId === plan.id" class="pt-0">
            <div v-if="loadingTransactions" class="py-4 text-center text-sm text-gray-500">
              Carregando parcelas...
            </div>
            <div v-else-if="planTransactions.length > 0">
              <table class="w-full text-sm">
                <thead>
                  <tr class="border-b text-left text-gray-500">
                    <th class="py-2 pr-4">Parcela</th>
                    <th class="py-2 pr-4">Data</th>
                    <th class="py-2 pr-4">Valor</th>
                    <th class="py-2">Categoria</th>
                  </tr>
                </thead>
                <tbody>
                  <tr
                    v-for="txn in planTransactions"
                    :key="txn.id"
                    class="border-b last:border-0 hover:bg-gray-50"
                  >
                    <td class="py-2 pr-4 font-medium">
                      {{ txn.installment_number }}/{{ txn.installments_total }}
                    </td>
                    <td class="py-2 pr-4 text-gray-600">{{ formatDate(txn.occurred_at) }}</td>
                    <td class="py-2 pr-4">{{ formatCurrency(txn.amount) }}</td>
                    <td class="py-2 text-gray-600">{{ txn.subcategory?.name || txn.category?.name || '-' }}</td>
                  </tr>
                </tbody>
              </table>
            </div>
            <p v-else class="py-4 text-sm text-gray-500 text-center">Nenhuma parcela encontrada.</p>
          </CardContent>
        </Card>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import type { Transaction } from '~/types/transactions'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Skeleton } from '@/components/ui/skeleton'
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert'

definePageMeta({
  middleware: 'auth'
})

const {
  installmentPlans,
  loading,
  error,
  loadInstallmentPlans,
  deleteInstallmentPlan,
  loadPlanTransactions,
} = useInstallmentPlans()

const expandedPlanId = ref<number | null>(null)
const planTransactions = ref<Transaction[]>([])
const loadingTransactions = ref(false)

const formatCurrency = (value: string | number) => {
  return new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(Number(value))
}

const formatDate = (date: string) => {
  const [year, month, day] = date.split('-')
  return `${day}/${month}/${year}`
}

const togglePlanTransactions = async (planId: number) => {
  if (expandedPlanId.value === planId) {
    expandedPlanId.value = null
    planTransactions.value = []
    return
  }

  expandedPlanId.value = planId
  loadingTransactions.value = true

  const result = await loadPlanTransactions(planId)
  if (result.success && result.data) {
    planTransactions.value = result.data as Transaction[]
  } else {
    planTransactions.value = []
  }

  loadingTransactions.value = false
}

const handleDelete = async (plan: any) => {
  const label = plan.description || `parcelamento #${plan.id}`
  if (!confirm(`Tem certeza que deseja excluir o ${label} e todas as suas ${plan.installments_count} parcelas?`)) return
  await deleteInstallmentPlan(plan.id)
  if (expandedPlanId.value === plan.id) {
    expandedPlanId.value = null
    planTransactions.value = []
  }
}

onMounted(async () => {
  await loadInstallmentPlans()
})
</script>
