# OPlague

OPlague — локальная рабочая станция для инвентаризации устройств Windows, read-only проверки пакетов драйверов и анализа доказательств совместимости для инженеров поддержки и QA-команд.

[English](README.md) · [Українська](README.uk.md) · [Русский](README.ru.md) · [简体中文](README.zh-CN.md)

<picture><source media="(prefers-color-scheme: dark)" srcset="assets/readme/dashboard.svg"><img src="assets/readme/dashboard-light.svg" alt="Обзор OPlague: устройства Windows, ограниченная проверка пакетов и отчёты о кандидатной совместимости" width="100%"></picture>

[![Windows build](https://img.shields.io/github/actions/workflow/status/Ivan-VHS/OPlague/desktop-build.yml?branch=main&style=flat-square&label=Windows%20build)](https://github.com/Ivan-VHS/OPlague/actions/workflows/desktop-build.yml) [![Последний коммит](https://img.shields.io/github/last-commit/Ivan-VHS/OPlague?style=flat-square)](https://github.com/Ivan-VHS/OPlague/commits/main) [![Apache-2.0](https://img.shields.io/github/license/Ivan-VHS/OPlague?style=flat-square)](LICENSE)

[Быстрый старт](#быстрый-старт) · [Скриншоты](#скриншоты) · [Архитектура](#архитектура) · [План развития](#план-развития) · [Документация](docs/README.md)

> **Статус:** активная разработка. Есть Tkinter desktop, инспекторы пакетов, CLI-инструменты, тесты и Windows packaging workflow. Живой Plug and Play доступен только в Windows.
> **Требования:** Python 3.10+, Tkinter, Git; live PnP требует Windows и PowerShell/CIM.

## Быстрый старт

Запуск:

~~~sh
python oplague_app.py
~~~

Проверки и тесты:

~~~sh
python -m compileall -q oplague_app.py oplage_app.py tests
python tools/validate_visual_canon.py ui_theme.py
python -m unittest discover -s tests -v
~~~

Проверка файлов:

~~~sh
python tools/pe_inspector.py driver.sys --output driver-pe-report.json
python tools/sbom_inventory.py ./staging --output staging.spdx.json
python tools/udrv_inspector.py path/to/package.udrv --json
~~~

## Возможности и границы

| Компонент | Реализовано | Граница |
|---|---|---|
| Windows PnP | Чтение identity, статуса и PNPDeviceID | Только Windows, read-only |
| INF / ZIP | Метаданные, hardware ID, размеры, пути, compression ratio и хеши | Без запуска директив и распаковки payload |
| PE/COFF | Заголовки, секции, entry point и certificate-table location | Без загрузки образа и verdict подписи |
| SPDX | SPDX 2.3 file/hash inventory | Без выводов о зависимостях или лицензиях |
| Compatibility graph | Кандидаты по точным normalized hardware ID | Нужна ручная проверка |
| Metric Lab | Сравнение переданных normalized profiles | Рекомендательная аналитика |
| UDRV v1 | Manifest, размеры и SHA-256 | Целостность не равна аутентификации |
| Gaming Lab | Восстанавливаемые power-plan сессии Windows и frametime/CSV | Без модификации драйверов |

OPlague **не устанавливает, не загружает, не распаковывает и не меняет драйверы**. Hardware ID и хеши — доказательства для проверки, но не подтверждение совместимости, безопасности или происхождения.

## Скриншоты

<picture><source media="(prefers-color-scheme: dark)" srcset="assets/readme/workflow-dark.svg"><img src="assets/readme/workflow.svg" alt="Поток OPlague от Windows PnP и выбранных файлов к ограниченной проверке и отчёту" width="100%"></picture>

<p align="center"><a href="assets/screenshots/oplague-workbench.png"><img src="assets/screenshots/oplague-workbench.png" alt="Реальный снимок Windows-рабочей станции OPlague" width="100%"></a></p>
<sub>Настоящий снимок Windows 1920×1080 из workflow упаковки. SVG выше — схема, не скриншот.</sub>

## Архитектура и лимиты

~~~mermaid
flowchart LR
 A[Windows PnP или файл] --> B[Ограниченный парсер]
 B --> C[Нормализованные ID и хеши]
 C --> D[Сравнение кандидатов]
 D --> E[Отчёт доказательств]
~~~

| Вход | Лимит |
|---|---:|
| INF / ZIP | 512 MiB |
| ZIP entries | 10 000 |
| Распакованный ZIP | 2 GiB |
| Отдельный INF | 2 MiB |
| ZIP ratio | 200:1 |
| UDRV manifest / entries | 4 MiB / 10 000 |

## Совместимость

| Платформа | Поддерживаемый сценарий |
|---|---|
| Windows | Desktop UI, PnP, инспекция пакетов, gaming sessions |
| Linux | Исходники и сохранённые данные; без live Windows PnP |
| macOS | Анализ сохранённых данных; системная интеграция не заявлена |
| Python | 3.10+ |

## План развития

- [x] Read-only PnP и ограниченная INF/ZIP инспекция.
- [x] PE/COFF headers, SPDX file inventory и UDRV v1.
- [x] Кандидатный compatibility graph с ручной проверкой.
- [x] Восстанавливаемые Windows power sessions.
- [ ] Расширять trust verification только с независимыми доказательствами и тестами.

См. [документацию](docs/README.md), [архитектуру](docs/ARCHITECTURE.md), [CONTRIBUTING](CONTRIBUTING.md), [issues](https://github.com/Ivan-VHS/OPlague/issues). Лицензия: Apache-2.0.
