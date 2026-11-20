# OPlague

**原生桌面驱动管理、驱动包工程与硬件诊断平台。**

[English](README.md) · [Русский](README.ru.md) · [Українська](README.uk.md) · [简体中文](README.zh-CN.md)

OPlague 是一个原生桌面应用项目，旨在构建 **DuckDriver OmniCore (DDO)**：以更安全的方式发现硬件、检查驱动程序包并创建可移植驱动容器。

> **状态：** 已实现早期 Windows x64 桌面预览版。设备清单和 INF/ZIP 驱动包检查仅以只读方式提供；驱动安装、UDRV 创建、恢复和高级诊断尚未实现。

## 产品愿景

- **硬件清单：** 发现设备，并展示硬件标识、设备关系和驱动状态。
- **驱动工作区：** 在安装前导入、检查、验证、编目和比较驱动包。
- **通用驱动容器（.udrv）：** 规划中的可移植格式，用于封装驱动文件、清单、元数据、兼容性信息和完整性数据。
- **DuckDriver OmniCore：** 协调硬件发现、分析、验证、打包和部署准备。
- **配置档案与恢复：** 保存已知可用配置，并提供明确的回滚流程。
- **诊断：** 展示设备状态和受支持的系统指标；在平台 API 允许时计划提供 DPC/ISR 延迟分析。
- **原生桌面体验：** 采用统一的白、蓝、红视觉体系。

## 安全原则

1. 在信任驱动包之前先检查清单、结构、元数据和可用的哈希信息。
2. 将导入的驱动包、脚本和二进制文件视为不可信输入。
3. 不为了识别或检查硬件而执行外部内核代码。
4. 将只读发现和包分析与特权安装分离。
5. 使高权限操作明确、可审查，并在平台允许时可撤销。
6. 对证据不足和验证失败给出报告，不猜测兼容性。

`.udrv` 是一种打包方案，并不保证任意驱动都具有通用兼容性或安全性。实际安装取决于操作系统、硬件、签名策略和供应商要求。

## 架构

| 层 | 职责 |
| --- | --- |
| 原生桌面外壳 | 生命周期、导航、设置和用户流程 |
| 硬件发现 | 设备枚举和稳定的硬件标识 |
| 驱动目录 | 驱动包、版本、供应商及兼容性索引 |
| 包验证器 | 清单、内容、哈希和一致性检查 |
| UDRV 容器 | 可移植包结构与元数据规范 |
| OmniCore 编排器 | 协调分析、打包和部署准备 |
| 诊断模块 | 设备状态和受支持的性能指标 |
| 恢复管理器 | 配置档案、快照和回滚计划 |

以上是计划中的架构边界，并不表示所有模块都已存在于 `main` 分支。

## 路线图

- [x] 原生桌面外壳（早期 Windows 预览版）
- [ ] 硬件发现及可搜索的设备清单
- [ ] 版本化的 `.udrv` 容器规范
- [ ] 驱动包导入、检查和验证
- [ ] 驱动目录及兼容性依据
- [ ] 配置档案快照和受保护的恢复流程
- [ ] 诊断功能，包括受支持平台上的 DPC/ISR 分析
- [ ] 自动化测试、签名发布和平台打包

## 截图

待应用拥有可运行的界面后再添加真实截图。概念图和模型图不会被标注为已实现软件的截图。

## 参与贡献

请提交范围明确且可复现的改动，并在适当情况下附上测试或验证记录。请说明操作系统和硬件假设；不要提交专有驱动二进制文件、凭据、私人设备数据或未经许可的供应商资料。特权操作必须保持隔离且可审查。

## 原生桌面应用

已实现早期 **Windows x64 桌面预览版**：只读 Plug and Play 设备清单；INF 元数据和 ZIP 驱动包检查；SHA-256 计算以及路径、大小、条目数和压缩比检查。应用不会安装驱动、加载内核代码、解压或执行包内内容。

- [Windows x64 Releases](https://github.com/Ivan-VHS/OPlague/releases)
- [桌面构建工作流与 CI 工件](https://github.com/Ivan-VHS/OPlague/actions/workflows/desktop-build.yml)
- [最新构建运行](https://github.com/Ivan-VHS/OPlague/actions/workflows/desktop-build.yml?query=branch%3Amain)

成功运行会上传 `OPlague-windows-x64.zip`；`v*` 标签会发布 GitHub Release。Windows + Python 3.10+ 源码启动命令：`python oplague_app.py`。UDRV 创建、驱动安装、回滚、签名和 DPC/ISR 诊断仍属于后续计划。


Windows 源码启动文件的正确名称为 `oplague_app.py`，桌面构建工作流使用该入口。

## 已实现功能与联邦集成

当前桌面应用和工具包含：

- **只读设备清单：**枚举 Windows Plug and Play 设备，不更改设备状态。
- **INF / ZIP 检查：**读取本地元数据、SHA-256、INF Hardware ID 和目标架构证据，并执行有界的路径、归档条目数、展开大小及压缩率检查。
- **批量报告合成：**按输入顺序生成 oplage.inspection-bundle.v1 汇总，包含聚合计数和确定性 bundle 指纹。
- **UDRV 完整性检查：**验证版本化 manifest、payload 清单、声明大小与哈希、路径和资源限制。检查过程不会解压、安装、加载或执行 payload。
- **Metric Lab 与兼容性 dry-run：**分析归一化指标、加权距离，并仅根据完全匹配的规范化 Hardware ID 建立候选边。候选项不是兼容性或安装结论。
- **联邦设备快照：**tools/federation.py 按版本化的 oplage.device-snapshot.v1 schema 导出快照，并可在支持的 Python 平台上比较已保存的快照。实时 PnP 采集需要 Windows 和 PowerShell；上限为 10,000 台设备和 16 MiB JSON。导出省略原始 PnP InstanceId，改用 SHA-256 假名指纹；这些指纹仍可关联，并非匿名化。
- **跨项目桥接：**Reaper 可读取快照和指标配置。只有调用方显式提供可信 ABI v1 库的绝对路径时，才会启用可选的 Pytyliki 原生交叉核验；加载 DLL/SO 会执行原生代码。

快照与离线比较示例：

~~~powershell
python -m tools.federation snapshot --output device-snapshot.json
python -m tools.federation compare --reference baseline.json --candidate current.json --output comparison.json
~~~

联邦流程不会修改设备或驱动，只写入明确指定的报告文件。该桥接尚未实现驱动安装/卸载、设备启用/禁用、签名、恢复或实时 DPC/ISR 诊断。

参见 [联邦集成契约](docs/FEDERATED_INTEGRATION.md)、[快照 schema](schemas/oplage.device-snapshot.v1.schema.json)、[报告合成架构](docs/CONCATENATION_ARCHITECTURE.md) 和 [精确 ID 兼容性图](docs/DEVICE_COMPATIBILITY_GRAPH.md)。

## 许可证

许可条款请参阅 [LICENSE](LICENSE)。

## 精确硬件 ID 兼容性图与 dry-run

桌面端 **Compatibility & dry-run** 标签页将本机只读 PnP 设备清单与
已检查 INF 文件 `Models` 节中的硬件标识进行匹配。只有规范化后的
硬件标识完全一致时才会生成候选边；架构不匹配会单独报告。前缀或设备
名称相似不会被视为兼容。

候选项**不代表**驱动排名、签名、可信度、Windows 版本兼容性或安全结论。
生成的计划严格只读：`install_attempted=false`、
`system_modified=false`、`proposed_operation=none`。任何后续特权操作
都必须经过人工审核并补充证据。详见
[兼容性图规范](docs/DEVICE_COMPATIBILITY_GRAPH.md)。

## 已实现的检查工具（2026 年 11 月 20 日）

- **UDRV v1 Integrity Inspector：** 以只读方式检查目录包或 ZIP，不解压或执行内容。验证清单版本、完整文件清单、文件大小和 SHA-256；拒绝未声明或缺失文件、路径穿越、符号链接、重复项及超出资源限制的包。目录清单读取严格限制为 4 MiB；包限制为最多 10,000 个条目、单文件 512 MiB、总计 2 GiB。
- **批量报告组合：** 将最多 256 份 INF/ZIP 检查结果按输入顺序组合为规范 JSON，汇总大小、压缩包条目、INF 和 .cat 文件数量；拒绝重复 SHA-256，并计算整个报告的 SHA-256 指纹。该指纹不是供应商签名。
- **兼容性图与 dry-run：** 只有规范化 Hardware ID 完全匹配时才会将设备连接到 INF 候选项。架构不匹配单独报告；名称或前缀相似不代表兼容。计划明确输出 install_attempted=false、system_modified=false、proposed_operation=none。
- **INF 目标架构分析：** 支持显式 x86、amd64、ARM、ARM64 和 legacy IA64 目标，并返回 explicit_match、explicit_nonmatch 或 unknown。
- **Metric Lab：** 比较键和维度一致的归一化 JSON 配置档案，计算欧几里得距离、加权距离、余弦相似度、角度、正交性、能量和重复测量的样本方差。

以上工具均在本地以只读方式运行。它们不会安装、解压、加载或执行驱动；完整性检查也不代表供应商真实性或驱动兼容性。


## 项目生态

本仓库属于由三个独立项目组成的协作体系。Reaper 负责编程语言、运行时与工作流编排；OPlague 负责只读 Windows 设备清单和驱动程序包检查；Pytyliki 负责基于 C11 的处理器、内存与数值计算核心。 See the [3 × 3 项目协作矩阵](https://github.com/Ivan-VHS/Reaper/blob/main/docs/PROJECT_FEDERATION_MATRIX.md) for the 3 × 3 cross-product, implemented interfaces, data directions and safety boundaries.

- [Reaper — 编程语言、运行时与工作流编排](https://github.com/Ivan-VHS/Reaper/blob/main/README.zh-CN.md) · [integration contract](https://github.com/Ivan-VHS/Reaper/blob/main/docs/FEDERATED_INTEGRATION.md)
- [OPlague — 只读 Windows 设备清单与驱动程序包检查](https://github.com/Ivan-VHS/OPlague/blob/main/README.zh-CN.md) · [integration contract](https://github.com/Ivan-VHS/OPlague/blob/main/docs/FEDERATED_INTEGRATION.md)
- [Pytyliki — C11 处理器、内存与数值计算核心](https://github.com/Ivan-VHS/Pytyliki/blob/main/README.zh-CN.md) · [integration contract](https://github.com/Ivan-VHS/Pytyliki/blob/main/docs/FEDERATED_INTEGRATION.md)
