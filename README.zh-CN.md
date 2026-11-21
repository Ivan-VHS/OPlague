# OPlague — 驱动工作台

[Windows 桌面构建](https://github.com/Ivan-VHS/OPlague/actions/workflows/desktop-build.yml) · [CI](https://github.com/Ivan-VHS/OPlague/actions) · Python 3.10+ · Windows · Apache-2.0
**开发者：** [Ivan-VHS](https://github.com/Ivan-VHS)

**OPlague 是只读工作台：用于 Windows 设备盘点、驱动包检查和基于证据的比较。它不会安装、加载或修改驱动。**

[English](README.md) · [Русский](README.ru.md) · [Українська](README.uk.md) · [简体中文](README.zh-CN.md)

## Windows 实际运行截图

<p align="center"><img src="assets/screenshots/oplague-workbench.png" alt="Windows 中运行的 OPlague 工作台" width="100%"></p>
<sub>由 desktop-build 工作流捕获的真实桌面画面，1920×1080。SVG 示意预览仍单独保留：<a href="assets/oplague-workbench-preview.svg">查看示意图</a>。</sub>

## 工作台模块

| 模块 | 证据 / 输出 | 边界 |
|---|---|---|
| 设备盘点 | Plug and Play 身份、状态和硬件 ID | 只读检测 |
| INF / ZIP 检查 | 元数据、哈希、路径和资源限制 | 不执行软件包、不安装驱动 |
| 架构检查 | INF target 与主机架构比较 | 证据，不是兼容性结论 |
| 兼容性图 | 精确规范化的硬件 ID 关系 | 仅为候选关系 |
| UDRV v1 | manifest、载荷大小和 SHA-256 | 完整性检查；不安装/加载 |
| DRIVE-LENS | 来源记录、HMAC 假名及属性/时间窗口分组 | 不自动判定 |
| 批量报告 | 有序结果、汇总和报告 fingerprint | 不写入系统 |
| Metric Lab | 归一化向量、加权距离和方差 | 对用户提供的数据进行分析 |
| Clinical Systems | 120 条原则记录和 36 项遥测检查 | 操作建议，不是医疗或设备认证 |
| Impact Profiles | 20 个可搜索语义配置及五个序数维度 | 仅词汇目录；不推断硬件信息 |

## 界面动效与无障碍

工作台标题栏中的 **Движение** 按钮可打开并保存 **Reduce Motion** 和 **Eco / Low-CPU Visuals** 偏好设置。启用后，过渡时长不超过 80 ms，并抑制空间移动及非必要效果。由于 OPlague 没有音频传输，**Sync to Transport / BPM** 保持禁用。详见 [界面动效规范](docs/UI_MOTION.md)。

## 运行与测试

启动 Windows 桌面工作台：

```sh
python oplague_app.py
```

运行测试并检查语义配置目录：

```sh
python -m unittest discover -s tests -v
python -m oplague --verify
python -m oplague --catalog
python -m oplague --search "баллистический"
python -m oplague --profile 5
python -m oplague --rank reach
python tools/udrv_inspector.py path/to/package.udrv --json
python tools/clinical_systems.py --catalog --pretty
```

Windows 工作流会检查视觉规范并运行测试，构建独立的 `OPlague.exe`，捕获实际运行中的应用界面，并发布 Windows x64 压缩包。

## 数值参考

| INF target | PE machine |
|---|---:|
| NTx86 | `0x014C` |
| NTamd64 | `0x8664` |
| NTarm | `0x01C4` |
| NTarm64 | `0xAA64` |
| NTia64（旧版） | `0x0200` |

UDRV v1 限制：manifest ≤4 MiB · ≤10,000 项 · 单文件 ≤512 MiB · 总载荷 ≤2 GiB · SHA-256 缓冲区 1 MiB。

ID 或哈希匹配不证明发布者可信、系统兼容、设备适用或安装安全。HMAC 假名和报告 fingerprint 有助于保持一致性与来源记录，但本身不能证明真实性。

[功能](docs/FEATURES.md) · [架构](docs/ARCHITECTURE.md) · [UDRV 格式](docs/UDRV_FORMAT_V1.md) · [CSR-120](docs/CLINICAL_SYSTEMS_CSR120.md) · [Impact Profiles](oplague/impact.py) · [项目规范](docs/PROJECT_STEWARDSHIP_STANDARD.md) · [设计](docs/DUCK_SOVEREIGN_CANON.md) · [文档索引](docs/README.md) · [许可证](LICENSE)

## DUCK CORE // README 与 Motion Suite

交互式演示和 UI 文档采用统一视觉参考，包含三套配色：**Pond Noir**（默认深色画布）、**Golden Reed**（暖色高对比强调色）和 **Arctic Glacier**（冷色青蓝强调色）。应使用画布、表面、边框、文本、强调色和焦点等语义令牌，避免组件随意硬编码互相冲突的颜色。

动效遵循明确层级：有目的的进入和反馈使用克制的 spring 缓动，常规过渡使用平滑缓动；Zen / Hyper 强度预设仅在应用确实提供时启用。视差、漂浮图形和 ripple 波纹属于非必要装饰，不得承载关键信息或阻挡输入。 `reduced-motion` 优先于所有动效模式，并关闭装饰性运动。

**无障碍与响应式：**保持清晰的文本对比度、可见的键盘焦点、适合触控的控件尺寸、明确的 active/disabled 状态，并确保窄屏布局自然折叠。动效不得造成布局跳动或妨碍操作。

本节是 DUCK CORE 视觉参考，**不代表**每个应用都已实现所有主题、动画或控件。实际发布的实现和项目专属规范才是最终依据：[界面动效规范](docs/UI_MOTION.md)。


## Motion Constitution v2026

跨项目规范见 [Motion Constitution v2026](docs/MOTION_CONSTITUTION_V2026.md)。它统一弹簧/快速缓动、0.4×–2.2× 动效缩放范围、Reduce Motion 优先级、主题、2×2/焦点场景以及绑定真实数据的 SVG/Canvas 遥测。[原生界面动效规范](docs/UI_MOTION.md)记录已交付的 Tk 行为和无障碍偏好。OPlague 仍是只读工具：设备盘点、INF/ZIP 证据、哈希和候选兼容关系均来自真实数据；固件 OTA、驱动安装、USB 动画以及设备 DPI/轮询频率控制均不可用。
