# 发布检查清单

## 构建前置条件

1. 确认已安装 Node.js 18+
2. 确认已安装 Python 3.10+
3. 确认仓库根目录存在 `backend_env`
4. 确认 `backend_env` 中已安装后端依赖
5. 确认 `src/backend/.env` 已按目标模型提供商配置
6. 建议在干净 shell 中运行构建/检查命令，避免 conda 自动初始化干扰：
   `powershell -NoProfile -ExecutionPolicy Bypass -File scripts/release_check.ps1`
7. 本地开发与中文显示检查建议使用 UTF-8 启动：
   `npm run dev:utf8`

## 后端构建（PyInstaller）

1. `cd src/backend`
2. `..\..\backend_env\Scripts\activate`
3. `..\..\backend_env\Scripts\python -m PyInstaller origin-backend.spec -y`
4. 确认产物存在：`src/backend/dist/origin_backend/`

## Electron 构建

1. `cd ../..`
2. `npm run build:win`
3. 确认产物存在：`dist/LmNotebook Setup 1.0.0.exe`

## 本地冒烟测试

1. 启动应用
2. 新建笔记并编辑内容
3. 删除并恢复一条笔记
4. 使用 `@笔记知识库` 执行一次知识检索
5. 在 Model Settings 中切换模型提供商
6. 确认聊天流式输出正常，且工具操作会更新 UI
7. 确认以下位置中文无乱码：
   - Agent 输入框占位提示
   - 聊天消息/状态文案
   - 后端控制台日志
8. 验证 `Manual Review` 审批流程：
   - 写操作任务先显示“待执行”卡片（不应直接运行）
   - 点击 `Accept` 后：状态应从待执行变为执行中，再到完成
   - 点击 `Reject` 后：不应改动笔记内容
9. 验证恢复安全性：
   - 使用过期/陈旧会话恢复时，应返回明确错误（不能静默重置成 `Hello`）
   - 状态不确定时，不应执行破坏性 checkpoint 清理

## 产物检查

1. `dist/` 中存在安装包
2. 安装后的应用目录中存在 `resources/backend/origin_backend.exe`
3. 用户数据目录中的 `models.json` 与 `checkpoints.db` 可持久化保存

## 可选项

1. 发版测试前先备份用户数据目录
2. 为发布版本打 git tag


