export interface FileFilter {
  name: string
  extensions: string[]
}

export interface ExportOptions {
  defaultName: string
  filters: FileFilter[]
  content: string
}

export interface ImportOptions {
  filters: FileFilter[]
}

export interface ExportResult {
  success: boolean
  filePath?: string
}

export interface ImportResult {
  success: boolean
  content?: string
  filePath?: string
}

export interface IElectronAPI {
  minimizeWindow: () => void
  maximizeWindow: () => void
  closeWindow: () => void
  isMaximized: () => Promise<boolean>
  exportFile: (options: ExportOptions) => Promise<ExportResult>
  importFile: (options: ImportOptions) => Promise<ImportResult>
  platform: string
}

declare global {
  interface Window {
    electronAPI: IElectronAPI
  }
}
