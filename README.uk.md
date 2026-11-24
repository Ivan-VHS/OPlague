# OPlague

OPlague — локальна робоча станція для інвентаризації пристроїв Windows, read-only перевірки пакетів драйверів і аналізу доказів сумісності для інженерів підтримки та QA-команд.

[English](README.md) · [Українська](README.uk.md) · [Русский](README.ru.md) · [简体中文](README.zh-CN.md)

<picture><source media="(prefers-color-scheme: dark)" srcset="assets/readme/dashboard.svg"><img src="assets/readme/dashboard-light.svg" alt="Огляд OPlague: пристрої Windows, обмежена перевірка пакетів і звіти про кандидатну сумісність" width="100%"></picture>

[![Windows build](https://img.shields.io/github/actions/workflow/status/Ivan-VHS/OPlague/desktop-build.yml?branch=main&style=flat-square&label=Windows%20build)](https://github.com/Ivan-VHS/OPlague/actions/workflows/desktop-build.yml) [![Останній коміт](https://img.shields.io/github/last-commit/Ivan-VHS/OPlague?style=flat-square)](https://github.com/Ivan-VHS/OPlague/commits/main) [![Apache-2.0](https://img.shields.io/github/license/Ivan-VHS/OPlague?style=flat-square)](LICENSE)

[Швидкий старт](#швидкий-старт) · [Знімки екрана](#знімки-екрана) · [Архітектура](#архітектура) · [План розвитку](#план-розвитку) · [Документація](docs/README.md)

> **Статус:** активна розробка. Є desktop-застосунок Tkinter, локальні інспектори пакетів, CLI-утиліти, тести та workflow збирання Windows. Жива інвентаризація Plug and Play працює лише у Windows.
> **Вимоги:** Python 3.10+, Tkinter, Git; живий PnP-збір додатково потребує Windows і PowerShell/CIM.

## Інтеграція з Reaper

OPlague може використовувати версійований C17 ABI Reaper для обмежених цілочисельних виразів над уже перевіреними даними. Це не передає Reaper керування драйверами, встановленням пакетів або висновками щодо сумісності.

Докладніше: [інтеграція Reaper](docs/REAPER_RUNTIME_INTEGRATION.md).

## Швидкий старт

Запуск застосунку:

~~~sh
python oplague_app.py
~~~

Перевірки та тести:

~~~sh
python -m compileall -q oplague_app.py oplage_app.py tests
python tools/validate_visual_canon.py ui_theme.py
python -m unittest discover -s tests -v
~~~

Інспекція локальних файлів:

~~~sh
python tools/pe_inspector.py driver.sys --output driver-pe-report.json
python tools/sbom_inventory.py ./staging --output staging.spdx.json
python tools/udrv_inspector.py path/to/package.udrv --json
~~~

## Можливості та межі

| Компонент | Реалізовано | Межа |
|---|---|---|
| Windows PnP | Читання ідентичності, статусу та PNPDeviceID | Лише Windows, read-only |
| INF / ZIP | Метадані, hardware ID, розміри, шляхи, коефіцієнт стиснення та хеші | Без виконання директив і розпакування payload |
| PE/COFF | Заголовки, секції, entry point і certificate-table location | Не завантажує образ і не оцінює довіру до підпису |
| SPDX | SPDX 2.3 file/hash inventory | Не виводить залежності чи ліцензійні висновки |
| Compatibility graph | Кандидати за точними нормалізованими hardware ID | Потрібна ручна перевірка |
| Metric Lab | Порівняння переданих нормалізованих профілів | Рекомендаційний аналіз |
| UDRV v1 | Manifest, розміри та SHA-256 | Цілісність не дорівнює автентифікації |
| Gaming Lab | Відновлювані power-plan сесії Windows і frametime/CSV аналіз | Без модифікації драйверів |

OPlague **не встановлює, не завантажує, не розпаковує та не змінює драйвери**. Hardware ID і хеші є доказами для перевірки, але не сертифікують сумісність, безпеку чи походження.

## Скріншоти

<picture><source media="(prefers-color-scheme: dark)" srcset="assets/readme/workflow-dark.svg"><img src="assets/readme/workflow.svg" alt="Потік OPlague від Windows PnP і вибраних файлів до обмеженої інспекції та звіту" width="100%"></picture>

<p align="center"><a href="assets/screenshots/oplague-workbench.png"><img src="assets/screenshots/oplague-workbench.png" alt="Реальний знімок Windows-робочої станції OPlague" width="100%"></a></p>
<sub>Справжній знімок Windows 1920×1080 зі workflow пакування. SVG вище — схема, а не скриншот.</sub>

## Архітектура та вхідні обмеження

~~~mermaid
flowchart LR
 A[Windows PnP або файл] --> B[Обмежений парсер]
 B --> C[Нормалізовані ID та хеші]
 C --> D[Порівняння кандидатів]
 D --> E[Звіт доказів]
~~~

| Вхід | Ліміт |
|---|---:|
| INF / ZIP | 512 MiB |
| ZIP entries | 10 000 |
| Розпакований ZIP | 2 GiB |
| Окремий INF | 2 MiB |
| ZIP ratio | 200:1 |
| UDRV manifest / entries | 4 MiB / 10 000 |

## Сумісність

| Платформа | Підтримуваний сценарій |
|---|---|
| Windows | Desktop UI, живий PnP, інспекція пакетів, gaming sessions |
| Linux | Запуск із вихідного коду та аналіз збережених даних; без live Windows PnP |
| macOS | Аналіз збережених даних; системна інтеграція не заявлена |
| Python | 3.10+ |

## План розвитку

- [x] Read-only PnP та обмежена інспекція INF/ZIP.
- [x] PE/COFF headers, SPDX file inventory та UDRV v1.
- [x] Кандидатний граф сумісності з ручною перевіркою.
- [x] Відновлювані power sessions Windows.
- [ ] Розширювати перевірку довіри лише з незалежними доказами, тестами й явним рішенням оператора.

Дивіться [документацію](docs/README.md), [архітектуру](docs/ARCHITECTURE.md), [CONTRIBUTING](CONTRIBUTING.md) та [issues](https://github.com/Ivan-VHS/OPlague/issues). Ліцензія: Apache-2.0.
