# Maa Local Lab — Windows 本地视觉自动化工作台

Tauri 2 + React + Rust + MaaFramework（Python）桌面项目。支持任务配置、Pipeline JSON 编辑与节点预览、Windows 试验窗口的 OCR 点击验证、日志及历史记录。

## 下载 Windows 程序

- [GitHub Releases](https://github.com/weepwood/Maa-Local-Lab/releases) — 每次推送 main 自动发布 **预览版本**，推送 `v*` 标签发布正式版本。
- [GitHub Actions](https://github.com/weepwood/Maa-Local-Lab/actions/workflows/windows-release.yml) — 每次 PR 也会自动打包，在构建详情的 **Artifacts** 下载。

每次完整构建应生成：
- `Maa-Local-Lab-setup-win-x64.exe`：Windows x64 NSIS 安装包；
- `Maa-Local-Lab-portable-win-x64.zip`：Windows x64 便携版（解压后运行 `Maa Local Lab.exe`）；
- `SHA256SUMS.txt`：文件校验值。

**发行包已经设计为捆绑** Python/PyInstaller MaaFramework 执行器、OCR 模型、测试窗口和 Pipeline，无需用户自行安装 Python。需要 Windows 10/11 x64、可用的 WebView2 运行时，并保持交互式 Windows 桌面会话。未签名的安装程序可能触发 SmartScreen。

> 只有 GitHub Actions **全部构建成功**且包含上述资产时才代表已产出可下载安装包。当前未实现通用任意窗口执行；自定义任务可创建编辑，实际执行仍只支持内置隔离实验。

### 便携版与安装版的数据目录

运行时将默认 Pipeline 复制到系统的 Tauri `app_data_dir`（应用用户数据目录）作为可编辑副本；实验记录保存在 `app_data_dir/runs`。安装目录及便携版程序目录仅存放**只读资源**，不会要求管理员权限回写程序文件。

## 本地开发

Windows 需要 Node.js 22、Python 3.12、Rust stable、Microsoft C++ Build Tools、WebView2。

```powershell
npm install
.\run_windows.cmd
npm run tauri dev
```

这里 `run_windows.cmd` 会初始化 MaaFramework 和 OCR 模型，然后运行一次试验；之后打开 Tauri 工作台。单独构建发行包需要先执行 Windows CI 中的 PyInstaller 及资源准备步骤，否则 Tauri 的发行资源不完整。

### Actions 触发规则

| 触发 | 结果 |
| --- | --- |
| Pull Request | 自动编译 NSIS + Portable，作为 Actions Artifact（30 天） |
| push main | 自动编译并发布名为 `snapshot-<run_number>` 的预览 Release |
| push v* tag | 自动编译并发布正式 Release |
| Actions → Run workflow | 手动编译并生成预览 Release |

框架：https://github.com/MaaXYZ/MaaFramework

## 限制

试验程序仍需要 OCR 识别稳定性与后台控制的真机测试。GitHub Actions 在无交互桌面的 runner 上执行 DLL/资源自检，**不宣称**已完成真实 GUI 点击测试。停止任务会尝试结束 Python 执行器及其子进程。通用 RPA、可视化拖拽流程、任务定时器尚未实现。
