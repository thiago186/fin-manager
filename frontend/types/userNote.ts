export interface UserNote {
  id: number
  content: string
  created_at: string
  updated_at: string
}

export interface SaveUserNoteRequest {
  content: string
}

export interface UserNoteApiResult<T> {
  success: boolean
  data?: T
  error?: { message: string; code?: string }
}
