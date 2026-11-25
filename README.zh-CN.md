# OPlague — 设备、驱动与游戏性能工作台

[English](README.md) · [Українська](README.uk.md) · [Русский](README.ru.md) · [简体中文](README.zh-CN.md)

[![Windows build](https://img.shields.io/github/actions/workflow/status/Ivan-VHS/OPlague/desktop-build.yml?branch=main&label=Windows%20build)](https://github.com/Ivan-VHS/OPlague/actions/workflows/desktop-build.yml) [![文档检查](https://img.shields.io/github/actions/workflow/status/Ivan-VHS/OPlague/docs.yml?branch=main&label=Docs%20checks)](https://github.com/Ivan-VHS/OPlague/actions/workflows/docs.yml) [![Apache-2.0](https://img.shields.io/github/license/Ivan-VHS/OPlague)](LICENSE)

<p align="center"><img src="assets/readme/dashboard.svg" alt="OPlague 项目概览" width="100%"></p>
<p align="center"><a href="assets/screenshots/oplague-workbench.png"><img src="assets/screenshots/oplague-workbench.png" alt="OPlague Windows 工作台" width="100%"></a></p>

OPlague 是一款用于设备与驱动检查、软件包分析、兼容性证据和游戏性能诊断的本地桌面工作台。

**默认边界：**检查仅执行只读操作。设备发现和用户选定文件分析不会安装、启用、卸载或修改驱动。兼容性候选和遥测数据仅供审查，不构成认证。

## 功能

- Windows Plug-and-Play 设备盘点及受限 INF/ZIP 软件包检查。
- PE 与 Authenticode 检查、标准化硬件 ID、哈希和 SPDX 清单。
- 设备兼容性证据、UDRV 软件包验证和结构化报告。
- 本地游戏遥测、帧时间分析和可撤销的用户级性能配置。

详细资料：[功能](docs/FEATURES.md) · [架构](docs/ARCHITECTURE.md) · [Authenticode](docs/AUTHENTICODE.md) · [驱动目标架构](docs/DRIVER_TARGET_ARCHITECTURE.md) · [UDRV 格式](docs/UDRV_FORMAT_V1.md) · [游戏工作台](docs/GAMING_PERFORMANCE_WORKBENCH.md) · [GPU telemetry bridge v1](docs/GPU_TELEMETRY_BRIDGE_V1.md)。

## 运行与测试

当前桌面工具和验证脚本需要 Python 3.10–3.12。

```sh
python oplague_app.py
python -m unittest discover -s tests -v
python -m oplague --verify
python -m oplague --catalog
```

检查软件包：

```sh
python tools/udrv_inspector.py path/to/package.udrv --json
```

使用 PyInstaller 构建独立 Windows 程序：

```sh
python -m pip install --upgrade pyinstaller
python -m PyInstaller --noconfirm --clean --onefile --windowed --name OPlague oplague_app.py
```

## 集成与证据

- [文档索引](docs/README.md) · [Reaper 运行时集成](docs/REAPER_RUNTIME_INTEGRATION.md)
- [DAK 与 Mora 集成](https://github.com/Ivan-VHS/DAK/blob/main/docs/GAMING_PERFORMANCE_INTEGRATION.md)
- [生态共享标准](https://github.com/Ivan-VHS/DAK/blob/main/docs/SHARED_STANDARDS.md)

当前行为以源码、Schema 和测试为准。工作台不会刷写固件、安装驱动或自动认证硬件兼容性。

[贡献指南](CONTRIBUTING.md) · [安全策略](SECURITY.md) · [Apache-2.0 许可证](LICENSE)
