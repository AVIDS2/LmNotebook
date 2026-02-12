export interface ComposerAttachment {
  id: string
  kind: 'image' | 'file'
  name: string
  mimeType?: string
  sizeBytes?: number
  dataUrl?: string
  textContent?: string
}

export function formatAttachmentSize(sizeBytes?: number): string {
  if (!sizeBytes || sizeBytes <= 0) return ''
  if (sizeBytes < 1024) return `${sizeBytes} B`
  if (sizeBytes < 1024 * 1024) return `${(sizeBytes / 1024).toFixed(1)} KB`
  return `${(sizeBytes / (1024 * 1024)).toFixed(1)} MB`
}

export function isImageFile(file: File): boolean {
  return file.type.startsWith('image/')
}

export function isTextReadableFile(file: File): boolean {
  const mime = file.type.toLowerCase()
  if (!mime) {
    return /\.(txt|md|markdown|json|yaml|yml|csv|tsv|log|xml|html?|css|js|ts|tsx|jsx|py|java|go|rs|c|cpp|h)$/i.test(file.name)
  }
  if (mime.startsWith('text/')) return true
  return ['application/json', 'application/xml', 'application/javascript'].includes(mime)
}

export function isDocxFile(file: File): boolean {
  const mime = (file.type || '').toLowerCase()
  if (mime === 'application/vnd.openxmlformats-officedocument.wordprocessingml.document') {
    return true
  }
  return /\.docx$/i.test(file.name || '')
}

export function readFileAsDataUrl(file: File): Promise<string> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader()
    reader.onload = () => resolve(String(reader.result || ''))
    reader.onerror = () => reject(reader.error || new Error('Failed to read file as data URL'))
    reader.readAsDataURL(file)
  })
}

export function readFileAsText(file: File): Promise<string> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader()
    reader.onload = () => resolve(String(reader.result || ''))
    reader.onerror = () => reject(reader.error || new Error('Failed to read file text'))
    reader.readAsText(file, 'utf-8')
  })
}

export async function readDocxAsText(file: File): Promise<string> {
  try {
    const mammoth = await import('mammoth/mammoth.browser')
    const arrayBuffer = await file.arrayBuffer()
    const result = await mammoth.extractRawText({ arrayBuffer })
    return String(result?.value || '').trim()
  } catch (error) {
    console.warn('[Agent] Failed to extract .docx text:', file.name, error)
    return ''
  }
}

export async function buildComposerAttachment(file: File): Promise<ComposerAttachment | null> {
  const id = crypto.randomUUID()
  const base: ComposerAttachment = {
    id,
    kind: isImageFile(file) ? 'image' : 'file',
    name: file.name || `attachment-${id.slice(0, 6)}`,
    mimeType: file.type || '',
    sizeBytes: file.size
  }

  if (base.kind === 'image') {
    const dataUrl = await readFileAsDataUrl(file)
    return {
      ...base,
      dataUrl
    }
  }

  if (isDocxFile(file)) {
    const docxText = await readDocxAsText(file)
    if (docxText) {
      return {
        ...base,
        textContent: docxText.length > 24000 ? `${docxText.slice(0, 24000)}\n...[truncated]` : docxText
      }
    }
    return base
  }

  if (isTextReadableFile(file)) {
    const text = await readFileAsText(file)
    return {
      ...base,
      textContent: text.length > 24000 ? `${text.slice(0, 24000)}\n...[truncated]` : text
    }
  }

  return base
}
