# OPlague — рабочая станция драйверов

Python 3.10+ · Windows · Apache-2.0 · [Desktop CI](https://github.com/Ivan-VHS/OPlague/actions/workflows/desktop-build.yml)
**Разработчик:** [Ivan-VHS](https://github.com/Ivan-VHS)

**Инструмент только для чтения:** инвентаризация Windows, анализ пакетов драйверов и сопоставление доказательств. Не устанавливает, не загружает и не изменяет драйверы.

[English](README.md) · [Русский](README.ru.md) · [Українська](README.uk.md) · [简体中文](README.zh-CN.md)

| Модуль | Результат | Граница |
|---|---|---|
| Устройства | Plug and Play, статус, hardware ID | read-only |
| INF/ZIP | метаданные, хеши, пути, лимиты | без распаковки/запуска |
| Архитектура | INF target vs host | признак, не вердикт |
| Граф | точный hardware ID | кандидат |
| UDRV v1 | manifest, размер, SHA-256 | только проверка |
| DRIVE-LENS | происхождение, HMAC-псевдонимы | без автоматического вердикта |
| Отчёты | порядок, итоги, fingerprint | без изменений системы |
| Clinical Systems | 120 принципов, 36 проверок метрик | только рекомендации |

Запуск: `python oplague_app.py` · Тесты: `python -m unittest discover -s tests -v`.

| INF target | PE machine |
|---|---:|
| NTx86 | 0x014C |
| NTamd64 | 0x8664 |
| NTarm | 0x01C4 |
| NTarm64 | 0xAA64 |
| NTia64 (legacy) | 0x0200 |

UDRV v1: manifest ≤4 МиБ · ≤10 000 записей · файл ≤512 МиБ · сумма ≤2 ГиБ · SHA-256 buffer 1 МиБ.

ID/hash не подтверждают подпись издателя, совместимость с ОС или безопасность установки. См. [функции](docs/FEATURES.md), [архитектуру](docs/ARCHITECTURE.md), [UDRV](docs/UDRV_FORMAT_V1.md), [регламент](docs/PROJECT_STEWARDSHIP_STANDARD.md), [дизайн](docs/DUCK_SOVEREIGN_CANON.md), [индекс](docs/README.md).

[Apache-2.0](LICENSE)
