# OPlague — 设备与驱动证据工作台

[English](README.md) · [Українська](README.uk.md) · [Русский](README.ru.md) · [简体中文](README.zh-CN.md)

> 本地只读工作台，用于 Windows 设备清单、受限驱动包检查、硬件 ID 候选分析和带来源标识的遥测。

**规格**

| 字段 | 当前记录 |
|---|---|
| 仓库 | [Ivan-VHS/OPlague](https://github.com/Ivan-VHS/OPlague) |
| 项目状态 | 开发中；Windows 优先的检查工作台 |
| 产品版本 | 项目契约未声明统一版本 |
| 主要技术栈 | Python 3.10+；JSON Schema；受限原生集成组件 |
| 运行范围 | Windows、Linux、macOS 的受支持离线工作流 |
| 实时设备清单 | 仅 Windows |
| 桌面平台 | Windows |
| 许可证 | [Apache-2.0](LICENSE) |
| 行为准则 | 尚未发布根目录 `CODE_OF_CONDUCT.md` |
| 文档审核日期 | 2026-11-26 |

<p align="center"><img src="assets/oplague-workbench-preview.svg" alt="OPlague 工作台架构预览" width="100%"></p>
<p align="center"><a href="assets/screenshots/oplague-workbench.png"><img src="assets/screenshots/oplague-workbench.png" alt="OPlague 工作台截图" width="100%"></a></p>

## 目录
- [用途与范围](#用途与范围)
- [架构与数据流](#架构与数据流)
- [要求与快速开始](#要求与快速开始)
- [接口与证据](#接口与证据)
- [安全与限制](#安全与限制)
- [发布与文档](#发布与文档)

## 用途与范围

OPlague 是本地证据工作台，提供只读 Windows Plug-and-Play 清单、受限 INF/ZIP/UDRV 元数据检查、精确规范化硬件 ID 候选匹配、本地指标和 GPU 遥测导出。如果某个离线文件或报告工作流不需要实时 Plug-and-Play 数据，则可在 Windows 之外使用。

本产品不会安装、删除、启用、卸载或修改驱动程序。它不会执行软件包 payload，不会认证设备兼容性，也不会将元数据匹配当成安全结论。

## 架构与数据流

~~~mermaid
flowchart TB
  U["用户选择的设备或文件"] --> I["受限检查器"]
  I --> N["规范化 ID、路径、大小和哈希"]
  N --> E["证据记录与候选图"]
  E --> R["本地报告 / 版本化 JSON 快照"]
  P["Windows PnP 只读查询"] --> E
  G["NVIDIA 遥测来源（只读）"] --> T["GPU 遥测快照"]
  T --> R
  R -.-> X["不安装、不加载、不解包、不认证"]
~~~

主要流程为：本地输入 → 受限解析器或固定只读系统查询 → 规范化证据 → 报告。分析前会限制不可信归档元数据。驱动包 payload 不会被解包或执行。

## 要求与快速开始

当前工具需要 Python 3.10+；实时 Plug-and-Play 清单需要 Windows。离线文件和报告检查可在受支持的 Python 环境中运行。

~~~sh
python -m venv .venv
python oplague_app.py
~~~

运行项目测试并检查用户选定的本地软件包：

~~~sh
python -m unittest discover -s tests -v
python tools/udrv_inspector.py path/to/package.udrv --json
~~~

UDRV 命令验证 manifest、声明的文件清单、大小、哈希和路径/资源限制。它不会安装、加载、解包或执行 payload。

## 接口与证据

| 接口 | 契约 | 边界 |
|---|---|---|
| Device snapshot | `oplage.device-snapshot.v1` | 版本化 JSON；设备指纹采用假名化处理 |
| GPU telemetry | `oplage.gpu-telemetry.v1` | 只读来源元数据；缺失数据保留为 unknown |
| UDRV | UDRV v1 manifest | 仅执行受限验证 |
| Batch report | `oplage.inspection-bundle.v1` | 有序本地摘要和确定性 digest |
| Pytyliki | `pytyliki.c-abi.v1` | 通过显式可信库的可选原生调用 |
| Pytyliki Iron Core | `pytyliki.iron-core-ast.v1` | 只读结构证据；源代码声明不会被视为 CI 证明 |
| Reaper | 版本化 JSON 比较 | 离线比较，不修改设备 |

规范化硬件 ID 的精确匹配只生成候选边，不进行排序、认证、安装或安全判定。NVIDIA 遥测包含来源信息；不会默认假定 GPU 或遥测提供方存在。

## 安全与限制

> **只读边界：** 文档中的检查路径不会安装、加载、解包或执行驱动软件包及其 payload。

应将 INF、ZIP、UDRV 和导入的报告视为不可信输入。解析器对条目数量、路径、大小和压缩率实施限制；SHA-256 可检测内容变化，但不是数字签名，也不能验证发布者身份。Authenticode 元数据仅针对选定的受支持文件采集，不能证明设备兼容性或运行安全性。

实时 Plug-and-Play 清单仅支持 Windows。离线报告/软件包检查与实时清单是不同的工作流。Rust 2021 diagnostics ABI consumer 是一个范围有限的集成组件，并非将整个工作台迁移到 Rust/Slint。项目契约未声明统一产品版本。

Beelzebul 仓库扫描器是本地静态源码保障工具，不是终端恶意软件防护、进程内存扫描或隔离区。其具体行为和漏洞披露流程见 [SECURITY.md](SECURITY.md)。

## 发布与文档

请从[文档索引](docs/README.md)和[信息架构图](docs/INFORMATION_ARCHITECTURE.md)开始。

- [功能矩阵](docs/FEATURES.md)
- [架构](docs/ARCHITECTURE.md)
- [UDRV v1 格式](docs/UDRV_FORMAT_V1.md)
- [设备兼容性图](docs/DEVICE_COMPATIBILITY_GRAPH.md)
- [GPU telemetry bridge v1](docs/GPU_TELEMETRY_BRIDGE_V1.md)
- [联邦集成](docs/FEDERATED_INTEGRATION.md)
- [Windows 发布分发](docs/RELEASE.md)
- [安全策略](SECURITY.md)

Windows 发布工作流只创建供维护者审核的 **GitHub Release 草稿**。SHA-256 sidecar 用于检测相对于摘要的字节变化，不是数字签名，也不能认证发布者。正式发布需要维护者单独操作。

修改解析器、schema、候选匹配或 telemetry 前，请阅读 [CONTRIBUTING.md](CONTRIBUTING.md)。本仓库采用 [Apache-2.0](LICENSE)；请保留上游声明和归属信息。

## 发布历史

当前项目契约未声明统一产品版本。不要从草稿工作流或包元数据推断正式发布版本。公开发布和支持状态必须由真实标签与已发布制品证明。JSON schema 或 UDRV manifest 的破坏性变更需要明确版本和迁移说明。