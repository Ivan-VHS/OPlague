
<p align="center"><picture><source media="(prefers-color-scheme: dark)" srcset="assets/readme/hero-banner-dark.svg"><source media="(prefers-color-scheme: light)" srcset="assets/readme/hero-banner-light.svg"><img src="assets/readme/hero-banner-light.svg" alt="OPlague 设备、驱动与游戏工作台" width="880"></picture></p>
<h1 align="center">OPlague — 设备、驱动与游戏性能工作台</h1>
<p align="center"><strong>本地 Windows 工作站，用于受限设备/驱动检查、证据报告和可恢复的游戏会话调优。</strong></p>
<p align="center"><a href="https://github.com/Ivan-VHS/OPlague/actions/workflows/completeness-check.yml"><img alt="Quality checks" src="https://img.shields.io/github/actions/workflow/status/Ivan-VHS/OPlague/completeness-check.yml?branch=main&style=flat-square&label=Quality"></a> <a href="https://github.com/Ivan-VHS/OPlague/actions/workflows/desktop-build.yml"><img alt="Windows build" src="https://img.shields.io/github/actions/workflow/status/Ivan-VHS/OPlague/desktop-build.yml?branch=main&style=flat-square&label=Windows%20build"></a> <a href="LICENSE"><img alt="Apache-2.0" src="https://img.shields.io/github/license/Ivan-VHS/OPlague?style=flat-square"></a></p>

[快速开始](#快速开始) · [Revival 更新](#文档-revival-更新) · [视觉概览](#视觉概览) · [架构](#架构) · [文档索引](docs/README.md)

> **安全边界：**驱动和软件包检查为只读操作：payload 不会被解压、执行、安装或加载。精确 hardware ID 匹配只是候选证据，不是兼容性认证。独立的游戏会话可在保存 snapshot 后临时选择 Windows 内置电源计划；恢复逻辑会避免覆盖之后发生的外部更改。

## 快速开始

**环境要求：**Python 3；实时 Plug and Play 设备清单需要 Windows。保存的报告和软件包元数据可离线检查。桌面 UI 需要 Tkinter。

~~~sh
git clone https://github.com/Ivan-VHS/OPlague.git
cd OPlague
python oplague_app.py
~~~

运行测试与视觉契约检查：

~~~sh
python -m compileall -q oplague_app.py oplage_app.py tests
python tools/validate_visual_canon.py ui_theme.py
python -m unittest discover -s tests -v
~~~

常用 CLI 检查：

~~~sh
python -m oplague --verify
python -m oplague --catalog
python -m oplague --search "ballistic"
python -m oplague --profile 5
python -m oplague --rank reach
~~~

## 文档 Revival 更新

| 之前 | Revival 文档 |
|---|---|
| 静态项目概览，图片角色不清楚 | 主题适配 Hero，并分别标注真实截屏和架构图 |
| 驱动分析与游戏设置看起来属于同一权限边界 | 只读检查与显式、可恢复的电源计划会话分离 |
| 功能成熟度描述不一致 | 功能矩阵明确标注来源、数据和安全边界 |
| 快速开始与运维细节混杂 | 已核对的启动、测试和 CLI 命令置顶 |
| 文档链接分散 | 主题 Hub、文档索引和发布规范 |

这是文档更新，**不代表软件版本升级或新 Release**。行为以源代码、测试、Schema 和当前 CI workflow 为准。

## 已实现范围

| 领域 | 当前行为 | 边界 |
|---|---|---|
| 设备清单 | Windows Plug and Play identity/status 收集 | 实时清单仅限 Windows |
| INF / ZIP 检查 | 受限元数据解析、路径校验、hash 和架构提示 | 不解压、不执行 |
| Authenticode | 所选文件的签名、signer 和 timestamp 元数据 | 不是安装/加载，也不是安全结论 |
| 兼容性匹配 | 基于规范化 hardware ID 的精确候选关联 | 仅供人工审查的证据 |
| UDRV v1 | Manifest、文件大小与 SHA-256 校验 | 不安装、不加载驱动 |
| 报告与快照 | 版本化 JSON、批量摘要与离线对比 | 本地数据；hash 不证明发布者可信 |
| 游戏会话 | Snapshot、临时内置电源计划和受保护恢复 | 不涉及 GPU 超频、驱动修改或固件控制 |
| 指标 | 加权距离和配置对比 | 仅供参考，不是认证评分 |

## 视觉概览

<table><tr><td width="50%"><a href="assets/screenshots/oplague-workbench.png"><img src="assets/screenshots/oplague-workbench.png" alt="OPlague Windows 设备与驱动工作台实际截屏" width="100%"></a><p><sub><strong>真实应用截屏</strong> — Windows desktop，1920×1080。</sub></p></td><td width="50%"><img src="assets/readme/workflow.svg" alt="OPlague 本地输入、受限解析、证据、候选分析和报告流程图" width="100%"><p><sub><strong>架构示意图</strong> — 证据处理流程，不是 UI 截图。</sub></p></td></tr></table>

## 架构

~~~mermaid
flowchart LR
  A[Windows PnP / 本地软件包] --> B[受限元数据解析器]
  B --> C[已验证证据记录]
  C --> D[候选匹配与审查]
  D --> E[Dry-run 报告]
  E --> F[显式 JSON 导出]
  G[已保存设备快照] --> D
  H[游戏会话] --> I[电源计划快照]
  I --> J[临时内置计划]
  J --> K[受保护恢复]
~~~

驱动检查与游戏会话是独立流程。驱动流水线不会安装、加载、解压或执行软件包内容。

## 配置与访问

项目不需要托管服务、API Token、账户、根目录 .env 或测试登录。实时设备清单通过本地 Windows PowerShell/CIM 获取。如果提供程序不可用，应用会报告错误，不会伪造设备列表。

桌面界面提供 Duck 配色与动效偏好。系统电源计划修改仅属于单独、显式的游戏会话流程。

## 仓库结构

| 路径 | 职责 |
|---|---|
| oplague_app.py | 对外桌面入口 |
| oplage_app.py | 桌面实现与检查逻辑 |
| tools/ | CLI、报告、指标和 UDRV 工具 |
| tests/ | 使用合成 fixture 的单元与回归测试 |
| schemas/ | 版本化报告和软件包契约 |
| docs/ | 架构、安全、集成与操作文档 |
| assets/readme/ | 主题适配 Hero 和流程示意图 |
| assets/screenshots/ | Windows 应用实际截屏 |
| .github/workflows/ | CI、Windows 打包与质量门禁 |

## 验证与项目状态

~~~sh
python -m unittest discover -s tests -v
python -m oplague --verify
python tools/udrv_inspector.py path/to/package.udrv --json
git diff --check
~~~

当前能力与限制见 [功能矩阵](docs/FEATURES.md)、[架构](docs/ARCHITECTURE.md)、[设备与驱动检查 Hub](docs/clusters/device-driver-inspection.md) 和 [信息架构地图](docs/INFORMATION_ARCHITECTURE.md)。Heuristic 或匹配结果不能视为恶意软件 verdict 或设备认证。

## 参与开发与安全

修改 parser、系统集成或安全控制前，请阅读 [CONTRIBUTING.md](CONTRIBUTING.md)。发布规则见 [README Visual Standard](docs/README_VISUAL_STANDARD.md)，安全策略见 [SECURITY.md](SECURITY.md)。

## 许可证

[Apache-2.0](LICENSE)。
