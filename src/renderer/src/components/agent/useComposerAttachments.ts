import { ref, type Ref } from 'vue'
import { buildComposerAttachment, type ComposerAttachment } from './attachmentUtils'

interface UseComposerAttachmentsOptions {
  closeInputMenu?: () => void
}

interface UseComposerAttachmentsApi {
  composerAttachments: Ref<ComposerAttachment[]>
  imageUploadInputRef: Ref<HTMLInputElement | null>
  fileUploadInputRef: Ref<HTMLInputElement | null>
  isComposerDragActive: Ref<boolean>
  handleImageInputChange: (event: Event) => Promise<void>
  handleFileInputChange: (event: Event) => Promise<void>
  handleComposerDragEnter: (event: DragEvent) => void
  handleComposerDragOver: (event: DragEvent) => void
  handleComposerDragLeave: (event: DragEvent) => void
  handleComposerDrop: (event: DragEvent) => Promise<void>
  handleComposerPaste: (event: ClipboardEvent) => Promise<void>
  openImageUpload: () => void
  openFileUpload: () => void
  removeComposerAttachment: (id: string) => void
}

export function useComposerAttachments(options: UseComposerAttachmentsOptions = {}): UseComposerAttachmentsApi {
  const composerAttachments = ref<ComposerAttachment[]>([])
  const imageUploadInputRef = ref<HTMLInputElement | null>(null)
  const fileUploadInputRef = ref<HTMLInputElement | null>(null)
  const isComposerDragActive = ref(false)
  const composerDragDepth = ref(0)

  function mergeComposerAttachments(next: ComposerAttachment[]): void {
    if (!next.length) return
    const existing = composerAttachments.value
    const seen = new Set(existing.map(a => `${a.name}:${a.sizeBytes || 0}:${a.mimeType || ''}`))
    const merged = [...existing]
    for (const att of next) {
      const key = `${att.name}:${att.sizeBytes || 0}:${att.mimeType || ''}`
      if (seen.has(key)) continue
      seen.add(key)
      merged.push(att)
      if (merged.length >= 8) break
    }
    composerAttachments.value = merged
  }

  async function appendComposerFiles(files: File[]): Promise<void> {
    if (!files.length) return
    const parsed = await Promise.all(
      files.map(async (file) => {
        try {
          return await buildComposerAttachment(file)
        } catch (err) {
          console.warn('[Agent] Failed to parse attachment:', file.name, err)
          return null
        }
      })
    )
    mergeComposerAttachments(parsed.filter((item): item is ComposerAttachment => Boolean(item)))
  }

  function removeComposerAttachment(id: string): void {
    composerAttachments.value = composerAttachments.value.filter(att => att.id !== id)
  }

  function openImageUpload(): void {
    options.closeInputMenu?.()
    imageUploadInputRef.value?.click()
  }

  function openFileUpload(): void {
    options.closeInputMenu?.()
    fileUploadInputRef.value?.click()
  }

  async function handleImageInputChange(event: Event): Promise<void> {
    const input = event.target as HTMLInputElement
    const files = Array.from(input.files || [])
    await appendComposerFiles(files)
    input.value = ''
  }

  async function handleFileInputChange(event: Event): Promise<void> {
    const input = event.target as HTMLInputElement
    const files = Array.from(input.files || [])
    await appendComposerFiles(files)
    input.value = ''
  }

  function hasTransferFiles(dataTransfer: DataTransfer | null): boolean {
    if (!dataTransfer) return false
    if (dataTransfer.files && dataTransfer.files.length > 0) return true
    return Array.from(dataTransfer.items || []).some(item => item.kind === 'file')
  }

  function handleComposerDragEnter(event: DragEvent): void {
    if (!hasTransferFiles(event.dataTransfer)) return
    composerDragDepth.value += 1
    isComposerDragActive.value = true
  }

  function handleComposerDragOver(event: DragEvent): void {
    if (!hasTransferFiles(event.dataTransfer)) return
    isComposerDragActive.value = true
  }

  function handleComposerDragLeave(event: DragEvent): void {
    if (!hasTransferFiles(event.dataTransfer)) return
    composerDragDepth.value = Math.max(0, composerDragDepth.value - 1)
    if (composerDragDepth.value === 0) {
      isComposerDragActive.value = false
    }
  }

  async function handleComposerDrop(event: DragEvent): Promise<void> {
    const files = Array.from(event.dataTransfer?.files || [])
    composerDragDepth.value = 0
    isComposerDragActive.value = false
    await appendComposerFiles(files)
  }

  async function handleComposerPaste(event: ClipboardEvent): Promise<void> {
    const items = Array.from(event.clipboardData?.items || [])
    const files = items
      .filter(item => item.kind === 'file')
      .map(item => item.getAsFile())
      .filter((file): file is File => Boolean(file))
    if (!files.length) return
    event.preventDefault()
    await appendComposerFiles(files)
  }

  return {
    composerAttachments,
    imageUploadInputRef,
    fileUploadInputRef,
    isComposerDragActive,
    handleImageInputChange,
    handleFileInputChange,
    handleComposerDragEnter,
    handleComposerDragOver,
    handleComposerDragLeave,
    handleComposerDrop,
    handleComposerPaste,
    openImageUpload,
    openFileUpload,
    removeComposerAttachment
  }
}
