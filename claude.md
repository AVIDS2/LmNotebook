# 本次开发记录

## 新增功能
- 支持导出/导入 JSON 备份（全部笔记 + 分类）
- 支持导出 Markdown：
  - 侧边栏导出全部笔记为单个 .md 文件
  - 编辑器导出当前笔记为 .md 文件

## 实现点
- 主进程新增文件对话框 IPC：export-file / import-file
- 预加载脚本暴露 exportFile / importFile API
- 新增 `exportService` 处理 JSON/MD 导出与导入
- 侧边栏增加导出/导入入口按钮
- 编辑器工具栏新增“导出 Markdown”按钮

## 相关文件
- src/main/index.ts
- src/preload/index.ts
- src/preload/index.d.ts
- src/renderer/src/services/exportService.ts
- src/renderer/src/components/sidebar/TheSidebar.vue
- src/renderer/src/components/notes/NoteEditor.vue
