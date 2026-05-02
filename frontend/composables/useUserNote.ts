import type {
  SaveUserNoteRequest,
  UserNote,
  UserNoteApiResult,
} from '~/types/userNote'

export const useUserNote = () => {
  const config = useRuntimeConfig()

  const note = ref<UserNote | null>(null)
  const loading = ref(false)
  const error = ref<string | null>(null)

  const loadNote = async (): Promise<UserNoteApiResult<UserNote>> => {
    loading.value = true
    error.value = null

    try {
      const response = await $fetch<UserNote>('/users/note/', {
        baseURL: config.public.apiBase,
        credentials: 'include',
      })

      note.value = response
      return { success: true, data: response }
    } catch (err: any) {
      const errorMessage = err?.data?.message || 'Failed to load note'
      error.value = errorMessage
      console.error('Error loading note:', err)
      return {
        success: false,
        error: { message: errorMessage, code: err?.status?.toString() },
      }
    } finally {
      loading.value = false
    }
  }

  const saveNote = async (content: string): Promise<UserNoteApiResult<UserNote>> => {
    loading.value = true
    error.value = null

    try {
      const requestData: SaveUserNoteRequest = { content }
      const response = await $fetch<UserNote>('/users/note/', {
        baseURL: config.public.apiBase,
        method: 'PUT',
        body: requestData,
        credentials: 'include',
      })

      note.value = response
      return { success: true, data: response }
    } catch (err: any) {
      const errorMessage = err?.data?.message || 'Failed to save note'
      error.value = errorMessage
      console.error('Error saving note:', err)
      return {
        success: false,
        error: { message: errorMessage, code: err?.status?.toString() },
      }
    } finally {
      loading.value = false
    }
  }

  return {
    note: readonly(note),
    loading: readonly(loading),
    error: readonly(error),
    loadNote,
    saveNote,
    clearError: () => { error.value = null },
  }
}
