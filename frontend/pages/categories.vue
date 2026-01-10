<template>
  <div class="py-8">
    <!-- Categories Section -->
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 mb-12">
      <!-- Section Header -->
      <div class="flex justify-between items-center mb-6">
        <div>
          <h1 class="text-3xl font-bold text-gray-900">Categories</h1>
          <p class="mt-1 text-sm text-gray-500">Manage your income and expense categories</p>
        </div>
        <ButtonGroup>
          <Button @click="openCreateCategoryModal('income')">
            Receita
          </Button>
          <ButtonGroupSeparator />
          <Button @click="openCreateCategoryModal('expense')">
            Despesa
          </Button>
        </ButtonGroup>
      </div>

      <!-- Filters -->
      <Card class="mb-6">
        <CardHeader>
          <CardTitle class="text-base">Filters</CardTitle>
          <CardDescription>Refine the categories list.</CardDescription>
        </CardHeader>
        <CardContent class="grid gap-4 md:grid-cols-[1fr_auto]">
          <div class="space-y-2">
            <Label>Transaction Type</Label>
            <Select v-model="categoryFilters.transaction_type" @update:model-value="handleLoadCategories">
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
            <Button variant="outline" @click="handleLoadCategories">
              Refresh
            </Button>
          </div>
        </CardContent>
      </Card>

      <Alert v-if="categoriesError" variant="destructive" class="mb-4">
        <AlertTitle>Erro ao carregar categorias</AlertTitle>
        <AlertDescription>{{ categoriesError }}</AlertDescription>
      </Alert>

      <!-- Loading State -->
      <div v-if="categoriesLoading" class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        <Skeleton v-for="n in 3" :key="`cat-skel-${n}`" class="h-32 w-full" />
      </div>

      <!-- Categories Grid -->
      <div v-else-if="categories.length > 0" class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        <Card
          v-for="category in categories"
          :key="category.id"
          class="hover:shadow-md transition-shadow"
        >
          <CardHeader class="pb-3 flex flex-row items-start justify-between gap-2">
            <div>
              <CardTitle class="text-lg">{{ category.name }}</CardTitle>
              <CardDescription class="flex items-center gap-2 mt-2">
                <Badge :variant="category.transaction_type === 'income' ? 'secondary' : 'destructive'">
                  {{ category.transaction_type }}
                </Badge>
                <Badge v-if="!category.is_active" variant="outline">Inactive</Badge>
              </CardDescription>
            </div>
            <div class="flex gap-2">
              <Button variant="ghost" size="icon" @click="editCategory(category)" title="Edit category">
                <svg class="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z"></path>
                </svg>
              </Button>
              <Button variant="ghost" size="icon" @click="handleDeleteCategory(category)" title="Delete category">
                <svg class="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"></path>
                </svg>
              </Button>
            </div>
          </CardHeader>
          <CardContent class="text-sm text-gray-600">
            Created: {{ formatDate(category.created_at) }}
          </CardContent>
        </Card>
      </div>

      <!-- Empty State -->
      <div v-else class="text-center py-12">
        <div class="mx-auto h-12 w-12 text-gray-400">
          <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10"></path>
          </svg>
        </div>
        <h3 class="mt-2 text-sm font-medium text-gray-900">No categories found</h3>
        <p class="mt-1 text-sm text-gray-500">Get started by creating a new category.</p>
        <div class="mt-6">
          <ButtonGroup>
            <Button @click="openCreateCategoryModal('income')">
              Receita
            </Button>
            <ButtonGroupSeparator />
            <Button @click="openCreateCategoryModal('expense')">
              Despesa
            </Button>
          </ButtonGroup>
        </div>
      </div>
    </div>

    <!-- Subcategories Section -->
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
      <!-- Section Header -->
      <div class="flex justify-between items-center mb-6">
        <div>
          <h2 class="text-3xl font-bold text-gray-900">Subcategories</h2>
          <p class="mt-1 text-sm text-gray-500">Manage subcategories for your categories</p>
        </div>
        <Button @click="showCreateSubcategoryModal = true">
          <svg class="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4"></path>
          </svg>
          Add Subcategory
        </Button>
      </div>

      <!-- Filters -->
      <Card class="mb-6">
        <CardHeader>
          <CardTitle class="text-base">Filters</CardTitle>
          <CardDescription>Refine the subcategories list.</CardDescription>
        </CardHeader>
        <CardContent class="grid gap-4 md:grid-cols-[1fr_auto]">
          <div class="space-y-2">
            <Label>Category</Label>
            <Select v-model="subcategoryFilters.category" @update:model-value="handleLoadSubcategories">
              <SelectTrigger>
                <SelectValue placeholder="All Categories" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem :value="null">All Categories</SelectItem>
                <SelectItem v-for="category in categories" :key="category.id" :value="String(category.id)">
                  {{ category.name }}
                </SelectItem>
              </SelectContent>
            </Select>
          </div>
          <div class="flex items-end justify-start md:justify-end">
            <Button variant="outline" @click="handleLoadSubcategories">
              Refresh
            </Button>
          </div>
        </CardContent>
      </Card>

      <Alert v-if="subcategoriesError" variant="destructive" class="mb-4">
        <AlertTitle>Erro ao carregar subcategorias</AlertTitle>
        <AlertDescription>{{ subcategoriesError }}</AlertDescription>
      </Alert>

      <!-- Loading State -->
      <div v-if="subcategoriesLoading" class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        <Skeleton v-for="n in 3" :key="`subcat-skel-${n}`" class="h-32 w-full" />
      </div>

      <!-- Subcategories Grid -->
      <div v-else-if="subcategories.length > 0" class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        <Card
          v-for="subcategory in subcategories"
          :key="subcategory.id"
          class="hover:shadow-md transition-shadow"
        >
          <CardHeader class="pb-3 flex flex-row items-start justify-between gap-2">
            <div>
              <CardTitle class="text-lg">{{ subcategory.name }}</CardTitle>
              <CardDescription class="flex items-center gap-2 mt-2">
                <Badge :variant="subcategory.transaction_type === 'income' ? 'secondary' : 'destructive'">
                  {{ subcategory.transaction_type }}
                </Badge>
                <Badge v-if="!subcategory.is_active" variant="outline">Inactive</Badge>
              </CardDescription>
            </div>
            <div class="flex gap-2">
              <Button variant="ghost" size="icon" @click="editSubcategory(subcategory)" title="Edit subcategory">
                <svg class="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z"></path>
                </svg>
              </Button>
              <Button variant="ghost" size="icon" @click="handleDeleteSubcategory(subcategory)" title="Delete subcategory">
                <svg class="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"></path>
                </svg>
              </Button>
            </div>
          </CardHeader>
          <CardContent class="text-sm text-gray-500 mb-2">
            Category: {{ getCategoryName(subcategory.category) }}
          </CardContent>
        </Card>
      </div>

      <!-- Empty State -->
      <div v-else class="text-center py-12">
        <div class="mx-auto h-12 w-12 text-gray-400">
          <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10"></path>
          </svg>
        </div>
        <h3 class="mt-2 text-sm font-medium text-gray-900">No subcategories found</h3>
        <p class="mt-1 text-sm text-gray-500">Get started by creating a new subcategory.</p>
        <div class="mt-6">
          <Button @click="showCreateSubcategoryModal = true">
            Add Subcategory
          </Button>
        </div>
      </div>
    </div>

    <!-- Create/Edit Category Modal -->
    <Dialog v-if="showCreateCategoryModal || showEditCategoryModal" :open="true" @update:open="(open) => !open && closeCategoryModal()">
      <DialogContent class="sm:max-w-md">
        <DialogHeader>
          <DialogTitle>{{ showEditCategoryModal ? 'Edit Category' : 'Create Category' }}</DialogTitle>
          <DialogDescription>
            Defina nome, tipo e status da categoria.
          </DialogDescription>
        </DialogHeader>

        <form @submit.prevent="showEditCategoryModal ? handleUpdateCategory() : handleCreateCategory()" class="space-y-4">
          <div class="space-y-2">
            <Label>Name</Label>
            <Input
              v-model="categoryForm.name"
              type="text"
              required
              maxlength="100"
              placeholder="Category name"
            />
          </div>

          <div class="space-y-2">
            <Label>Transaction Type</Label>
            <Select v-model="categoryForm.transaction_type" required>
              <SelectTrigger>
                <SelectValue placeholder="Select type" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="income">Income</SelectItem>
                <SelectItem value="expense">Expense</SelectItem>
              </SelectContent>
            </Select>
          </div>

          <div class="space-y-2">
            <Label>Description (Optional)</Label>
            <Textarea
              v-model="categoryForm.description"
              rows="3"
              placeholder="Category description"
            />
          </div>

          <div class="flex items-center gap-2">
            <Checkbox v-model:checked="categoryForm.is_active" id="category_is_active" />
            <Label for="category_is_active" class="text-sm">Active (can be used for transactions)</Label>
          </div>

          <DialogFooter class="gap-2">
            <Button type="button" variant="outline" @click="closeCategoryModal" :disabled="categorySubmitting">
              Cancel
            </Button>
            <Button type="submit" :disabled="categorySubmitting">
              <span v-if="categorySubmitting" class="mr-2 inline-flex h-4 w-4 animate-spin rounded-full border-b-2 border-white"></span>
              {{ categorySubmitting ? 'Saving...' : (showEditCategoryModal ? 'Update' : 'Create') }}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>

    <!-- Create/Edit Subcategory Modal -->
    <Dialog v-if="showCreateSubcategoryModal || showEditSubcategoryModal" :open="true" @update:open="(open) => !open && closeSubcategoryModal()">
      <DialogContent class="sm:max-w-md">
        <DialogHeader>
          <DialogTitle>{{ showEditSubcategoryModal ? 'Edit Subcategory' : 'Create Subcategory' }}</DialogTitle>
          <DialogDescription>
            Associe a subcategoria a uma categoria e defina o status.
          </DialogDescription>
        </DialogHeader>

        <form @submit.prevent="showEditSubcategoryModal ? handleUpdateSubcategory() : handleCreateSubcategory()" class="space-y-4">
          <div class="space-y-2">
            <Label>Name</Label>
            <Input
              v-model="subcategoryForm.name"
              type="text"
              required
              maxlength="100"
              placeholder="Subcategory name"
            />
          </div>
          
          <div class="space-y-2">
            <Label>Category</Label>
            <Select v-model="subcategoryForm.category" required>
              <SelectTrigger>
                <SelectValue placeholder="Select category" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem :value="null">Select category</SelectItem>
                <SelectItem v-for="category in categories" :key="category.id" :value="String(category.id)">
                  {{ category.name }}
                </SelectItem>
              </SelectContent>
            </Select>
          </div>

          <div class="space-y-2">
            <Label>Description (Optional)</Label>
            <Textarea
              v-model="subcategoryForm.description"
              rows="3"
              placeholder="Subcategory description"
            />
          </div>

          <div class="flex items-center gap-2">
            <Checkbox v-model:checked="subcategoryForm.is_active" id="subcategory_is_active" />
            <Label for="subcategory_is_active" class="text-sm">Active (can be used for transactions)</Label>
          </div>

          <DialogFooter class="gap-2">
            <Button type="button" variant="outline" @click="closeSubcategoryModal" :disabled="subcategorySubmitting">
              Cancel
            </Button>
            <Button type="submit" :disabled="subcategorySubmitting">
              <span v-if="subcategorySubmitting" class="mr-2 inline-flex h-4 w-4 animate-spin rounded-full border-b-2 border-white"></span>
              {{ subcategorySubmitting ? 'Saving...' : (showEditSubcategoryModal ? 'Update' : 'Create') }}
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
  CardFooter,
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
import { Textarea } from '@/components/ui/textarea'
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
import { ButtonGroup, ButtonGroupSeparator } from '@/components/ui/button-group'

// Define page metadata
definePageMeta({
  middleware: 'auth'
})

// Use the categories composable
const {
  categories,
  loading: categoriesLoading,
  error: categoriesError,
  loadCategories,
  createCategory: createCategoryApi,
  updateCategory: updateCategoryApi,
  deleteCategory: deleteCategoryApi,
  formatCategoryData,
  initialize: initializeCategories,
  clearError: clearCategoriesError
} = useCategories()

// Use the subcategories composable
const {
  subcategories,
  loading: subcategoriesLoading,
  error: subcategoriesError,
  loadSubcategories,
  createSubcategory: createSubcategoryApi,
  updateSubcategory: updateSubcategoryApi,
  deleteSubcategory: deleteSubcategoryApi,
  formatSubcategoryData,
  initialize: initializeSubcategories,
  clearError: clearSubcategoriesError
} = useSubcategories()

// Category state
const categorySubmitting = ref(false)
const showCreateCategoryModal = ref(false)
const showEditCategoryModal = ref(false)
const editingCategory = ref(null)

const categoryFilters = ref({
  transaction_type: ''
})

const categoryForm = ref({
  name: '',
  transaction_type: '',
  description: '',
  is_active: true
})

// Subcategory state
const subcategorySubmitting = ref(false)
const showCreateSubcategoryModal = ref(false)
const showEditSubcategoryModal = ref(false)
const editingSubcategory = ref(null)

const subcategoryFilters = ref({
  category: ''
})

const subcategoryForm = ref({
  name: '',
  category: '',
  description: '',
  is_active: true
})

// Methods
const openCreateCategoryModal = (transactionType) => {
  categoryForm.value = {
    name: '',
    transaction_type: transactionType,
    description: '',
    is_active: true
  }
  showCreateCategoryModal.value = true
}

const handleLoadCategories = async () => {
  const filtersData = {
    transaction_type: categoryFilters.value.transaction_type || null
  }
  
  const result = await loadCategories(filtersData)
  if (!result.success) {
    console.error('Failed to load categories:', result.error?.message)
  }
}

const handleCreateCategory = async () => {
  categorySubmitting.value = true
  try {
    const categoryData = formatCategoryData(categoryForm.value)
    const result = await createCategoryApi(categoryData)
    
    if (result.success) {
      closeCategoryModal()
      // Reload subcategories to refresh category dropdown
      await handleLoadSubcategories()
    } else {
      console.error('Failed to create category:', result.error?.message)
    }
  } catch (error) {
    console.error('Error creating category:', error)
  } finally {
    categorySubmitting.value = false
  }
}

const editCategory = (category) => {
  editingCategory.value = category
  categoryForm.value = {
    name: category.name,
    transaction_type: category.transaction_type,
    description: category.description || '',
    is_active: category.is_active
  }
  showEditCategoryModal.value = true
}

const handleUpdateCategory = async () => {
  categorySubmitting.value = true
  try {
    const categoryData = formatCategoryData(categoryForm.value)
    const result = await updateCategoryApi(editingCategory.value.id, categoryData)
    
    if (result.success) {
      closeCategoryModal()
      // Reload subcategories to refresh category dropdown
      await handleLoadSubcategories()
    } else {
      console.error('Failed to update category:', result.error?.message)
    }
  } catch (error) {
    console.error('Error updating category:', error)
  } finally {
    categorySubmitting.value = false
  }
}

const handleDeleteCategory = async (category) => {
  if (!confirm(`Are you sure you want to delete "${category.name}"?`)) {
    return
  }

  const result = await deleteCategoryApi(category.id)
  if (!result.success) {
    console.error('Failed to delete category:', result.error?.message)
  } else {
    // Reload subcategories to refresh category dropdown
    await handleLoadSubcategories()
  }
}

const closeCategoryModal = () => {
  showCreateCategoryModal.value = false
  showEditCategoryModal.value = false
  editingCategory.value = null
  categoryForm.value = {
    name: '',
    transaction_type: '',
    description: '',
    is_active: true
  }
  clearCategoriesError()
}

const handleLoadSubcategories = async () => {
  const filtersData = {
    category: subcategoryFilters.value.category ? Number(subcategoryFilters.value.category) : null
  }
  
  const result = await loadSubcategories(filtersData)
  if (!result.success) {
    console.error('Failed to load subcategories:', result.error?.message)
  }
}

const handleCreateSubcategory = async () => {
  subcategorySubmitting.value = true
  try {
    const subcategoryData = formatSubcategoryData(subcategoryForm.value)
    const result = await createSubcategoryApi(subcategoryData)
    
    if (result.success) {
      closeSubcategoryModal()
    } else {
      console.error('Failed to create subcategory:', result.error?.message)
    }
  } catch (error) {
    console.error('Error creating subcategory:', error)
  } finally {
    subcategorySubmitting.value = false
  }
}

const editSubcategory = (subcategory) => {
  editingSubcategory.value = subcategory
  subcategoryForm.value = {
    name: subcategory.name,
    category: String(subcategory.category),
    description: subcategory.description || '',
    is_active: subcategory.is_active
  }
  showEditSubcategoryModal.value = true
}

const handleUpdateSubcategory = async () => {
  subcategorySubmitting.value = true
  try {
    const subcategoryData = formatSubcategoryData(subcategoryForm.value)
    const result = await updateSubcategoryApi(editingSubcategory.value.id, subcategoryData)
    
    if (result.success) {
      closeSubcategoryModal()
    } else {
      console.error('Failed to update subcategory:', result.error?.message)
    }
  } catch (error) {
    console.error('Error updating subcategory:', error)
  } finally {
    subcategorySubmitting.value = false
  }
}

const handleDeleteSubcategory = async (subcategory) => {
  if (!confirm(`Are you sure you want to delete "${subcategory.name}"?`)) {
    return
  }

  const result = await deleteSubcategoryApi(subcategory.id)
  if (!result.success) {
    console.error('Failed to delete subcategory:', result.error?.message)
  }
}

const closeSubcategoryModal = () => {
  showCreateSubcategoryModal.value = false
  showEditSubcategoryModal.value = false
  editingSubcategory.value = null
  subcategoryForm.value = {
    name: '',
    category: '',
    description: '',
    is_active: true
  }
  clearSubcategoriesError()
}

const getCategoryName = (categoryId) => {
  const category = categories.value.find(cat => cat.id === categoryId)
  return category ? category.name : 'Unknown'
}

const formatDate = (dateString) => {
  if (!dateString) return 'N/A'
  try {
    const date = new Date(dateString)
    if (isNaN(date.getTime())) {
      console.warn('Invalid date string:', dateString)
      return 'N/A'
    }
    return date.toLocaleDateString()
  } catch (error) {
    console.warn('Error parsing date:', dateString, error)
    return 'N/A'
  }
}

// Load data on mount
onMounted(async () => {
  await Promise.all([initializeCategories(), initializeSubcategories()])
})
</script>
