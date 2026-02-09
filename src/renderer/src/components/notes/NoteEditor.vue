<template>
  <div class="note-editor" ref="editorRootRef">
    <!-- 无笔记状态 -->
    <div v-if="!noteStore.currentNote" class="note-editor__empty">
      <svg width="64" height="64" viewBox="0 0 64 64" fill="none">
        <rect x="12" y="8" width="40" height="48" rx="4" stroke="currentColor" stroke-width="2"/>
        <path d="M22 22H42M22 32H38M22 42H34" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
      </svg>
      <p>{{ t('editor.emptyHint') }}</p>
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
              :title="t('editor.fontSize')"
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

          <!-- 撤销 / 重做（仅当前笔记编辑历史） -->
          <button
            class="note-editor__tool toolbar-hide-sm"
            :title="`${t('editor.undo')} (Ctrl+Z)`"
            :disabled="!canUndo"
            @click="handleUndo"
          >
            <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
              <path d="M6 5L3 8L6 11" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
              <path d="M4 8H9.2C11.3 8 13 9.7 13 11.8V12.2" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
            </svg>
          </button>
          <button
            class="note-editor__tool toolbar-hide-sm"
            :title="`${t('editor.redo')} (Ctrl+Y)`"
            :disabled="!canRedo"
            @click="handleRedo"
          >
            <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
              <path d="M10 5L13 8L10 11" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
              <path d="M12 8H6.8C4.7 8 3 9.7 3 11.8V12.2" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
            </svg>
          </button>

          <div class="toolbar-divider toolbar-hide-sm"></div>

          <!-- 基础格式：加粗、斜体、下划线 -->
          <button class="note-editor__tool" :class="{ 'note-editor__tool--active': editor?.isActive('bold') }" :title="t('editor.bold')" @click="editor?.chain().focus().toggleBold().run()">
            <strong>B</strong>
          </button>
          <button class="note-editor__tool" :class="{ 'note-editor__tool--active': editor?.isActive('italic') }" :title="t('editor.italic')" @click="editor?.chain().focus().toggleItalic().run()">
            <em>I</em>
          </button>
          <button class="note-editor__tool" :class="{ 'note-editor__tool--active': editor?.isActive('underline') }" :title="t('editor.underline')" @click="editor?.chain().focus().toggleUnderline().run()">
            <u>U</u>
          </button>
          <!-- 删除线 - 小屏幕隐藏 -->
          <button class="note-editor__tool toolbar-hide-sm" :class="{ 'note-editor__tool--active': editor?.isActive('strike') }" :title="t('editor.strike')" @click="editor?.chain().focus().toggleStrike().run()">
            <s>S</s>
          </button>

          <div class="toolbar-divider"></div>

          <!-- 文字颜色下拉 -->
          <div class="toolbar-dropdown toolbar-hide-md" ref="textColorDropdownRef">
            <button 
              class="toolbar-dropdown__trigger toolbar-dropdown__trigger--color"
              @click.stop="toggleTextColorDropdown"
              :title="t('editor.textColor')"
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
              <button class="color-swatch color-swatch--clear" :title="t('editor.clearColor')" @click="clearTextColor">
                <svg width="12" height="12" viewBox="0 0 12 12"><path d="M2 2L10 10M10 2L2 10" stroke="currentColor" stroke-width="1.5"/></svg>
              </button>
            </div>
          </div>

          <!-- 背景高亮下拉 - 小屏幕隐藏 -->
          <div class="toolbar-dropdown toolbar-hide-sm" ref="highlightDropdownRef">
            <button 
              class="toolbar-dropdown__trigger toolbar-dropdown__trigger--color"
              @click.stop="toggleHighlightDropdown"
              :title="t('editor.highlight')"
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
              <button class="color-swatch color-swatch--clear" :title="t('editor.clearHighlight')" @click="clearHighlight">
                <svg width="12" height="12" viewBox="0 0 12 12"><path d="M2 2L10 10M10 2L2 10" stroke="currentColor" stroke-width="1.5"/></svg>
              </button>
            </div>
          </div>

          <div class="toolbar-divider toolbar-hide-sm"></div>

          <!-- 标题下拉 -->
          <div class="toolbar-dropdown toolbar-hide-md" ref="headingDropdownRef">
            <button 
              class="toolbar-dropdown__trigger"
              @click.stop="toggleHeadingDropdown"
              :title="t('editor.heading')"
            >
              <span class="toolbar-dropdown__label">{{ currentHeadingLabel }}</span>
              <svg width="10" height="10" viewBox="0 0 10 10"><path d="M2 4L5 7L8 4" stroke="currentColor" stroke-width="1.2" fill="none"/></svg>
            </button>
            <div v-show="headingDropdownOpen" class="toolbar-dropdown__menu">
              <button class="toolbar-dropdown__item" :class="{ 'toolbar-dropdown__item--active': !editor?.isActive('heading') }" @click="setParagraph">{{ t('editor.paragraph') }}</button>
              <button class="toolbar-dropdown__item" :class="{ 'toolbar-dropdown__item--active': editor?.isActive('heading', { level: 1 }) }" @click="setHeading(1)">{{ t('editor.heading1') }}</button>
              <button class="toolbar-dropdown__item" :class="{ 'toolbar-dropdown__item--active': editor?.isActive('heading', { level: 2 }) }" @click="setHeading(2)">{{ t('editor.heading2') }}</button>
              <button class="toolbar-dropdown__item" :class="{ 'toolbar-dropdown__item--active': editor?.isActive('heading', { level: 3 }) }" @click="setHeading(3)">{{ t('editor.heading3') }}</button>
            </div>
          </div>

          <div class="toolbar-divider toolbar-hide-md"></div>

          <!-- 列表下拉 -->
          <div class="toolbar-dropdown toolbar-hide-md" ref="listDropdownRef">
            <button 
              class="toolbar-dropdown__trigger"
              :class="{ 'toolbar-dropdown__trigger--active': editor?.isActive('bulletList') || editor?.isActive('orderedList') || editor?.isActive('taskList') }"
              @click.stop="toggleListDropdown"
              :title="t('editor.list')"
            >
              <svg width="16" height="16" viewBox="0 0 16 16"><circle cx="3" cy="4" r="1.5" fill="currentColor"/><circle cx="3" cy="8" r="1.5" fill="currentColor"/><circle cx="3" cy="12" r="1.5" fill="currentColor"/><line x1="6" y1="4" x2="14" y2="4" stroke="currentColor" stroke-width="1.5"/><line x1="6" y1="8" x2="14" y2="8" stroke="currentColor" stroke-width="1.5"/><line x1="6" y1="12" x2="14" y2="12" stroke="currentColor" stroke-width="1.5"/></svg>
              <svg width="10" height="10" viewBox="0 0 10 10"><path d="M2 4L5 7L8 4" stroke="currentColor" stroke-width="1.2" fill="none"/></svg>
            </button>
            <div v-show="listDropdownOpen" class="toolbar-dropdown__menu">
              <button class="toolbar-dropdown__item" :class="{ 'toolbar-dropdown__item--active': editor?.isActive('bulletList') }" @click="toggleBulletList">
                <svg width="14" height="14" viewBox="0 0 14 14"><circle cx="2" cy="3" r="1.2" fill="currentColor"/><circle cx="2" cy="7" r="1.2" fill="currentColor"/><circle cx="2" cy="11" r="1.2" fill="currentColor"/><line x1="5" y1="3" x2="12" y2="3" stroke="currentColor" stroke-width="1.2"/><line x1="5" y1="7" x2="12" y2="7" stroke="currentColor" stroke-width="1.2"/><line x1="5" y1="11" x2="12" y2="11" stroke="currentColor" stroke-width="1.2"/></svg>
                {{ t('editor.bulletList') }}
              </button>
              <button class="toolbar-dropdown__item" :class="{ 'toolbar-dropdown__item--active': editor?.isActive('orderedList') }" @click="toggleOrderedList">
                <svg width="14" height="14" viewBox="0 0 14 14"><text x="1" y="5" font-size="5" fill="currentColor">1</text><text x="1" y="9" font-size="5" fill="currentColor">2</text><text x="1" y="13" font-size="5" fill="currentColor">3</text><line x1="5" y1="3" x2="12" y2="3" stroke="currentColor" stroke-width="1.2"/><line x1="5" y1="7" x2="12" y2="7" stroke="currentColor" stroke-width="1.2"/><line x1="5" y1="11" x2="12" y2="11" stroke="currentColor" stroke-width="1.2"/></svg>
                {{ t('editor.orderedList') }}
              </button>
              <button class="toolbar-dropdown__item" :class="{ 'toolbar-dropdown__item--active': editor?.isActive('taskList') }" @click="toggleTaskList">
                <svg width="14" height="14" viewBox="0 0 14 14"><rect x="1" y="1" width="4" height="4" rx="0.5" stroke="currentColor" fill="none"/><path d="M2 3L2.8 3.8L4.2 2.2" stroke="currentColor" stroke-width="0.8"/><rect x="1" y="5" width="4" height="4" rx="0.5" stroke="currentColor" fill="none"/><rect x="1" y="9" width="4" height="4" rx="0.5" stroke="currentColor" fill="none"/><line x1="7" y1="3" x2="13" y2="3" stroke="currentColor" stroke-width="1.2"/><line x1="7" y1="7" x2="13" y2="7" stroke="currentColor" stroke-width="1.2"/><line x1="7" y1="11" x2="13" y2="11" stroke="currentColor" stroke-width="1.2"/></svg>
                {{ t('editor.taskList') }}
              </button>
            </div>
          </div>

          <!-- 引用 - 小屏幕隐藏 -->
          <button class="note-editor__tool toolbar-hide-sm" :class="{ 'note-editor__tool--active': editor?.isActive('blockquote') }" :title="t('editor.quote')" @click="editor?.chain().focus().toggleBlockquote().run()">
            <svg width="16" height="16" viewBox="0 0 16 16"><path d="M4 4C2.5 4 2 5 2 6.5C2 8 2.5 9 4 9C5.5 9 6 8 6 6.5C6 4 4 11 4 11" stroke="currentColor" stroke-width="1.5" fill="none"/><path d="M11 4C9.5 4 9 5 9 6.5C9 8 9.5 9 11 9C12.5 9 13 8 13 6.5C13 4 11 11 11 11" stroke="currentColor" stroke-width="1.5" fill="none"/></svg>
          </button>

          <!-- 代码 - 小屏幕隐藏 -->
          <button class="note-editor__tool toolbar-hide-sm" :class="{ 'note-editor__tool--active': editor?.isActive('code') }" :title="t('editor.inlineCode')" @click="editor?.chain().focus().toggleCode().run()">
            &lt;/&gt;
          </button>

          <div class="toolbar-divider toolbar-hide-sm toolbar-hide-narrow"></div>

          <!-- 插入下拉 -->
          <div class="toolbar-dropdown" ref="insertDropdownRef">
            <button 
              class="toolbar-dropdown__trigger"
              @click.stop="toggleInsertDropdown"
              :title="t('editor.insert')"
            >
              <svg width="16" height="16" viewBox="0 0 16 16"><line x1="8" y1="3" x2="8" y2="13" stroke="currentColor" stroke-width="1.5"/><line x1="3" y1="8" x2="13" y2="8" stroke="currentColor" stroke-width="1.5"/></svg>
              <svg width="10" height="10" viewBox="0 0 10 10"><path d="M2 4L5 7L8 4" stroke="currentColor" stroke-width="1.2" fill="none"/></svg>
            </button>
            <div v-show="insertDropdownOpen" class="toolbar-dropdown__menu">
              <button class="toolbar-dropdown__item" @click="insertTable">
                <svg width="14" height="14" viewBox="0 0 14 14"><rect x="1" y="1" width="12" height="12" rx="1" stroke="currentColor" fill="none"/><line x1="1" y1="5" x2="13" y2="5" stroke="currentColor"/><line x1="5" y1="1" x2="5" y2="13" stroke="currentColor"/></svg>
                {{ t('editor.table') }}
              </button>
              <button class="toolbar-dropdown__item" @click="insertImage">
                <svg width="14" height="14" viewBox="0 0 14 14"><rect x="1" y="2" width="12" height="10" rx="1" stroke="currentColor" fill="none"/><circle cx="4" cy="5" r="1.2" fill="currentColor"/><path d="M1 10L4 7L7 10L10 6L13 9" stroke="currentColor" stroke-width="1" fill="none"/></svg>
                {{ t('editor.image') }}
              </button>
              <button class="toolbar-dropdown__item" @click="insertMath">
                <svg width="14" height="14" viewBox="0 0 14 14"><text x="1" y="11" font-size="9" font-style="italic" fill="currentColor">∑</text><text x="8" y="7" font-size="5" fill="currentColor">x²</text></svg>
                {{ t('editor.math') }}
              </button>
              <button class="toolbar-dropdown__item" @click="deleteTable" v-if="editor?.isActive('table')">
                <svg width="14" height="14" viewBox="0 0 14 14"><rect x="1" y="1" width="12" height="12" rx="1" stroke="currentColor" fill="none"/><line x1="1" y1="5" x2="13" y2="5" stroke="currentColor"/><line x1="5" y1="1" x2="5" y2="13" stroke="currentColor"/><line x1="3" y1="3" x2="11" y2="11" stroke="#e74c3c" stroke-width="1.5"/><line x1="11" y1="3" x2="3" y2="11" stroke="#e74c3c" stroke-width="1.5"/></svg>
                {{ t('editor.deleteTable') }}
              </button>
              <!-- 小屏幕下显示更多格式选项 -->
              <div class="toolbar-dropdown__divider toolbar-show-sm"></div>
              <button class="toolbar-dropdown__item toolbar-show-sm" :class="{ 'toolbar-dropdown__item--active': editor?.isActive('strike') }" @click="editor?.chain().focus().toggleStrike().run(); insertDropdownOpen = false">
                <s>S</s> {{ t('editor.strike') }}
              </button>
              <button class="toolbar-dropdown__item toolbar-show-sm" :class="{ 'toolbar-dropdown__item--active': editor?.isActive('blockquote') }" @click="editor?.chain().focus().toggleBlockquote().run(); insertDropdownOpen = false">
                <svg width="14" height="14" viewBox="0 0 14 14"><path d="M3 3C1.8 3 1.5 3.8 1.5 5C1.5 6.2 1.8 7 3 7C4.2 7 4.5 6.2 4.5 5C4.5 3 3 9 3 9" stroke="currentColor" stroke-width="1.2" fill="none"/><path d="M9 3C7.8 3 7.5 3.8 7.5 5C7.5 6.2 7.8 7 9 7C10.2 7 10.5 6.2 10.5 5C10.5 3 9 9 9 9" stroke="currentColor" stroke-width="1.2" fill="none"/></svg>
                {{ t('editor.quote') }}
              </button>
              <button class="toolbar-dropdown__item toolbar-show-sm" :class="{ 'toolbar-dropdown__item--active': editor?.isActive('code') }" @click="editor?.chain().focus().toggleCode().run(); insertDropdownOpen = false">
                &lt;/&gt; 代码
              </button>
            </div>
          </div>
        </div>

        <div class="note-editor__actions">
          <button
            ref="outlineButtonRef"
            class="note-editor__tool"
            :class="{ 'note-editor__tool--active': showOutlinePanel }"
            :title="t('editor.outline')"
            @click="toggleOutlinePanel"
          >
            <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
              <circle cx="3" cy="4" r="1.3" fill="currentColor" />
              <circle cx="3" cy="8" r="1.3" fill="currentColor" />
              <circle cx="3" cy="12" r="1.3" fill="currentColor" />
              <line x1="6" y1="4" x2="14" y2="4" stroke="currentColor" stroke-width="1.4" stroke-linecap="round" />
              <line x1="6" y1="8" x2="14" y2="8" stroke="currentColor" stroke-width="1.4" stroke-linecap="round" />
              <line x1="6" y1="12" x2="14" y2="12" stroke="currentColor" stroke-width="1.4" stroke-linecap="round" />
            </svg>
          </button>

          <!-- 分类选择 -->
          <div class="note-editor__category-select">
            <select
              :value="noteStore.currentNote.categoryId || ''"
              @change="handleCategoryChange"
            >
              <option value="">{{ t('editor.categoryNone') }}</option>
              <option
                v-for="cat in categoryStore.categories"
                :key="cat.id"
                :value="cat.id"
              >
                {{ cat.name }}
              </option>
            </select>
          </div>

          <!-- Markdown 渲染按钮 -->
          <button
            v-if="noteStore.currentView !== 'trash'"
            class="note-editor__tool"
            :title="t('editor.renderMarkdown')"
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
            :title="t('editor.pin')"
            @click="handleTogglePin"
          >
            <svg width="18" height="18" viewBox="0 0 18 18" fill="none">
              <path d="M9 2L10.5 6.5L15 7L11.5 10L12.5 15L9 12.5L5.5 15L6.5 10L3 7L7.5 6.5L9 2Z" stroke="currentColor" stroke-width="1.3" stroke-linejoin="round" :fill="noteStore.currentNote.isPinned ? 'currentColor' : 'none'"/>
            </svg>
          </button>

          <!-- 更多操作菜单 -->
          <div class="toolbar-dropdown" ref="moreMenuRef">
            <button 
              ref="moreMenuButtonRef"
              class="note-editor__tool"
              @click.stop="toggleMoreMenu"
              :title="t('editor.more')"
            >
              <svg width="18" height="18" viewBox="0 0 18 18" fill="none">
                <circle cx="9" cy="4" r="1.5" fill="currentColor"/>
                <circle cx="9" cy="9" r="1.5" fill="currentColor"/>
                <circle cx="9" cy="14" r="1.5" fill="currentColor"/>
              </svg>
            </button>
          </div>
        </div>
      </div>

      <!-- 标题输入 -->
      <div class="note-editor__title-wrapper">
        <input
          ref="titleInputRef"
          :value="localTitle"
          class="note-editor__title"
          type="text"
          :placeholder="t('editor.titlePlaceholder')"
          :readonly="noteStore.currentView === 'trash'"
          @input="handleTitleInput"
          @blur="handleTitleBlur"
        />
        <span v-if="isDirty" class="note-editor__dirty-indicator" :title="t('editor.unsaved')">*</span>
      </div>

      <!-- 富文本编辑器 -->
      <div class="note-editor__content allow-select" ref="editorContainerRef">
        <EditorContent :editor="editor" />
        
        <!-- 图片调整手柄已移除，使用右键菜单调整 -->
      </div>
    </template>
  </div>

  <Teleport to="body">
    <div
      v-if="showOutlinePanel"
      class="note-editor__outline note-editor__outline--floating"
      :style="outlinePanelStyle"
      @click.stop
    >
      <div class="note-editor__outline-header">{{ t('editor.outline') }}</div>
      <div v-if="!outlineItems.length" class="note-editor__outline-empty">{{ t('editor.outlineEmpty') }}</div>
      <button
        v-for="item in outlineItems"
        :key="item.id"
        class="note-editor__outline-item"
        :class="{ 'note-editor__outline-item--active': item.id === activeOutlineId }"
        :style="{ '--outline-indent': `${(item.level - 1) * 12}px` }"
        @click="jumpToHeading(item)"
      >
        <span class="note-editor__outline-level">H{{ item.level }}</span>
        <span class="note-editor__outline-text">{{ item.text }}</span>
      </button>
    </div>
  </Teleport>
  
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

  <!-- AI 选中文本浮动菜单 -->
  <div 
    v-if="selectionMenu.visible && !aiResult.visible" 
    class="selection-ai-menu"
    :style="selectionMenuStyle"
    @mousedown.prevent
  >
    <div class="selection-ai-menu__actions">
      <button 
        class="selection-ai-menu__btn" 
        @click="handleAIAction('polish')"
        :disabled="aiProcessing"
        title="润色"
      >
        <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
          <path d="M7 1L8.5 4.5L12 5.5L9 8L10 12L7 10L4 12L5 8L2 5.5L5.5 4.5L7 1Z" stroke="currentColor" stroke-width="1.2" fill="none"/>
        </svg>
        润色
      </button>
      <button 
        class="selection-ai-menu__btn" 
        @click="handleAIAction('translate')"
        :disabled="aiProcessing"
        title="翻译"
      >
        <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
          <path d="M2 3H8M5 3V11M8 7L11 11M11 7L8 11" stroke="currentColor" stroke-width="1.2" stroke-linecap="round"/>
        </svg>
        翻译
      </button>
      <button 
        class="selection-ai-menu__btn" 
        @click="handleAIAction('explain')"
        :disabled="aiProcessing"
        title="解释"
      >
        <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
          <circle cx="7" cy="7" r="5" stroke="currentColor" stroke-width="1.2" fill="none"/>
          <path d="M7 4V8M7 10V10.5" stroke="currentColor" stroke-width="1.2" stroke-linecap="round"/>
        </svg>
        解释
      </button>
      <button 
        class="selection-ai-menu__btn" 
        @click="handleAIAction('summarize')"
        :disabled="aiProcessing"
        title="总结"
      >
        <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
          <path d="M3 3H11M3 6H9M3 9H7M3 12H5" stroke="currentColor" stroke-width="1.2" stroke-linecap="round"/>
        </svg>
        总结
      </button>
      <button 
        class="selection-ai-menu__btn" 
        @click="handleAIAction('expand')"
        :disabled="aiProcessing"
        title="扩写"
      >
        <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
          <path d="M7 2V12M2 7H12" stroke="currentColor" stroke-width="1.2" stroke-linecap="round"/>
        </svg>
        扩写
      </button>
      <div class="selection-ai-menu__divider"></div>
      <button 
        class="selection-ai-menu__btn selection-ai-menu__btn--ask" 
        @click="toggleAskInput"
        :disabled="aiProcessing"
        :class="{ 'selection-ai-menu__btn--active': showAskInput }"
        title="自由提问"
      >
        <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
          <path d="M7 1C3.7 1 1 3.2 1 6C1 7.5 1.8 8.8 3 9.7V13L6 10.5C6.3 10.5 6.7 10.5 7 10.5C10.3 10.5 13 8.3 13 5.5C13 3.2 10.3 1 7 1Z" stroke="currentColor" stroke-width="1.2" fill="none"/>
        </svg>
        询问
      </button>
    </div>
    <!-- 自由提问输入框 -->
    <div v-if="showAskInput" class="selection-ai-menu__ask-input">
      <input 
        ref="askInputRef"
        v-model="askInputText"
        type="text"
        placeholder="针对选中文本提问..."
        @keyup.enter="handleAskSubmit"
        @keyup.esc="showAskInput = false"
        :disabled="aiProcessing"
      />
      <button 
        class="selection-ai-menu__ask-submit"
        @click="handleAskSubmit"
        :disabled="aiProcessing || !askInputText.trim()"
      >
        <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
          <path d="M1 7H13M9 3L13 7L9 11" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
        </svg>
      </button>
    </div>
    <div v-if="aiProcessing" class="selection-ai-menu__loading">
      <span class="loading-dot"></span>
      <span>{{ aiStatusText }}</span>
      <button class="selection-ai-menu__cancel" @click.stop="cancelAIProcessing">{{ t('common.cancel') }}</button>
    </div>
  </div>

  <!-- AI 结果预览面板 -->
  <div 
    v-if="aiResult.visible" 
    class="ai-result-panel"
    :style="aiResultStyle"
    @mousedown.prevent
  >
    <div class="ai-result-panel__header">
      <span class="ai-result-panel__action-label">{{ aiResult.actionLabel }}</span>
      <div class="ai-result-panel__header-actions">
        <button v-if="aiProcessing" class="ai-result-panel__stop" @click="cancelAIProcessing">停止</button>
        <button class="ai-result-panel__close" @click="closeAIResult" title="关闭">
          <svg width="12" height="12" viewBox="0 0 12 12"><path d="M2 2L10 10M10 2L2 10" stroke="currentColor" stroke-width="1.5"/></svg>
        </button>
      </div>
    </div>
    <div class="ai-result-panel__content">
      <div v-html="aiResultHtml"></div>
    </div>
    <div class="ai-result-panel__actions">
      <button class="ai-result-panel__btn ai-result-panel__btn--primary" :disabled="aiProcessing" @click="applyAIResult('insert')">
        <svg width="12" height="12" viewBox="0 0 12 12"><path d="M2 6L5 9L10 3" stroke="currentColor" stroke-width="1.5" fill="none"/></svg>
        确认插入
      </button>
      <button class="ai-result-panel__btn" :disabled="aiProcessing" @click="applyAIResult('replace')">
        <svg width="12" height="12" viewBox="0 0 12 12"><path d="M2 6H10M6 2V10" stroke="currentColor" stroke-width="1.5"/></svg>
        替换选中
      </button>
      <button class="ai-result-panel__btn ai-result-panel__btn--secondary" @click="closeAIResult">
        取消
      </button>
    </div>
  </div>

  <!-- 笔记信息弹窗 -->
  <div v-if="noteInfoVisible" class="note-info-modal" @click.self="noteInfoVisible = false">
    <div class="note-info-modal__content">
      <h3 class="note-info-modal__title">笔记信息</h3>
      <div class="note-info-modal__body">
        <div class="note-info-modal__row">
          <span class="note-info-modal__label">{{ t('editor.noteInfo.category') }}</span>
          <span class="note-info-modal__value">{{ noteInfoData.category }}</span>
        </div>
        <div class="note-info-modal__row">
          <span class="note-info-modal__label">{{ t('editor.noteInfo.createdAt') }}</span>
          <span class="note-info-modal__value">{{ noteInfoData.createdAt }}</span>
        </div>
        <div class="note-info-modal__row">
          <span class="note-info-modal__label">{{ t('editor.noteInfo.updatedAt') }}</span>
          <span class="note-info-modal__value">{{ noteInfoData.updatedAt }}</span>
        </div>
        <div class="note-info-modal__row">
          <span class="note-info-modal__label">{{ t('editor.noteInfo.wordCount') }}</span>
          <span class="note-info-modal__value">{{ noteInfoData.wordCount }}</span>
        </div>
        <div class="note-info-modal__row">
          <span class="note-info-modal__label">{{ t('editor.noteInfo.backlinks') }}</span>
          <span class="note-info-modal__value">{{ backlinks.length }}</span>
        </div>
        <div class="note-info-modal__backlinks">
          <div v-if="backlinksLoading" class="note-info-modal__backlinks-loading">
            {{ t('editor.noteInfo.loadingBacklinks') }}
          </div>
          <div v-else-if="backlinks.length === 0" class="note-info-modal__backlinks-empty">
            {{ t('editor.noteInfo.noBacklinks') }}
          </div>
          <button
            v-for="item in backlinks"
            :key="item.id"
            class="note-info-modal__backlink-item"
            type="button"
            @click="handleOpenBacklink(item.id)"
          >
            <span class="note-info-modal__backlink-title">{{ item.title }}</span>
          </button>
        </div>
      </div>
      <button class="note-info-modal__btn" @click="noteInfoVisible = false">{{ t('common.confirm') }}</button>
    </div>
  </div>

  <!-- 更多菜单浮层（脱离编辑器层叠上下文） -->
  <Teleport to="body">
    <div
      v-if="moreMenuOpen"
      ref="moreMenuFloatingRef"
      class="toolbar-dropdown__menu toolbar-dropdown__menu--floating"
      :style="moreMenuStyle"
      @click.stop
    >
      <template v-if="noteStore.currentView !== 'trash'">
        <button class="toolbar-dropdown__item" @click="handleDelete">
          <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
            <path d="M3 4H13M5 4V3.5C5 2.67 5.67 2 6.5 2H9.5C10.33 2 11 2.67 11 3.5V4M12 4V13C12 13.55 11.55 14 11 14H5C4.45 14 4 13.55 4 13V4" stroke="currentColor" stroke-width="1.2" stroke-linecap="round"/>
          </svg>
          删除
        </button>
        <button class="toolbar-dropdown__item" @click="handleToggleLock">
          <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
            <rect x="3" y="7" width="10" height="7" rx="1" stroke="currentColor" stroke-width="1.2"/>
            <path d="M5 7V5C5 3.34 6.34 2 8 2C9.66 2 11 3.34 11 5V7" stroke="currentColor" stroke-width="1.2" stroke-linecap="round"/>
            <circle cx="8" cy="10.5" r="1" fill="currentColor"/>
          </svg>
          {{ noteStore.currentNote.isLocked ? '解锁' : '加锁' }}
        </button>
        <div class="toolbar-dropdown__divider"></div>
        <div class="toolbar-dropdown__submenu">
          <button class="toolbar-dropdown__item toolbar-dropdown__item--has-arrow" @click.stop="toggleExportSubmenu">
            <svg class="arrow-left" width="10" height="10" viewBox="0 0 10 10"><path d="M6 2L3 5L6 8" stroke="currentColor" stroke-width="1.2" fill="none"/></svg>
            <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
              <path d="M3 3H10L13 6V13H3V3Z" stroke="currentColor" stroke-width="1.2" stroke-linecap="round"/>
              <path d="M10 3V6H13" stroke="currentColor" stroke-width="1.2" stroke-linecap="round"/>
            </svg>
            导出
          </button>
          <div v-show="exportSubmenuOpen" class="toolbar-dropdown__submenu-panel">
            <button class="toolbar-dropdown__item" @click="handleExport('markdown')">导出为 Markdown</button>
            <button class="toolbar-dropdown__item" @click="handleExport('txt')">导出为纯文本</button>
            <button class="toolbar-dropdown__item" @click="handleExport('html')">导出为 HTML</button>
            <button class="toolbar-dropdown__item" @click="handleExport('docx')">导出为 Word</button>
            <button class="toolbar-dropdown__item" @click="handleExport('pdf')">导出为 PDF</button>
          </div>
        </div>
        <div class="toolbar-dropdown__divider"></div>
        <button class="toolbar-dropdown__item" @click="showNoteInfo">
          <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
            <circle cx="8" cy="8" r="6" stroke="currentColor" stroke-width="1.2"/>
            <path d="M8 5V5.5M8 7V11" stroke="currentColor" stroke-width="1.2" stroke-linecap="round"/>
          </svg>
          笔记信息
        </button>
      </template>
      <template v-else>
        <button class="toolbar-dropdown__item" @click="handleRestore">
          <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
            <path d="M2 8C2 4.69 4.69 2 8 2C9.96 2 11.68 3.01 12.65 4.54" stroke="currentColor" stroke-width="1.2" stroke-linecap="round"/>
            <path d="M14 8C14 11.31 11.31 14 8 14C6.04 14 4.32 12.99 3.35 11.46" stroke="currentColor" stroke-width="1.2" stroke-linecap="round"/>
            <path d="M12 2V5H9" stroke="currentColor" stroke-width="1.2" stroke-linecap="round" stroke-linejoin="round"/>
          </svg>
          恢复
        </button>
        <button class="toolbar-dropdown__item toolbar-dropdown__item--danger" @click="handleDelete">
          <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
            <path d="M3 4H13M5 4V3.5C5 2.67 5.67 2 6.5 2H9.5C10.33 2 11 2.67 11 3.5V4M12 4V13C12 13.55 11.55 14 11 14H5C4.45 14 4 13.55 4 13V4" stroke="currentColor" stroke-width="1.2" stroke-linecap="round"/>
          </svg>
          永久删除
        </button>
      </template>
    </div>
  </Teleport>
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
import { noteRepository, type BacklinkSummary } from '@/database/noteRepository'
import { exportService } from '@/services/exportService'
import { Extension } from '@tiptap/core'
import { useI18n } from '@/i18n'
import { findActiveHeadingId } from '@/utils/noteOutline.mjs'

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
      setFontSize: (fontSize: string) => ({ chain }: any) => {
        return chain().setMark('textStyle', { fontSize }).run()
      },
      unsetFontSize: () => ({ chain }: any) => {
        return chain().setMark('textStyle', { fontSize: null }).removeEmptyTextStyle().run()
      },
    } as any
  },
})

const lowlight = createLowlight(common)

const noteStore = useNoteStore()
const categoryStore = useCategoryStore()
const { t } = useI18n()
const editorStateVersion = ref(0)

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
const editorRootRef = ref<HTMLElement>()
const editorContainerRef = ref<HTMLElement>()
const outlineButtonRef = ref<HTMLElement>()
type NoteOutlineHeading = {
  id: string
  level: number
  text: string
  start: number
  pos: number
}
const outlineItems = ref<NoteOutlineHeading[]>([])
const activeOutlineId = ref('')
const outlineOpen = ref(false)
let outlineSyncRaf: number | null = null
const outlinePanelPosition = reactive({
  top: 0,
  left: 0,
  width: 320,
  maxHeight: 320
})

// ========== 新版工具栏状态 ==========
// 下拉菜单 refs
const fontSizeDropdownRef = ref<HTMLElement>()
const textColorDropdownRef = ref<HTMLElement>()
const highlightDropdownRef = ref<HTMLElement>()
const headingDropdownRef = ref<HTMLElement>()
const listDropdownRef = ref<HTMLElement>()
const insertDropdownRef = ref<HTMLElement>()
const moreMenuRef = ref<HTMLElement>()
const moreMenuButtonRef = ref<HTMLElement>()
const moreMenuFloatingRef = ref<HTMLElement>()

// 下拉菜单开关状态
const fontSizeDropdownOpen = ref(false)
const textColorDropdownOpen = ref(false)
const highlightDropdownOpen = ref(false)
const headingDropdownOpen = ref(false)
const listDropdownOpen = ref(false)
const insertDropdownOpen = ref(false)
const moreMenuOpen = ref(false)
const exportSubmenuOpen = ref(false)

// 笔记信息弹窗
const noteInfoVisible = ref(false)
const noteInfoData = reactive({
  category: '',
  createdAt: '',
  updatedAt: '',
  wordCount: 0
})
const backlinks = ref<BacklinkSummary[]>([])
const backlinksLoading = ref(false)
const moreMenuPosition = reactive({
  top: 0,
  left: 0,
})

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
  if (!editor.value) return t('editor.paragraph')
  if (editor.value.isActive('heading', { level: 1 })) return 'H1'
  if (editor.value.isActive('heading', { level: 2 })) return 'H2'
  if (editor.value.isActive('heading', { level: 3 })) return 'H3'
  return t('editor.paragraph')
})
const moreMenuStyle = computed(() => ({
  top: `${moreMenuPosition.top}px`,
  left: `${moreMenuPosition.left}px`,
}))

const canUndo = computed(() => {
  // 依赖编辑器事务，确保按钮状态实时更新
  void editorStateVersion.value
  return editor.value?.can().chain().focus().undo().run() ?? false
})

const canRedo = computed(() => {
  // 依赖编辑器事务，确保按钮状态实时更新
  void editorStateVersion.value
  return editor.value?.can().chain().focus().redo().run() ?? false
})

const showOutlinePanel = computed(() => outlineOpen.value)
const outlinePanelStyle = computed(() => ({
  top: `${outlinePanelPosition.top}px`,
  left: `${outlinePanelPosition.left}px`,
  width: `${outlinePanelPosition.width}px`,
  maxHeight: `${outlinePanelPosition.maxHeight}px`
}))

function toggleOutlinePanel() {
  outlineOpen.value = !outlineOpen.value
  if (outlineOpen.value) {
    nextTick(() => {
      updateOutlinePanelPosition()
      requestAnimationFrame(updateOutlinePanelPosition)
    })
  }
}

function scheduleOutlineSync(): void {
  if (outlineSyncRaf !== null) return
  outlineSyncRaf = requestAnimationFrame(() => {
    outlineSyncRaf = null
    syncOutlineFromEditor()
  })
}

function syncOutlineFromEditor() {
  if (!editor.value) {
    outlineItems.value = []
    activeOutlineId.value = ''
    return
  }

  const headings: NoteOutlineHeading[] = []
  editor.value.state.doc.descendants((node, pos) => {
    if (node.type.name === 'heading' && node.textContent.trim()) {
      const level = Number(node.attrs?.level || 1)
      headings.push({
        id: `heading-${headings.length}`,
        level: level >= 1 && level <= 3 ? level : 1,
        text: node.textContent.trim(),
        start: pos,
        pos
      })
    }
  })

  outlineItems.value = headings
  activeOutlineId.value = findActiveHeadingId(outlineItems.value, editor.value.state.selection.from)
}

function updateActiveOutlineByScroll() {
  const host = editorContainerRef.value
  if (!host || !outlineItems.value.length) return
  const headingEls = host.querySelectorAll<HTMLElement>('.tiptap h1, .tiptap h2, .tiptap h3')
  if (!headingEls.length) return

  const viewportTop = host.getBoundingClientRect().top + 24
  let activeId = outlineItems.value[0].id
  for (let index = 0; index < headingEls.length; index += 1) {
    const el = headingEls[index]
    const id = outlineItems.value[index]?.id
    if (!id) continue
    if (el.getBoundingClientRect().top <= viewportTop) activeId = id
    else break
  }
  activeOutlineId.value = activeId
}

function jumpToHeading(item: NoteOutlineHeading) {
  if (!editor.value) return
  const docSize = editor.value.state.doc.content.size
  const targetPos = Math.max(1, Math.min(item.pos + 1, docSize))
  editor.value.chain().focus().setTextSelection(targetPos).run()
  activeOutlineId.value = item.id

  const targetNode = editor.value.view.nodeDOM(item.pos) as HTMLElement | null
  targetNode?.scrollIntoView({ behavior: 'smooth', block: 'start' })
}

function updateOutlinePanelPosition() {
  if (!outlineOpen.value || !outlineButtonRef.value) return

  const rect = outlineButtonRef.value.getBoundingClientRect()
  const margin = 8
  const viewportWidth = window.innerWidth
  const viewportHeight = window.innerHeight

  const panelWidth = Math.min(420, Math.max(280, Math.floor(viewportWidth * 0.28)))
  const compactWidth = viewportWidth < 900 ? Math.min(360, viewportWidth - margin * 2) : panelWidth
  const width = Math.max(260, compactWidth)

  let left = rect.right - width
  const minLeft = margin
  const maxLeft = viewportWidth - width - margin
  left = Math.max(minLeft, Math.min(maxLeft, left))

  let top = rect.bottom + 8
  let maxHeight = viewportHeight - top - margin
  if (maxHeight < 220) {
    const fallbackHeight = Math.min(420, viewportHeight - margin * 2)
    top = Math.max(margin, rect.top - fallbackHeight - 8)
    maxHeight = viewportHeight - top - margin
  }

  outlinePanelPosition.left = left
  outlinePanelPosition.top = top
  outlinePanelPosition.width = width
  outlinePanelPosition.maxHeight = Math.max(180, maxHeight)
}

// 关闭所有下拉菜单
function closeAllDropdowns() {
  fontSizeDropdownOpen.value = false
  textColorDropdownOpen.value = false
  highlightDropdownOpen.value = false
  headingDropdownOpen.value = false
  listDropdownOpen.value = false
  insertDropdownOpen.value = false
  moreMenuOpen.value = false
  exportSubmenuOpen.value = false
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

function toggleMoreMenu() {
  const wasOpen = moreMenuOpen.value
  closeAllDropdowns()
  moreMenuOpen.value = !wasOpen
  if (!wasOpen) {
    nextTick(() => {
      updateMoreMenuPosition()
      requestAnimationFrame(updateMoreMenuPosition)
    })
  }
}

function toggleExportSubmenu() {
  exportSubmenuOpen.value = !exportSubmenuOpen.value
}

function updateMoreMenuPosition() {
  if (!moreMenuOpen.value || !moreMenuButtonRef.value) return
  const rect = moreMenuButtonRef.value.getBoundingClientRect()
  const menuWidth = moreMenuFloatingRef.value?.offsetWidth || 170
  const menuHeight = moreMenuFloatingRef.value?.offsetHeight || 260
  const gap = 6
  const minLeft = 8
  const maxLeft = window.innerWidth - menuWidth - 8
  const preferredLeft = rect.right - menuWidth

  moreMenuPosition.left = Math.max(minLeft, Math.min(maxLeft, preferredLeft))

  let top = rect.bottom + gap
  if (top + menuHeight > window.innerHeight - 8) {
    top = rect.top - menuHeight - gap
  }
  moreMenuPosition.top = Math.max(8, top)
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
  const latex = prompt(`${t('editor.math')}:`, 'E=mc^2')
  if (latex !== null) {
    const isBlock = confirm('是否作为独立行(Block)显示？')
    editor.value?.chain().focus().insertMath(latex, isBlock).run()
  }
}

function handleUndo() {
  editor.value?.chain().focus().undo().run()
}

function handleRedo() {
  editor.value?.chain().focus().redo().run()
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

// ========== AI 选中文本菜单状态 ==========
const selectionMenu = reactive({
  visible: false,
  x: 0,
  y: 0,
  selectedText: '',
  selectionFrom: 0,
  selectionTo: 0
})
const aiProcessing = ref(false)
const aiStatusText = ref('处理中...')
const aiAbortController = ref<AbortController | null>(null)
let aiTimeoutTimer: ReturnType<typeof setTimeout> | null = null

// 自由提问状态
const showAskInput = ref(false)
const askInputText = ref('')
const askInputRef = ref<HTMLInputElement | null>(null)


// AI 结果预览状态
const aiResult = reactive({
  visible: false,
  text: '',
  action: '',
  actionLabel: '',
  x: 0,
  y: 0
})

const aiResultHtml = computed(() => {
  const source = aiResult.text || ''
  const rendered = marked.parse(source, { gfm: true, breaks: true })
  if (typeof rendered === 'string') {
    return DOMPurify.sanitize(rendered)
  }
  return DOMPurify.sanitize(source.replace(/\n/g, '<br/>'))
})

// 操作标签映射
const actionLabels: Record<string, string> = {
  polish: '润色后',
  translate: '翻译结果',
  explain: '解释',
  summarize: '总结',
  expand: '扩写后'
}

// 选中菜单位置计算
const selectionMenuStyle = computed(() => {
  // 菜单宽度估算（包含询问输入框时会更宽）
  const menuWidth = showAskInput.value ? 480 : 360
  const menuHeight = 50
  const padding = 16
  
  // 获取编辑器容器的边界（如果存在）
  const editorEl = document.querySelector('.note-editor')
  const containerRect = editorEl?.getBoundingClientRect()
  
  // 使用容器边界，但也确保不超出窗口
  const maxRight = Math.min(
    containerRect ? containerRect.right : window.innerWidth,
    window.innerWidth
  )
  const minLeft = Math.max(
    containerRect ? containerRect.left : 0,
    0
  )

  let x = selectionMenu.x - menuWidth / 2 // 居中显示
  let y = selectionMenu.y - menuHeight - 10 // 显示在选区上方
  
  // 右边界检查：确保 x + menuWidth <= maxRight - padding
  const rightLimit = maxRight - padding - menuWidth
  if (x > rightLimit) {
    x = rightLimit
  }
  // 左边界检查
  if (x < minLeft + padding) {
    x = minLeft + padding
  }
  // 顶部边界检查
  if (y < padding) {
    y = selectionMenu.y + 25 // 如果上方空间不够，显示在下方
  }
  
  return {
    left: x + 'px',
    top: y + 'px'
  }
})






// AI 结果面板位置计算
const aiResultStyle = computed(() => {
  const panelWidth = 320
  const panelHeight = 200 // 估计面板高度
  const padding = 8
  
  let x = aiResult.x - panelWidth / 2
  let y = aiResult.y + 5 // 显示在选区下方
  
  // 右边界检查
  if (x + panelWidth > window.innerWidth - padding) {
    x = window.innerWidth - panelWidth - padding
  }
  // 左边界检查
  if (x < padding) x = padding
  
  // 底部边界检查：如果超出底部，显示在选区上方
  if (y + panelHeight > window.innerHeight - padding) {
    y = aiResult.y - panelHeight - 10
  }
  // 顶部边界检查
  if (y < padding) y = padding
  
  return {
    left: x + 'px',
    top: y + 'px'
  }
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

function htmlToMarkdown(html: string): string {
  return html
    .replace(/<h1[^>]*>(.*?)<\/h1>/gis, '# $1\n\n')
    .replace(/<h2[^>]*>(.*?)<\/h2>/gis, '## $1\n\n')
    .replace(/<h3[^>]*>(.*?)<\/h3>/gis, '### $1\n\n')
    .replace(/<h4[^>]*>(.*?)<\/h4>/gis, '#### $1\n\n')
    .replace(/<h5[^>]*>(.*?)<\/h5>/gis, '##### $1\n\n')
    .replace(/<h6[^>]*>(.*?)<\/h6>/gis, '###### $1\n\n')
    .replace(/<strong[^>]*>(.*?)<\/strong>/gis, '**$1**')
    .replace(/<b[^>]*>(.*?)<\/b>/gis, '**$1**')
    .replace(/<em[^>]*>(.*?)<\/em>/gis, '*$1*')
    .replace(/<i[^>]*>(.*?)<\/i>/gis, '*$1*')
    .replace(/<code[^>]*>(.*?)<\/code>/gis, '`$1`')
    .replace(/<blockquote[^>]*>(.*?)<\/blockquote>/gis, '> $1\n\n')
    .replace(/<li[^>]*data-checked="true"[^>]*>(.*?)<\/li>/gis, '- [x] $1\n')
    .replace(/<li[^>]*data-checked="false"[^>]*>(.*?)<\/li>/gis, '- [ ] $1\n')
    .replace(/<li[^>]*>(.*?)<\/li>/gis, '- $1\n')
    .replace(/<p[^>]*>(.*?)<\/p>/gis, '$1\n\n')
    .replace(/<br\s*\/?>/gi, '\n')
    .replace(/<[^>]+>/g, '')
    .replace(/&nbsp;/g, ' ')
    .replace(/&lt;/g, '<')
    .replace(/&gt;/g, '>')
    .replace(/&amp;/g, '&')
    .replace(/\n{3,}/g, '\n\n')
    .trim()
}

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
    editorStateVersion.value += 1
    activeOutlineId.value = findActiveHeadingId(outlineItems.value, editor.state.selection.from)
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
    handleDOMEvents: {
      copy: (_view, event) => {
        const clipboard = event.clipboardData
        if (!clipboard) return false

        const selection = window.getSelection()
        if (selection && selection.rangeCount > 0 && !selection.isCollapsed) {
          const fragment = selection.getRangeAt(0).cloneContents()
          const container = document.createElement('div')
          container.appendChild(fragment)
          const markdown = htmlToMarkdown(container.innerHTML)
          event.preventDefault()
          clipboard.setData('text/plain', markdown)
          return true
        }

        const markdown = htmlToMarkdown(editor.value?.getHTML() || '')
        event.preventDefault()
        clipboard.setData('text/plain', markdown)
        return true
      }
    },
    handlePaste: (view, event) => {
      const clipboardData = event.clipboardData
      if (!clipboardData) return false

      // 1. 检查是否有 HTML 内容（WPS/Excel 复制的表格会带 HTML）
      const html = clipboardData.getData('text/html')
      if (html && html.includes('<table')) {
        // 有表格的 HTML，让 Tiptap 默认处理
        return false
      }

      // 2. 对于纯文本或 Markdown 源码，强制以纯文本插入
      const text = clipboardData.getData('text/plain')
      if (text) {
        const normalized = text
          .replace(/\r\n?/g, '\n')
          .replace(/[ \t]+\n/g, '\n')
          .replace(/\n{3,}/g, '\n\n')
        const { tr } = view.state
        const textNode = view.state.schema.text(normalized)
        view.dispatch(tr.replaceSelectionWith(textNode, false))
        return true
      }

      // 3. 纯图片粘贴
      const items = clipboardData.items
      for (let i = 0; i < items.length; i++) {
        const item = items[i]
        if (item.type.startsWith('image/')) {
          const file = item.getAsFile()
          if (file) {
            const reader = new FileReader()
            reader.onload = async (e) => {
              const base64 = e.target?.result as string
              if (base64) {
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

      return false
    }
  },
  onTransaction: () => {
    editorStateVersion.value += 1
    scheduleOutlineSync()
  },
  // 使用 requestAnimationFrame 优化更新
  onUpdate: ({ editor }) => {
    editorStateVersion.value += 1
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
watch(editorContainerRef, (newVal, oldVal) => {
  if (oldVal) {
    oldVal.removeEventListener('scroll', updateActiveOutlineByScroll)
  }
  if (newVal) {
    attachImageListeners(newVal)
    newVal.addEventListener('scroll', updateActiveOutlineByScroll, { passive: true })
    nextTick(() => {
      scheduleOutlineSync()
      updateActiveOutlineByScroll()
    })
  }
})

watch(moreMenuOpen, (open) => {
  if (!open) return
  nextTick(() => {
    updateMoreMenuPosition()
    requestAnimationFrame(updateMoreMenuPosition)
  })
})

onMounted(() => {
  window.addEventListener('resize', updateMoreMenuPosition)
  window.addEventListener('scroll', updateMoreMenuPosition, true)
  window.addEventListener('resize', updateOutlinePanelPosition)
  window.addEventListener('scroll', updateOutlinePanelPosition, true)
  scheduleOutlineSync()
  nextTick(() => {
    updateActiveOutlineByScroll()
    updateOutlinePanelPosition()
  })

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
    
    // 关闭 AI 选中菜单（如果点击不在菜单内）
    if (!target.closest('.selection-ai-menu') && !target.closest('.ai-result-panel')) {
      selectionMenu.visible = false
      closeAIResult()
    }
  })
  
  // 监听选中变化，显示 AI 菜单
  document.addEventListener('mouseup', handleSelectionChange)
  document.addEventListener('keyup', (e) => {
    // Shift + 方向键选中时也触发
    if (e.shiftKey) handleSelectionChange()
  })
})

// 处理选中变化
function handleSelectionChange(): void {
  // 延迟执行，确保选区已更新
  setTimeout(() => {
    if (!editor.value || noteStore.currentView === 'trash') {
      selectionMenu.visible = false
      return
    }
    
    const { from, to, empty } = editor.value.state.selection
    
    // 没有选中或选中的是图片节点，不显示菜单
    if (empty || from === to) {
      selectionMenu.visible = false
      showAskInput.value = false // 重置询问输入状态
      return
    }
    
    // 获取选中区域的内容
    let selectedText = ''
    
    // 检查选区是否在表格内部（通过解析父节点）
    const $from = editor.value.state.doc.resolve(from)
    let isInTable = false
    for (let d = $from.depth; d > 0; d--) {
      const node = $from.node(d)
      if (node.type.name === 'table') {
        isInTable = true
        break
      }
    }
    
    console.log('[AI Menu] isInTable:', isInTable, 'from:', from, 'to:', to)
    
    if (isInTable) {
      // 选区在表格内：自动扩展到整个表格，获取所有行的内容
      const $from = editor.value.state.doc.resolve(from)
      
      // 找到选区所在的表格（table）
      let tableNode: any = null
      for (let d = $from.depth; d > 0; d--) {
        const node = $from.node(d)
        if (node.type.name === 'table') {
          tableNode = node
          break
        }
      }
      
      if (tableNode) {
        // 提取整个表格的所有行
        const rows: string[] = []
        tableNode.content.forEach((row: any) => {
          if (row.type.name === 'tableRow') {
            const cells: string[] = []
            row.content.forEach((cell: any) => {
              const cellText = cell.textContent.trim()
              if (cellText) {
                cells.push(cellText)
              }
            })
            if (cells.length > 0) {
              rows.push(cells.join(' | '))
            }
          }
        })
        selectedText = rows.join('\n')
        console.log('[AI Menu] Extracted full table:', rows.length, 'rows')
      } else {
        // 找不到表格，回退到默认方法
        selectedText = editor.value.state.doc.textBetween(from, to, '\n', ' ')
        console.log('[AI Menu] Fallback to default extraction')
      }

    } else {
      // 普通文本使用默认方式
      selectedText = editor.value.state.doc.textBetween(from, to, '\n', ' ')
    }

    
    // 选中内容太短（少于3个字符）不显示
    if (selectedText.trim().length < 3) {
      selectionMenu.visible = false
      return
    }

    // 获取选区的屏幕坐标

    // 注意：选区可能是从左到右，也可能是从右到左选择
    const view = editor.value.view
    const startCoords = view.coordsAtPos(from)
    const endCoords = view.coordsAtPos(to)
    
    // 计算菜单位置（选区顶部中间位置）
    // 使用 Math.min 确保获取最上方的位置
    const minY = Math.min(startCoords.top, endCoords.top)
    const minX = Math.min(startCoords.left, endCoords.left)
    const maxX = Math.max(startCoords.right, endCoords.right)
    
    selectionMenu.x = (minX + maxX) / 2
    selectionMenu.y = minY
    selectionMenu.selectedText = selectedText
    selectionMenu.selectionFrom = from
    selectionMenu.selectionTo = to
    selectionMenu.visible = true

  }, 10)
}

// 处理 AI 操作 - 显示预览而不是直接替换
async function handleAIAction(action: string): Promise<void> {
  if (!editor.value || !selectionMenu.selectedText || aiProcessing.value) return
  
  aiProcessing.value = true
  const view = editor.value.view
  const endCoords = view.coordsAtPos(selectionMenu.selectionTo)
  aiResult.text = ''
  aiResult.action = action
  aiResult.actionLabel = actionLabels[action] || action
  aiResult.x = (selectionMenu.x + endCoords.right) / 2
  aiResult.y = endCoords.bottom
  aiResult.visible = true
  selectionMenu.visible = false
  
  try {
    const processed = await requestTextProcess({
      text: selectionMenu.selectedText,
      action,
      target_lang: action === 'translate' ? 'zh' : undefined
    }, (streamingText) => {
      aiResult.text = streamingText
    })

    if (processed) {
      aiResult.text = processed
    }
  } finally {
    aiProcessing.value = false
    aiStatusText.value = aiResult.text ? '已完成' : '处理中...'
  }
}

// 应用 AI 结果
function applyAIResult(mode: 'insert' | 'replace'): void {
  if (!editor.value || !aiResult.text) return
  
  if (mode === 'replace') {
    // 替换选中文本
    editor.value.chain()
      .focus()
      .setTextSelection({ from: selectionMenu.selectionFrom, to: selectionMenu.selectionTo })
      .deleteSelection()
      .insertContent(aiResult.text)
      .run()
  } else {
    // 在选区后插入（保留原文）
    editor.value.chain()
      .focus()
      .setTextSelection(selectionMenu.selectionTo)
      .insertContent('\n\n' + aiResult.text)
      .run()
  }
  
  closeAIResult()
}

// 关闭 AI 结果面板
function closeAIResult(): void {
  if (aiProcessing.value) {
    aiAbortController.value?.abort()
  }
  aiResult.visible = false
  aiResult.text = ''
  aiResult.action = ''
}

// 切换自由提问输入框
function toggleAskInput(): void {
  showAskInput.value = !showAskInput.value
  if (showAskInput.value) {
    nextTick(() => {
      askInputRef.value?.focus()
    })
  }
}

// 处理自由提问提交
async function handleAskSubmit(): Promise<void> {
  if (!editor.value || !selectionMenu.selectedText || !askInputText.value.trim() || aiProcessing.value) return
  
  aiProcessing.value = true
  const view = editor.value.view
  const endCoords = view.coordsAtPos(selectionMenu.selectionTo)
  aiResult.text = ''
  aiResult.action = 'ask'
  aiResult.actionLabel = '回答'
  aiResult.x = (selectionMenu.x + endCoords.right) / 2
  aiResult.y = endCoords.bottom
  aiResult.visible = true
  selectionMenu.visible = false
  
  try {
    const processed = await requestTextProcess({
      text: selectionMenu.selectedText,
      action: 'ask',
      question: askInputText.value.trim()
    }, (streamingText) => {
      aiResult.text = streamingText
    })

    if (processed) {
      aiResult.text = processed
      showAskInput.value = false
      askInputText.value = ''
    }
  } finally {
    aiProcessing.value = false
    aiStatusText.value = aiResult.text ? '已完成' : '处理中...'
  }
}

function cancelAIProcessing(): void {
  if (!aiProcessing.value) return
  aiStatusText.value = '已取消'
  aiAbortController.value?.abort()
}

async function requestTextProcess(
  payload: Record<string, unknown>,
  onStreamingText?: (fullText: string) => void
): Promise<string | null> {
  aiAbortController.value?.abort()
  aiAbortController.value = new AbortController()
  aiStatusText.value = '处理中...'

  if (aiTimeoutTimer) {
    clearTimeout(aiTimeoutTimer)
    aiTimeoutTimer = null
  }
  aiTimeoutTimer = setTimeout(() => {
    aiStatusText.value = '请求超时，已取消'
    aiAbortController.value?.abort()
  }, 45000)

  try {
    let streamFailed = false
    try {
      const response = await fetch('http://127.0.0.1:8765/api/chat/process-text/stream', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        signal: aiAbortController.value.signal,
        body: JSON.stringify(payload)
      })

      if (!response.ok) {
        throw new Error(`AI processing failed: ${response.status}`)
      }

      if (!response.body) {
        streamFailed = true
        throw new Error('No response stream body')
      }

      const reader = response.body.getReader()
      const decoder = new TextDecoder('utf-8')
      let buffer = ''
      let accumulated = ''

      while (true) {
        const { value, done } = await reader.read()
        if (done) break

        buffer += decoder.decode(value, { stream: true })
        const events = buffer.split('\n\n')
        buffer = events.pop() ?? ''

        for (const event of events) {
          const lines = event.split('\n')
          for (const line of lines) {
            const trimmed = line.trim()
            if (!trimmed.startsWith('data:')) continue
            const payloadText = trimmed.slice(5).trim()
            if (!payloadText) continue
            if (payloadText === '[DONE]') {
              return accumulated.trim()
            }
            const parsed = JSON.parse(payloadText)
            if (parsed?.error) {
              throw new Error(parsed.error)
            }
            if (typeof parsed?.delta === 'string') {
              accumulated += parsed.delta
              onStreamingText?.(accumulated)
            }
            if (typeof parsed?.final === 'string') {
              accumulated = parsed.final
              onStreamingText?.(accumulated)
            }
          }
        }
      }

      return accumulated.trim()
    } catch (error: any) {
      if (error?.name === 'AbortError') {
        return null
      }
      console.error('AI text process stream failed, fallback to non-stream:', error)
      streamFailed = true
    }

    if (streamFailed) {
      try {
        const response = await fetch('http://127.0.0.1:8765/api/chat/process-text', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          signal: aiAbortController.value?.signal,
          body: JSON.stringify(payload)
        })
        if (!response.ok) throw new Error(`AI processing failed: ${response.status}`)
        const result = await response.json()
        const finalText = typeof result?.processed === 'string' ? result.processed : null
        if (finalText) onStreamingText?.(finalText)
        return finalText
      } catch (error: any) {
        if (error?.name === 'AbortError') return null
        console.error('AI text process failed:', error)
        alert('AI 处理失败，请检查后端服务是否运行')
        return null
      }
    }

    return null
  } finally {
    if (aiTimeoutTimer) {
      clearTimeout(aiTimeoutTimer)
      aiTimeoutTimer = null
    }
    aiAbortController.value = null
  }
}


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
      alert(`${t('editor.renderMarkdown')}: # heading, **bold**, - list, \`\`\`code\`\`\`, $math$`)
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
      
      // Fast-path: only run formula transforms when '$' exists.
      if (newContent.includes('$')) {
        newContent = newContent.replace(/\$\$([\s\S]+?)\$\$/g, (match, formula) => {
          const escaped = formula.replace(/"/g, '&quot;')
          return `<div data-math="true" data-latex="${escaped}" data-display="true"></div>`
        })
        newContent = newContent.replace(/\$([^\$\n]+?)\$/g, (match, formula) => {
          const escaped = formula.replace(/"/g, '&quot;')
          return `<span data-math="true" data-latex="${escaped}"></span>`
        })
      }
      
      // 只在切换笔记时重置历史
      if (newId !== oldId) {
        const { state, view } = editor.value
        const tr = state.tr.setMeta('addToHistory', false)
        view.dispatch(tr)
      }
      
      editor.value.commands.setContent(newContent, false, { preserveWhitespace: 'full' })
      nextTick(() => {
        scheduleOutlineSync()
        updateActiveOutlineByScroll()
      })

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

watch(
  () => [noteStore.currentNote?.id, noteStore.currentNote?.title, noteInfoVisible.value] as const,
  async ([, , visible]) => {
    if (!visible) {
      backlinks.value = []
      backlinksLoading.value = false
      return
    }
    await loadBacklinks()
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

// 导出当前笔记
async function handleExport(format: 'markdown' | 'txt' | 'html' | 'docx' | 'pdf'): Promise<void> {
  if (!noteStore.currentNote) return
  closeAllDropdowns()
  
  const title = noteStore.currentNote.title || 'note'
  const content = noteStore.currentNote.content || ''
  const plainText = noteStore.currentNote.plainText || ''
  
  if (format === 'markdown') {
    await exportService.exportNoteAsMarkdown(noteStore.currentNote)
  } else if (format === 'txt') {
    // 导出纯文本
    const blob = new Blob([plainText], { type: 'text/plain;charset=utf-8' })
    downloadBlob(blob, `${title}.txt`)
  } else if (format === 'html') {
    // 导出 HTML
    const html = `<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <title>${title}</title>
  <style>body{font-family:system-ui,-apple-system,sans-serif;max-width:800px;margin:40px auto;padding:0 20px;line-height:1.6;color:#333;}h1,h2,h3{margin-top:1.5em;}code{background:#f4f4f4;padding:2px 6px;border-radius:3px;}pre{background:#f4f4f4;padding:16px;border-radius:6px;overflow-x:auto;}blockquote{border-left:3px solid #ddd;margin:0;padding-left:16px;color:#666;}table{border-collapse:collapse;width:100%;}td,th{border:1px solid #ddd;padding:8px 12px;}img{max-width:100%;}</style>
</head>
<body>
  <h1>${title}</h1>
  ${content}
</body>
</html>`
    const blob = new Blob([html], { type: 'text/html;charset=utf-8' })
    downloadBlob(blob, `${title}.html`)
  } else if (format === 'docx') {
    // 导出 Word
    try {
      const { asBlob } = await import('html-docx-js-typescript')
      const htmlForDocx = `<!DOCTYPE html>
<html>
<head><meta charset="utf-8"></head>
<body>
  <h1>${title}</h1>
  ${content}
</body>
</html>`
      const blob = await asBlob(htmlForDocx) as Blob
      downloadBlob(blob, `${title}.docx`)
    } catch (e) {
      console.error('Word export failed:', e)
      alert('Word 导出失败')
    }
  } else if (format === 'pdf') {
    // 导出 PDF - 使用 Electron 的打印功能
    try {
      const htmlForPdf = `<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <style>
    body{font-family:system-ui,-apple-system,"Microsoft YaHei",sans-serif;max-width:100%;padding:20px 40px;line-height:1.8;color:#333;font-size:14px;}
    h1{font-size:24px;margin-bottom:20px;}
    h2{font-size:20px;}
    h3{font-size:16px;}
    code{background:#f4f4f4;padding:2px 6px;border-radius:3px;font-size:13px;}
    pre{background:#f4f4f4;padding:16px;border-radius:6px;overflow-x:auto;font-size:13px;}
    blockquote{border-left:3px solid #ddd;margin:16px 0;padding-left:16px;color:#666;}
    table{border-collapse:collapse;width:100%;margin:16px 0;}
    td,th{border:1px solid #ddd;padding:8px 12px;}
    img{max-width:100%;}
  </style>
</head>
<body>
  <h1>${title}</h1>
  ${content}
</body>
</html>`
      const pdfData = await window.electronAPI.exportPdf(htmlForPdf)
      if (pdfData) {
        const blob = new Blob([pdfData as unknown as BlobPart], { type: 'application/pdf' })
        downloadBlob(blob, `${title}.pdf`)
      }
    } catch (e) {
      console.error('PDF export failed:', e)
      alert('PDF 导出失败')
    }
  }
}

// 下载 Blob 文件
function downloadBlob(blob: Blob, filename: string): void {
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = filename
  a.click()
  URL.revokeObjectURL(url)
}

// 切换加锁状态
async function handleToggleLock(): Promise<void> {
  if (!noteStore.currentNote) return
  closeAllDropdowns()
  
  const newLockState = !noteStore.currentNote.isLocked
  await noteStore.updateNote(noteStore.currentNote.id, { isLocked: newLockState })
}

// 显示笔记信息
async function showNoteInfo(): Promise<void> {
  if (!noteStore.currentNote) return
  closeAllDropdowns()
  
  // 获取分类名称
  const category = categoryStore.categories.find(c => c.id === noteStore.currentNote?.categoryId)
  noteInfoData.category = category?.name || t('editor.categoryNone')
  
  // 格式化时间
  const formatDate = (timestamp: number) => {
    const date = new Date(timestamp)
    return `${date.getFullYear()}/${String(date.getMonth() + 1).padStart(2, '0')}/${String(date.getDate()).padStart(2, '0')} ${String(date.getHours()).padStart(2, '0')}:${String(date.getMinutes()).padStart(2, '0')}`
  }
  
  noteInfoData.createdAt = formatDate(noteStore.currentNote.createdAt)
  noteInfoData.updatedAt = formatDate(noteStore.currentNote.updatedAt)
  
  // 计算字数
  const plainText = noteStore.currentNote.plainText || ''
  noteInfoData.wordCount = plainText.replace(/\s/g, '').length

  await loadBacklinks()
  noteInfoVisible.value = true
}

async function loadBacklinks(): Promise<void> {
  const current = noteStore.currentNote
  if (!current || !current.title?.trim()) {
    backlinks.value = []
    return
  }

  backlinksLoading.value = true
  try {
    backlinks.value = await noteRepository.getBacklinks(current.id, current.title, 50)
  } catch (error) {
    console.error('Failed to load backlinks:', error)
    backlinks.value = []
  } finally {
    backlinksLoading.value = false
  }
}

async function handleOpenBacklink(noteId: string): Promise<void> {
  const target = await noteRepository.getById(noteId)
  if (!target) return
  await noteStore.selectNote(target)
  noteInfoVisible.value = false
}

onBeforeUnmount(() => {
  window.removeEventListener('resize', updateMoreMenuPosition)
  window.removeEventListener('scroll', updateMoreMenuPosition, true)
  window.removeEventListener('resize', updateOutlinePanelPosition)
  window.removeEventListener('scroll', updateOutlinePanelPosition, true)
  editorContainerRef.value?.removeEventListener('scroll', updateActiveOutlineByScroll)
  aiAbortController.value?.abort()
  if (aiTimeoutTimer) {
    clearTimeout(aiTimeoutTimer)
    aiTimeoutTimer = null
  }
  if (outlineSyncRaf !== null) {
    cancelAnimationFrame(outlineSyncRaf)
    outlineSyncRaf = null
  }
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
  position: relative;
  z-index: 10020;
  overflow: visible;
}

.note-editor__tools {
  display: flex;
  align-items: center;
  gap: 2px;
  flex-wrap: nowrap;
  flex-shrink: 1;
  min-width: 0;
  overflow: visible;
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
    z-index: 10030;
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
    
    &--danger {
      color: var(--color-danger);
    }
    
    &--has-arrow {
      .arrow-left {
        opacity: 0.5;
        flex-shrink: 0;
      }
    }
    
    svg {
      flex-shrink: 0;
    }
  }
  
  &__submenu {
    position: relative;
  }
  
  &__submenu-panel {
    position: absolute;
    right: 100%;
    top: 0;
    margin-right: 4px;
    min-width: 140px;
    background: var(--color-bg-card);
    border: 1px solid var(--color-border);
    border-radius: $radius-md;
    box-shadow: var(--shadow-lg);
    padding: 4px;
    z-index: 10031;
  }
  
  &__menu--right {
    left: auto;
    right: 0;
  }

  &__menu--floating {
    position: fixed;
    margin-top: 0;
    right: auto !important;
    z-index: 12000;
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

  &:disabled {
    opacity: 0.45;
    cursor: not-allowed;
    background: transparent;
    color: var(--color-text-muted);
  }

  &:disabled:hover {
    background: transparent;
    color: var(--color-text-muted);
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

// 中等宽度：保持单行，通过隐藏次要工具避免重叠
@container editor (max-width: 1180px) {
  .note-editor__toolbar {
    padding: 6px 10px;
  }

  .toolbar-hide-md {
    display: none !important;
  }
}

// 更窄时继续精简
@container editor (max-width: 900px) {
  .toolbar-hide-narrow {
    display: none !important;
  }
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

.note-editor__outline {
  position: fixed;
  overflow: auto;
  background: var(--color-bg-card);
  border: 1px solid var(--color-border-light);
  border-radius: $radius-md;
  box-shadow: var(--shadow-lg);
  z-index: 12040;
  padding: 8px;
}

.note-editor__outline--floating {
  backdrop-filter: blur(6px);
}

.note-editor__outline-header {
  font-size: 12px;
  font-weight: 600;
  color: var(--color-text-muted);
  padding: 4px 6px 8px;
}

.note-editor__outline-empty {
  font-size: 12px;
  color: var(--color-text-muted);
  padding: 6px;
}

.note-editor__outline-item {
  width: 100%;
  border: none;
  background: transparent;
  color: var(--color-text-secondary);
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px 6px 6px calc(6px + var(--outline-indent, 0px));
  border-radius: $radius-sm;
  cursor: pointer;
  text-align: left;

  &:hover {
    background: var(--color-bg-hover);
    color: var(--color-text-primary);
  }

  &--active {
    background: var(--color-bg-active);
    color: var(--color-text-primary);
  }
}

.note-editor__outline-level {
  flex-shrink: 0;
  min-width: 20px;
  font-size: 11px;
  color: var(--color-text-muted);
}

.note-editor__outline-text {
  font-size: 13px;
  line-height: 1.3;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
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

// AI 选中文本浮动菜单
.selection-ai-menu {
  position: fixed;
  background: var(--color-bg-card);
  border: 1px solid var(--color-border);
  border-radius: $radius-lg;
  box-shadow: var(--shadow-lg);
  padding: 6px 8px;
  z-index: 9999;
  animation: fadeInUp 0.15s ease;
  
  @keyframes fadeInUp {
    from {
      opacity: 0;
      transform: translateY(4px);
    }
    to {
      opacity: 1;
      transform: translateY(0);
    }
  }
  
  &__actions {
    display: flex;
    gap: 2px;
  }
  
  &__btn {
    display: flex;
    align-items: center;
    gap: 4px;
    padding: 6px 10px;
    border: none;
    border-radius: $radius-sm;
    background: transparent;
    color: var(--color-text-secondary);
    font-size: 12px;
    cursor: pointer;
    transition: all 0.15s ease;
    white-space: nowrap;
    
    &:hover:not(:disabled) {
      background: var(--color-bg-hover);
      color: var(--color-text-primary);
    }
    
    &:disabled {
      opacity: 0.5;
      cursor: not-allowed;
    }
    
    svg {
      flex-shrink: 0;
    }
  }
  
  &__loading {
    display: flex;
    align-items: center;
    gap: 6px;
    padding: 4px 8px;
    font-size: 11px;
    color: var(--color-text-muted);
    border-top: 1px solid var(--color-border-light);
    margin-top: 4px;
    
    .loading-dot {
      width: 6px;
      height: 6px;
      background: var(--color-accent);
      border-radius: 50%;
      animation: pulse 1s infinite;
    }
    
    @keyframes pulse {
      0%, 100% { opacity: 0.4; }
      50% { opacity: 1; }
    }
  }

  &__cancel {
    margin-left: auto;
    border: 1px solid var(--color-border);
    border-radius: $radius-sm;
    background: transparent;
    color: var(--color-text-secondary);
    font-size: 11px;
    padding: 2px 8px;
    cursor: pointer;

    &:hover {
      background: var(--color-bg-hover);
      color: var(--color-text-primary);
    }
  }
  
  // 分隔线
  &__divider {
    width: 1px;
    height: 20px;
    background: var(--color-border-light);
    margin: 0 4px;
    align-self: center;
  }
  
  // 询问按钮特殊样式
  &__btn--ask {
    color: var(--color-accent);
    
    &:hover:not(:disabled) {
      background: rgba(var(--color-accent-rgb, 59, 130, 246), 0.1);
    }
  }
  
  &__btn--active {
    background: var(--color-bg-active);
    color: var(--color-accent);
  }
  
  // 自由提问输入框
  &__ask-input {
    display: flex;
    align-items: center;
    gap: 6px;
    padding: 6px 8px;
    border-top: 1px solid var(--color-border-light);
    margin-top: 4px;
    
    input {
      flex: 1;
      min-width: 180px;
      padding: 6px 10px;
      border: 1px solid var(--color-border);
      border-radius: $radius-sm;
      background: var(--color-bg-primary);
      color: var(--color-text-primary);
      font-size: 12px;
      outline: none;
      
      &::placeholder {
        color: var(--color-text-placeholder);
      }
      
      &:focus {
        border-color: var(--color-accent);
      }
      
      &:disabled {
        opacity: 0.6;
      }
    }
  }
  
  &__ask-submit {
    display: flex;
    align-items: center;
    justify-content: center;
    width: 28px;
    height: 28px;
    border: none;
    border-radius: $radius-sm;
    background: var(--color-accent);
    color: white;
    cursor: pointer;
    transition: all 0.15s ease;
    
    &:hover:not(:disabled) {
      opacity: 0.9;
      transform: translateX(2px);
    }
    
    &:disabled {
      opacity: 0.5;
      cursor: not-allowed;
    }
    
    svg {
      width: 14px;
      height: 14px;
    }
  }
}


// AI 结果预览面板
.ai-result-panel {
  position: fixed;
  width: 320px;
  max-width: calc(100vw - 32px);
  background: var(--color-bg-card);
  border: 1px solid var(--color-border);
  border-radius: $radius-lg;
  box-shadow: var(--shadow-xl);
  z-index: 10000;
  animation: fadeInDown 0.2s ease;
  overflow: hidden;
  
  @keyframes fadeInDown {
    from {
      opacity: 0;
      transform: translateY(-8px);
    }
    to {
      opacity: 1;
      transform: translateY(0);
    }
  }
  
  &__header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 10px 12px;
    background: var(--color-bg-secondary);
    border-bottom: 1px solid var(--color-border-light);
  }
  
  &__action-label {
    font-size: 12px;
    font-weight: 500;
    color: var(--color-text-secondary);
  }

  &__header-actions {
    display: flex;
    align-items: center;
    gap: 6px;
  }

  &__stop {
    border: 1px solid var(--color-border);
    background: var(--color-bg-card);
    color: var(--color-text-secondary);
    border-radius: $radius-sm;
    padding: 2px 8px;
    font-size: 11px;
    cursor: pointer;

    &:hover {
      background: var(--color-bg-hover);
      color: var(--color-text-primary);
    }
  }
  
  &__close {
    display: flex;
    align-items: center;
    justify-content: center;
    width: 20px;
    height: 20px;
    border: none;
    border-radius: $radius-sm;
    background: transparent;
    color: var(--color-text-muted);
    cursor: pointer;
    
    &:hover {
      background: var(--color-bg-hover);
      color: var(--color-text-primary);
    }
  }
  
  &__content {
    padding: 12px;
    font-size: 13px;
    line-height: 1.6;
    color: var(--color-text-primary);
    max-height: 200px;
    overflow-y: auto;
    background: #fffbeb; // 淡黄色背景，类似 vivo
    
    // 暗色模式
    :root[data-theme="dark"] & {
      background: rgba(255, 251, 235, 0.08);
    }

    :deep(p) {
      margin: 0 0 8px;
    }

    :deep(p:last-child) {
      margin-bottom: 0;
    }

    :deep(ul), :deep(ol) {
      margin: 0 0 8px 18px;
      padding: 0;
    }

    :deep(code) {
      background: rgba(0, 0, 0, 0.06);
      border-radius: 4px;
      padding: 1px 4px;
      font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace;
    }

    :deep(pre) {
      margin: 8px 0;
      padding: 8px;
      border-radius: 6px;
      overflow: auto;
      background: rgba(0, 0, 0, 0.06);
    }
  }
  
  &__actions {
    display: flex;
    gap: 8px;
    padding: 10px 12px;
    border-top: 1px solid var(--color-border-light);
    background: var(--color-bg-primary);
  }
  
  &__btn {
    display: flex;
    align-items: center;
    gap: 4px;
    padding: 6px 12px;
    border: 1px solid var(--color-border);
    border-radius: $radius-sm;
    background: var(--color-bg-card);
    color: var(--color-text-secondary);
    font-size: 12px;
    cursor: pointer;
    transition: all 0.15s ease;
    
    &:hover {
      background: var(--color-bg-hover);
      color: var(--color-text-primary);
    }

    &:disabled {
      opacity: 0.45;
      cursor: not-allowed;
      background: var(--color-bg-card);
      color: var(--color-text-muted);
    }
    
    &--primary {
      background: var(--color-accent);
      border-color: var(--color-accent);
      color: white;
      
      &:hover {
        opacity: 0.9;
        background: var(--color-accent);
        color: white;
      }
    }
    
    &--secondary {
      border-color: transparent;
      background: transparent;
      
      &:hover {
        background: var(--color-bg-hover);
      }
    }
    
    svg {
      flex-shrink: 0;
    }
  }
}

// 笔记信息弹窗
.note-info-modal {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.4);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 10001;
  animation: fadeIn 0.15s ease;
  
  @keyframes fadeIn {
    from { opacity: 0; }
    to { opacity: 1; }
  }
  
  &__content {
    background: var(--color-bg-card);
    border-radius: $radius-lg;
    box-shadow: var(--shadow-xl);
    width: 300px;
    max-width: calc(100vw - 40px);
    animation: scaleIn 0.2s ease;
    
    @keyframes scaleIn {
      from {
        opacity: 0;
        transform: scale(0.95);
      }
      to {
        opacity: 1;
        transform: scale(1);
      }
    }
  }
  
  &__title {
    font-size: 16px;
    font-weight: 600;
    text-align: center;
    padding: 20px 20px 16px;
    margin: 0;
    color: var(--color-text-primary);
  }
  
  &__body {
    padding: 0 20px 20px;
  }
  
  &__row {
    display: flex;
    padding: 8px 0;
    font-size: 14px;
    
    &:not(:last-child) {
      border-bottom: 1px solid var(--color-border-light);
    }
  }
  
  &__label {
    color: var(--color-text-secondary);
    min-width: 80px;
  }
  
  &__value {
    color: var(--color-text-primary);
    flex: 1;
  }
  
  &__btn {
    display: block;
    width: 100%;
    padding: 14px;
    border: none;
    border-top: 1px solid var(--color-border-light);
    background: transparent;
    color: var(--color-text-primary);
    font-size: 15px;
    cursor: pointer;
    transition: background-color 0.15s ease;
    border-radius: 0 0 $radius-lg $radius-lg;
    
    &:hover {
      background: var(--color-bg-hover);
    }
  }

  &__backlinks {
    margin-top: 8px;
    max-height: 180px;
    overflow-y: auto;
    border-top: 1px solid var(--color-border-light);
    padding-top: 8px;
  }

  &__backlinks-loading,
  &__backlinks-empty {
    font-size: 13px;
    color: var(--color-text-muted);
    padding: 6px 0;
  }

  &__backlink-item {
    width: 100%;
    border: 1px solid var(--color-border-light);
    background: var(--color-bg-primary);
    border-radius: $radius-sm;
    color: var(--color-text-primary);
    text-align: left;
    padding: 8px 10px;
    margin-bottom: 6px;
    cursor: pointer;

    &:hover {
      background: var(--color-bg-hover);
      border-color: var(--color-border);
    }
  }

  &__backlink-title {
    display: block;
    font-size: 13px;
    line-height: 1.4;
    word-break: break-word;
  }
}
</style>
