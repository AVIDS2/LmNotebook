import { defineStore } from 'pinia'
import { ref } from 'vue'
import { v4 as uuidv4 } from 'uuid'
import * as db from '@/services/database'
import type { Category } from '@/services/database'

export const useCategoryStore = defineStore('categories', () => {
  const categories = ref<Category[]>([])

  // 加载所有分类
  async function loadCategories(): Promise<void> {
    categories.value = await db.getAllCategories()
  }

  // 添加分类
  async function addCategory(name: string, color: string): Promise<Category> {
    const maxOrder = categories.value.length > 0
      ? Math.max(...categories.value.map((c: Category) => c.order))
      : -1

    const category: Category = {
      id: uuidv4(),
      name,
      color,
      order: maxOrder + 1
    }

    await db.createCategory(category)
    await loadCategories()
    return category
  }

  // 更新分类
  async function updateCategory(id: string, data: Partial<Category>): Promise<void> {
    await db.updateCategory(id, data)
    await loadCategories()
  }

  // 删除分类
  async function deleteCategory(id: string): Promise<void> {
    await db.deleteCategory(id)
    await loadCategories()
  }

  // 获取分类
  function getCategoryById(id: string | null): Category | undefined {
    if (!id) return undefined
    return categories.value.find((c: Category) => c.id === id)
  }

  // 重新排序分类（拖拽）
  async function reorderCategories(draggedId: string, targetId: string): Promise<void> {
    const draggedIndex = categories.value.findIndex((c: Category) => c.id === draggedId)
    const targetIndex = categories.value.findIndex((c: Category) => c.id === targetId)

    if (draggedIndex === -1 || targetIndex === -1) return

    // 从数组中移除拖拽的项
    const [draggedCategory] = categories.value.splice(draggedIndex, 1)

    // 插入到目标位置
    const insertIndex = draggedIndex < targetIndex ? targetIndex : targetIndex
    categories.value.splice(insertIndex, 0, draggedCategory)

    // 更新所有分类的 order 值
    for (let i = 0; i < categories.value.length; i++) {
      await db.updateCategory(categories.value[i].id, { order: i })
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
