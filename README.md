# Maa Local Lab — Tauri 2 本地自动化管理平台

使用 **Tauri 2 + React + Rust + Python MaaFramework** 创建的 Windows 视觉自动化实验工作台。

## 已实现
- 仪表盘、任务管理与本地 JSON 持久化
- MaaFramework Pipeline JSON 编辑、节点预览
- 隔离 Tkinter 测试窗口、OCR 自动识别、点击、结果验证
- 前后台实验模式、失败模拟、实时日志、运行停止和实验报告
- 浏览器预览安全降级（不具备执行本地命令权限）

## 本地开发

需要：Windows、Node.js 22、Python 3、Rust、Visual Studio C++ Build Tools、WebView2。

```powershell
npm install
.\run_windows.cmd
npm run tauri dev
```

其中 `run_windows.cmd` 会初始化 Python 虚拟环境、下载 OCR 模型并执行一次实验。首次运行后，使用 Tauri 工作台的「运行实验」。

构建前端：`npm run build`；生成桌面安装包：`npm run tauri build`。

**当前阶段限制：** 只有内置测试对象可执行；自定义任务 CRUD 不代表通用执行器已实现。编辑器目前是 JSON + 节点预览，尚未提供拖拽连线；未嵌入 Python/OCR 模型作为 sidecar，发行构建需完善资源打包和生产路径解析。停止命令目前只杀死 Python 主进程，可能留下子进程。运行需从仓库根目录启动。

MaaFramework：https://github.com/MaaXYZ/MaaFramework
