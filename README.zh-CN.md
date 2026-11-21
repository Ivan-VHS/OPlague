# OPlague — 驱动工作台

<p align="center">
  <a href="https://github.com/Ivan-VHS/OPlague/actions/workflows/desktop-build.yml"><img alt="Windows 桌面构建" src="https://github.com/Ivan-VHS/OPlague/actions/workflows/desktop-build.yml/badge.svg"></a>
  <img alt="Python 3.10+" src="https://img.shields.io/badge/runtime-Python%203.10%2B-2563EB?style=flat-square">
  <img alt="Windows" src="https://img.shields.io/badge/desktop-Windows-DC2626?style=flat-square">
  <img alt="Apache 2.0" src="https://img.shields.io/badge/license-Apache--2.0-334155?style=flat-square">
</p>

**OPlague 是一款面向 Windows 的只读工作台，用于硬件清单和驱动包诊断。** 不会安装或修改驱动。

[English](README.md) · [Українська](README.uk.md) · [Русский](README.ru.md) · [简体中文](README.zh-CN.md)

## 桌面界面预览

<p align="center"><img src="assets/oplague-workbench-preview.svg" alt="OPlague 桌面工作台示意图" width="100%"></p>
<sub>根据仓库中的 Tkinter 布局重构的示意图，并非真实运行的 Windows 应用截图。当前尚未提交实机截图。</sub>

## 工作台与工具

- **设备清单：** 只读查询 Windows Plug and Play 设备名称、状态、制造商和硬件 ID。
- **INF / ZIP 检查器：** 提取选定 INF 元数据、计算 SHA-256、检查压缩包路径与资源上限，并分析精确硬件 ID 和目标架构。不提取或执行包内容。
- **批量报告：** 按顺序合并检查结果，生成汇总计数和确定性 bundle 指纹。
- **UDRV 检查器：** 验证版本化清单、payload 列表、声明大小、哈希及路径/资源限制；不会安装、加载或执行 payload。
- **DRIVE-LENS 证据账本：** 对设备引用进行 HMAC 假名化，保留来源摘要，按精确属性与时间窗口分组，并显式保留 PnP/INF/UDRV/目录元数据冲突；不会自动给出驱动结论（[设计说明](docs/DRIVE_LENS_EVIDENCE_LEDGER.md)）。
- **兼容性 dry-run：** 仅通过精确规范化硬件 ID 关联设备与 INF Models。候选关系不是驱动排名或兼容性结论。
- **Metric Lab：** 通过加权距离、余弦相似度、正交性和重复测量方差比较归一化配置。
- **设备联邦：** 导出有界版本化 JSON 快照须由操作者明确确认，并支持离线比较。PnP ID 默认使用临时密钥进行 HMAC 假名化；可显式提供受保护密钥以进行跨快照匹配。假名仍可能被关联，并非匿名化。
- **原生交叉验证：** 调用方明确提供可信库路径时，可选用 Pytyliki C ABI v1 验证度量结果。
- **QCS 验证器：** 一套紧凑语法和 66 个命名硬件域配置，用于检查 contour 元数据和交接标记；不是编译器或硬件验证器。
- **系统目录：** 66 项语言/工具链能力条目，只通过 `PATH` 查找工具。

## 运行桌面应用

需要 Windows x64 和 Python 3.10+。

```bash
git clone https://github.com/Ivan-VHS/OPlague.git
cd OPlague
python oplague_app.py
python -m unittest discover -s tests -v
```

Windows workflow 会构建 `OPlague.exe` 并上传 `OPlague-windows-x64.zip`。推送 `v*` 标签后，工作流会将压缩包发布为 GitHub Release。

## 只读命令行工具

```bash
python tools/udrv_inspector.py path/to/package.udrv --json
python -m tools.federation snapshot --output device-snapshot.json
python -m tools.federation compare --reference baseline.json --candidate current.json
python -m tools.qcs dialects
python -m tools.qcs validate path/to/example.qcs
python tools/systems_languages.py --profile oplague
```

## 项目演进与安全边界

OPlague 于 2026 年 11 月 19 日以 Windows 驱动工作台项目启动。之后 main 分支加入 PnP 清单、受限 INF/ZIP 检查、架构分析、精确 ID dry-run、UDRV 完整性检查、批量报告、度量、版本化设备快照、Pytyliki 桥接和 QCS 验证器。

**尚未实现：** 驱动安装/卸载、启用/禁用、签名、回滚、固件修改和实时 DPC/ISR 诊断。包完整性不等于供应商真实性、驱动安全性或兼容性。导入文件均视为不可信输入。QCS 正文仅作为文本保留，不会编译或执行。

## 文档与下载

[DRIVE-LENS 证据账本](docs/DRIVE_LENS_EVIDENCE_LEDGER.md)

[UDRV 格式](docs/UDRV_FORMAT_V1.md) · [设备兼容图](docs/DEVICE_COMPATIBILITY_GRAPH.md) · [设备联邦契约](docs/FEDERATED_INTEGRATION.md) · [QCS 语法](docs/QUANTUM_CONTOUR_SYNTAX.md) · [统一工程标准](docs/UNIFIED_ENGINEERING_STANDARD.md)


[治理与授权](docs/HUMAN_FIRST_GOVERNANCE.md) · [Anatidae 桌面设计系统](docs/ANATIDAE_DESKTOP_DESIGN_SYSTEM.md) · [UI/UX 架构](docs/UI_UX_ARCHITECTURE.md) · [12 项动效原则](docs/DISNEY_MOTION_SYSTEM.md) · [项目契约](docs/UNIFIED_PROJECT_CONTRACT.md)
[Windows 发布版](https://github.com/Ivan-VHS/OPlague/releases) · [桌面构建](https://github.com/Ivan-VHS/OPlague/actions/workflows/desktop-build.yml)

**项目协作：** [Reaper](https://github.com/Ivan-VHS/Reaper) · [Pytyliki](https://github.com/Ivan-VHS/Pytyliki) · [3×3 集成矩阵](https://github.com/Ivan-VHS/Reaper/blob/main/docs/PROJECT_FEDERATION_MATRIX.md)。

## Anatidae 准则与安全契约

- **以操作者意图为先：** 设备清单和检查均为只读；导出快照必须由操作者明确确认。原生互操作为可选功能，必须显式提供可信库路径。
- **将驱动包视为不可信输入：** 强制执行路径和资源上限；检查元数据时不解压或执行 payload。
- **依据证据而非猜测：** 兼容性 dry-run 只通过精确规范化硬件 ID 建立关联。候选关联仅供人工复核，不是驱动推荐或兼容性结论。
- **数据最小化：** PnP ID 默认使用临时密钥进行 HMAC 假名化；可显式提供受保护密钥以进行跨快照匹配。假名仍可能被关联，因此不属于匿名化。
- **安全功能边界：** 驱动安装、卸载、启用、禁用、签名、回滚，固件修改及实时 DPC/ISR 诊断均未实现。
- **无障碍桌面体验：** 提供清晰的状态与错误提示、键盘操作和可见焦点、本地化及减少动态效果支持。动效不得掩盖警告或操作后果。

软件包哈希只能证明字节级完整性，不能证明发布者身份、驱动安全性或兼容性。

## 许可证

[Apache License 2.0](LICENSE)

UI motion: [12 animation principles](docs/DISNEY_MOTION_SYSTEM.md).
