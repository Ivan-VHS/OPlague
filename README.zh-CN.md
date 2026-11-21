# OPlague — 驱动工作台

Python 3.10+ · Windows · Apache-2.0 · [桌面 CI](https://github.com/Ivan-VHS/OPlague/actions/workflows/desktop-build.yml)
**开发者：** [Ivan-VHS](https://github.com/Ivan-VHS)

**只读工作台：** Windows 设备盘点、驱动包检查与兼容性证据比较。不会安装、加载或修改驱动。

[English](README.md) · [Русский](README.ru.md) · [Українська](README.uk.md) · [简体中文](README.zh-CN.md)

| 模块 | 输出 | 边界 |
|---|---|---|
| 设备 | Plug and Play、状态、硬件 ID | 只读 |
| INF/ZIP | 元数据、哈希、路径、限制 | 不解压/执行 |
| 架构 | INF target 与 host 对比 | 证据，不是结论 |
| 兼容图 | 精确硬件 ID 关系 | 候选项 |
| UDRV v1 | manifest、大小、SHA-256 | 仅检查 |
| DRIVE-LENS | 溯源、HMAC 假名 | 不自动判定 |
| 报告 | 顺序、汇总、fingerprint | 不改系统 |
| Clinical Systems | 120 项原则、36 项指标检查 | 仅供参考 |

运行：`python oplague_app.py` · 测试：`python -m unittest discover -s tests -v`。

| INF target | PE machine |
|---|---:|
| NTx86 | 0x014C |
| NTamd64 | 0x8664 |
| NTarm | 0x01C4 |
| NTarm64 | 0xAA64 |
| NTia64（旧版） | 0x0200 |

UDRV v1：manifest ≤4 MiB · ≤10,000 项 · 单文件 ≤512 MiB · 总计 ≤2 GiB · SHA-256 缓冲区 1 MiB。

ID/hash 匹配不证明发布者可信、系统兼容或安装安全。参见[功能](docs/FEATURES.md)、[架构](docs/ARCHITECTURE.md)、[UDRV](docs/UDRV_FORMAT_V1.md)、[项目规范](docs/PROJECT_STEWARDSHIP_STANDARD.md)、[设计](docs/DUCK_SOVEREIGN_CANON.md)、[文档索引](docs/README.md)。

[Apache-2.0](LICENSE)
