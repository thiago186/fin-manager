<template>
  <Dialog :open="true" @update:open="(open) => !open && handleClose()">
    <DialogContent class="sm:max-w-2xl">
      <DialogHeader>
        <DialogTitle>Importar Transações</DialogTitle>
        <DialogDescription>
          Envie seu arquivo CSV ou JSON e associe a uma conta ou cartão.
        </DialogDescription>
      </DialogHeader>

      <!-- File Upload Area -->
      <div v-if="!selectedFile && !currentReport" class="mb-6">
        <div
          @drop.prevent="handleDrop"
          @dragover.prevent="isDragging = true"
          @dragleave.prevent="isDragging = false"
          :class="[
            'border-2 border-dashed rounded-lg p-8 text-center transition-colors',
            isDragging ? 'border-primary/70 bg-primary/5' : 'border-border hover:border-primary/40'
          ]"
        >
          <CloudArrowUpIcon class="mx-auto h-12 w-12 text-muted-foreground mb-4" />
          <p class="text-sm text-muted-foreground mb-2">
            Arraste e solte um arquivo CSV ou JSON aqui, ou
          </p>
          <Button variant="default" type="button" @click="fileInput?.click()">
            Selecionar arquivo
          </Button>
          <input
            ref="fileInput"
            type="file"
            accept=".csv,.json"
            class="hidden"
            @change="handleFileSelect"
          />
          <p class="text-xs text-muted-foreground mt-2">
            Apenas arquivos .csv e .json são aceitos
          </p>
        </div>
      </div>

      <!-- Selected File Preview -->
      <div v-if="selectedFile && !isUploading && !currentReport" class="mb-6">
        <div class="rounded-lg border border-border bg-muted/30 p-4">
          <div class="flex items-center justify-between">
            <div class="flex items-center">
              <DocumentIcon class="h-8 w-8 text-muted-foreground mr-3" />
              <div>
                <p class="text-sm font-medium">{{ selectedFile.name }}</p>
                <p class="text-xs text-muted-foreground">
                  {{ formatFileSize(selectedFile.size) }}
                </p>
              </div>
            </div>
            <Button variant="ghost" size="icon" @click="clearFile" :disabled="isUploading">
              <XMarkIcon class="h-5 w-5" />
            </Button>
          </div>
        </div>
      </div>

      <!-- Account/Credit Card Selection -->
      <div v-if="selectedFile && !isUploading && !currentReport" class="mb-6 space-y-2">
        <div class="flex items-center gap-1">
          <Label>Associar a conta ou cartão de crédito</Label>
          <span class="text-red-500">*</span>
        </div>
        <div
          v-if="accounts.length === 0 && creditCards.length === 0"
          class="rounded-md border border-yellow-200 bg-yellow-50 p-3 text-sm text-yellow-800"
        >
          Você precisa criar pelo menos uma conta bancária ou cartão de crédito antes de importar transações.
        </div>
        <Select v-else v-model="selectedAccountOrCard">
          <SelectTrigger :class="!selectedAccountOrCard && showValidationError ? 'border-destructive' : ''">
            <SelectValue placeholder="Selecione uma conta ou cartão de crédito" />
          </SelectTrigger>
          <SelectContent>
            <SelectLabel>Contas Bancárias</SelectLabel>
            <SelectItem
              v-for="account in accounts"
              :key="`account-${account.id}`"
              :value="`account-${account.id}`"
            >
              {{ account.name }}
            </SelectItem>
            <SelectSeparator v-if="accounts.length && creditCards.length" />
            <SelectLabel v-if="creditCards.length">Cartões de Crédito</SelectLabel>
            <SelectItem
              v-for="creditCard in creditCards"
              :key="`credit-card-${creditCard.id}`"
              :value="`credit-card-${creditCard.id}`"
            >
              {{ creditCard.name }}
            </SelectItem>
          </SelectContent>
        </Select>
        <p v-if="!selectedAccountOrCard && showValidationError" class="text-sm text-destructive">
          É necessário selecionar uma conta ou cartão de crédito
        </p>
      </div>

      <!-- Upload Status Display -->
      <div v-if="isUploading || currentReport" class="mb-6 space-y-3">
        <Alert v-if="currentReport?.status === 'SENT'" variant="default">
          <ClockIcon class="h-4 w-4" />
          <AlertTitle>Arquivo enviado</AlertTitle>
          <AlertDescription>Processamento iniciará em breve...</AlertDescription>
        </Alert>

        <Alert v-if="currentReport?.status === 'PROCESSING'" variant="default">
          <div class="flex items-center gap-2">
            <span class="inline-flex h-4 w-4 animate-spin rounded-full border-b-2 border-primary"></span>
            <AlertTitle>Importando transações...</AlertTitle>
          </div>
          <AlertDescription>Aguarde enquanto processamos seu arquivo.</AlertDescription>
        </Alert>

        <Alert v-if="currentReport?.status === 'IMPORTED'" variant="success">
          <CheckCircleIcon class="h-4 w-4" />
          <AlertTitle>Importação concluída com sucesso!</AlertTitle>
          <AlertDescription class="space-y-2">
            <p>✓ {{ currentReport.success_count }} transações importadas</p>
            <p v-if="currentReport.error_count > 0" class="text-yellow-700">
              ⚠ {{ currentReport.error_count }} transações falharam
            </p>
            <div v-if="currentReport.errors && currentReport.errors.length > 0" class="space-y-2">
              <Button variant="link" class="px-0" @click="showErrors = !showErrors">
                {{ showErrors ? 'Ocultar' : 'Mostrar' }} erros ({{ currentReport.errors.length }})
              </Button>
              <div v-if="showErrors" class="rounded border border-border bg-background p-3 max-h-48 overflow-y-auto">
                <ul class="text-xs text-muted-foreground space-y-1">
                  <li v-for="(error, index) in currentReport.errors" :key="index" class="flex items-start gap-1">
                    <ExclamationCircleIcon class="h-4 w-4 text-destructive mt-0.5" />
                    <span>{{ error }}</span>
                  </li>
                </ul>
              </div>
            </div>
          </AlertDescription>
        </Alert>

        <Alert v-if="currentReport?.status === 'FAILED'" variant="destructive">
          <XCircleIcon class="h-4 w-4" />
          <AlertTitle>Importação falhou</AlertTitle>
          <AlertDescription>
            {{ currentReport.failed_reason || 'Ocorreu um erro ao processar o arquivo.' }}
          </AlertDescription>
        </Alert>
      </div>

      <!-- Upload Progress -->
      <div v-if="isUploading" class="mb-6">
        <div class="flex items-center justify-center py-4">
          <span class="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></span>
          <span class="ml-3 text-sm text-muted-foreground">Enviando arquivo...</span>
        </div>
      </div>

      <!-- Error Display -->
      <Alert v-if="uploadError" variant="destructive" class="mb-6">
        <ExclamationTriangleIcon class="h-4 w-4" />
        <AlertTitle>Erro ao fazer upload</AlertTitle>
        <AlertDescription>{{ uploadError }}</AlertDescription>
      </Alert>

      <DialogFooter class="gap-2">
        <Button
          v-if="selectedFile && !isUploading && !currentReport"
          type="button"
          :disabled="!selectedAccountOrCard"
          @click="handleUpload"
        >
          Importar
        </Button>
        <Button
          type="button"
          variant="outline"
          :disabled="!!(isUploading || (currentReport && currentReport.status !== 'IMPORTED' && currentReport.status !== 'FAILED'))"
          @click="handleClose"
        >
          {{ currentReport?.status === 'IMPORTED' || currentReport?.status === 'FAILED' ? 'Fechar' : 'Cancelar' }}
        </Button>
      </DialogFooter>
    </DialogContent>
  </Dialog>
</template>

<script setup lang="ts">
import {
  CloudArrowUpIcon,
  DocumentIcon,
  XMarkIcon,
  ClockIcon,
  CheckCircleIcon,
  XCircleIcon,
  ExclamationTriangleIcon,
  ExclamationCircleIcon
} from '@heroicons/vue/24/outline'
import type { ImportReport } from '~/types/importReports'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle
} from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectLabel,
  SelectSeparator,
  SelectTrigger,
  SelectValue
} from '@/components/ui/select'
import { Label } from '@/components/ui/label'
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert'

// Emits
const emit = defineEmits<{
  close: []
  imported: []
}>()

// Composables
const {
  uploadCSV,
  uploadJSON,
  pollImportStatus,
  stopPolling,
  clearError
} = useImportReports()

const { loadTransactions } = useTransactions()
const { accounts, loadAccounts } = useAccounts()
const { creditCards, loadCreditCards } = useCreditCards()

// Local state
const fileInput = ref<HTMLInputElement | null>(null)
const selectedFile = ref<File | null>(null)
const selectedAccountOrCard = ref<string>('')
const showValidationError = ref(false)
const isDragging = ref(false)
const isUploading = ref(false)
const uploadError = ref<string | null>(null)
const currentReport = ref<ImportReport | null>(null)
const showErrors = ref(false)
const stopPollingFn = ref<(() => void) | null>(null)

// Methods
const handleFileSelect = (event: Event) => {
  const target = event.target as HTMLInputElement
  if (target.files && target.files.length > 0) {
    const file = target.files[0]
    const fileName = file.name.toLowerCase()
    if (fileName.endsWith('.csv') || fileName.endsWith('.json')) {
      selectedFile.value = file
      uploadError.value = null
    } else {
      uploadError.value = 'Por favor, selecione um arquivo CSV (.csv) ou JSON (.json)'
    }
  }
}

const handleDrop = (event: DragEvent) => {
  isDragging.value = false
  if (event.dataTransfer?.files && event.dataTransfer.files.length > 0) {
    const file = event.dataTransfer.files[0]
    const fileName = file.name.toLowerCase()
    if (fileName.endsWith('.csv') || fileName.endsWith('.json')) {
      selectedFile.value = file
      uploadError.value = null
    } else {
      uploadError.value = 'Por favor, selecione um arquivo CSV (.csv) ou JSON (.json)'
    }
  }
}

const clearFile = () => {
  selectedFile.value = null
  selectedAccountOrCard.value = ''
  showValidationError.value = false
  uploadError.value = null
  if (fileInput.value) {
    fileInput.value.value = ''
  }
}

const handleUpload = async () => {
  if (!selectedFile.value) return

  // Validate account/card selection
  if (!selectedAccountOrCard.value) {
    showValidationError.value = true
    return
  }

  showValidationError.value = false
  isUploading.value = true
  uploadError.value = null
  clearError()

  // Parse selected account or card
  const isAccount = selectedAccountOrCard.value.startsWith('account-')
  // Extract ID from either "account-123" or "credit-card-123" format
  const parts = selectedAccountOrCard.value.split('-')
  const id = parseInt(parts[parts.length - 1])

  const uploadOptions = isAccount
    ? { account_id: id }
    : { credit_card_id: id }

  // Determine file type and call appropriate upload function
  const fileName = selectedFile.value.name.toLowerCase()
  const isJSON = fileName.endsWith('.json')
  const uploadFunction = isJSON ? uploadJSON : uploadCSV

  try {
    const result = await uploadFunction(selectedFile.value, uploadOptions)

    if (!result.success || !result.data) {
      uploadError.value = result.error?.message || 'Falha ao fazer upload do arquivo'
      isUploading.value = false
      return
    }

    const reportId = result.data.report_id
    isUploading.value = false

    // Start polling for status updates
    stopPollingFn.value = pollImportStatus(
      reportId,
      (report) => {
        // Update UI with current status
        currentReport.value = report
      },
      (finalReport) => {
        // Import complete
        currentReport.value = finalReport
        
        // Refresh transactions if import was successful
        if (finalReport.status === 'IMPORTED') {
          loadTransactions()
          emit('imported')
        }
      }
    )
  } catch (err: any) {
    uploadError.value = err?.message || 'Erro desconhecido ao fazer upload'
    isUploading.value = false
  }
}

const handleClose = () => {
  // Only allow closing if not uploading and status is final
  if (isUploading.value) return
  if (currentReport.value && 
      currentReport.value.status !== 'IMPORTED' && 
      currentReport.value.status !== 'FAILED') {
    return
  }

  // Stop polling if active
  if (stopPollingFn.value) {
    stopPollingFn.value()
    stopPollingFn.value = null
  }

  // Reset state
  selectedFile.value = null
  selectedAccountOrCard.value = ''
  showValidationError.value = false
  currentReport.value = null
  uploadError.value = null
  showErrors.value = false
  isDragging.value = false
  clearFile()

  emit('close')
}

// Load accounts and credit cards when modal opens
onMounted(async () => {
  await Promise.all([
    loadAccounts(),
    loadCreditCards()
  ])
})

const formatFileSize = (bytes: number): string => {
  if (bytes === 0) return '0 Bytes'
  const k = 1024
  const sizes = ['Bytes', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i]
}

// Cleanup on unmount
onUnmounted(() => {
  if (stopPollingFn.value) {
    stopPollingFn.value()
  }
})
</script>

