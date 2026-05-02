<template>
  <div class="py-8">
    <div class="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
      <!-- Header -->
      <Card class="mb-8">
        <CardHeader>
          <CardTitle class="text-3xl">Settings</CardTitle>
          <CardDescription>Manage your application settings and preferences</CardDescription>
        </CardHeader>
      </Card>

      <!-- Cashflows Section -->
      <Card class="mb-8">
        <CardHeader>
          <div class="flex justify-between items-center">
            <div>
              <CardTitle>Cashflows</CardTitle>
              <CardDescription>Manage your cash flow views and configurations</CardDescription>
            </div>
            <Button @click="handleCreateCashflow" disabled class="opacity-50 cursor-not-allowed">
              <svg class="h-5 w-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
              </svg>
              Create Cashflow
            </Button>
          </div>
        </CardHeader>
        <CardContent>
          <p class="text-sm text-gray-500">Cashflow management options will be available here.</p>
        </CardContent>
      </Card>

      <!-- Notes Section -->
      <Card class="mb-8">
        <CardHeader>
          <CardTitle>Notes</CardTitle>
          <CardDescription>
            Keep a single personal note with reminders, annotations, and anything you want to persist.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div v-if="isLoadingNote" class="text-center py-6">
            <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600 mx-auto" />
            <p class="mt-3 text-sm text-gray-500">Loading note...</p>
          </div>

          <div v-else class="space-y-4">
            <Alert v-if="noteSuccessMessage" variant="default" class="bg-green-50 border-green-200">
              <svg class="h-4 w-4 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
              </svg>
              <AlertTitle class="text-green-800">Success</AlertTitle>
              <AlertDescription class="text-green-700">{{ noteSuccessMessage }}</AlertDescription>
            </Alert>

            <Alert v-if="noteError" variant="destructive">
              <AlertTitle>Error</AlertTitle>
              <AlertDescription>{{ noteError }}</AlertDescription>
            </Alert>

            <div class="space-y-2">
              <Label for="user-note">Your note</Label>
              <Textarea
                id="user-note"
                v-model="noteContent"
                placeholder="Write your note here..."
                class="min-h-[220px]"
              />
            </div>

            <div class="flex justify-end">
              <Button type="button" @click="handleSaveNote" :disabled="isSavingNote">
                <span v-if="isSavingNote" class="flex items-center">
                  <svg class="animate-spin -ml-1 mr-2 h-4 w-4 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                    <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
                    <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                  </svg>
                  Saving...
                </span>
                <span v-else>Save Note</span>
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>

      <!-- AI Instructions Section -->
      <Card class="mb-8">
        <CardHeader>
          <div class="flex justify-between items-center">
            <div>
              <CardTitle>AI Instructions</CardTitle>
              <CardDescription>Configure instructions for AI transaction classification</CardDescription>
            </div>
            <NuxtLink to="/settings/ai-instructions">
              <Button>
                <svg class="h-5 w-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                </svg>
                Edit Instructions
              </Button>
            </NuxtLink>
          </div>
        </CardHeader>
        <CardContent>
          <p class="text-sm text-gray-500">
            Customize how AI classifies your transactions by providing specific instructions and guidelines.
          </p>
        </CardContent>
      </Card>
    </div>
  </div>
</template>

<script setup lang="ts">
import { Button } from '@/components/ui/button'
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card'
import { Textarea } from '@/components/ui/textarea'
import { Label } from '@/components/ui/label'
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert'

definePageMeta({
  middleware: 'auth',
})

const {
  loadNote,
  saveNote,
  error: composableNoteError,
  clearError: clearNoteError,
} = useUserNote()

const noteContent = ref('')
const isLoadingNote = ref(false)
const isSavingNote = ref(false)
const noteError = ref<string | null>(null)
const noteSuccessMessage = ref<string | null>(null)

onMounted(async () => {
  isLoadingNote.value = true
  noteError.value = null

  try {
    const result = await loadNote()
    if (result.success) {
      noteContent.value = result.data?.content ?? ''
    } else {
      noteError.value = result.error?.message || 'Failed to load note'
    }
  } catch (err: any) {
    noteError.value = err?.message || 'An unexpected error occurred while loading your note'
  } finally {
    isLoadingNote.value = false
  }
})

const handleSaveNote = async () => {
  isSavingNote.value = true
  noteError.value = null
  noteSuccessMessage.value = null
  clearNoteError()

  try {
    const result = await saveNote(noteContent.value)

    if (result.success) {
      noteSuccessMessage.value = 'Note saved successfully!'
      setTimeout(() => {
        noteSuccessMessage.value = null
      }, 3000)
    } else {
      noteError.value = result.error?.message || 'Failed to save note'
    }
  } catch (err: any) {
    noteError.value = err?.message || 'An unexpected error occurred while saving your note'
  } finally {
    isSavingNote.value = false
  }
}

watch(composableNoteError, (newError) => {
  if (newError) {
    noteError.value = newError
  }
})

const handleCreateCashflow = () => {
  // Disabled for now
  // navigateTo('/cash-flow/create')
}
</script>
