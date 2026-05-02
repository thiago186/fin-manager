<template>
  <div class="py-8">
    <!-- Page Header -->
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 mb-6">
      <h1 class="text-3xl font-bold text-gray-900">Gráficos</h1>
      <p class="mt-1 text-sm text-gray-500">Visualize despesas por categoria ao longo do ano</p>
    </div>

    <!-- Error State -->
    <div v-if="error" class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 mb-6">
      <Alert variant="destructive">
        <AlertTitle>Erro</AlertTitle>
        <AlertDescription>{{ error }}</AlertDescription>
      </Alert>
    </div>

    <!-- Loading State -->
    <div v-if="loading" class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
      <div class="space-y-4">
        <Skeleton class="h-8 w-48" />
        <Skeleton class="h-[520px] w-full" />
      </div>
    </div>

    <!-- Content -->
    <div v-else-if="data && data.categories.length > 0" class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
      <Card>
        <CardHeader class="flex flex-row items-center justify-between gap-4 flex-wrap">
          <CardTitle class="text-base">
            Despesas por Categoria — {{ selectedYear }}
          </CardTitle>
          <div class="flex items-center gap-2">
            <!-- Category filter popover -->
            <PopoverRoot>
              <PopoverTrigger as-child>
                <Button size="sm" variant="outline" class="gap-1.5">
                  <SlidersHorizontal class="w-3.5 h-3.5" />
                  Categorias
                  <span class="text-xs text-muted-foreground">
                    ({{ activeCount }}/{{ data.categories.length }})
                  </span>
                </Button>
              </PopoverTrigger>
              <PopoverPortal>
                <PopoverContent
                  class="z-50 w-64 rounded-lg border bg-popover p-4 shadow-md outline-none"
                  :side-offset="6"
                  align="end"
                >
                  <div class="flex items-center gap-2 mb-3 pb-3 border-b">
                    <Checkbox
                      :model-value="allSelected"
                      @update:model-value="toggleAll"
                      id="select-all"
                    />
                    <Label for="select-all" class="text-sm font-medium cursor-pointer">
                      {{ allSelected ? 'Desmarcar todas' : 'Selecionar todas' }}
                    </Label>
                  </div>
                  <div class="space-y-2.5 max-h-72 overflow-y-auto pr-1">
                    <div
                      v-for="category in data.categories"
                      :key="category.id"
                      class="flex items-center gap-2"
                    >
                      <Checkbox
                        :id="`cat-${category.id}`"
                        :model-value="selectedCategories[category.id]"
                        @update:model-value="(val) => toggleCategory(category.id, val)"
                      />
                      <Label
                        :for="`cat-${category.id}`"
                        class="text-sm cursor-pointer flex items-center gap-2"
                      >
                        <span
                          class="inline-block w-3 h-3 rounded-full flex-shrink-0"
                          :style="{ backgroundColor: categoryColors[category.id] }"
                        />
                        {{ category.name }}
                      </Label>
                    </div>
                  </div>
                </PopoverContent>
              </PopoverPortal>
            </PopoverRoot>

            <Button size="sm" variant="outline" @click="stacked = !stacked">
              {{ stacked ? 'Ver agrupado' : 'Ver empilhado' }}
            </Button>

            <Select v-model="selectedYear">
              <SelectTrigger class="w-28 h-9 text-sm">
                <SelectValue :placeholder="String(currentYear)" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem
                  v-for="year in availableYears"
                  :key="year"
                  :value="String(year)"
                >
                  {{ year }}
                </SelectItem>
              </SelectContent>
            </Select>
          </div>
        </CardHeader>
        <CardContent>
          <div class="relative h-[520px] w-full">
            <Bar :data="chartData" :options="chartOptions" />
          </div>
        </CardContent>
      </Card>
    </div>

    <!-- Empty State -->
    <div v-else class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
      <div class="text-center py-12">
        <p class="text-gray-500 text-lg">Nenhuma despesa encontrada para o ano selecionado.</p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted } from 'vue'
import { Bar } from 'vue-chartjs'
import {
  Chart as ChartJS,
  Title,
  Tooltip,
  Legend,
  BarElement,
  CategoryScale,
  LinearScale,
  type ChartData,
  type ChartOptions
} from 'chart.js'
import { PopoverRoot, PopoverTrigger, PopoverContent, PopoverPortal } from 'reka-ui'
import { SlidersHorizontal } from 'lucide-vue-next'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue
} from '@/components/ui/select'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Checkbox } from '@/components/ui/checkbox'
import { Label } from '@/components/ui/label'
import { Alert, AlertTitle, AlertDescription } from '@/components/ui/alert'
import { Skeleton } from '@/components/ui/skeleton'
import { Button } from '@/components/ui/button'

definePageMeta({ middleware: 'auth' })

ChartJS.register(Title, Tooltip, Legend, BarElement, CategoryScale, LinearScale)

const { data, loading, error, loadMonthlyByCategory } = useGraphs()

const currentYear = new Date().getFullYear()
const selectedYear = ref(String(currentYear))
const selectedCategories = ref<Record<number, boolean>>({})
const stacked = ref(true)

const availableYears = Array.from({ length: 5 }, (_, i) => currentYear - i)

const monthLabels = [
  'Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun',
  'Jul', 'Ago', 'Set', 'Out', 'Nov', 'Dez'
]

const PALETTE = [
  '#3b82f6', '#ef4444', '#10b981', '#f59e0b', '#8b5cf6',
  '#ec4899', '#14b8a6', '#f97316', '#6366f1', '#84cc16',
  '#06b6d4', '#e11d48', '#7c3aed', '#059669', '#dc2626'
]

const categoryColors = computed<Record<number, string>>(() => {
  if (!data.value) return {}
  const map: Record<number, string> = {}
  data.value.categories.forEach((cat, index) => {
    map[cat.id] = PALETTE[index % PALETTE.length]
  })
  return map
})

const allSelected = computed(() => {
  if (!data.value || data.value.categories.length === 0) return false
  return data.value.categories.every((cat) => selectedCategories.value[cat.id])
})

const activeCount = computed(() => {
  if (!data.value) return 0
  return data.value.categories.filter((cat) => selectedCategories.value[cat.id]).length
})

function toggleAll(value: boolean | 'indeterminate') {
  if (!data.value) return
  const next: Record<number, boolean> = {}
  for (const cat of data.value.categories) {
    next[cat.id] = value === true
  }
  selectedCategories.value = next
}

function toggleCategory(id: number, value: boolean | 'indeterminate') {
  selectedCategories.value = { ...selectedCategories.value, [id]: value === true }
}

const chartData = computed<ChartData<'bar'>>(() => {
  if (!data.value) return { labels: [], datasets: [] }

  const datasets = data.value.categories
    .filter((cat) => selectedCategories.value[cat.id])
    .map((cat) => ({
      label: cat.name,
      data: Array.from({ length: 12 }, (_, i) => {
        const val = cat.monthly_totals[String(i + 1)]
        return val ? parseFloat(val) : 0
      }),
      backgroundColor: categoryColors.value[cat.id],
      borderColor: categoryColors.value[cat.id],
      borderWidth: 1,
      borderRadius: stacked.value ? 0 : 4,
      maxBarThickness: stacked.value ? undefined : 20
    }))

  return { labels: monthLabels, datasets }
})

const chartOptions = computed<ChartOptions<'bar'>>(() => ({
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    legend: {
      display: stacked.value,
      position: 'bottom',
      labels: {
        boxWidth: 12,
        padding: 16
      }
    },
    tooltip: {
      mode: 'index',
      intersect: false,
      callbacks: {
        label: (context) => {
          const value = context.parsed.y as number
          if (value === 0) return null as any
          return `${context.dataset.label}: ${formatCurrency(value)}`
        }
      }
    }
  },
  scales: {
    x: {
      stacked: stacked.value,
      grid: { display: false }
    },
    y: {
      stacked: stacked.value,
      beginAtZero: true,
      ticks: {
        callback: (value) => formatCurrency(Number(value))
      }
    }
  },
  interaction: {
    mode: 'index',
    intersect: false
  }
}))

function formatCurrency(value: number): string {
  return new Intl.NumberFormat('pt-BR', {
    style: 'currency',
    currency: 'BRL'
  }).format(value)
}

watch(selectedYear, async (year) => {
  if (year) {
    await loadMonthlyByCategory(Number(year))
    if (data.value) {
      const next: Record<number, boolean> = {}
      for (const cat of data.value.categories) {
        next[cat.id] = true
      }
      selectedCategories.value = next
    }
  }
})

onMounted(async () => {
  await loadMonthlyByCategory(Number(selectedYear.value))
  if (data.value) {
    const next: Record<number, boolean> = {}
    for (const cat of data.value.categories) {
      next[cat.id] = true
    }
    selectedCategories.value = next
  }
})
</script>
