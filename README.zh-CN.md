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
- **兼容性 dry-run：** 仅通过精确规范化硬件 ID 关联设备与 INF Models。候选关系不是驱动排名或兼容性结论。
- **Metric Lab：** 通过加权距离、余弦相似度、正交性和重复测量方差比较归一化配置。
- **设备联邦：** 导出有界版本化 JSON 快照并离线比较。原始 PnP ID 会替换为假名哈希；它们仍可被关联，并非匿名化。
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

[UDRV 格式](docs/UDRV_FORMAT_V1.md) · [设备兼容图](docs/DEVICE_COMPATIBILITY_GRAPH.md) · [设备联邦契约](docs/FEDERATED_INTEGRATION.md) · [QCS 语法](docs/QUANTUM_CONTOUR_SYNTAX.md) · [统一工程标准](docs/UNIFIED_ENGINEERING_STANDARD.md)

[Windows 发布版](https://github.com/Ivan-VHS/OPlague/releases) · [桌面构建](https://github.com/Ivan-VHS/OPlague/actions/workflows/desktop-build.yml)

**项目协作：** [Reaper](https://github.com/Ivan-VHS/Reaper) · [Pytyliki](https://github.com/Ivan-VHS/Pytyliki) · [3×3 集成矩阵](https://github.com/Ivan-VHS/Reaper/blob/main/docs/PROJECT_FEDERATION_MATRIX.md)。

## 许可证

[Apache License 2.0](LICENSE)

UI motion: [12 animation principles](docs/DISNEY_MOTION_SYSTEM.md).
