<p align="center"><picture><source media="(prefers-color-scheme: dark)" srcset="assets/readme/hero-banner-dark.svg"><source media="(prefers-color-scheme: light)" srcset="assets/readme/hero-banner-light.svg"><img src="assets/readme/hero-banner-light.svg" alt="OPlague 设备、驱动与游戏工作台" width="880"></picture></p>

# OPlague — 设备、驱动与游戏性能工作台

[English](README.md) · [Українська](README.uk.md) · [Русский](README.ru.md) · [简体中文](README.zh-CN.md)

[![Quality](https://img.shields.io/github/actions/workflow/status/Ivan-VHS/OPlague/completeness-check.yml?branch=main&style=flat-square&label=Quality)](https://github.com/Ivan-VHS/OPlague/actions/workflows/completeness-check.yml) [![Windows build](https://img.shields.io/github/actions/workflow/status/Ivan-VHS/OPlague/desktop-build.yml?branch=main&style=flat-square&label=Windows%20build)](https://github.com/Ivan-VHS/OPlague/actions/workflows/desktop-build.yml) [![Apache-2.0](https://img.shields.io/github/license/Ivan-VHS/OPlague?style=flat-square)](LICENSE)

> 本地 Windows 优先工作站，用于有界设备与驱动证据检查、注明来源的遥测，以及显式且可恢复的游戏会话电源计划流程。

**项目记录：** 开发中 · 尚未声明统一产品版本 · Python 3.10+ · JSON Schema · 部分 Rust 2021 diagnostics consumer · Windows 桌面与实时设备盘点 · Apache-2.0 · **文档审核：** 2026-11-27 UTC

## 项目用途与范围

OPlague 包含两个刻意分离的工作流程：

1. **设备与软件包证据。** 只读 Windows Plug-and-Play 盘点、有界 INF/ZIP/UDRV 检查、规范化硬件 ID 候选匹配、本地报告和带来源信息的 GPU 遥测。
2. **游戏会话规划。** 显式的 Windows 流程：保存本地快照，并可临时选择 Windows 内置电源计划。只有当当前计划仍是 OPlague 应用的计划时，才会恢复原来的计划。

驱动与软件包检查不会安装、删除、启用、卸载、解压或执行驱动及其 payload。游戏会话流程是独立且需要用户确认的系统更改：它不会修改驱动、注册表、固件、时钟频率、电压、服务或网络配置。

## 功能

- **实时设备盘点：** 通过固定的只读查询收集当前 Windows Plug-and-Play 记录。实时盘点仅支持 Windows。
- **有界软件包检查：** 检查 INF 元数据和 ZIP 结构，并限制路径、条目数量、大小及压缩比。
- **UDRV v1 完整性检查：** 验证 manifest、声明的 payload 清单、文件大小、SHA-256 和资源/路径限制，不解压或执行 payload。
- **证据报告：** 确定性批量摘要、内容 digest，以及带伪匿名设备指纹的版本化 JSON 快照。
- **候选兼容性图：** 规范化硬件 ID 的精确匹配只会创建候选边，不会对驱动排序、认证，也不证明其安全或兼容。
- **指标与遥测：** 比较规范化配置，并可通过 `nvidia-smi` 读取 NVIDIA 传感器数据。缺失的传感器值保持未知；遥测只读。
- **游戏会话：** 用户明确确认后，保存设备、驱动和电源计划快照，并可临时切换到 Windows 内置 High Performance 电源计划。恢复过程带保护：若电源计划在会话之外被更改，OPlague 不会覆盖用户的新选择。
- **互操作：** 版本化设备快照与 Reaper 报告；通过调用方明确选择的可信库，可选调用 Pytyliki C ABI。
- **Rust 诊断桥接：** Pytyliki diagnostics ABI 的 Rust 2021 有界消费者仅部分实现；这并非完整的 Rust/Slint 迁移。

在不需要实时 Plug-and-Play 数据的情况下，受支持的 Python 环境可在 Windows 之外离线分析软件包和报告。

## 快速开始

需要 Python 3.10+；桌面应用、实时 Plug-and-Play 盘点和电源计划控制需要 Windows。NVIDIA 遥测还需要本机可用且受支持的 `nvidia-smi` 提供程序。

启动 Windows 工作台：

~~~sh
python oplague_app.py
~~~

运行测试并检查用户选择的 UDRV 软件包：

~~~sh
python -m unittest discover -s tests -v
python tools/udrv_inspector.py path/to/package.udrv --json
~~~

UDRV 检查器会在固定限制内验证元数据和文件 digest。它不会解压、安装、加载或执行软件包内容。

## 数据契约

| 接口 | 契约 | 边界 |
|---|---|---|
| Device snapshot | `oplage.device-snapshot.v1` | 版本化 JSON；伪匿名指纹 |
| GPU telemetry | `oplage.gpu-telemetry.v1` | 只读来源元数据；未知值保持未知 |
| Batch evidence | `oplage.inspection-bundle.v1` | 有序报告与确定性 digest |
| 驱动软件包 | UDRV v1 | 仅有界 manifest/完整性验证 |
| Reaper comparison | `reaper.oplage-comparison.v1` | 离线报告验证，不修改设备 |
| Pytyliki metrics | `pytyliki.c-abi.v1` | 通过显式信任的库进行可选原生调用 |
| 游戏会话 | `oplague.gaming.v1` | 本地快照与受保护的 Windows 电源计划切换 |

SHA-256 用于发现相对于已记录摘要的字节变化；它不是数字签名、发布者认证或安全证明。Authenticode 元数据是有关受支持文件的证据，不是设备兼容性认证。

## 安全与限制

将 INF、ZIP、UDRV、遥测导出和导入报告视为不可信输入。解析器遵守资源限制；软件包 payload 不会被解压或执行。硬件 ID 匹配表示候选关系，而非安全结论。

电源计划切换是明确且独立的操作，并非设备检查的一部分。该功能目前仅支持 Windows，会保存会话前快照，并且不会覆盖后来由外部操作设置的电源计划。选择电源计划或比较 frametime 数据不保证性能提升。

Beelzebul 仓库扫描器是本地/静态源码保障工具，不是端点恶意软件防护、进程内存检查或隔离工具。

## 文档

- [文档索引](docs/README.md) · [信息架构](docs/INFORMATION_ARCHITECTURE.md)
- [功能矩阵](docs/FEATURES.md) · [架构](docs/ARCHITECTURE.md)
- [UDRV v1 格式](docs/UDRV_FORMAT_V1.md) · [设备兼容性图](docs/DEVICE_COMPATIBILITY_GRAPH.md)
- [GPU telemetry v1 桥接](docs/GPU_TELEMETRY_BRIDGE_V1.md) · [设备与驱动检查](docs/clusters/device-driver-inspection.md)
- [联邦集成](docs/FEDERATED_INTEGRATION.md) · [Windows 发布流程](docs/RELEASE.md)
- [Pytyliki diagnostics ABI](docs/PYTYLIKI_DIAGNOSTICS_ABI.md) · [安全策略](SECURITY.md)
- [视觉发布标准](docs/README_VISUAL_STANDARD.md)

Windows 发布工作流会创建供维护者审查的 GitHub Release 草稿。正式发布需要维护者另行操作；SHA-256 sidecar 不是数字签名。

## 贡献与许可证

修改解析器、schema、遥测或系统集成前，请阅读 [CONTRIBUTING.md](CONTRIBUTING.md)。保留输入资源限制、显式权限和证据来源。不要提交私有驱动 payload 或可识别个人身份的硬件导出。

本项目采用 [Apache-2.0](LICENSE) 许可证。请保留第三方声明和归属信息。
