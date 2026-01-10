<template>
  <div class="py-8">
    <!-- Page Header -->
    <div class="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 mb-6">
      <div class="flex items-center justify-between">
        <div class="flex items-center">
          <NuxtLink
            to="/cash-flow"
            class="inline-flex items-center text-sm font-medium text-gray-700 hover:text-gray-900 mr-4"
          >
            <ArrowLeftIcon class="h-4 w-4 mr-2" />
            Voltar
          </NuxtLink>
          <div>
            <h1 class="text-3xl font-bold text-gray-900">Nova Visualização</h1>
            <p class="mt-1 text-sm text-gray-500">
              Configure sua visualização de fluxo de caixa
            </p>
          </div>
        </div>
      </div>
    </div>

    <!-- Form Content -->
    <div class="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
      <form @submit.prevent="handleSubmit" class="space-y-8">
        <!-- Error Alert -->
        <Alert v-if="error" variant="destructive">
          <ExclamationTriangleIcon class="h-4 w-4" />
          <AlertTitle>Erro</AlertTitle>
          <AlertDescription>{{ error }}</AlertDescription>
        </Alert>

        <!-- Cash Flow Name Section -->
        <Card>
          <CardHeader>
            <CardTitle>Informações Básicas</CardTitle>
            <CardDescription>
              Defina o nome da sua visualização de fluxo de caixa
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div class="space-y-2">
              <Label for="name">Nome da Visualização *</Label>
              <Input
                id="name"
                v-model="form.name"
                type="text"
                placeholder="Ex: Fluxo de Caixa Mensal"
                required
                maxlength="100"
              />
            </div>
          </CardContent>
        </Card>

        <!-- Groups Section -->
        <Card>
          <CardHeader>
            <div class="flex items-center justify-between">
              <div>
                <CardTitle>Grupos</CardTitle>
                <CardDescription>
                  Crie grupos para organizar suas categorias. Cada grupo agrupará valores de categorias específicas.
                </CardDescription>
              </div>
              <Button type="button" variant="outline" size="sm" @click="addGroup">
                <PlusIcon class="h-4 w-4 mr-2" />
                Adicionar Grupo
              </Button>
            </div>
          </CardHeader>
          <CardContent>
            <div v-if="form.groups.length === 0" class="text-center py-8 text-gray-500">
              <FolderIcon class="h-12 w-12 mx-auto text-gray-400 mb-2" />
              <p>Nenhum grupo criado</p>
              <p class="text-sm">Clique em "Adicionar Grupo" para começar</p>
            </div>

            <div v-else class="space-y-6">
              <div
                v-for="(group, groupIndex) in form.groups"
                :key="groupIndex"
                class="border border-gray-200 rounded-lg p-4 bg-gray-50"
              >
                <div class="flex items-start justify-between mb-4">
                  <div class="flex items-center">
                    <span class="inline-flex items-center justify-center h-6 w-6 rounded-full bg-indigo-100 text-indigo-600 text-sm font-medium mr-3">
                      {{ groupIndex + 1 }}
                    </span>
                    <span class="text-sm font-medium text-gray-700">Grupo {{ groupIndex + 1 }}</span>
                  </div>
                  <Button
                    type="button"
                    variant="ghost"
                    size="sm"
                    class="text-red-600 hover:text-red-700 hover:bg-red-50"
                    @click="removeGroup(groupIndex)"
                  >
                    <TrashIcon class="h-4 w-4" />
                  </Button>
                </div>

                <div class="space-y-4">
                  <!-- Group Name -->
                  <div class="space-y-2">
                    <Label :for="`group-name-${groupIndex}`">Nome do Grupo *</Label>
                    <Input
                      :id="`group-name-${groupIndex}`"
                      v-model="group.name"
                      type="text"
                      placeholder="Ex: Receitas, Despesas Operacionais"
                      required
                      maxlength="100"
                    />
                  </div>

                  <!-- Category Selection -->
                  <div class="space-y-2">
                    <Label>Categorias *</Label>
                    <p class="text-sm text-gray-500 mb-2">
                      Selecione as categorias que pertencem a este grupo
                    </p>
                    
                    <div v-if="categoriesLoading" class="text-sm text-gray-500">
                      Carregando categorias...
                    </div>
                    
                    <div v-else-if="categories.length === 0" class="text-sm text-gray-500">
                      Nenhuma categoria disponível
                    </div>
                    
                    <div v-else class="grid grid-cols-2 md:grid-cols-3 gap-2 max-h-48 overflow-y-auto p-2 border rounded-md bg-white">
                      <div
                        v-for="category in categories"
                        :key="`group-${groupIndex}-cat-${category.id}`"
                        class="flex items-center space-x-2"
                      >
                        <Checkbox
                          :key="`checkbox-${groupIndex}-${category.id}`"
                          :id="`group-${groupIndex}-cat-${category.id}`"
                          :model-value="isCategorySelected(groupIndex, category.id)"
                          @update:model-value="(checked: boolean | 'indeterminate') => toggleCategory(groupIndex, category.id, checked === true)"
                        />
                        <Label
                          :for="`group-${groupIndex}-cat-${category.id}`"
                          class="text-sm font-normal cursor-pointer flex-1"
                        >
                          {{ category.name }}
                          <span
                            :class="[
                              'ml-1 text-xs',
                              category.transaction_type === 'income' ? 'text-green-600' : 'text-red-600'
                            ]"
                          >
                            ({{ category.transaction_type === 'income' ? 'Receita' : 'Despesa' }})
                          </span>
                        </Label>
                      </div>
                    </div>
                    
                    <p v-if="group.category_ids.length > 0" class="text-sm text-gray-600 mt-1">
                      {{ group.category_ids.length }} categoria(s) selecionada(s)
                    </p>
                  </div>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>

        <!-- Results Section -->
        <Card>
          <CardHeader>
            <div class="flex items-center justify-between">
              <div>
                <CardTitle>Linhas de Resultado</CardTitle>
                <CardDescription>
                  Defina linhas de resultado que calcularão totais entre os grupos.
                </CardDescription>
              </div>
              <Button type="button" variant="outline" size="sm" @click="addResult">
                <PlusIcon class="h-4 w-4 mr-2" />
                Adicionar Resultado
              </Button>
            </div>
          </CardHeader>
          <CardContent>
            <div v-if="form.results.length === 0" class="text-center py-8 text-gray-500">
              <CalculatorIcon class="h-12 w-12 mx-auto text-gray-400 mb-2" />
              <p>Nenhuma linha de resultado criada</p>
              <p class="text-sm">Clique em "Adicionar Resultado" para começar</p>
            </div>

            <div v-else class="space-y-4">
              <div
                v-for="(result, resultIndex) in form.results"
                :key="resultIndex"
                class="flex items-center gap-4 border border-gray-200 rounded-lg p-4 bg-gray-50"
              >
                <span class="inline-flex items-center justify-center h-6 w-6 rounded-full bg-emerald-100 text-emerald-600 text-sm font-medium">
                  {{ resultIndex + 1 }}
                </span>
                
                <div class="flex-1">
                  <Input
                    v-model="result.name"
                    type="text"
                    placeholder="Ex: Lucro Bruto, Resultado Operacional"
                    required
                    maxlength="100"
                  />
                </div>
                
                <Button
                  type="button"
                  variant="ghost"
                  size="sm"
                  class="text-red-600 hover:text-red-700 hover:bg-red-50"
                  @click="removeResult(resultIndex)"
                >
                  <TrashIcon class="h-4 w-4" />
                </Button>
              </div>
            </div>
          </CardContent>
        </Card>

        <!-- Position Information -->
        <Card>
          <CardHeader>
            <CardTitle>Ordem de Exibição</CardTitle>
            <CardDescription>
              A ordem dos itens no relatório segue a ordem em que foram adicionados. Grupos e resultados serão intercalados conforme a posição.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div v-if="orderedItems.length === 0" class="text-center py-4 text-gray-500">
              <p>Adicione grupos e resultados para visualizar a ordem</p>
            </div>
            <div v-else class="space-y-2">
              <div
                v-for="(item, index) in orderedItems"
                :key="`${item.type}-${index}`"
                class="flex items-center gap-3 p-2 rounded-md"
                :class="item.type === 'group' ? 'bg-indigo-50' : 'bg-emerald-50'"
              >
                <span class="text-sm font-medium text-gray-600">{{ index + 1 }}.</span>
                <span
                  :class="[
                    'text-xs px-2 py-0.5 rounded-full',
                    item.type === 'group' ? 'bg-indigo-100 text-indigo-700' : 'bg-emerald-100 text-emerald-700'
                  ]"
                >
                  {{ item.type === 'group' ? 'Grupo' : 'Resultado' }}
                </span>
                <span class="text-sm text-gray-900">{{ item.name || '(sem nome)' }}</span>
              </div>
            </div>
          </CardContent>
        </Card>

        <!-- Submit Button -->
        <div class="flex flex-col items-end gap-4">
          <!-- Category Selection Warning -->
          <Alert v-if="categorySelectionWarning" variant="default" class="w-full max-w-md">
            <ExclamationTriangleIcon class="h-4 w-4" />
            <AlertTitle>Atenção</AlertTitle>
            <AlertDescription>
              {{ categorySelectionWarning.message }}
              <span class="block mt-1 text-xs text-gray-600">
                Total de categorias selecionadas: {{ categorySelectionWarning.selectedCount }} / {{ categorySelectionWarning.totalCount }}
              </span>
            </AlertDescription>
          </Alert>
          
          <div class="flex justify-end gap-4">
            <NuxtLink to="/cash-flow">
              <Button type="button" variant="outline">
                Cancelar
              </Button>
            </NuxtLink>
            <Button 
              type="submit" 
              :disabled="isSubmitting || !isFormValid"
              @click="handleSubmit"
            >
              <span v-if="isSubmitting" class="flex items-center">
                <svg class="animate-spin -ml-1 mr-2 h-4 w-4" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                  <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                  <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                Salvando...
              </span>
              <span v-else>Criar Visualização</span>
            </Button>
          </div>
        </div>
        
        <!-- Validation Help Text -->
        <div v-if="!isFormValid && (form.name || form.groups.length > 0 || form.results.length > 0)" class="text-sm text-gray-500 text-right space-y-1">
          <p v-if="!form.name.trim()" class="text-red-600">Nome da visualização é obrigatório</p>
          <p v-else-if="form.groups.length === 0" class="text-red-600">Adicione pelo menos um grupo</p>
          <template v-else>
            <template v-for="(group, idx) in form.groups" :key="`group-${idx}`">
              <p v-if="!group.name.trim()" class="text-red-600">
                Grupo {{ idx + 1 }} precisa de um nome
              </p>
              <p v-else-if="group.category_ids.length === 0" class="text-red-600">
                Grupo {{ idx + 1 }} precisa de pelo menos uma categoria
              </p>
            </template>
            <template v-for="(result, idx) in form.results" :key="`result-${idx}`">
              <p v-if="!result.name.trim()" class="text-red-600">
                Resultado {{ idx + 1 }} precisa de um nome
              </p>
            </template>
          </template>
        </div>
      </form>
    </div>
  </div>
</template>

<script setup lang="ts">
import {
  ArrowLeftIcon,
  PlusIcon,
  TrashIcon,
  ExclamationTriangleIcon,
  FolderIcon,
  CalculatorIcon
} from '@heroicons/vue/24/outline'
import type { CashFlowViewForm, CashFlowGroupForm, CashFlowResultForm } from '~/types/cashFlowViews'
import { Checkbox } from '@/components/ui/checkbox'
import { Label } from '@/components/ui/label'

// Page metadata
definePageMeta({
  middleware: 'auth'
})

// Composables
const router = useRouter()
const { createCashFlowView, formatViewData } = useCashFlowViews()
const { categories, loading: categoriesLoading, loadCategories } = useCategories()

// Form state
const form = ref<CashFlowViewForm>({
  name: '',
  groups: [],
  results: []
})

// UI state
const isSubmitting = ref(false)
const error = ref<string | null>(null)

// Position counter - tracks next position for groups and results
const nextPosition = ref(0)

// Computed: ordered items for preview
const orderedItems = computed(() => {
  const items: Array<{ type: 'group' | 'result'; name: string; position: number }> = []
  
  form.value.groups.forEach(g => {
    items.push({ type: 'group', name: g.name, position: g.position })
  })
  
  form.value.results.forEach(r => {
    items.push({ type: 'result', name: r.name, position: r.position })
  })
  
  return items.sort((a, b) => a.position - b.position)
})

// Computed: form validation
const isFormValid = computed(() => {
  // Name is required
  if (!form.value.name.trim()) {
    console.log('Validation failed: name is empty')
    return false
  }
  
  // At least one group is required
  if (form.value.groups.length === 0) {
    console.log('Validation failed: no groups')
    return false
  }
  
  // Each group must have a name and at least one category
  for (let i = 0; i < form.value.groups.length; i++) {
    const group = form.value.groups[i]
    if (!group.name.trim()) {
      console.log(`Validation failed: group ${i} has no name`)
      return false
    }
    console.log(`Group ${i} (${group.name}): ${group.category_ids.length} categories`, group.category_ids)
    if (group.category_ids.length === 0) {
      console.log(`Validation failed: group ${i} has no categories`)
      return false
    }
  }
  
  // Each result must have a name
  for (let i = 0; i < form.value.results.length; i++) {
    const result = form.value.results[i]
    if (!result.name.trim()) {
      console.log(`Validation failed: result ${i} has no name`)
      return false
    }
  }
  
  console.log('Form is valid!')
  return true
})

// Computed: check if all categories are selected across all groups
const categorySelectionWarning = computed(() => {
  if (categories.value.length === 0 || form.value.groups.length === 0) {
    return null
  }
  
  // Count total category selections (including duplicates)
  const totalSelected = form.value.groups.reduce((sum, group) => sum + group.category_ids.length, 0)
  
  // Get total categories in database
  const totalCategories = categories.value.length
  
  // Simple comparison
  if (totalSelected > totalCategories) {
    return {
      message: 'Você provavelmente selecionou categorias duplicadas em múltiplos grupos.',
      selectedCount: totalSelected,
      totalCount: totalCategories
    }
  } else if (totalSelected < totalCategories) {
    return {
      message: 'Você provavelmente esqueceu de selecionar algumas categorias.',
      selectedCount: totalSelected,
      totalCount: totalCategories
    }
  }
  
  return null
})

// Helper function to check if a category is selected in a group
// Normalizes IDs to numbers to handle potential type mismatches
// Made reactive by accessing form.value directly
const isCategorySelected = (groupIndex: number, categoryId: number): boolean => {
  const group = form.value.groups[groupIndex]
  if (!group) {
    return false
  }
  const normalizedCategoryId = Number(categoryId)
  const isSelected = group.category_ids.some(id => Number(id) === normalizedCategoryId)
  
  return isSelected
}

// Methods
const addGroup = () => {
  const newGroup: CashFlowGroupForm = {
    name: '',
    position: nextPosition.value++,
    category_ids: []
  }
  form.value.groups.push(newGroup)
}

const removeGroup = (index: number) => {
  form.value.groups.splice(index, 1)
}

const toggleCategory = (groupIndex: number, categoryId: number, checked: boolean) => {
  const group = form.value.groups[groupIndex]
  if (!group) {
    console.error('Group not found at index:', groupIndex)
    return
  }
  
  // Find category name for logging
  const category = categories.value.find(c => c.id === categoryId)
  const categoryName = category?.name || `ID: ${categoryId}`
  const action = checked ? 'SELECTED' : 'UNSELECTED'
  
  console.log(`[CATEGORY ${action}] Group ${groupIndex + 1} (${group.name || 'unnamed'}) - Category: ${categoryName} (ID: ${categoryId})`)
  console.log('toggleCategory called:', { groupIndex, categoryId, checked, currentIds: [...group.category_ids] })
  
  // Normalize category IDs to numbers for comparison
  const normalizedCategoryId = Number(categoryId)
  
  // Create a new array to ensure reactivity, normalizing all IDs to numbers
  const newCategoryIds = group.category_ids.map(id => Number(id))
  
  if (checked) {
    if (!newCategoryIds.includes(normalizedCategoryId)) {
      newCategoryIds.push(normalizedCategoryId)
      console.log(`✅ Category ADDED to group. New category_ids:`, newCategoryIds)
    } else {
      console.log(`⚠️ Category already in group, no change needed`)
    }
  } else {
    const idx = newCategoryIds.indexOf(normalizedCategoryId)
    if (idx > -1) {
      newCategoryIds.splice(idx, 1)
      console.log(`❌ Category REMOVED from group. New category_ids:`, newCategoryIds)
    } else {
      console.log(`⚠️ Category not in group, no change needed`)
    }
  }
  
  // Update the group with new array to ensure reactivity
  group.category_ids = newCategoryIds
  
  console.log('Form state after toggle - group category_ids:', group.category_ids)
  console.log('Form validation state:', isFormValid.value)
  console.log('---')
}

const addResult = () => {
  const newResult: CashFlowResultForm = {
    name: '',
    position: nextPosition.value++
  }
  form.value.results.push(newResult)
}

const removeResult = (index: number) => {
  form.value.results.splice(index, 1)
}

const handleSubmit = async (e?: Event) => {
  if (e) {
    e.preventDefault()
  }
  
  console.log('handleSubmit called', { isFormValid: isFormValid.value, form: form.value })
  
  if (!isFormValid.value) {
    error.value = 'Por favor, preencha todos os campos obrigatórios'
    console.log('Form validation failed')
    return
  }
  
  isSubmitting.value = true
  error.value = null
  
  try {
    // Format form data for API - ensure category_ids are numbers
    const requestData = formatViewData(form.value)
    
    // Ensure all category_ids are integers
    requestData.groups = requestData.groups.map(group => ({
      ...group,
      category_ids: group.category_ids.map(id => Number(id))
    }))
    
    console.log('Submitting request:', requestData)
    
    const result = await createCashFlowView(requestData)
    
    if (result.success) {
      // Navigate back to cash flow list
      router.push('/cash-flow')
    } else {
      error.value = result.error?.message || 'Erro ao criar visualização'
      console.error('API error:', result.error)
    }
  } catch (err: any) {
    error.value = err?.message || 'Erro desconhecido ao criar visualização'
    console.error('Error creating cash flow view:', err)
  } finally {
    isSubmitting.value = false
  }
}

// Watch form changes for debugging
watch(() => form.value, (newForm) => {
  console.log('Form changed:', {
    name: newForm.name,
    groupsCount: newForm.groups.length,
    groups: newForm.groups.map(g => ({
      name: g.name,
      categoryCount: g.category_ids.length,
      categoryIds: g.category_ids
    })),
    resultsCount: newForm.results.length,
    isValid: isFormValid.value
  })
}, { deep: true })

// Initialize
onMounted(async () => {
  await loadCategories()
})
</script>
