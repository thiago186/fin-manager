<template>
  <div v-if="insights.length > 0" class="mb-6">
    <div class="flex items-center gap-2 mb-3">
      <ChartPieIcon v-if="showAll" class="h-5 w-5 text-indigo-500" />
      <ExclamationTriangleIcon v-else class="h-5 w-5 text-amber-500" />
      <h2 class="text-sm font-semibold text-gray-900">
        {{ showAll ? 'Orçamentos do Mês' : 'Alertas de Orçamento' }}
      </h2>
    </div>
    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
      <Card
        v-for="insight in insights"
        :key="insight.category.id"
        :class="[
          'border-l-4',
          statusBorderClass(insight.status)
        ]"
      >
        <CardContent class="p-4">
          <div class="flex items-center justify-between mb-2">
            <span class="text-sm font-medium text-gray-900">
              {{ insight.category.name }}
            </span>
            <Badge :variant="statusBadgeVariant(insight.status)">
              {{ statusLabel(insight.status) }}
            </Badge>
          </div>

          <div class="mb-2">
            <div class="flex justify-between text-xs text-gray-500 mb-1">
              <span>{{ formatCurrency(insight.spent_amount) }}</span>
              <span>de {{ formatCurrency(insight.budget_amount) }}</span>
            </div>
            <div class="w-full bg-gray-200 rounded-full h-2">
              <div
                class="h-2 rounded-full transition-all duration-300"
                :class="statusProgressClass(insight.status)"
                :style="{ width: `${Math.min(insight.percentage, 100)}%` }"
              />
            </div>
          </div>

          <div class="text-xs text-gray-500">
            <span v-if="insight.status === 'over-budget'">
              Excedido em {{ formatCurrency(insight.remaining_amount.replace('-', '')) }}
            </span>
            <span v-else>
              Restante: {{ formatCurrency(insight.remaining_amount) }}
            </span>
            <span class="float-right font-medium" :class="statusTextClass(insight.status)">
              {{ insight.percentage.toFixed(0) }}%
            </span>
          </div>
        </CardContent>
      </Card>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ExclamationTriangleIcon, ChartPieIcon } from '@heroicons/vue/24/outline'
import { Card, CardContent } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import type { BudgetInsight } from '~/types/budgets'

const props = defineProps<{
  insights: readonly BudgetInsight[]
  showAll?: boolean
}>()

const statusBorderClass = (status: string): string => {
  switch (status) {
    case 'safe':
      return 'border-l-green-400'
    case 'warning':
      return 'border-l-yellow-400'
    case 'critical':
      return 'border-l-orange-500'
    case 'over-budget':
      return 'border-l-red-500'
    default:
      return 'border-l-gray-300'
  }
}

const statusBadgeVariant = (status: string): 'default' | 'secondary' | 'destructive' | 'outline' => {
  switch (status) {
    case 'safe':
      return 'outline'
    case 'warning':
      return 'secondary'
    case 'critical':
      return 'destructive'
    case 'over-budget':
      return 'destructive'
    default:
      return 'secondary'
  }
}

const statusProgressClass = (status: string): string => {
  switch (status) {
    case 'safe':
      return 'bg-green-400'
    case 'warning':
      return 'bg-yellow-400'
    case 'critical':
      return 'bg-orange-500'
    case 'over-budget':
      return 'bg-red-500'
    default:
      return 'bg-gray-400'
  }
}

const statusTextClass = (status: string): string => {
  switch (status) {
    case 'safe':
      return 'text-green-600'
    case 'warning':
      return 'text-yellow-600'
    case 'critical':
      return 'text-orange-600'
    case 'over-budget':
      return 'text-red-600'
    default:
      return 'text-gray-600'
  }
}

const statusLabel = (status: string): string => {
  switch (status) {
    case 'safe':
      return 'Dentro do limite'
    case 'warning':
      return 'Atenção'
    case 'critical':
      return 'Crítico'
    case 'over-budget':
      return 'Estourado'
    default:
      return status
  }
}

const formatCurrency = (amount: string): string => {
  return new Intl.NumberFormat('pt-BR', {
    style: 'currency',
    currency: 'BRL'
  }).format(parseFloat(amount))
}
</script>
