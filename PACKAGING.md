# Origin Notes 打包指南

## 打包流程概述

项目采用 **Electron + Python 后端** 的混合架构，打包分两步：
1. PyInstaller 打包 Python 后端为 exe
2. electron-builder 打包整个应用为安装程序

## 前置条件

- Node.js 环境
- Python 虚拟环境 `backend_env`（位于项目根目录）

## 打包步骤

### 第一步：打包 Python 后端

```powershell
# 1. 进入后端目录
cd src/backend

# 2. 激活专用虚拟环境（重要！不要用 Anaconda base）
..\..\backend_env\Scripts\activate

# 3. 执行 PyInstaller 打包
pyinstaller origin-backend.spec -y
```

打包完成后，输出目录为 `src/backend/dist/origin_backend/`

### 第二步：打包 Electron 应用

```powershell
# 回到项目根目录
cd ../..

# 执行完整打包
npm run build:win
```

打包完成后，安装程序位于 `dist/Origin Notes Setup 1.0.0.exe`

## 注意事项

### 为什么必须用 backend_env？

| 环境 | 结果 |
|------|------|
| `backend_env` | 精简依赖，后端约 20-30MB |
| Anaconda base | 全家桶依赖，后端可能 500MB+ |

Anaconda base 环境包含大量科学计算库（torch、tensorflow、sklearn 等），PyInstaller 会把它们全部打包进去，导致体积爆炸。

### 目录模式 vs 单文件模式

当前使用**目录模式**（`exclude_binaries=True` + `COLLECT`）：
- 优点：启动快（无需解压），便于调试
- 输出：`dist/origin_backend/` 文件夹

单文件模式（`--onefile`）：
- 缺点：每次启动需解压到临时目录，冷启动慢
- 输出：单个 `origin_backend.exe`

### package.json 配置

`extraResources` 配置将后端目录复制到安装包：

```json
"extraResources": [
  {
    "from": "src/backend/dist/origin_backend",
    "to": "backend",
    "filter": ["**/*"]
  }
]
```

运行时路径：`resources/backend/origin_backend.exe`

## 快速命令（一键打包）

```powershell
# 在项目根目录执行
cd src/backend ; ..\..\backend_env\Scripts\activate ; pyinstaller origin-backend.spec -y ; cd ../.. ; npm run build:win
```

## 预期输出

- 安装包大小：约 110MB
- 安装包位置：`dist/Origin Notes Setup 1.0.0.exe`
