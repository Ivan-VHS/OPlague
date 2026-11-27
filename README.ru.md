<p align="center"><picture><source media="(prefers-color-scheme: dark)" srcset="assets/readme/hero-banner-dark.svg"><source media="(prefers-color-scheme: light)" srcset="assets/readme/hero-banner-light.svg"><img src="assets/readme/hero-banner-light.svg" alt="Рабочая станция OPlague для устройств, драйверов и игр" width="880"></picture></p>

# OPlague — рабочая станция устройств, драйверов и игровой производительности

[English](README.md) · [Українська](README.uk.md) · [Русский](README.ru.md) · [简体中文](README.zh-CN.md)

[![Quality](https://img.shields.io/github/actions/workflow/status/Ivan-VHS/OPlague/completeness-check.yml?branch=main&style=flat-square&label=Quality)](https://github.com/Ivan-VHS/OPlague/actions/workflows/completeness-check.yml) [![Сборка Windows](https://img.shields.io/github/actions/workflow/status/Ivan-VHS/OPlague/desktop-build.yml?branch=main&style=flat-square&label=Windows%20build)](https://github.com/Ivan-VHS/OPlague/actions/workflows/desktop-build.yml) [![Apache-2.0](https://img.shields.io/github/license/Ivan-VHS/OPlague?style=flat-square)](LICENSE)

> Локальная Windows-first рабочая станция для ограниченной проверки устройств и драйверов, телеметрии с указанием источника и явного обратимого игрового power-plan workflow.

**Сведения о проекте:** разработка · единая версия продукта не объявлена · Python 3.10+ · JSON Schema · частичный Rust 2021 diagnostics consumer · Windows desktop и live-инвентаризация · Apache-2.0 · **Документация проверена:** 2026-11-27 UTC

## Назначение и область проекта

OPlague объединяет два намеренно разделённых сценария:

1. **Доказательства об устройствах и пакетах.** Read-only-инвентаризация Windows Plug-and-Play, ограниченная проверка метаданных INF/ZIP/UDRV, сопоставление нормализованных hardware ID, локальные отчёты и GPU-телеметрия с указанием источника.
2. **Игровой сеанс.** Явный workflow Windows, который сохраняет локальный снимок и может временно выбрать встроенный план электропитания Windows. Восстановление предыдущего плана выполняется только тогда, когда активным остаётся план, установленный самим OPlague.

Инспекция драйверов и пакетов не устанавливает, не удаляет, не включает, не выгружает, не извлекает и не выполняет драйверы или payload. Игровой workflow — отдельное изменение системы, требующее подтверждения пользователя: он не меняет драйверы, реестр, прошивку, частоты, напряжения, службы или сетевые настройки.

## Возможности

- **Live-инвентаризация устройств:** текущие записи Windows Plug-and-Play через фиксированный read-only-запрос. Live-инвентаризация доступна только в Windows.
- **Ограниченная проверка пакетов:** метаданные INF и структура ZIP с лимитами путей, количества записей, размера и сжатия.
- **UDRV v1:** проверка manifest, объявленного состава payload, размеров файлов, SHA-256 и ограничений ресурсов/путей без извлечения и выполнения payload.
- **Отчёты доказательств:** детерминированные batch-сводки, digest содержимого и версионированные JSON-снимки с псевдонимным отпечатком устройства.
- **Граф кандидатов совместимости:** точное совпадение нормализованных hardware ID создаёт только ребро-кандидат. Оно не ранжирует, не сертифицирует и не доказывает безопасность или совместимость драйвера.
- **Метрики и телеметрия:** сравнение нормализованных профилей и необязательные показания NVIDIA через `nvidia-smi`. Отсутствующие значения датчиков остаются unknown; телеметрия доступна только для чтения.
- **Игровой сеанс:** после явного подтверждения сохраняется снимок устройств, драйверов и плана питания, затем может временно включаться штатный план High Performance. Восстановление защищено: если активный план был изменён вне сеанса, OPlague не перезаписывает новый выбор.
- **Интеграция:** версионированные снимки устройств и отчёты Reaper; необязательные вызовы C ABI Pytyliki через доверенную библиотеку, выбранную вызывающей стороной.
- **Мост Rust diagnostics:** ограниченный потребитель Pytyliki diagnostics ABI на Rust 2021 реализован частично; это не полная миграция на Rust/Slint.

Offline-анализ пакетов и отчётов доступен в поддерживаемых Python-окружениях вне Windows, если конкретный сценарий не требует live Plug-and-Play.

## Быстрый запуск

Требуется Python 3.10+; Windows нужен для desktop-приложения, live-инвентаризации Plug-and-Play и управления планом питания. Для NVIDIA-телеметрии дополнительно нужен поддерживаемый локальный провайдер `nvidia-smi`.

Запуск Windows workstation:

~~~sh
python oplague_app.py
~~~

Запуск тестов и проверка выбранного UDRV-пакета:

~~~sh
python -m unittest discover -s tests -v
python tools/udrv_inspector.py path/to/package.udrv --json
~~~

Инспектор UDRV проверяет метаданные и digest файлов в заданных пределах. Он никогда не извлекает, не устанавливает, не загружает и не выполняет содержимое пакета.

## Контракты данных

| Интерфейс | Контракт | Граница |
|---|---|---|
| Device snapshot | `oplage.device-snapshot.v1` | Версионируемый JSON; псевдонимный fingerprint |
| GPU telemetry | `oplage.gpu-telemetry.v1` | Read-only-метаданные источника; неизвестные значения остаются unknown |
| Batch evidence | `oplage.inspection-bundle.v1` | Упорядоченный отчёт и детерминированный digest |
| Пакет драйвера | UDRV v1 | Только ограниченная проверка manifest и целостности |
| Reaper comparison | `reaper.oplage-comparison.v1` | Offline-валидация отчёта без изменения устройства |
| Метрики Pytyliki | `pytyliki.c-abi.v1` | Необязательный native-вызов через явно доверенную библиотеку |
| Игровой сеанс | `oplague.gaming.v1` | Локальный снимок и защищённое изменение Windows power plan |

SHA-256 обнаруживает изменение байтов относительно сохранённого digest; это не цифровая подпись, не аутентификация издателя и не доказательство безопасности. Метаданные Authenticode — свидетельство о поддерживаемом файле, но не сертификация совместимости устройства.

## Безопасность и ограничения

Считайте INF, ZIP, UDRV, экспорт телеметрии и импортируемые отчёты недоверенными данными. Парсеры соблюдают ресурсные лимиты; payload пакетов не извлекается и не выполняется. Совпадение hardware ID формирует отношения кандидатов, а не вердикт о безопасности.

Переключение power plan — явная отдельная операция, не часть инспекции. Сейчас она поддерживается только в Windows, сохраняет исходный снимок и не перезаписывает более поздний внешний выбор плана. Выбор плана питания и сравнение frametime не гарантируют повышения производительности.

Сканер репозитория Beelzebul — локальный/static-инструмент проверки исходников. Это не endpoint-антивирус, не сканирование памяти процессов и не карантин.

## Документация

- [Индекс документации](docs/README.md) · [Информационная архитектура](docs/INFORMATION_ARCHITECTURE.md)
- [Матрица функций](docs/FEATURES.md) · [Архитектура](docs/ARCHITECTURE.md)
- [Формат UDRV v1](docs/UDRV_FORMAT_V1.md) · [Граф совместимости устройств](docs/DEVICE_COMPATIBILITY_GRAPH.md)
- [Мост GPU telemetry v1](docs/FEATURES.md) · [Инспекция устройств и драйверов](docs/clusters/device-driver-inspection.md)
- [Федеративная интеграция](docs/FEDERATED_INTEGRATION.md) · [Релиз Windows](.github/workflows/desktop-build.yml)
- [Reaper runtime integration](docs/REAPER_RUNTIME_INTEGRATION.md) · [Политика безопасности](SECURITY.md)
- [Стандарт визуальной публикации](docs/README_VISUAL_STANDARD.md)

Workflow релиза Windows создаёт черновик GitHub Release для проверки сопровождающим. Публикация выполняется отдельно; SHA-256 sidecar не является цифровой подписью.

## Участие и лицензия

Перед изменением парсеров, схем, телеметрии или системных интеграций прочитайте [CONTRIBUTING.md](CONTRIBUTING.md). Сохраняйте ограниченность входных данных, явность разрешений и происхождение доказательств. Не добавляйте частные payload драйверов или персонализированные hardware exports.

Лицензия — [Apache-2.0](LICENSE). Сохраняйте уведомления и атрибуцию сторонних компонентов.
