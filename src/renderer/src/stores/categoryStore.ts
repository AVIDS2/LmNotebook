import { defineStore } from 'pinia'
import { ref } from 'vue'
import { db } from '@/database'
import type { Category } from '@/types/note'
import { v4 as uuidv4 } from 'uuid'

export const useCategoryStore = defineStore('categories', () => {
  const categories = ref<Category[]>([])

  // 加载所有分类
  async function loadCategories(): Promise<void> {
    const list = await db.categories.orderBy('order').toArray()
    categories.value = list
  }

  // 添加分类
  async function addCategory(name: string, color: string): Promise<Category> {
    const maxOrder = categories.value.length > 0
      ? Math.max(...categories.value.map(c => c.order))
      : -1

    const category: Category = {
      id: uuidv4(),
      name,
      color,
      order: maxOrder + 1
    }

    await db.categories.add(category)
    await loadCategories()
    return category
  }

  // 更新分类
  async function updateCategory(id: string, data: Partial<Category>): Promise<void> {
    await db.categories.update(id, data)
    await loadCategories()
  }

  // 删除分类
  async function deleteCategory(id: string): Promise<void> {
    await db.categories.delete(id)
    // 将该分类的笔记设为无分类
    await db.notes.where('categoryId').equals(id).modify({ categoryId: null })
    await loadCategories()
  }

  // 获取分类
  function getCategoryById(id: string | null): Category | undefined {
    if (!id) return undefined
    return categories.value.find(c => c.id === id)
  }

  // 重新排序分类（拖拽）
  async function reorderCategories(draggedId: string, targetId: string): Promise<void> {
    const draggedIndex = categories.value.findIndex(c => c.id === draggedId)
    const targetIndex = categories.value.findIndex(c => c.id === targetId)

    if (draggedIndex === -1 || targetIndex === -1) return

    // 从数组中移除拖拽的项
    const [draggedCategory] = categories.value.splice(draggedIndex, 1)

    // 插入到目标位置
    const insertIndex = draggedIndex < targetIndex ? targetIndex : targetIndex
    categories.value.splice(insertIndex, 0, draggedCategory)

    // 更新所有分类的 order 值
    const updates = categories.value.map((category, index) => ({
      id: category.id,
      order: index
    }))

    // 批量更新数据库
    for (const update of updates) {
      await db.categories.update(update.id, { order: update.order })
    }

    await loadCategories()
  }

  return {
    categories,
    loadCategories,
    addCategory,
    updateCategory,
    deleteCategory,
    getCategoryById,
    reorderCategories
  }
})
