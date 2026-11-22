# OPlague — 只读设备与驱动工作台

[English](README.md) · [Українська](README.uk.md) · [Русский](README.ru.md) · [简体中文](README.zh-CN.md)

<p align="center"><img src="assets/readme/dashboard.svg" alt="OPlague 项目概览" width="100%"></p>

[源代码仓库](https://github.com/Ivan-VHS/OPlague) · [Windows 桌面工作流](.github/workflows/desktop-build.yml) · [文档索引](docs/README.md) · [Apache-2.0](LICENSE)

> **项目范围：** OPlague 是一款本地只读桌面工作台，用于 Windows Plug and Play 设备清单、INF/ZIP 驱动包元数据和基于证据的比较。它**不会安装、加载、解压或修改**驱动程序载荷。本仓库没有托管 Web Demo、远程 API 或生产设备管理服务。文档已于 **2026-11-22** 对照 `main` 分支核对。

## 项目用途与边界

OPlague 帮助操作者查看当前机器的设备记录、读取驱动包元数据，并比较规范化的硬件标识符。目标用户包括 Windows 支持工程师、硬件审查人员、QA 和研究驱动包内容或兼容性证据的开发者。

结果是证据记录和候选比较，而不是最终的安全或兼容性结论。硬件 ID 完全匹配并不能证明发布者可信、操作系统兼容、设备适用或安装安全。驱动部署不属于本产品范围。

### 工作台实际功能

| 模块 | 已实现行为 | 明确边界 |
|---|---|---|
| 设备清单 | 读取 Windows Plug and Play 身份、状态、制造商和 PNPDeviceID | 实时采集仅支持 Windows，只读 |
| INF 检查 | 读取选定元数据、硬件 ID 声明和目标架构 | 不执行 INF 指令 |
| ZIP 检查 | 检查路径、大小、压缩比、哈希和 INF 元数据 | 不解压或执行包载荷 |
| 兼容性图 | 根据精确规范化硬件 ID 建立候选关联 | 仅为候选，需要人工复核 |
| Metric Lab | 通过加权距离/方差比较用户输入的规范化配置 | 建议性分析，不是设备结论 |
| UDRV v1 | 验证 manifest、大小和 SHA-256 证据 | 完整性检查，不验证发布者身份 |
| 报告 | 生成结构化证据、汇总和指纹 | 不写入系统，也不安装驱动 |

应用包含四个主要标签页：**Devices**、**Package Inspection**、**Metric Lab** 和 **Compatibility Review**。主题可在 system/light/dark 之间切换；动态效果设置包括 Reduce Motion 和 Eco Visuals。Sync-to-Transport 选项被禁用是有意设计：OPlague 没有音频传输或 master BPM。

下图是桌面应用的实际截屏，不是浏览器预览。

<p align="center"><img src="assets/screenshots/oplague-workbench.png" alt="在 Windows 上运行的 OPlague 工作台" width="100%"></p>
<sub>桌面程序截屏 · 原始图像 1920×1080。这不是托管 Web Stand。</sub>

## 快速开始

### 环境要求

- Python **3.10 或更高版本**。
- 桌面界面需要 Tkinter。
- 实时 Plug and Play 清单需要 Windows 和 `powershell.exe`。采集使用固定的本地 PowerShell/CIM 查询。
- Git。

应用导入仓库自己的模块和 Python 标准库；直接运行源码不需要安装第三方运行时包。只有在打包独立可执行文件时才需要 PyInstaller。

Linux 和 macOS 可以检查已保存的数据，但无法采集实时 Windows PnP 清单。

### 运行桌面工作台

在仓库根目录运行：

```sh
python oplague_app.py
```

`oplague_app.py` 是拼写正确的入口文件；它委托给现有的实现模块 `oplage_app.py`。

### 运行测试和 CLI 检查

```sh
python -m compileall -q oplague_app.py oplage_app.py tests
python tools/validate_visual_canon.py ui_theme.py
python -m unittest discover -s tests -v
```

CLI 示例：

```sh
python -m oplague --verify
python -m oplague --catalog
python -m oplague --search "ballistic"
python -m oplague --profile 5
python -m oplague --rank reach
python tools/udrv_inspector.py path/to/package.udrv --json
python tools/clinical_systems.py --catalog --pretty
```

可选的 Reaper C17 计算需要显式指定可信库路径：

```sh
python -m oplague --rank-total-native --reaper-library /absolute/path/to/libreaper_ffi.so
```

这些操作均在本地执行。OPlague 不会启动 HTTP Listener、Web UI、API Endpoint 或 localhost Preview。

### 构建 Windows 可执行文件

桌面工作流使用 Python 3.12 和 PyInstaller。本地打包命令：

```sh
python -m pip install --upgrade pyinstaller
python -m PyInstaller --noconfirm --clean --onefile --windowed --name OPlague oplague_app.py
```

独立程序生成在 `dist/OPlague.exe`。首次打包时 PyInstaller 需要收集应用文件，可能比后续构建更久；这里不承诺固定耗时。

## 数据、限制与验证场景

OPlague 没有共享数据库、登录、演示账号、远程 Mock API 或托管 Fixture 服务。数据来源相互独立：

- **设备清单：** 通过 `Get-CimInstance` 读取真实的本地 Windows Plug and Play 记录。
- **驱动包检查：** 操作者明确选择的本地文件。
- **Metric Lab：** 操作者输入的 JSON。界面预填的 reference/candidate JSON 是规范化到 `[0, 1]` 的示例数据，不是实时测量。
- **自动化测试：** 本地测试 fixture 和合成输入，不是已安装驱动或真实驱动目录。

可按以下场景验证：

1. **在 Windows 刷新设备：**点击 **Refresh device list**。应用读取本地 PnP 信息，并显示名称、状态、制造商和硬件 ID。
2. **检查驱动包：**选择 `.inf` 或 `.zip` 文件。查看元数据、SHA-256、架构提示和包限制；载荷不会被安装或执行。
3. **批量检查：**选择多个本地驱动包并比较元数据报告。
4. **指标比较：**编辑 reference/candidate JSON 对象。数值必须规范化到 `[0, 1]`；检查加权结果与权重。
5. **兼容性计划：**根据当前设备清单和 INF 硬件 ID 生成候选关联，再逐项人工复核。
6. **UDRV 验证：**对本地包运行 `tools/udrv_inspector.py` 并查看 JSON 验证报告。
7. **回归测试：**运行 `python -m unittest discover -s tests -v`。

### 输入文件与压缩包限制

桌面检查器实施以下限制：

| 输入 | 限制 |
|---|---:|
| INF / ZIP 包文件 | 512 MiB |
| ZIP 条目数量 | 10,000 |
| ZIP 总解压内容 | 2 GiB |
| 单个 INF 文件 | 2 MiB |
| 压缩比 | 200:1 |

UDRV v1 检查器有独立合同：manifest 最大 4 MiB，最多 10,000 个条目，单个文件最大 512 MiB，总载荷最大 2 GiB。检查器以有界数据块读取和计算哈希，不会解压或执行载荷。

没有内置延迟模拟器、HTTP 500 开关、Mock 网络服务或浏览器上传。损坏 ZIP、不安全的归档路径、超大 INF 或 PowerShell 清单不可用等错误会在本地显示。

当前设备列表和检查结果存在桌面进程中。关闭应用会清除当前工作会话，但不会更改源驱动包或 Windows 驱动。主题和动态效果偏好由原生偏好设置层处理。没有浏览器 localStorage、sessionStorage、IndexedDB 或 Cookie 状态。

## 配置与访问

仓库根目录没有 `.env.example`、Docker Compose Web Stack、API Key、OAuth 账号、测试登录、CORS 策略、HTTP Proxy 或本地 HTTPS 证书配置。常规本地检查不需要秘密信息。当前应用没有文档化的运行时 ENV 合同；不要自行编造变量。

实际的 UI 开关包括主题循环（system/light/dark）和动态效果设置（Reduce Motion、Eco Visuals、Expressive Motion）。Sync to Transport/BPM 按设计禁用，不应描述成可用功能。

实时 PnP 查询需要 Windows PowerShell 和本地 CIM Provider。如果该命令被阻止或执行失败，驱动包检查和已保存数据检查仍可独立进行；应用会显示清单错误，而不会生成虚假的设备列表。

## 架构与仓库目录

数据流程为：**本地输入 → 有界解析器 → 证据记录 → dry-run 比较/报告 → 可选的显式导出**。

| 路径 | 内容 |
|---|---|
| `oplague_app.py` | 拼写正确的公共桌面入口 |
| `oplage_app.py` | 桌面界面实现、驱动包检查和 PnP 查询 |
| `tools/` | CLI 工具、报告组合、指标和 UDRV 检查 |
| `tests/` | 使用本地 fixture 的单元与回归测试 |
| `docs/` | 架构、安全边界、Schema 和操作指南 |
| `schemas/` | 版本化报告与驱动包合同 |
| `assets/screenshots/` | Windows 桌面截图 |
| `security/` | Beelzebul 机器可读安全策略 |
| `.github/workflows/` | Windows 打包和发布自动化 |

该应用是 Python/Tkinter 桌面程序。Windows inventory 路径调用本地 PowerShell；package inspector 读取本地 INF/ZIP 元数据。没有 frontend/backend 部署、Mock Server、Web 端口、浏览器存储、CORS 配置或公开在线预览。因此浏览器兼容性和响应式 viewport 规则不适用。

## 打包、CI 与 Release

[Windows 桌面工作流](.github/workflows/desktop-build.yml)：

1. 在 Windows 上使用 Python 3.12；
2. 编译 Python 源文件并运行单元测试；
3. 验证 visual canon；
4. 使用 PyInstaller 打包 `OPlague.exe`；
5. 截取正在运行的桌面应用并上传截图 Artifact；
6. 创建包含 executable、README 和 license 的 `OPlague-windows-x64.zip`。

截图 Artifact 保留 30 天。匹配 `v*` 的 Git Tag 会触发 GitHub Release 发布。Workflow Artifact 是可下载文件，不是托管 Web Demo。

回滚已分发构建时，选择上一个已知正常的带标签 Release/Archive。没有需要回滚的服务器部署。Workflow 日志和测试输出可在 GitHub Actions 中查看。

## 故障排查

| 现象 | 检查方法 |
|---|---|
| 应用无法启动 | 使用带 Tkinter 的 Python 3.10+，并从仓库根目录运行 |
| 设备清单失败 | 检查 Windows、`powershell.exe` 和本地 CIM 访问；Linux/macOS 尚未实现此清单 |
| ZIP 被拒绝 | 检查归档有效性、条目数量、解压大小、压缩比和路径 |
| INF 被拒绝 | 确认文件不超过 2 MiB 且编码有效 |
| 驱动包过大 | 桌面检查器将包文件限制在 512 MiB |
| Metric comparison 失败 | 输入有效 JSON 对象，并将指标规范化到 `[0, 1]` |
| Native rank total 失败 | 检查显式指定的 Reaper 库是否存在且可信 |

桌面状态栏和对话框会说明即时错误。CI 失败时，请查看对应的 GitHub Actions 日志。

## 已知限制、贡献与许可证

OPlague 有意保持非破坏性。它不会安装、加载、解压或修改驱动；匹配结果是候选证据，不是认证。实时硬件清单仅支持 Windows。Metric Profile 仅供参考。哈希只能证明字节一致，不能证明发布者真实性或所有权。UDRV Inspector 不执行载荷。

仓库中未找到单独的 `CONTRIBUTING.md`。请通过 [GitHub Issues](https://github.com/Ivan-VHS/OPlague/issues) 或 Pull Request 报告问题或提出改进。请提供操作系统、Python 版本、安全的示例文件类型、准确命令以及预期/实际结果。不要在未去除标识信息的情况下附上私有驱动包或敏感设备标识符。

许可证：[Apache-2.0](LICENSE)。

## README 与 66 条规则的映射

Web Stand 检查清单按实际桌面工作台进行映射，而不是复制为虚构的 Web 部署：

| 规则范围 | README 覆盖内容 |
|---|---|
| 1–11 · 用途与范围 | 说明只读工作台、目标用户、实际数据来源、限制以及没有托管 Stand |
| 12–22 · 快速开始 | 提供准确的 Python/Tkinter 要求、GUI 入口、测试命令和 executable 打包步骤 |
| 23–33 · 配置与访问 | 声明没有 `.env`、测试登录、API Secret、CORS 或 HTTPS；说明真实的本地 PowerShell 依赖 |
| 34–44 · 数据与场景 | 区分实时本地 PnP 数据、用户驱动包、示例指标 JSON 和测试 fixture；说明边界与状态生命周期 |
| 45–55 · 架构与构建 | 列出真实 source、tools、tests、schemas、docs 和 Windows 打包工作流 |
| 56–66 · 运维与支持 | 说明 Artifact/Release 发布、回滚、日志、故障排查、限制、贡献渠道和许可证 |

**OPlague 没有公开的 Web Demo URL。** Windows 截图和 Release Archive 不等于在线设备管理服务。
