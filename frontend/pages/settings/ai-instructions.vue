<template>
  <div class="py-8">
    <!-- Page Header -->
    <div class="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 mb-6">
      <div class="flex items-center">
        <NuxtLink
          to="/settings"
          class="inline-flex items-center text-sm font-medium text-gray-700 hover:text-gray-900 mr-4"
        >
          <ArrowLeftIcon class="h-4 w-4 mr-2" />
          Back to Settings
        </NuxtLink>
        <div>
          <h1 class="text-3xl font-bold text-gray-900">AI Instructions</h1>
          <p class="mt-1 text-sm text-gray-500">
            Configure instructions for AI transaction classification
          </p>
        </div>
      </div>
    </div>

    <!-- Form Content -->
    <div class="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
      <!-- Loading State for Initial Fetch -->
      <div v-if="isLoading" class="text-center py-12">
        <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600 mx-auto"></div>
        <p class="mt-4 text-gray-500">Loading instructions...</p>
      </div>

      <!-- Form -->
      <form v-else @submit.prevent="handleSubmit" class="space-y-6">
        <!-- Warning Alert for Fetch Errors (non-blocking) -->
        <Alert v-if="fetchError" variant="default" class="bg-yellow-50 border-yellow-200">
          <ExclamationTriangleIcon class="h-4 w-4 text-yellow-600" />
          <AlertTitle class="text-yellow-800">Notice</AlertTitle>
          <AlertDescription class="text-yellow-700">
            Could not load existing instructions: {{ fetchError }}. You can create new instructions below.
          </AlertDescription>
        </Alert>

        <!-- Success Alert -->
        <Alert v-if="successMessage" variant="default" class="bg-green-50 border-green-200">
          <svg class="h-4 w-4 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"></path>
          </svg>
          <AlertTitle class="text-green-800">Success</AlertTitle>
          <AlertDescription class="text-green-700">{{ successMessage }}</AlertDescription>
        </Alert>

        <!-- Error Alert -->
        <Alert v-if="error" variant="destructive">
          <ExclamationTriangleIcon class="h-4 w-4" />
          <AlertTitle>Error</AlertTitle>
          <AlertDescription>{{ error }}</AlertDescription>
        </Alert>

        <!-- Instructions Section -->
        <Card>
          <CardHeader>
            <CardTitle>Classification Instructions</CardTitle>
            <CardDescription>
              Provide specific instructions and guidelines for how AI should classify your transactions.
              These instructions will help the AI understand your preferences and categorization rules.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div class="space-y-2">
              <Label for="instructions">Instructions</Label>
              <Textarea
                id="instructions"
                v-model="instructions"
                :default-value="instructions ? instructions : undefined"
                :placeholder="instructions ? undefined: 'Enter your classification instructions here...'"
                class="min-h-[300px] font-mono text-sm"
              />
              <p class="text-xs text-gray-500">
                Be specific about how transactions should be categorized based on descriptions, amounts, merchants, etc.
              </p>
            </div>
          </CardContent>
        </Card>

        <!-- Actions -->
        <div class="flex justify-end gap-4">
          <Button
            type="button"
            variant="outline"
            @click="handleCancel"
            :disabled="isSaving"
          >
            Cancel
          </Button>
          <Button
            type="submit"
            :disabled="isSaving || !instructions"
          >
            <span v-if="isSaving" class="flex items-center">
              <svg class="animate-spin -ml-1 mr-2 h-4 w-4 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
              </svg>
              Saving...
            </span>
            <span v-else>Save Instructions</span>
          </Button>
        </div>
      </form>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ArrowLeftIcon, ExclamationTriangleIcon } from '@heroicons/vue/24/outline'
import { Button } from '@/components/ui/button'
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle
} from '@/components/ui/card'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert'

// Page metadata
definePageMeta({
  middleware: 'auth'
})

// Composables
const router = useRouter()
const { 
  loadInstruction, 
  saveInstruction,
  loading,
  error: composableError,
  clearError
} = useAIClassifierInstructions()

// State
const instructions = ref('')
const isLoading = ref(false)
const isSaving = ref(false)
const error = ref<string | null>(null)
const successMessage = ref<string | null>(null)
const fetchError = ref<string | null>(null)

// Load existing instruction on mount
onMounted(async () => {
  isLoading.value = true
  fetchError.value = null
  
  try {
    const result = await loadInstruction()
    
    if (result.success) {
      // Check if instructions exist and have content
      const instructionData = result.data
      const hasInstructions = instructionData?.instructions && instructionData.instructions.trim().length > 0
      
      if (hasInstructions && instructionData) {
        // Pre-fill the textarea with existing instructions
        instructions.value = instructionData.instructions
      } else {
        // No instructions exist, start with empty string (placeholder will show)
        instructions.value = ''
      }
    } else {
      // If fetch failed, still allow user to create new instructions
      // Show warning but don't block the form
      fetchError.value = result.error?.message || 'Failed to load instructions'
      instructions.value = ''
    }
  } catch (err: any) {
    // Even if there's an error, allow user to create new instructions
    fetchError.value = err?.message || 'An unexpected error occurred'
    instructions.value = ''
  } finally {
    isLoading.value = false
  }
})

// Handle form submission
const handleSubmit = async () => {
  if (!instructions.value.trim()) {
    error.value = 'Instructions cannot be empty'
    return
  }

  isSaving.value = true
  error.value = null
  successMessage.value = null
  clearError()

  try {
    const result = await saveInstruction(instructions.value.trim())
    
    if (result.success) {
      successMessage.value = 'Instructions saved successfully!'
      // Clear success message after 3 seconds
      setTimeout(() => {
        successMessage.value = null
      }, 3000)
    } else {
      error.value = result.error?.message || 'Failed to save instructions'
    }
  } catch (err: any) {
    error.value = err?.message || 'An unexpected error occurred'
  } finally {
    isSaving.value = false
  }
}

// Handle cancel
const handleCancel = () => {
  router.push('/settings')
}

// Watch for composable errors
watch(composableError, (newError) => {
  if (newError) {
    error.value = newError
  }
})
</script>

