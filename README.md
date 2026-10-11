# Maa Local Lab — powered by MXU

**Maa Local Lab 的主界面现在使用 [MistEO/MXU](https://github.com/MistEO/MXU) 原版客户端，而不是仿照 MXU 重新设计的界面。**

MXU 本身使用 Tauri 2 + React + MaaFramework，支持任务管理、Win32/ADB 控制器、实时画面、日志、多实例、主题和定时任务。本项目负责提供 **ProjectInterface V2** 描述文件、OCR Pipeline、隔离测试窗口及 Windows 自动发布包。

## 下载

[GitHub Releases](https://github.com/weepwood/Maa-Local-Lab/releases) 提供：

- `Maa-Local-Lab-MXU-setup-win-x64.exe`：Windows NSIS 安装版
- `Maa-Local-Lab-MXU-portable-win-x64.zip`：解压即用的便携版
- `SHA256SUMS.txt`：SHA256 校验

此版本使用 MXU v2.7.1（AGPL-3.0）及 MaaFramework v5.14.3（LGPL-3.0），在 GitHub Actions 中下载**固定版本**的官方发行文件；不是定期漂移的 latest。许可证和源代码链接见 [THIRD_PARTY.md](THIRD_PARTY.md)。

## 实验操作

1. 启动 `Maa Local Lab.exe`，进入 MXU 原生界面。
2. 选择 `Windows 实验窗口` 控制器和 `实验资源`。
3. 勾选 `自动点击并验证保存`，点击开始。MXU 在连接控制器前通过 `pretask` 自动打开独立 Tkinter 测试窗口。
4. 通过 MXU 的实时画面和日志查看识别、点击、状态校验。
5. `debug/lab-saved.json` 为本地结果文件；MXU 也有自己的调试日志。

若你已经打开多个同名实验窗口，请先关闭旧窗口，避免窗口选择不确定。部分机器上 `ScreenDC` 前台截图要求实验窗口未被遮挡、未最小化。

## 文件职责

- `interface.json`：PI V2 元信息、Windows 控制器、资源、实验预任务及任务列表
- `resource/pipeline/main.json`：OCR 匹配「执行保存」，点击后 OCR 验证「保存成功」
- `demo_app.py`：Tkinter 测试目标；打包后位于 `tools/maa-lab-target.exe`
- `scripts/stage_mxu.py`：将上游二进制、MaaFramework DLL、OCR 模型、测试目标及许可证组装成安装目录
- `scripts/validate_mxu.py`：验证发行包与任务资源结构
- `installers/windows-mxu.nsi`：NSIS 安装程序
- `.github/workflows/windows-release.yml`：PR / main / v* Windows 自动构建与发布

## 本地开发

此仓库 **不再自己编译重复的 Tauri 前端**；主界面直接来自 MXU 项目。若要单独开发 MXU，请参考 https://github.com/MistEO/MXU 。

执行静态验证：

```powershell
python -m unittest discover -s tests -v
python -m py_compile demo_app.py scripts/stage_mxu.py scripts/validate_mxu.py
```

在 Windows 测试独立窗口：`python demo_app.py`。

## 已知边界与安全提醒

- 真正的 UI 由 MXU 官方提供，原有 React 工作台源码暂从发行构建中退役。
- 用户可通过 MXU 配置界面选择任务和 Win32 窗口，但本项目只预置隔离测试目标，不会为任意业务软件自动生成流水线。
- MXU 官方 Windows release 默认会请求管理员权限，即使我们的安装器本身是用户级安装。**不要未经确认就以管理员权限对不可信软件自动化。**
- GitHub Actions 的无图形环境只执行结构检查和无 GUI 自检；实际 OCR 点击必须在 Windows 交互桌面手动验证。
- 如无特殊需要，请勿同时运行旧版 Maa Local Lab 和 MXU 版，防止窗口重复。

源码归属和许可证见 [THIRD_PARTY.md](THIRD_PARTY.md)。
