<template>
  <div class="note-editor">
    <!-- 无笔记状态 -->
    <div v-if="!noteStore.currentNote" class="note-editor__empty">
      <svg width="64" height="64" viewBox="0 0 64 64" fill="none">
        <rect x="12" y="8" width="40" height="48" rx="4" stroke="currentColor" stroke-width="2"/>
        <path d="M22 22H42M22 32H38M22 42H34" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
      </svg>
      <p>选择一篇笔记或创建新笔记</p>
    </div>

    <!-- 编辑器 -->
    <template v-else>
      <!-- 新版专业工具栏 -->
      <div class="note-editor__toolbar">
        <div class="note-editor__tools">
          <!-- 字体大小下拉 -->
          <div class="toolbar-dropdown" ref="fontSizeDropdownRef">
            <button 
              class="toolbar-dropdown__trigger"
              :class="{ 'toolbar-dropdown__trigger--active': fontSizeDropdownOpen }"
              @click.stop="toggleFontSizeDropdown"
              title="字体大小"
            >
              <span class="toolbar-dropdown__label">{{ currentFontSizeLabel }}</span>
              <svg width="10" height="10" viewBox="0 0 10 10"><path d="M2 4L5 7L8 4" stroke="currentColor" stroke-width="1.2" fill="none"/></svg>
            </button>
            <div v-show="fontSizeDropdownOpen" class="toolbar-dropdown__menu">
              <button 
                v-for="size in fontSizes" 
                :key="size.value"
                class="toolbar-dropdown__item"
                :class="{ 'toolbar-dropdown__item--active': currentFontSize === size.value }"
                @click="setFontSize(size.value)"
              >{{ size.label }}</button>
            </div>
          </div>

          <div class="toolbar-divider"></div>

          <!-- 基础格式：加粗、斜体、下划线 -->
          <button class="note-editor__tool" :class="{ 'note-editor__tool--active': editor?.isActive('bold') }" title="加粗" @click="editor?.chain().focus().toggleBold().run()">
            <strong>B</strong>
          </button>
          <button class="note-editor__tool" :class="{ 'note-editor__tool--active': editor?.isActive('italic') }" title="斜体" @click="editor?.chain().focus().toggleItalic().run()">
            <em>I</em>
          </button>
          <button class="note-editor__tool" :class="{ 'note-editor__tool--active': editor?.isActive('underline') }" title="下划线" @click="editor?.chain().focus().toggleUnderline().run()">
            <u>U</u>
          </button>
          <!-- 删除线 - 小屏幕隐藏 -->
          <button class="note-editor__tool toolbar-hide-sm" :class="{ 'note-editor__tool--active': editor?.isActive('strike') }" title="删除线" @click="editor?.chain().focus().toggleStrike().run()">
            <s>S</s>
          </button>

          <div class="toolbar-divider"></div>

          <!-- 文字颜色下拉 -->
          <div class="toolbar-dropdown" ref="textColorDropdownRef">
            <button 
              class="toolbar-dropdown__trigger toolbar-dropdown__trigger--color"
              @click.stop="toggleTextColorDropdown"
              title="文字颜色"
            >
              <span class="color-icon" :style="{ '--underline-color': currentTextColor }">A</span>
              <svg width="10" height="10" viewBox="0 0 10 10"><path d="M2 4L5 7L8 4" stroke="currentColor" stroke-width="1.2" fill="none"/></svg>
            </button>
            <div v-show="textColorDropdownOpen" class="toolbar-dropdown__menu toolbar-dropdown__menu--colors">
              <button 
                v-for="color in textColors" 
                :key="color.value"
                class="color-swatch"
                :style="{ backgroundColor: color.value }"
                :title="color.label"
                @click="setTextColor(color.value)"
              ></button>
              <button class="color-swatch color-swatch--clear" title="清除颜色" @click="clearTextColor">
                <svg width="12" height="12" viewBox="0 0 12 12"><path d="M2 2L10 10M10 2L2 10" stroke="currentColor" stroke-width="1.5"/></svg>
              </button>
            </div>
          </div>

          <!-- 背景高亮下拉 - 小屏幕隐藏 -->
          <div class="toolbar-dropdown toolbar-hide-sm" ref="highlightDropdownRef">
            <button 
              class="toolbar-dropdown__trigger toolbar-dropdown__trigger--color"
              @click.stop="toggleHighlightDropdown"
              title="背景高亮"
            >
              <span class="highlight-icon" :style="{ '--bg-color': currentHighlightColor }">
                <svg width="14" height="14" viewBox="0 0 14 14"><path d="M2 10L5 3H9L12 10H9L8 8H6L5 10H2Z" fill="currentColor"/></svg>
              </span>
              <svg width="10" height="10" viewBox="0 0 10 10"><path d="M2 4L5 7L8 4" stroke="currentColor" stroke-width="1.2" fill="none"/></svg>
            </button>
            <div v-show="highlightDropdownOpen" class="toolbar-dropdown__menu toolbar-dropdown__menu--colors">
              <button 
                v-for="color in highlightColors" 
                :key="color.value"
                class="color-swatch"
                :style="{ backgroundColor: color.value }"
                :title="color.label"
                @click="setHighlight(color.value)"
              ></button>
              <button class="color-swatch color-swatch--clear" title="清除高亮" @click="clearHighlight">
                <svg width="12" height="12" viewBox="0 0 12 12"><path d="M2 2L10 10M10 2L2 10" stroke="currentColor" stroke-width="1.5"/></svg>
              </button>
            </div>
          </div>

          <div class="toolbar-divider toolbar-hide-sm"></div>

          <!-- 标题下拉 -->
          <div class="toolbar-dropdown" ref="headingDropdownRef">
            <button 
              class="toolbar-dropdown__trigger"
              @click.stop="toggleHeadingDropdown"
              title="标题"
            >
              <span class="toolbar-dropdown__label">{{ currentHeadingLabel }}</span>
              <svg width="10" height="10" viewBox="0 0 10 10"><path d="M2 4L5 7L8 4" stroke="currentColor" stroke-width="1.2" fill="none"/></svg>
            </button>
            <div v-show="headingDropdownOpen" class="toolbar-dropdown__menu">
              <button class="toolbar-dropdown__item" :class="{ 'toolbar-dropdown__item--active': !editor?.isActive('heading') }" @click="setParagraph">正文</button>
              <button class="toolbar-dropdown__item" :class="{ 'toolbar-dropdown__item--active': editor?.isActive('heading', { level: 1 }) }" @click="setHeading(1)">标题 1</button>
              <button class="toolbar-dropdown__item" :class="{ 'toolbar-dropdown__item--active': editor?.isActive('heading', { level: 2 }) }" @click="setHeading(2)">标题 2</button>
              <button class="toolbar-dropdown__item" :class="{ 'toolbar-dropdown__item--active': editor?.isActive('heading', { level: 3 }) }" @click="setHeading(3)">标题 3</button>
            </div>
          </div>

          <div class="toolbar-divider"></div>

          <!-- 列表下拉 -->
          <div class="toolbar-dropdown" ref="listDropdownRef">
            <button 
              class="toolbar-dropdown__trigger"
              :class="{ 'toolbar-dropdown__trigger--active': editor?.isActive('bulletList') || editor?.isActive('orderedList') || editor?.isActive('taskList') }"
              @click.stop="toggleListDropdown"
              title="列表"
            >
              <svg width="16" height="16" viewBox="0 0 16 16"><circle cx="3" cy="4" r="1.5" fill="currentColor"/><circle cx="3" cy="8" r="1.5" fill="currentColor"/><circle cx="3" cy="12" r="1.5" fill="currentColor"/><line x1="6" y1="4" x2="14" y2="4" stroke="currentColor" stroke-width="1.5"/><line x1="6" y1="8" x2="14" y2="8" stroke="currentColor" stroke-width="1.5"/><line x1="6" y1="12" x2="14" y2="12" stroke="currentColor" stroke-width="1.5"/></svg>
              <svg width="10" height="10" viewBox="0 0 10 10"><path d="M2 4L5 7L8 4" stroke="currentColor" stroke-width="1.2" fill="none"/></svg>
            </button>
            <div v-show="listDropdownOpen" class="toolbar-dropdown__menu">
              <button class="toolbar-dropdown__item" :class="{ 'toolbar-dropdown__item--active': editor?.isActive('bulletList') }" @click="toggleBulletList">
                <svg width="14" height="14" viewBox="0 0 14 14"><circle cx="2" cy="3" r="1.2" fill="currentColor"/><circle cx="2" cy="7" r="1.2" fill="currentColor"/><circle cx="2" cy="11" r="1.2" fill="currentColor"/><line x1="5" y1="3" x2="12" y2="3" stroke="currentColor" stroke-width="1.2"/><line x1="5" y1="7" x2="12" y2="7" stroke="currentColor" stroke-width="1.2"/><line x1="5" y1="11" x2="12" y2="11" stroke="currentColor" stroke-width="1.2"/></svg>
                无序列表
              </button>
              <button class="toolbar-dropdown__item" :class="{ 'toolbar-dropdown__item--active': editor?.isActive('orderedList') }" @click="toggleOrderedList">
                <svg width="14" height="14" viewBox="0 0 14 14"><text x="1" y="5" font-size="5" fill="currentColor">1</text><text x="1" y="9" font-size="5" fill="currentColor">2</text><text x="1" y="13" font-size="5" fill="currentColor">3</text><line x1="5" y1="3" x2="12" y2="3" stroke="currentColor" stroke-width="1.2"/><line x1="5" y1="7" x2="12" y2="7" stroke="currentColor" stroke-width="1.2"/><line x1="5" y1="11" x2="12" y2="11" stroke="currentColor" stroke-width="1.2"/></svg>
                有序列表
              </button>
              <button class="toolbar-dropdown__item" :class="{ 'toolbar-dropdown__item--active': editor?.isActive('taskList') }" @click="toggleTaskList">
                <svg width="14" height="14" viewBox="0 0 14 14"><rect x="1" y="1" width="4" height="4" rx="0.5" stroke="currentColor" fill="none"/><path d="M2 3L2.8 3.8L4.2 2.2" stroke="currentColor" stroke-width="0.8"/><rect x="1" y="5" width="4" height="4" rx="0.5" stroke="currentColor" fill="none"/><rect x="1" y="9" width="4" height="4" rx="0.5" stroke="currentColor" fill="none"/><line x1="7" y1="3" x2="13" y2="3" stroke="currentColor" stroke-width="1.2"/><line x1="7" y1="7" x2="13" y2="7" stroke="currentColor" stroke-width="1.2"/><line x1="7" y1="11" x2="13" y2="11" stroke="currentColor" stroke-width="1.2"/></svg>
                任务列表
              </button>
            </div>
          </div>

          <!-- 引用 - 小屏幕隐藏 -->
          <button class="note-editor__tool toolbar-hide-sm" :class="{ 'note-editor__tool--active': editor?.isActive('blockquote') }" title="引用" @click="editor?.chain().focus().toggleBlockquote().run()">
            <svg width="16" height="16" viewBox="0 0 16 16"><path d="M4 4C2.5 4 2 5 2 6.5C2 8 2.5 9 4 9C5.5 9 6 8 6 6.5C6 4 4 11 4 11" stroke="currentColor" stroke-width="1.5" fill="none"/><path d="M11 4C9.5 4 9 5 9 6.5C9 8 9.5 9 11 9C12.5 9 13 8 13 6.5C13 4 11 11 11 11" stroke="currentColor" stroke-width="1.5" fill="none"/></svg>
          </button>

          <!-- 代码 - 小屏幕隐藏 -->
          <button class="note-editor__tool toolbar-hide-sm" :class="{ 'note-editor__tool--active': editor?.isActive('code') }" title="行内代码" @click="editor?.chain().focus().toggleCode().run()">
            &lt;/&gt;
          </button>

          <div class="toolbar-divider toolbar-hide-sm"></div>

          <!-- 插入下拉 -->
          <div class="toolbar-dropdown" ref="insertDropdownRef">
            <button 
              class="toolbar-dropdown__trigger"
              @click.stop="toggleInsertDropdown"
              title="插入"
            >
              <svg width="16" height="16" viewBox="0 0 16 16"><line x1="8" y1="3" x2="8" y2="13" stroke="currentColor" stroke-width="1.5"/><line x1="3" y1="8" x2="13" y2="8" stroke="currentColor" stroke-width="1.5"/></svg>
              <svg width="10" height="10" viewBox="0 0 10 10"><path d="M2 4L5 7L8 4" stroke="currentColor" stroke-width="1.2" fill="none"/></svg>
            </button>
            <div v-show="insertDropdownOpen" class="toolbar-dropdown__menu">
              <button class="toolbar-dropdown__item" @click="insertTable">
                <svg width="14" height="14" viewBox="0 0 14 14"><rect x="1" y="1" width="12" height="12" rx="1" stroke="currentColor" fill="none"/><line x1="1" y1="5" x2="13" y2="5" stroke="currentColor"/><line x1="5" y1="1" x2="5" y2="13" stroke="currentColor"/></svg>
                表格
              </button>
              <button class="toolbar-dropdown__item" @click="insertImage">
                <svg width="14" height="14" viewBox="0 0 14 14"><rect x="1" y="2" width="12" height="10" rx="1" stroke="currentColor" fill="none"/><circle cx="4" cy="5" r="1.2" fill="currentColor"/><path d="M1 10L4 7L7 10L10 6L13 9" stroke="currentColor" stroke-width="1" fill="none"/></svg>
                图片
              </button>
              <button class="toolbar-dropdown__item" @click="insertMath">
                <svg width="14" height="14" viewBox="0 0 14 14"><text x="1" y="11" font-size="9" font-style="italic" fill="currentColor">∑</text><text x="8" y="7" font-size="5" fill="currentColor">x²</text></svg>
                公式
              </button>
              <button class="toolbar-dropdown__item" @click="deleteTable" v-if="editor?.isActive('table')">
                <svg width="14" height="14" viewBox="0 0 14 14"><rect x="1" y="1" width="12" height="12" rx="1" stroke="currentColor" fill="none"/><line x1="1" y1="5" x2="13" y2="5" stroke="currentColor"/><line x1="5" y1="1" x2="5" y2="13" stroke="currentColor"/><line x1="3" y1="3" x2="11" y2="11" stroke="#e74c3c" stroke-width="1.5"/><line x1="11" y1="3" x2="3" y2="11" stroke="#e74c3c" stroke-width="1.5"/></svg>
                删除表格
              </button>
              <!-- 小屏幕下显示更多格式选项 -->
              <div class="toolbar-dropdown__divider toolbar-show-sm"></div>
              <button class="toolbar-dropdown__item toolbar-show-sm" :class="{ 'toolbar-dropdown__item--active': editor?.isActive('strike') }" @click="editor?.chain().focus().toggleStrike().run(); insertDropdownOpen = false">
                <s>S</s> 删除线
              </button>
              <button class="toolbar-dropdown__item toolbar-show-sm" :class="{ 'toolbar-dropdown__item--active': editor?.isActive('blockquote') }" @click="editor?.chain().focus().toggleBlockquote().run(); insertDropdownOpen = false">
                <svg width="14" height="14" viewBox="0 0 14 14"><path d="M3 3C1.8 3 1.5 3.8 1.5 5C1.5 6.2 1.8 7 3 7C4.2 7 4.5 6.2 4.5 5C4.5 3 3 9 3 9" stroke="currentColor" stroke-width="1.2" fill="none"/><path d="M9 3C7.8 3 7.5 3.8 7.5 5C7.5 6.2 7.8 7 9 7C10.2 7 10.5 6.2 10.5 5C10.5 3 9 9 9 9" stroke="currentColor" stroke-width="1.2" fill="none"/></svg>
                引用
              </button>
              <button class="toolbar-dropdown__item toolbar-show-sm" :class="{ 'toolbar-dropdown__item--active': editor?.isActive('code') }" @click="editor?.chain().focus().toggleCode().run(); insertDropdownOpen = false">
                &lt;/&gt; 代码
              </button>
            </div>
          </div>
        </div>

        <div class="note-editor__actions">
          <!-- 分类选择 -->
          <div class="note-editor__category-select">
            <select
              :value="noteStore.currentNote.categoryId || ''"
              @change="handleCategoryChange"
            >
              <option value="">无分类</option>
              <option
                v-for="cat in categoryStore.categories"
                :key="cat.id"
                :value="cat.id"
              >
                {{ cat.name }}
              </option>
            </select>
          </div>

          <!-- 导出 Markdown -->
          <button
            v-if="noteStore.currentView !== 'trash'"
            class="note-editor__tool"
            title="导出为 Markdown"
            @click="handleExportCurrentMarkdown"
          >
            <svg width="18" height="18" viewBox="0 0 18 18" fill="none">
              <path d="M4 3H11L14 6V15H4V3Z" stroke="currentColor" stroke-width="1.3" stroke-linecap="round" stroke-linejoin="round"/>
              <path d="M11 3V6H14" stroke="currentColor" stroke-width="1.3" stroke-linecap="round"/>
              <path d="M6 9H12M6 12H10" stroke="currentColor" stroke-width="1.3" stroke-linecap="round"/>
            </svg>
          </button>
 
          <!-- Markdown 渲染按钮 -->
          <button
            v-if="noteStore.currentView !== 'trash'"
            class="note-editor__tool"
            title="渲染 Markdown 内容"
            @click="handleRenderMarkdown"
          >
            <svg width="18" height="18" viewBox="0 0 18 18" fill="none">
              <path d="M3 5H15M3 9H15M3 13H10" stroke="currentColor" stroke-width="1.3" stroke-linecap="round"/>
              <path d="M13 11L15 13L13 15" stroke="currentColor" stroke-width="1.3" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
          </button>
 
          <!-- 置顶按钮 -->
          <button
            v-if="noteStore.currentView !== 'trash'"
            class="note-editor__tool"
            :class="{ 'note-editor__tool--active': noteStore.currentNote.isPinned }"
            title="置顶"
            @click="handleTogglePin"
          >
            <svg width="18" height="18" viewBox="0 0 18 18" fill="none">
              <path d="M9 2L10.5 6.5L15 7L11.5 10L12.5 15L9 12.5L5.5 15L6.5 10L3 7L7.5 6.5L9 2Z" stroke="currentColor" stroke-width="1.3" stroke-linejoin="round" :fill="noteStore.currentNote.isPinned ? 'currentColor' : 'none'"/>
            </svg>
          </button>

          <!-- 删除/恢复按钮 -->
          <button
            v-if="noteStore.currentView === 'trash'"
            class="note-editor__tool"
            title="恢复"
            @click="handleRestore"
          >
            <svg width="18" height="18" viewBox="0 0 18 18" fill="none">
              <path d="M3 9C3 5.68629 5.68629 3 9 3C11.2091 3 13.1204 4.26324 14.0583 6.10811" stroke="currentColor" stroke-width="1.3" stroke-linecap="round"/>
              <path d="M15 9C15 12.3137 12.3137 15 9 15C6.79086 15 4.87961 13.7368 3.94173 11.8919" stroke="currentColor" stroke-width="1.3" stroke-linecap="round"/>
              <path d="M14 3V6H11" stroke="currentColor" stroke-width="1.3" stroke-linecap="round" stroke-linejoin="round"/>
              <path d="M4 15V12H7" stroke="currentColor" stroke-width="1.3" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
          </button>

          <button
            class="note-editor__tool note-editor__tool--danger"
            :title="noteStore.currentView === 'trash' ? '永久删除' : '删除'"
            @click="handleDelete"
          >
            <svg width="18" height="18" viewBox="0 0 18 18" fill="none">
              <path d="M3 5H15M6 5V4C6 3.44772 6.44772 3 7 3H11C11.5523 3 12 3.44772 12 4V5M14 5V14C14 14.5523 13.5523 15 13 15H5C4.44772 15 4 14.5523 4 14V5" stroke="currentColor" stroke-width="1.3" stroke-linecap="round"/>
            </svg>
          </button>
        </div>
      </div>

      <!-- 标题输入 -->
      <div class="note-editor__title-wrapper">
        <input
          ref="titleInputRef"
          :value="localTitle"
          class="note-editor__title"
          type="text"
          placeholder="标题"
          :readonly="noteStore.currentView === 'trash'"
          @input="handleTitleInput"
          @blur="handleTitleBlur"
        />
        <span v-if="isDirty" class="note-editor__dirty-indicator" title="未保存">*</span>
      </div>

      <!-- 富文本编辑器 -->
      <div class="note-editor__content allow-select" ref="editorContainerRef">
        <EditorContent :editor="editor" />
        
        <!-- 图片调整手柄已移除，使用右键菜单调整 -->
      </div>
    </template>
  </div>
  
  <!-- 图片右键菜单 -->
  <div 
    v-if="imageContextMenu.visible" 
    class="image-context-menu"
    ref="imageMenuRef"
    :style="imageMenuStyle"
    @click.stop
  >
    <!-- 尺寸分段按钮组 -->
    <div class="menu-segment-group" v-if="!showCustomInput">
      <button 
        class="segment-btn" 
        :class="{ active: currentImageWidth === '25%' }"
        @click="setImageSize('25%')"
      >25%</button>
      <button 
        class="segment-btn" 
        :class="{ active: currentImageWidth === '50%' }"
        @click="setImageSize('50%')"
      >50%</button>
      <button 
        class="segment-btn" 
        :class="{ active: currentImageWidth === '100%' }"
        @click="setImageSize('100%')"
      >100%</button>
      <button 
        class="segment-btn"
        :class="{ active: isCustomWidth }"
        @click.stop="showCustomInput = true"
        title="自定义宽度"
      >...</button>
    </div>
    <!-- 自定义尺寸输入 -->
    <div class="custom-size-input" v-else>
      <input 
        ref="customSizeInputRef"
        type="number" 
        v-model="customSizeValue"
        min="1" 
        max="100" 
        placeholder="1-100"
        @keyup.enter="applyCustomSize"
        @keyup.esc="showCustomInput = false"
      />
      <span class="unit">%</span>
      <button class="apply-btn" @click="applyCustomSize">确定</button>
    </div>
    <!-- 对齐分段按钮组 -->
    <div class="menu-segment-group">
      <button 
        class="segment-btn" 
        :class="{ active: currentImageAlign === 'left' }"
        @click="setImageAlign('left')"
        title="居左"
      >
        <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
          <path d="M1 2H13M1 5H9M1 8H13M1 11H7" stroke="currentColor" stroke-width="1.3" stroke-linecap="round"/>
        </svg>
      </button>
      <button 
        class="segment-btn" 
        :class="{ active: currentImageAlign === 'center' }"
        @click="setImageAlign('center')"
        title="居中"
      >
        <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
          <path d="M1 2H13M3 5H11M1 8H13M4 11H10" stroke="currentColor" stroke-width="1.3" stroke-linecap="round"/>
        </svg>
      </button>
      <button 
        class="segment-btn" 
        :class="{ active: currentImageAlign === 'right' }"
        @click="setImageAlign('right')"
        title="居右"
      >
        <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
          <path d="M1 2H13M5 5H13M1 8H13M7 11H13" stroke="currentColor" stroke-width="1.3" stroke-linecap="round"/>
        </svg>
      </button>
    </div>
    <div class="menu-divider"></div>
    <div class="menu-item danger" @click="deleteImage">删除图片</div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch, onBeforeUnmount, onMounted, computed, nextTick, reactive, inject } from 'vue'
import { useEditor, EditorContent } from '@tiptap/vue-3'
import StarterKit from '@tiptap/starter-kit'
import History from '@tiptap/extension-history'
import Placeholder from '@tiptap/extension-placeholder'
import TaskList from '@tiptap/extension-task-list'
import TaskItem from '@tiptap/extension-task-item'
import Underline from '@tiptap/extension-underline'
import Table from '@tiptap/extension-table'
import { NodeSelection } from '@tiptap/pm/state'
import TableRow from '@tiptap/extension-table-row'
import TableCell from '@tiptap/extension-table-cell'
import TableHeader from '@tiptap/extension-table-header'
import Image from '@tiptap/extension-image'
import TextStyle from '@tiptap/extension-text-style'
import Color from '@tiptap/extension-color'
import Highlight from '@tiptap/extension-highlight'
import { Mathematics } from '@/extensions/Mathematics'
import 'katex/dist/katex.min.css'
import katex from 'katex'
import { marked } from 'marked'
import hljs from 'highlight.js'
import 'highlight.js/styles/github.css'
import CodeBlockLowlight from '@tiptap/extension-code-block-lowlight'
import { common, createLowlight } from 'lowlight'
import DOMPurify from 'dompurify'
import { useNoteStore } from '@/stores/noteStore'
import { useCategoryStore } from '@/stores/categoryStore'
import { noteRepository } from '@/database/noteRepository'
import { exportService } from '@/services/exportService'
import { Extension } from '@tiptap/core'

// 自定义字体大小扩展
const FontSize = Extension.create({
  name: 'fontSize',
  addOptions() {
    return { types: ['textStyle'] }
  },
  addGlobalAttributes() {
    return [{
      types: this.options.types,
      attributes: {
        fontSize: {
          default: null,
          parseHTML: element => element.style.fontSize?.replace(/['"]+/g, ''),
          renderHTML: attributes => {
            if (!attributes.fontSize) return {}
            return { style: `font-size: ${attributes.fontSize}` }
          },
        },
      },
    }]
  },
  addCommands() {
    return {
      setFontSize: (fontSize: string) => ({ chain }) => {
        return chain().setMark('textStyle', { fontSize }).run()
      },
      unsetFontSize: () => ({ chain }) => {
        return chain().setMark('textStyle', { fontSize: null }).removeEmptyTextStyle().run()
      },
    }
  },
})

const lowlight = createLowlight(common)

const noteStore = useNoteStore()
const categoryStore = useCategoryStore()

// Register AI format brush action
const registerEditorAction = inject<(fn: (html: string) => void) => void>('registerEditorAction')
if (registerEditorAction) {
  registerEditorAction((html: string) => {
    if (editor.value) {
      console.log('AI Applying new content to editor...')
      
      // 图片保护：提取当前文档中的所有图片节点及其位置信息
      interface ProtectedImage {
        src: string
        width: string
        align: string
        precedingText: string // 图片前面的文本，用于定位
      }
      const images: ProtectedImage[] = []
      let lastTextContent = ''
      
      editor.value.state.doc.descendants((node) => {
        if (node.isText) {
          lastTextContent = node.text || ''
        } else if (node.type.name === 'paragraph') {
          // 重置段落文本
          lastTextContent = node.textContent.slice(0, 50) // 取前50字符作为定位参考
        } else if (node.type.name === 'image') {
          images.push({
            src: node.attrs.src,
            width: node.attrs.width || '50%',
            align: node.attrs.align || 'left',
            precedingText: lastTextContent.slice(-30) // 取最后30字符
          })
        }
      })
      
      console.log(`Found ${images.length} image(s) in current document`)
      
      // 检查 AI 返回的内容是否包含实际的图片数据
      // 只有包含 base64 或 origin-image:// 的才算真正的图片
      const aiHasRealImages = /src=["'](data:image\/|origin-image:\/\/)/.test(html)
      
      console.log(`AI content has real images: ${aiHasRealImages}`)
      
      // 使用 chain 命令保留 undo 历史
      const { from } = editor.value.state.selection
      
      editor.value.chain()
        .selectAll()
        .deleteSelection()
        .insertContent(html)
        .setTextSelection(Math.min(from, editor.value.state.doc.content.size))
        .run()
      
      // 图片保护：如果原文档有图片但 AI 内容没有真正的图片数据，则恢复原有图片
      if (images.length > 0 && !aiHasRealImages) {
        console.log(`Restoring ${images.length} protected image(s)...`)
        
        // 在文档末尾恢复图片
        images.forEach((img, index) => {
          console.log(`Restoring image ${index + 1}: ${img.src.substring(0, 50)}...`)
          editor.value?.chain()
            .focus('end')
            .insertContent({
              type: 'paragraph',
              content: [{
                type: 'image',
                attrs: {
                  src: img.src,
                  width: img.width,
                  align: img.align
                }
              }]
            })
            .run()
        })
        
        console.log('Image restoration completed')
      }
    }
  })
}

// 本地标题状态（用于减少渲染）
const localTitle = ref('')
const titleInputRef = ref<HTMLInputElement>()
const editorContainerRef = ref<HTMLElement>()

// ========== 新版工具栏状态 ==========
// 下拉菜单 refs
const fontSizeDropdownRef = ref<HTMLElement>()
const textColorDropdownRef = ref<HTMLElement>()
const highlightDropdownRef = ref<HTMLElement>()
const headingDropdownRef = ref<HTMLElement>()
const listDropdownRef = ref<HTMLElement>()
const insertDropdownRef = ref<HTMLElement>()

// 下拉菜单开关状态
const fontSizeDropdownOpen = ref(false)
const textColorDropdownOpen = ref(false)
const highlightDropdownOpen = ref(false)
const headingDropdownOpen = ref(false)
const listDropdownOpen = ref(false)
const insertDropdownOpen = ref(false)

// 字体大小选项
const fontSizes = [
  { label: '12', value: '12px' },
  { label: '14', value: '14px' },
  { label: '16', value: '16px' },
  { label: '18', value: '18px' },
  { label: '20', value: '20px' },
  { label: '24', value: '24px' },
  { label: '28', value: '28px' },
  { label: '32', value: '32px' },
]

// 文字颜色选项（现代化配色）
const textColors = [
  { label: '黑色', value: '#1a1a1a' },
  { label: '深灰', value: '#666666' },
  { label: '红色', value: '#e53935' },
  { label: '橙色', value: '#fb8c00' },
  { label: '黄色', value: '#fdd835' },
  { label: '绿色', value: '#43a047' },
  { label: '蓝色', value: '#1e88e5' },
  { label: '紫色', value: '#8e24aa' },
]

// 高亮颜色选项（柔和背景色）
const highlightColors = [
  { label: '黄色', value: '#fff59d' },
  { label: '绿色', value: '#c8e6c9' },
  { label: '蓝色', value: '#bbdefb' },
  { label: '粉色', value: '#f8bbd9' },
  { label: '紫色', value: '#e1bee7' },
  { label: '橙色', value: '#ffe0b2' },
]

// 当前字体大小
const currentFontSize = computed(() => {
  if (!editor.value) return '16px'
  const attrs = editor.value.getAttributes('textStyle')
  return attrs.fontSize || '16px'
})

const currentFontSizeLabel = computed(() => {
  const size = currentFontSize.value.replace('px', '')
  return size || '16'
})

// 当前文字颜色
const currentTextColor = computed(() => {
  if (!editor.value) return '#1a1a1a'
  const attrs = editor.value.getAttributes('textStyle')
  return attrs.color || '#1a1a1a'
})

// 当前高亮颜色
const currentHighlightColor = computed(() => {
  if (!editor.value) return 'transparent'
  const attrs = editor.value.getAttributes('highlight')
  return attrs.color || 'transparent'
})

// 当前标题级别
const currentHeadingLabel = computed(() => {
  if (!editor.value) return '正文'
  if (editor.value.isActive('heading', { level: 1 })) return 'H1'
  if (editor.value.isActive('heading', { level: 2 })) return 'H2'
  if (editor.value.isActive('heading', { level: 3 })) return 'H3'
  return '正文'
})

// 关闭所有下拉菜单
function closeAllDropdowns() {
  fontSizeDropdownOpen.value = false
  textColorDropdownOpen.value = false
  highlightDropdownOpen.value = false
  headingDropdownOpen.value = false
  listDropdownOpen.value = false
  insertDropdownOpen.value = false
}

// 切换下拉菜单
function toggleFontSizeDropdown() {
  const wasOpen = fontSizeDropdownOpen.value
  closeAllDropdowns()
  fontSizeDropdownOpen.value = !wasOpen
}

function toggleTextColorDropdown() {
  const wasOpen = textColorDropdownOpen.value
  closeAllDropdowns()
  textColorDropdownOpen.value = !wasOpen
}

function toggleHighlightDropdown() {
  const wasOpen = highlightDropdownOpen.value
  closeAllDropdowns()
  highlightDropdownOpen.value = !wasOpen
}

function toggleHeadingDropdown() {
  const wasOpen = headingDropdownOpen.value
  closeAllDropdowns()
  headingDropdownOpen.value = !wasOpen
}

function toggleListDropdown() {
  const wasOpen = listDropdownOpen.value
  closeAllDropdowns()
  listDropdownOpen.value = !wasOpen
}

function toggleInsertDropdown() {
  const wasOpen = insertDropdownOpen.value
  closeAllDropdowns()
  insertDropdownOpen.value = !wasOpen
}

// 设置字体大小
function setFontSize(size: string) {
  editor.value?.chain().focus().setMark('textStyle', { fontSize: size }).run()
  fontSizeDropdownOpen.value = false
}

// 设置文字颜色
function setTextColor(color: string) {
  editor.value?.chain().focus().setColor(color).run()
  textColorDropdownOpen.value = false
}

function clearTextColor() {
  editor.value?.chain().focus().unsetColor().run()
  textColorDropdownOpen.value = false
}

// 设置高亮
function setHighlight(color: string) {
  editor.value?.chain().focus().toggleHighlight({ color }).run()
  highlightDropdownOpen.value = false
}

function clearHighlight() {
  editor.value?.chain().focus().unsetHighlight().run()
  highlightDropdownOpen.value = false
}

// 设置标题
function setHeading(level: 1 | 2 | 3) {
  editor.value?.chain().focus().toggleHeading({ level }).run()
  headingDropdownOpen.value = false
}

function setParagraph() {
  editor.value?.chain().focus().setParagraph().run()
  headingDropdownOpen.value = false
}

// 列表操作
function toggleBulletList() {
  editor.value?.chain().focus().toggleBulletList().run()
  listDropdownOpen.value = false
}

function toggleOrderedList() {
  editor.value?.chain().focus().toggleOrderedList().run()
  listDropdownOpen.value = false
}

function toggleTaskList() {
  editor.value?.chain().focus().toggleTaskList().run()
  listDropdownOpen.value = false
}

// 插入操作
function insertTable() {
  editor.value?.chain().focus().insertTable({ rows: 3, cols: 3, withHeaderRow: true }).run()
  insertDropdownOpen.value = false
}

function deleteTable() {
  editor.value?.chain().focus().deleteTable().run()
  insertDropdownOpen.value = false
}

function insertImage() {
  insertDropdownOpen.value = false
  const input = document.createElement('input')
  input.type = 'file'
  input.accept = 'image/*'
  input.onchange = async (e) => {
    const file = (e.target as HTMLInputElement).files?.[0]
    if (file) {
      const reader = new FileReader()
      reader.onload = async (event) => {
        const base64 = event.target?.result as string
        if (base64) {
          const imageSrc = await window.electronAPI.image.store(base64)
          editor.value?.chain().focus().setImage({ src: imageSrc }).run()
        }
      }
      reader.readAsDataURL(file)
    }
  }
  input.click()
}

function insertMath() {
  insertDropdownOpen.value = false
  const latex = prompt('输入 LaTeX 公式:', 'E=mc^2')
  if (latex !== null) {
    const isBlock = confirm('是否作为独立行(Block)显示？')
    editor.value?.chain().focus().insertMath(latex, isBlock).run()
  }
}

// 保存防抖定时器 - 使用 RAF 优化
let saveTimer: ReturnType<typeof setTimeout> | null = null
let titleSaveTimer: ReturnType<typeof setTimeout> | null = null

// 未保存状态指示
const isDirty = ref(false)

// 当前正在编辑的笔记ID
let currentEditingId: string | null = null

// 图片编辑状态（简化版）
const selectedImage = ref<HTMLImageElement | null>(null)
const selectedImagePos = ref<number | null>(null)
const imageMenuRef = ref<HTMLElement | null>(null)
const customSizeInputRef = ref<HTMLInputElement | null>(null)
const showCustomInput = ref(false)
const customSizeValue = ref('')
const imageContextMenu = reactive({
  visible: false,
  x: 0,
  y: 0
})

// 菜单位置计算，避免超出屏幕
const imageMenuStyle = computed(() => {
  const menuWidth = 160
  const menuHeight = 140
  const padding = 8
  
  let x = imageContextMenu.x
  let y = imageContextMenu.y
  
  // 检查右边界
  if (x + menuWidth > window.innerWidth - padding) {
    x = window.innerWidth - menuWidth - padding
  }
  
  // 检查下边界
  if (y + menuHeight > window.innerHeight - padding) {
    y = window.innerHeight - menuHeight - padding
  }
  
  // 检查左边界
  if (x < padding) {
    x = padding
  }
  
  // 检查上边界
  if (y < padding) {
    y = padding
  }
  
  return {
    left: x + 'px',
    top: y + 'px'
  }
})

// Tiptap 编辑器 - 优化配置
const editor = useEditor({
  extensions: [
    StarterKit.configure({
      heading: {
        levels: [1, 2, 3]
      },
      // Disable default CodeBlock since we'll use lowlight version
      codeBlock: false,
      history: false
    }),
    CodeBlockLowlight.configure({
      lowlight,
    }),
    // 单独添加 History 扩展，方便控制
    History.configure({
      depth: 100,
      newGroupDelay: 500
    }),
    Placeholder.configure({
      placeholder: '开始写点什么...'
    }),
    TaskList,
    TaskItem.configure({
      nested: true
    }),
    Underline,
    // 文字样式扩展（颜色、字体大小的基础）
    TextStyle,
    Color,
    Highlight.configure({
      multicolor: true,
    }),
    FontSize,
    Table.configure({
      resizable: true,
    }),
    TableRow,
    TableHeader,
    TableCell,
    Image.extend({
      addAttributes() {
        return {
          ...this.parent?.(),
          width: {
            default: '50%',
            parseHTML: element => element.getAttribute('width') || element.style.width || '50%',
            renderHTML: attributes => {
              const width = attributes.width || '50%'
              return {
                width: width,
                style: `width: ${width}; max-width: 100%; height: auto;`
              }
            },
          },
          align: {
            default: 'left',
            parseHTML: element => element.getAttribute('data-align') || 'left',
            renderHTML: attributes => ({
              'data-align': attributes.align,
              class: `image-align-${attributes.align}`
            }),
          }
        }
      }
    }).configure({
      allowBase64: true,
      inline: false,
    }),
    Mathematics
  ],
  content: '',
  editable: true,
  onSelectionUpdate({ editor }) {
    const { selection } = editor.state
    if (selection instanceof NodeSelection && selection.node.type.name === 'image') {
      const dom = editor.view.nodeDOM(selection.from) as HTMLImageElement
      if (dom && dom.tagName === 'IMG') {
        selectedImage.value = dom
        selectedImagePos.value = selection.from
        return
      }
    }
    selectedImage.value = null
    selectedImagePos.value = null
  },
  // 拦截粘贴事件，支持图片、表格和纯文本
  editorProps: {
    // 禁用浏览器拼写检查（避免代码内容显示红色波浪线）
    attributes: {
      spellcheck: 'false',
      autocorrect: 'off',
      autocapitalize: 'off',
    },
    handlePaste: (view, event) => {
      const clipboardData = event.clipboardData
      if (!clipboardData) return false

      // 1. 优先检查是否有图片
      const items = clipboardData.items
      for (let i = 0; i < items.length; i++) {
        const item = items[i]
        if (item.type.startsWith('image/')) {
          const file = item.getAsFile()
          if (file) {
            // 将图片转为 base64
            const reader = new FileReader()
            reader.onload = async (e) => {
              const base64 = e.target?.result as string
              if (base64) {
                // 使用图片存储服务（大图片会分离存储）
                const imageSrc = await window.electronAPI.image.store(base64)
                const node = view.state.schema.nodes.image.create({ src: imageSrc })
                const { tr } = view.state
                view.dispatch(tr.replaceSelectionWith(node))
              }
            }
            reader.readAsDataURL(file)
            return true
          }
        }
      }

      // 2. 检查是否有 HTML 内容（WPS/Excel 复制的表格会带 HTML）
      const html = clipboardData.getData('text/html')
      if (html && html.includes('<table')) {
        // 有表格的 HTML，让 Tiptap 默认处理
        return false
      }

      // 3. 对于纯文本或 Markdown 源码，强制以纯文本插入
      const text = clipboardData.getData('text/plain')
      if (text) {
        const { tr } = view.state
        const textNode = view.state.schema.text(text)
        view.dispatch(tr.replaceSelectionWith(textNode, false))
        return true
      }

      return false
    }
  },
  // 使用 requestAnimationFrame 优化更新
  onUpdate: ({ editor }) => {
    if (noteStore.currentNote && noteStore.currentView !== 'trash') {
      // 防抖保存 - 使用 RAF + setTimeout 组合优化
      if (saveTimer) {
        clearTimeout(saveTimer)
      }
      
      // 标记有待保存的内容
      isDirty.value = true

      saveTimer = setTimeout(() => {
        if (!isDirty.value) return
        
        // 使用 RAF 确保在下一帧执行，避免阻塞渲染
        requestAnimationFrame(async () => {
          if (!isDirty.value || !noteStore.currentNote) return
          
          const content = editor.getHTML()
          // 直接调用 repository 避免触发 store 的重新加载
          await noteRepository.update(noteStore.currentNote.id, { content })
          isDirty.value = false
        })
      }, 600) // 减少到 600ms，配合 RAF 更流畅
    }
  }
})

// ========== 图片编辑功能（简化版）==========

// 获取当前图片对齐方式
const currentImageAlign = computed(() => {
  if (!selectedImage.value) return 'left'
  return selectedImage.value.getAttribute('data-align') || 'left'
})

// 获取当前图片宽度
const currentImageWidth = computed(() => {
  if (!selectedImage.value) return '50%'
  return selectedImage.value.getAttribute('width') || '50%'
})

// 判断是否为自定义宽度
const isCustomWidth = computed(() => {
  const w = currentImageWidth.value
  return w !== '25%' && w !== '50%' && w !== '100%'
})

// 设置图片对齐
function setImageAlign(align: 'left' | 'center' | 'right'): void {
  if (!editor.value || selectedImagePos.value === null) return
  
  editor.value.chain()
    .focus()
    .setNodeSelection(selectedImagePos.value)
    .updateAttributes('image', { align })
    .run()
  
  // 关闭菜单
  imageContextMenu.visible = false
  showCustomInput.value = false
  selectedImage.value = null
  selectedImagePos.value = null
}

// 设置图片大小
function setImageSize(size: string): void {
  if (!editor.value || selectedImagePos.value === null) return
  
  editor.value.chain()
    .focus()
    .setNodeSelection(selectedImagePos.value)
    .updateAttributes('image', { width: size })
    .run()
  
  imageContextMenu.visible = false
  showCustomInput.value = false
  selectedImage.value = null
  selectedImagePos.value = null
}

// 应用自定义尺寸
function applyCustomSize(): void {
  const num = parseInt(customSizeValue.value, 10)
  if (!isNaN(num) && num >= 1 && num <= 100) {
    setImageSize(`${num}%`)
  }
  customSizeValue.value = ''
  showCustomInput.value = false
}

// 删除图片
function deleteImage(): void {
  if (!editor.value || selectedImagePos.value === null) return
  
  editor.value.chain()
    .focus()
    .setNodeSelection(selectedImagePos.value)
    .deleteSelection()
    .run()
  
  imageContextMenu.visible = false
  selectedImage.value = null
  selectedImagePos.value = null
}

// 监听编辑器中的图片右键事件
const attachImageListeners = (container: HTMLElement) => {
  // 右键菜单
  container.addEventListener('contextmenu', (e: MouseEvent) => {
    const target = e.target as HTMLElement
    if (target.tagName === 'IMG') {
      e.preventDefault()
      selectedImage.value = target as HTMLImageElement
      if (editor.value) {
        const pos = editor.value.view.posAtDOM(target, 0)
        selectedImagePos.value = pos
      }
      imageContextMenu.x = e.clientX
      imageContextMenu.y = e.clientY
      imageContextMenu.visible = true
    }
  })
}

// 监听容器 DOM 变化，当笔记切换显现后绑定事件
watch(editorContainerRef, (newVal) => {
  if (newVal) {
    attachImageListeners(newVal)
  }
})

onMounted(() => {
  // 全局点击关闭右键菜单和工具栏下拉
  document.addEventListener('click', (e) => {
    // 关闭图片右键菜单
    imageContextMenu.visible = false
    showCustomInput.value = false
    customSizeValue.value = ''
    
    // 关闭工具栏下拉菜单（如果点击不在下拉区域内）
    const target = e.target as HTMLElement
    if (!target.closest('.toolbar-dropdown')) {
      closeAllDropdowns()
    }
  })
})

// Markdown 渲染功能
// - 有选中文本：只渲染选中部分
// - 无选中文本：检测是否有 Markdown 语法，有才渲染
async function handleRenderMarkdown(): Promise<void> {
  if (!editor.value) return
  
  const { from, to, empty } = editor.value.state.selection
  
  // Markdown 语法检测正则（标题、粗体、列表、表格、公式、代码块等）
  const markdownSyntaxRegex = /^#{1,6}\s|^\s*[-*+]\s|^\s*\d+\.\s|\*\*[^*]+\*\*|__[^_]+__|`[^`]+`|```|\$\$?[^$]+\$\$?|^\s*>\s|^\|.+\|$/m
  
  if (!empty) {
    // === 有选中文本：只渲染选中部分 ===
    const selectedText = editor.value.state.doc.textBetween(from, to, '\n')
    if (!selectedText.trim()) return
    
    // 检测是否有 Markdown 语法
    if (!markdownSyntaxRegex.test(selectedText)) {
      alert('选中的文本未检测到 Markdown 语法。\n\n支持：# 标题、**粗体**、- 列表、```代码块、$公式$ 等')
      return
    }
    
    // 渲染选中部分
    let processedText = selectedText
    // 处理数学公式
    processedText = processedText.replace(/\$\$([\s\S]+?)\$\$/g, (_, formula) => {
      return `<div data-math="true" data-latex="${formula.replace(/"/g, '&quot;')}" data-display="true"></div>`
    })
    processedText = processedText.replace(/\$([^\$\n]+?)\$/g, (_, formula) => {
      return `<span data-math="true" data-latex="${formula.replace(/"/g, '&quot;')}"></span>`
    })
    
    const rawHtml = await marked.parse(processedText, { gfm: true, breaks: true })
    const cleanHtml = DOMPurify.sanitize(rawHtml, {
      ADD_ATTR: ['data-math', 'data-latex', 'data-display']
    })
    
    // 替换选中内容
    editor.value.chain().focus().deleteSelection().insertContent(cleanHtml).run()
    return
  }
  
  // === 无选中文本：检测全文是否有 Markdown 语法 ===
  const fullText = editor.value.getText({ blockSeparator: '\n' })
  if (!fullText.trim()) return
  
  // 检测是否有 Markdown 语法
  if (!markdownSyntaxRegex.test(fullText)) {
    alert('未检测到 Markdown 语法，无需渲染。\n\n提示：可以选中部分文本后点击此按钮进行局部渲染。')
    return
  }
  
  // 图片保护：提取所有图片
  interface ProtectedImg { src: string; width: string; align: string }
  const images: ProtectedImg[] = []
  editor.value.state.doc.descendants((node) => {
    if (node.type.name === 'image') {
      images.push({
        src: node.attrs.src,
        width: node.attrs.width || '50%',
        align: node.attrs.align || 'left'
      })
    }
  })
  
  // 处理数学公式
  let processedText = fullText
  processedText = processedText.replace(/\$\$([\s\S]+?)\$\$/g, (_, formula) => {
    return `<div data-math="true" data-latex="${formula.replace(/"/g, '&quot;')}" data-display="true"></div>`
  })
  processedText = processedText.replace(/\$([^\$\n]+?)\$/g, (_, formula) => {
    return `<span data-math="true" data-latex="${formula.replace(/"/g, '&quot;')}"></span>`
  })

  // 配置代码高亮
  const renderer = new marked.Renderer()
  renderer.code = function({ text, lang }) {
    const language = lang && hljs.getLanguage(lang) ? lang : 'plaintext'
    const highlighted = hljs.highlight(text, { language }).value
    return `<pre class="hljs-container"><code class="hljs language-${language}">${highlighted}</code></pre>`
  }

  // 渲染 Markdown
  const html = await marked.parse(processedText, { renderer, gfm: true, breaks: true })
  const cleanHtml = DOMPurify.sanitize(html, {
    ADD_ATTR: ['data-math', 'data-latex', 'data-display', 'contenteditable']
  })
  
  editor.value.chain().setContent(cleanHtml, true).focus().run()
  
  // 恢复图片
  if (images.length > 0) {
    images.forEach((img) => {
      editor.value?.chain()
        .focus('end')
        .insertContent({
          type: 'paragraph',
          content: [{
            type: 'image',
            attrs: { src: img.src, width: img.width, align: img.align }
          }]
        })
        .run()
    })
  }
}

// 监听当前笔记变化 - 只在切换笔记时更新编辑器
watch(
  () => noteStore.currentNote?.id,
  async (newId, oldId) => {
    // 等待编辑器准备好
    if (!editor.value) {
      // 如果编辑器还没准备好，等待一小段时间后重试
      await new Promise(resolve => setTimeout(resolve, 50))
      if (!editor.value) return
    }
    
    if (noteStore.currentNote) {
      currentEditingId = newId || null
      localTitle.value = noteStore.currentNote.title
      isDirty.value = false  // 切换笔记时重置未保存状态

      // 切换笔记时设置内容
      let newContent = noteStore.currentNote.content || ''
      
      // 自动识别并转换数学公式
      newContent = newContent.replace(/\$\$([\s\S]+?)\$\$/g, (match, formula) => {
        const escaped = formula.replace(/"/g, '&quot;')
        return `<div data-math="true" data-latex="${escaped}" data-display="true"></div>`
      })
      newContent = newContent.replace(/\$([^\$\n]+?)\$/g, (match, formula) => {
        const escaped = formula.replace(/"/g, '&quot;')
        return `<span data-math="true" data-latex="${escaped}"></span>`
      })
      
      // 只在切换笔记时重置历史
      if (newId !== oldId) {
        const { state, view } = editor.value
        const tr = state.tr.setMeta('addToHistory', false)
        view.dispatch(tr)
      }
      
      editor.value.commands.setContent(newContent, false, { preserveWhitespace: 'full' })

      // 设置可编辑状态
      const isTrash = noteStore.currentView === 'trash'
      editor.value.setEditable(!isTrash)
    }
  },
  { immediate: true }
)

// 同步本地标题
watch(
  () => noteStore.currentNote?.title,
  (newTitle) => {
    if (newTitle !== undefined && document.activeElement !== titleInputRef.value) {
      localTitle.value = newTitle
    }
  }
)

// 处理标题输入 - 使用本地状态
function handleTitleInput(event: Event): void {
  const input = event.target as HTMLInputElement
  localTitle.value = input.value
  isDirty.value = true

  // 防抖保存标题
  if (titleSaveTimer) {
    clearTimeout(titleSaveTimer)
  }

  titleSaveTimer = setTimeout(async () => {
    if (noteStore.currentNote) {
      await noteRepository.update(noteStore.currentNote.id, { title: localTitle.value })
      isDirty.value = false
    }
  }, 500)
}

// 失去焦点时立即保存
async function handleTitleBlur(): Promise<void> {
  if (titleSaveTimer) {
    clearTimeout(titleSaveTimer)
    titleSaveTimer = null
  }
  if (noteStore.currentNote && localTitle.value !== noteStore.currentNote.title) {
    await noteStore.updateNote(noteStore.currentNote.id, { title: localTitle.value })
    isDirty.value = false
  }
}

// 处理分类变化
async function handleCategoryChange(event: Event): Promise<void> {
  const select = event.target as HTMLSelectElement
  if (noteStore.currentNote) {
    await noteStore.updateNote(noteStore.currentNote.id, {
      categoryId: select.value || null
    })
  }
}

// 切换置顶
function handleTogglePin(): void {
  if (noteStore.currentNote) {
    noteStore.togglePin(noteStore.currentNote.id)
  }
}

// 删除笔记
function handleDelete(): void {
  if (noteStore.currentNote) {
    if (noteStore.currentView === 'trash') {
      if (confirm('确定要永久删除这篇笔记吗？此操作不可恢复。')) {
        noteStore.permanentDeleteNote(noteStore.currentNote.id)
      }
    } else {
      noteStore.deleteNote(noteStore.currentNote.id)
    }
  }
}

// 恢复笔记
function handleRestore(): void {
  if (noteStore.currentNote) {
    noteStore.restoreNote(noteStore.currentNote.id)
  }
}

// 导出当前笔记为 Markdown
async function handleExportCurrentMarkdown(): Promise<void> {
  if (noteStore.currentNote) {
    await exportService.exportNoteAsMarkdown(noteStore.currentNote)
  }
}

onBeforeUnmount(() => {
  editor.value?.destroy()
  if (saveTimer) {
    clearTimeout(saveTimer)
  }
  if (titleSaveTimer) {
    clearTimeout(titleSaveTimer)
  }
})
</script>

<style lang="scss" scoped>
.note-editor {
  flex: 1;
  display: flex;
  flex-direction: column;
  background: var(--color-bg-card);
  overflow: hidden;
  // 优化过渡
  transition: background-color 0.2s ease;
}

.note-editor__empty {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  color: var(--color-text-muted);

  svg {
    margin-bottom: $spacing-md;
    opacity: 0.4;
  }

  p {
    font-size: $font-size-md;
  }
}

.note-editor__toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: $spacing-sm $spacing-md;
  border-bottom: 1px solid var(--color-border-light);
  background: var(--color-bg-primary);
  flex-shrink: 0;
  transition: background-color 0.2s ease;
  gap: $spacing-sm;
}

.note-editor__tools {
  display: flex;
  align-items: center;
  gap: 2px;
  flex-wrap: wrap;
}

// 工具栏分隔线
.toolbar-divider {
  width: 1px;
  height: 20px;
  background: var(--color-border);
  margin: 0 6px;
}

// 下拉菜单组件
.toolbar-dropdown {
  position: relative;
  
  &__trigger {
    display: flex;
    align-items: center;
    gap: 4px;
    padding: 4px 8px;
    border: 1px solid transparent;
    border-radius: $radius-sm;
    background: transparent;
    color: var(--color-text-secondary);
    font-size: $font-size-sm;
    cursor: pointer;
    transition: all 0.15s ease;
    min-width: 40px;
    height: 32px;
    
    &:hover {
      background: var(--color-bg-hover);
      color: var(--color-text-primary);
    }
    
    &--active {
      background: var(--color-bg-hover);
      border-color: var(--color-border);
    }
    
    &--color {
      padding: 4px 6px;
      min-width: 36px;
    }
  }
  
  &__label {
    font-weight: 500;
    min-width: 20px;
    text-align: center;
  }
  
  &__menu {
    position: absolute;
    top: 100%;
    left: 0;
    margin-top: 4px;
    min-width: 100px;
    background: var(--color-bg-card);
    border: 1px solid var(--color-border);
    border-radius: $radius-md;
    box-shadow: var(--shadow-lg);
    z-index: 100;
    padding: 4px;
    
    &--colors {
      display: grid;
      grid-template-columns: repeat(4, 1fr);
      gap: 4px;
      min-width: 120px;
      padding: 8px;
    }
  }
  
  &__item {
    display: flex;
    align-items: center;
    gap: 8px;
    width: 100%;
    padding: 8px 12px;
    border: none;
    border-radius: $radius-sm;
    background: transparent;
    color: var(--color-text-primary);
    font-size: $font-size-sm;
    cursor: pointer;
    text-align: left;
    white-space: nowrap;
    transition: background-color 0.1s ease;
    
    &:hover {
      background: var(--color-bg-hover);
    }
    
    &--active {
      background: var(--color-bg-active);
      font-weight: 500;
    }
    
    svg {
      flex-shrink: 0;
    }
  }
}

// 颜色选择器
.color-swatch {
  width: 24px;
  height: 24px;
  border: 1px solid var(--color-border);
  border-radius: $radius-sm;
  cursor: pointer;
  transition: transform 0.1s ease, box-shadow 0.1s ease;
  
  &:hover {
    transform: scale(1.1);
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
  }
  
  &--clear {
    display: flex;
    align-items: center;
    justify-content: center;
    background: var(--color-bg-secondary);
    color: var(--color-text-muted);
  }
}

// 文字颜色图标
.color-icon {
  font-weight: bold;
  font-size: 14px;
  border-bottom: 3px solid var(--underline-color, #1a1a1a);
  line-height: 1;
  padding-bottom: 2px;
}

// 高亮图标
.highlight-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 18px;
  height: 18px;
  border-radius: 2px;
  background: var(--bg-color, transparent);
}

.note-editor__tool {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  border: 1px solid transparent;
  border-radius: $radius-sm;
  background: transparent;
  color: var(--color-text-secondary);
  font-size: $font-size-sm;
  cursor: pointer;
  transition: background-color 0.1s ease, color 0.1s ease, border-color 0.1s ease;

  &:hover {
    background: var(--color-bg-hover);
    color: var(--color-text-primary);
  }

  &--active {
    border-color: var(--color-border-dark);
    background: var(--color-bg-card);
    color: var(--color-text-primary);
  }

  &--danger:hover {
    background: rgba(196, 92, 92, 0.1);
    color: var(--color-danger);
  }
}

.note-editor__actions {
  display: flex;
  align-items: center;
  gap: $spacing-sm;
  flex-shrink: 0;
}

// 响应式工具栏 - 小屏幕隐藏/显示
.toolbar-hide-sm {
  display: flex;
}

.toolbar-show-sm {
  display: none !important;
}

// 下拉菜单分隔线
.toolbar-dropdown__divider {
  height: 1px;
  background: var(--color-border-light);
  margin: 4px 0;
}

// 使用容器查询实现真正的响应式
.note-editor {
  container-type: inline-size;
  container-name: editor;
}

// 当编辑器宽度 < 550px 时隐藏次要工具
@container editor (max-width: 550px) {
  .toolbar-hide-sm {
    display: none !important;
  }
  
  .toolbar-show-sm {
    display: flex !important;
  }
  
  .note-editor__toolbar {
    padding: 6px 8px;
  }
  
  .toolbar-divider {
    margin: 0 3px;
  }
  
  .toolbar-dropdown__trigger {
    padding: 3px 5px;
    min-width: 28px;
  }
  
  .note-editor__tool {
    width: 26px;
    height: 26px;
  }
  
  .note-editor__category-select select {
    max-width: 60px;
    font-size: 11px;
  }
}

.note-editor__category-select {
  select {
    padding: $spacing-xs $spacing-sm;
    border: 1px solid var(--color-border);
    border-radius: $radius-sm;
    background: var(--color-bg-card);
    font-size: $font-size-xs;
    color: var(--color-text-secondary);
    cursor: pointer;
    outline: none;

    &:focus {
      border-color: var(--color-primary);
    }
  }
}

.note-editor__title-wrapper {
  display: flex;
  align-items: center;
  gap: 4px;
  flex-shrink: 0;
}

.note-editor__title {
  flex: 1;
  padding: $spacing-md $spacing-lg;
  border: none;
  background: transparent;
  font-size: $font-size-2xl;
  font-weight: 600;
  color: var(--color-text-primary);
  outline: none;

  &::placeholder {
    color: var(--color-text-placeholder);
  }
}

.note-editor__dirty-indicator {
  font-size: 24px;
  font-weight: bold;
  color: var(--color-accent, #3b82f6);
  padding-right: 16px;
  line-height: 1;
}

.note-editor__content {
  flex: 1;
  padding: 0 $spacing-lg $spacing-lg;
  overflow-y: auto;
  overflow-x: hidden;
  position: relative;

  :deep(.tiptap) {
    outline: none;
    min-height: 100%;
    font-size: $font-size-md;
    line-height: 1.75;
    color: var(--color-text-primary);

    p {
      margin-bottom: $spacing-sm;
    }

    h1, h2, h3 {
      margin-top: $spacing-lg;
      margin-bottom: $spacing-sm;
      font-weight: 600;
      color: var(--color-text-primary);
    }

    h1 { font-size: $font-size-2xl; }
    h2 { font-size: $font-size-xl; }
    h3 { font-size: $font-size-lg; }

    ul, ol {
      padding-left: $spacing-xl;
      margin-bottom: $spacing-sm;
      
      li {
        margin-bottom: $spacing-xs;
        list-style-position: outside;
      }
    }

    ul {
      list-style-type: disc;
    }

    ol {
      list-style-type: decimal;
    }

    ul[data-type="taskList"] {
      list-style: none;
      padding-left: 0;

      li {
        display: flex;
        align-items: flex-start;
        gap: $spacing-sm;

        > label {
          flex-shrink: 0;
          margin-top: 3px;

          input[type="checkbox"] {
            width: 16px;
            height: 16px;
            cursor: pointer;
            accent-color: var(--color-primary);
          }
        }

        > div {
          flex: 1;
        }

        &[data-checked="true"] > div {
          text-decoration: line-through;
          color: var(--color-text-muted);
        }
      }
    }

    pre {
      background: var(--color-bg-secondary);
      border-radius: $radius-md;
      padding: $spacing-md;
      margin: $spacing-md 0;
      overflow-x: auto;
      border: 1px solid var(--color-border);
      
      code {
        background: transparent;
        padding: 0;
        border-radius: 0;
        font-size: 0.9em;
        color: inherit;
      }
    }

    code {
      background: var(--color-bg-secondary);
      padding: 2px 6px;
      border-radius: $radius-sm;
      font-family: 'SFMono-Regular', Consolas, 'Liberation Mono', Menlo, monospace;
      font-size: 0.9em;
      color: var(--color-text-primary);
    }

    .math-block {
      margin: $spacing-lg 0;
      text-align: center;
      overflow-x: auto;
    }

    .math-inline {
      padding: 0 2px;
    }

    .hljs-container {
      position: relative;
    }

    blockquote {
      border-left: 3px solid var(--color-border-dark);
      padding-left: $spacing-md;
      margin: $spacing-md 0;
      color: var(--color-text-secondary);
      font-style: italic;
    }

    table {
      border-collapse: collapse;
      table-layout: auto;
      width: 100%;
      margin: $spacing-md 0;
      overflow: hidden;
      border: 1px solid var(--color-border);
      border-radius: $radius-sm;

      td, th {
        min-width: 1em;
        border: 1px solid var(--color-border-light);
        padding: 8px 12px;
        vertical-align: middle;
        box-sizing: border-box;
        position: relative;
        text-align: left;

        > * {
          margin-bottom: 0;
        }
      }

      th {
        font-weight: 600;
        background-color: var(--color-bg-secondary);
        color: var(--color-text-primary);
        border-bottom: 2px solid var(--color-border);
      }

      tr:nth-child(even) {
        background-color: var(--color-bg-hover);
      }

      tr:hover {
        background-color: var(--color-bg-active);
      }

      .selectedCell:after {
        z-index: 2;
        position: absolute;
        content: "";
        left: 0; right: 0; top: 0; bottom: 0;
        background: rgba(200, 200, 255, 0.4);
        pointer-events: none;
      }

      .column-resize-handle {
        position: absolute;
        right: -2px;
        top: 0;
        bottom: -2px;
        width: 4px;
        background-color: #adf;
        pointer-events: none;
      }
    }

    img {
      max-width: 100%;
      height: auto;
      border-radius: $radius-sm;
      margin: $spacing-sm 0;
      display: block;
      cursor: default;

      &.ProseMirror-selectednode {
        outline: 2px solid var(--color-primary);
      }

      // 对齐样式
      &.image-align-left {
        margin-left: 0;
        margin-right: auto;
      }

      &.image-align-center {
        margin-left: auto;
        margin-right: auto;
      }

      &.image-align-right {
        margin-left: auto;
        margin-right: 0;
      }
    }

    // 数学公式样式
    .math-node {
      display: inline-block;
      padding: 2px 6px;
      margin: 0 2px;
      background: var(--color-bg-hover);
      border-radius: $radius-sm;
      cursor: pointer;
      transition: background $transition-fast;

      &:hover {
        background: var(--color-bg-active);
      }

      &.ProseMirror-selectednode {
        outline: 2px solid var(--color-primary);
        outline-offset: 2px;
      }
    }

    .math-placeholder {
      color: var(--color-text-muted);
      font-style: italic;
    }

    .math-error {
      color: var(--color-danger);
      font-family: monospace;
    }

    .is-editor-empty:first-child::before {
      content: attr(data-placeholder);
      float: left;
      color: var(--color-text-placeholder);
      pointer-events: none;
      height: 0;
    }
  }
}

// 图片右键菜单（全局定位）
.image-context-menu {
  position: fixed;
  background: var(--color-bg-secondary);
  border: 1px solid var(--color-border);
  border-radius: $radius-md;
  box-shadow: var(--shadow-lg);
  padding: $spacing-sm;
  z-index: 9999;
  min-width: 160px;
  
  .menu-item {
    padding: $spacing-sm $spacing-md;
    cursor: pointer;
    font-size: 13px;
    color: var(--color-text-primary);
    border-radius: $radius-sm;
    
    &:hover {
      background: var(--color-bg-hover);
    }
    
    &.danger {
      color: var(--color-danger);
    }
  }
  
  .menu-divider {
    height: 1px;
    background: var(--color-border);
    margin: $spacing-sm 0;
  }
  
  // 分段按钮组（通用）
  .menu-segment-group {
    display: flex;
    margin-bottom: $spacing-xs;
    border: 1px solid var(--color-border);
    border-radius: $radius-sm;
    overflow: hidden;
    
    .segment-btn {
      flex: 1;
      display: flex;
      align-items: center;
      justify-content: center;
      padding: 6px 4px;
      border: none;
      background: var(--color-bg-card);
      color: var(--color-text-secondary);
      cursor: pointer;
      font-size: 12px;
      transition: background-color 0.1s ease, color 0.1s ease;
      
      &:not(:last-child) {
        border-right: 1px solid var(--color-border);
      }
      
      &:hover {
        background: var(--color-bg-hover);
        color: var(--color-text-primary);
      }
      
      &.active {
        background: var(--color-accent);
        color: white;
      }
      
      svg {
        width: 14px;
        height: 14px;
      }
    }
  }
  
  // 自定义尺寸输入
  .custom-size-input {
    display: flex;
    align-items: center;
    gap: 4px;
    margin-bottom: $spacing-xs;
    padding: 4px;
    border: 1px solid var(--color-border);
    border-radius: $radius-sm;
    background: var(--color-bg-card);
    
    input {
      width: 50px;
      padding: 4px 6px;
      border: 1px solid var(--color-border);
      border-radius: $radius-sm;
      background: var(--color-bg-primary);
      color: var(--color-text-primary);
      font-size: 12px;
      outline: none;
      
      &:focus {
        border-color: var(--color-primary);
      }
      
      // 隐藏数字输入框的上下箭头
      &::-webkit-outer-spin-button,
      &::-webkit-inner-spin-button {
        -webkit-appearance: none;
        margin: 0;
      }
    }
    
    .unit {
      font-size: 12px;
      color: var(--color-text-secondary);
    }
    
    .apply-btn {
      padding: 4px 8px;
      border: none;
      border-radius: $radius-sm;
      background: var(--color-accent);
      color: white;
      font-size: 12px;
      cursor: pointer;
      
      &:hover {
        opacity: 0.9;
      }
    }
  }
}
</style>

