# OPlague — робоча станція драйверів

Python 3.10+ · Windows · Apache-2.0 · [Desktop CI](https://github.com/Ivan-VHS/OPlague/actions/workflows/desktop-build.yml)

**Інструмент лише для читання:** інвентаризація Windows, аналіз пакетів драйверів і зіставлення доказів. Не встановлює, не завантажує та не змінює драйвери.

[English](README.md) · [Русский](README.ru.md) · [Українська](README.uk.md) · [简体中文](README.zh-CN.md)

| Модуль | Результат | Межа |
|---|---|---|
| Пристрої | Plug and Play, стан, hardware ID | read-only |
| INF/ZIP | метадані, хеші, шляхи, ліміти | без розпакування/запуску |
| Архітектура | INF target vs host | ознака, не висновок |
| Граф | точний hardware ID | кандидат |
| UDRV v1 | manifest, розмір, SHA-256 | лише перевірка |
| DRIVE-LENS | походження, HMAC-псевдоніми | без автоматичного вердикту |
| Звіти | порядок, підсумки, fingerprint | без змін системи |
| Clinical Systems | 120 принципів, 36 перевірок метрик | лише поради |

Запуск: `python oplague_app.py` · Тести: `python -m unittest discover -s tests -v`.

| INF target | PE machine |
|---|---:|
| NTx86 | 0x014C |
| NTamd64 | 0x8664 |
| NTarm | 0x01C4 |
| NTarm64 | 0xAA64 |
| NTia64 (legacy) | 0x0200 |

UDRV v1: manifest ≤4 МіБ · ≤10 000 записів · файл ≤512 МіБ · загалом ≤2 ГіБ · SHA-256 buffer 1 МіБ.

Збіг ID/hash не підтверджує підпис, сумісність з ОС або безпечність інсталяції. [Функції](docs/FEATURES.md) · [Архітектура](docs/ARCHITECTURE.md) · [UDRV](docs/UDRV_FORMAT_V1.md) · [Регламент](docs/PROJECT_STEWARDSHIP_STANDARD.md) · [Дизайн](docs/DUCK_SOVEREIGN_CANON.md) · [Індекс](docs/README.md)

[Apache-2.0](LICENSE)
