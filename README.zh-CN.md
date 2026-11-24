# OPlague

OPlague 是用于 Windows 设备清单、只读驱动包检查和兼容性证据分析的本地工作台，面向技术支持工程师与 QA 团队。

[English](README.md) · [Українська](README.uk.md) · [Русский](README.ru.md) · [简体中文](README.zh-CN.md)

<picture><source media="(prefers-color-scheme: dark)" srcset="assets/readme/dashboard.svg"><img src="assets/readme/dashboard-light.svg" alt="OPlague 概览：Windows 设备输入、有界包检查和候选证据报告" width="100%"></picture>

[![Windows build](https://img.shields.io/github/actions/workflow/status/Ivan-VHS/OPlague/desktop-build.yml?branch=main&style=flat-square&label=Windows%20build)](https://github.com/Ivan-VHS/OPlague/actions/workflows/desktop-build.yml) [![最近提交](https://img.shields.io/github/last-commit/Ivan-VHS/OPlague?style=flat-square)](https://github.com/Ivan-VHS/OPlague/commits/main) [![Apache-2.0](https://img.shields.io/github/license/Ivan-VHS/OPlague?style=flat-square)](LICENSE)

[快速开始](#快速开始) · [截图](#截图) · [架构](#架构) · [路线图](#路线图) · [文档](docs/README.md)

> **状态：** 活跃开发。仓库包含 Tkinter 桌面工作台、本地包检查器、CLI 工具、测试和 Windows 打包工作流。实时 Plug and Play 清单仅在 Windows 可用。
> **要求：** Python 3.10+、Tkinter 和 Git；实时 PnP 需要 Windows 与 PowerShell/CIM。

## Reaper 集成

OPlague 可通过版本化的 Reaper C17 ABI，对已验证数据执行受限整数表达式计算。这不会将驱动控制、软件包安装或兼容性结论交给 Reaper。

详见 [Reaper 集成说明](docs/REAPER_RUNTIME_INTEGRATION.md)。

## 快速开始

启动桌面程序：

~~~sh
python oplague_app.py
~~~

运行项目检查和测试：

~~~sh
python -m compileall -q oplague_app.py oplage_app.py tests
python tools/validate_visual_canon.py ui_theme.py
python -m unittest discover -s tests -v
~~~

检查本地文件：

~~~sh
python tools/pe_inspector.py driver.sys --output driver-pe-report.json
python tools/sbom_inventory.py ./staging --output staging.spdx.json
python tools/udrv_inspector.py path/to/package.udrv --json
~~~

## 功能与边界

| 组件 | 当前实现 | 边界 |
|---|---|---|
| Windows PnP | 读取身份、状态和 PNPDeviceID | 仅 Windows 只读 |
| INF / ZIP | 元数据、硬件 ID、大小、路径、压缩比和哈希 | 不执行指令或解压 payload |
| PE/COFF | 头部、节、entry point 和证书表位置 | 不加载映像、不判断签名 |
| SPDX | SPDX 2.3 文件/哈希清单 | 不推断依赖或许可证结论 |
| 兼容性图 | 根据精确规范化硬件 ID 建立候选项 | 需要人工审核 |
| Metric Lab | 比较用户提供的规范化配置 | 仅供分析 |
| UDRV v1 | Manifest、大小和 SHA-256 | 完整性不等于发布者认证 |
| Gaming Lab | 可恢复的 Windows 电源计划会话和 frametime/CSV 分析 | 不修改驱动 |

OPlague **不会安装、加载、解压、删除或修改驱动**。硬件 ID 与哈希是分析证据，不证明兼容性、安全性或来源身份。

## 截图

<picture><source media="(prefers-color-scheme: dark)" srcset="assets/readme/workflow-dark.svg"><img src="assets/readme/workflow.svg" alt="OPlague 从 Windows PnP 和用户文件到有界检查与证据报告的数据流" width="100%"></picture>

<p align="center"><a href="assets/screenshots/oplague-workbench.png"><img src="assets/screenshots/oplague-workbench.png" alt="OPlague Windows 设备与驱动证据工作台真实截图" width="100%"></a></p>
<sub>由桌面打包工作流捕获的真实 1920×1080 Windows 截图。上方 SVG 是架构图。</sub>

## 架构与限制

~~~mermaid
flowchart LR
 A[Windows PnP 或文件] --> B[有界解析器]
 B --> C[规范化 ID 与哈希]
 C --> D[候选比较]
 D --> E[证据报告]
~~~

| 输入 | 上限 |
|---|---:|
| INF / ZIP | 512 MiB |
| ZIP 条目 | 10,000 |
| ZIP 展开内容 | 2 GiB |
| 单个 INF | 2 MiB |
| ZIP 压缩比 | 200:1 |
| UDRV manifest / entries | 4 MiB / 10,000 |

## 兼容性

| 平台 | 当前范围 |
|---|---|
| Windows | 桌面 UI、实时 PnP、包检查和游戏会话 |
| Linux | 源码运行和已保存数据检查；无实时 Windows PnP |
| macOS | 已保存数据检查；不声明系统集成 |
| Python | 3.10+ |

## 路线图

- [x] 只读 PnP 和有界 INF/ZIP 检查。
- [x] PE/COFF 头分析、SPDX 文件清单和 UDRV v1。
- [x] 需要人工审核的候选兼容性图。
- [x] 可恢复的 Windows 电源会话。
- [ ] 仅凭独立证据和测试扩展信任验证。

参阅[文档](docs/README.md)、[架构](docs/ARCHITECTURE.md)、[贡献指南](CONTRIBUTING.md)和 [Issues](https://github.com/Ivan-VHS/OPlague/issues)。许可证：Apache-2.0。
