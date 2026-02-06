import type { Note, Category } from '@/services/database'
import * as db from '@/services/database'

// 备份数据结构
interface BackupData {
  version: string
  exportedAt: number
  notes: Note[]
  categories: Category[]
}

// 将 HTML 转换为 Markdown（简化版）
function htmlToMarkdown(html: string): string {
  let md = html
    // 标题
    .replace(/<h1[^>]*>(.*?)<\/h1>/gi, '# $1\n\n')
    .replace(/<h2[^>]*>(.*?)<\/h2>/gi, '## $1\n\n')
    .replace(/<h3[^>]*>(.*?)<\/h3>/gi, '### $1\n\n')
    // 粗体和斜体
    .replace(/<strong[^>]*>(.*?)<\/strong>/gi, '**$1**')
    .replace(/<b[^>]*>(.*?)<\/b>/gi, '**$1**')
    .replace(/<em[^>]*>(.*?)<\/em>/gi, '*$1*')
    .replace(/<i[^>]*>(.*?)<\/i>/gi, '*$1*')
    .replace(/<u[^>]*>(.*?)<\/u>/gi, '$1')
    // 任务列表
    .replace(/<li[^>]*data-checked="true"[^>]*>(.*?)<\/li>/gi, '- [x] $1\n')
    .replace(/<li[^>]*data-checked="false"[^>]*>(.*?)<\/li>/gi, '- [ ] $1\n')
    // 列表
    .replace(/<ul[^>]*>/gi, '\n')
    .replace(/<\/ul>/gi, '\n')
    .replace(/<ol[^>]*>/gi, '\n')
    .replace(/<\/ol>/gi, '\n')
    .replace(/<li[^>]*>(.*?)<\/li>/gi, '- $1\n')
    // 段落和换行
    .replace(/<p[^>]*>(.*?)<\/p>/gi, '$1\n\n')
    .replace(/<br\s*\/?>/gi, '\n')
    // 删除其他标签
    .replace(/<[^>]+>/g, '')
    // 清理多余空行
    .replace(/\n{3,}/g, '\n\n')
    .trim()

  return md
}

export const exportService = {
  // 导出全部笔记为 JSON 备份
  async exportBackup(): Promise<boolean> {
    const data = await db.exportAllData()

    const backup: BackupData = {
      version: '1.0.0',
      exportedAt: Date.now(),
      notes: data.notes,
      categories: data.categories
    }

    const content = JSON.stringify(backup, null, 2)
    const date = new Date().toISOString().split('T')[0]

    const result = await window.electronAPI.exportFile({
      defaultName: `origin-notes-backup-${date}.json`,
      filters: [{ name: 'JSON 文件', extensions: ['json'] }],
      content
    })

    return result.success
  },

  // 从 JSON 备份导入
  async importBackup(): Promise<{ success: boolean; message: string }> {
    const result = await window.electronAPI.importFile({
      filters: [{ name: 'JSON 文件', extensions: ['json'] }]
    })

    if (!result.success || !result.content) {
      return { success: false, message: '取消导入' }
    }

    try {
      const backup: BackupData = JSON.parse(result.content)

      // 验证数据格式
      if (!backup.notes || !Array.isArray(backup.notes)) {
        return { success: false, message: '无效的备份文件格式' }
      }

      // 导入数据
      await db.importData({
        notes: backup.notes,
        categories: backup.categories || []
      })

      return {
        success: true,
        message: `成功导入 ${backup.notes.length} 条笔记`
      }
    } catch {
      return { success: false, message: '解析备份文件失败' }
    }
  },

  // 导出单个笔记为 Markdown
  async exportNoteAsMarkdown(note: Note): Promise<boolean> {
    const title = note.title || '未命名笔记'
    const content = note.markdownSource && note.markdownSource.trim()
      ? note.markdownSource
      : htmlToMarkdown(note.content)

    const markdown = `# ${title}\n\n${content}`

    // 清理文件名中的非法字符
    const safeTitle = title.replace(/[\\/:*?"<>|]/g, '_').slice(0, 50)

    const result = await window.electronAPI.exportFile({
      defaultName: `${safeTitle}.md`,
      filters: [{ name: 'Markdown 文件', extensions: ['md'] }],
      content: markdown
    })

    return result.success
  },

  // 导出所有笔记为 Markdown（单文件）
  async exportAllAsMarkdown(): Promise<boolean> {
    const notes = await db.getAllNotes()

    // 置顶在前，更新时间倒序
    notes.sort((a, b) => {
      if (a.isPinned !== b.isPinned) {
        return a.isPinned ? -1 : 1
      }
      return b.updatedAt - a.updatedAt
    })

    let content = '# Origin Notes 导出\n\n'
    content += `导出时间: ${new Date().toLocaleString()}\n\n`
    content += '---\n\n'

    for (const note of notes) {
      const title = note.title || '未命名笔记'
      const noteContent = (note.markdownSource && note.markdownSource.trim())
        ? note.markdownSource
        : htmlToMarkdown(note.content)
      content += `## ${title}\n\n`
      content += `${noteContent}\n\n`
      content += '---\n\n'
    }

    const date = new Date().toISOString().split('T')[0]

    const result = await window.electronAPI.exportFile({
      defaultName: `origin-notes-all-${date}.md`,
      filters: [{ name: 'Markdown 文件', extensions: ['md'] }],
      content
    })

    return result.success
  }
}
