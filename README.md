# Origin Notes

简约风格的本地笔记应用，专注快速记录与高效检索。基于 Electron + Vue 3 构建，数据完全保存在本地。

## 功能特性

- 富文本编辑（标题、列表、任务清单、引用、代码等）
- 置顶、分类、回收站
- 关键词搜索
- 导出/导入 JSON 备份（全部笔记 + 分类）
- 导出 Markdown
  - 侧边栏导出全部笔记为单个 .md 文件
  - 编辑器导出当前笔记为 .md 文件
- 本地离线存储（IndexedDB via Dexie）

## 预览

> 可在此放置应用截图：`/assets/screenshot.png`

## 快速开始

安装依赖：

```bash
npm install
```

启动开发：

```bash
npm run dev
```

构建产物：

```bash
npm run build
```

本地预览：

```bash
npm run preview
```

## 打包发布

- Windows：
  ```bash
  npm run build:win
  ```
- macOS：
  ```bash
  npm run build:mac
  ```
- Linux：
  ```bash
  npm run build:linux
  ```

## 项目结构

```
src/
  main/          Electron 主进程
  preload/       预加载脚本（IPC 桥接）
  renderer/      渲染进程（Vue 应用）
    assets/      样式与静态资源
    components/  视图组件
    database/    本地数据库与仓库
    services/    导入/导出等服务
```

## 备份与导出说明

- **JSON 备份**：包含全部笔记与分类，可用于完整迁移与恢复。
- **Markdown 导出**：支持导出当前笔记或全部笔记为单个 Markdown 文件。

## 许可协议

MIT License
