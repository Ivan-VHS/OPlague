# OPlague — рабочая станция устройств, драйверов и игровой производительности

[English](README.md) · [Українська](README.uk.md) · [Русский](README.ru.md) · [简体中文](README.zh-CN.md)

[![Сборка Windows](https://img.shields.io/github/actions/workflow/status/Ivan-VHS/OPlague/desktop-build.yml?branch=main&label=Windows%20build)](https://github.com/Ivan-VHS/OPlague/actions/workflows/desktop-build.yml) [![Проверка документации](https://img.shields.io/github/actions/workflow/status/Ivan-VHS/OPlague/docs.yml?branch=main&label=Docs%20checks)](https://github.com/Ivan-VHS/OPlague/actions/workflows/docs.yml) [![Apache-2.0](https://img.shields.io/github/license/Ivan-VHS/OPlague)](LICENSE)

<p align="center"><img src="assets/readme/dashboard.svg" alt="Обзор OPlague" width="100%"></p>
<p align="center"><a href="assets/screenshots/oplague-workbench.png"><img src="assets/screenshots/oplague-workbench.png" alt="Рабочая станция OPlague в Windows" width="100%"></a></p>

OPlague — локальная desktop-станция для проверки устройств и драйверов, анализа пакетов, доказательств совместимости и игровой производительности.

**Базовая граница:** проверка работает на чтение. Обнаружение устройств и анализ выбранных файлов не устанавливают, не включают, не отключают и не изменяют драйверы. Кандидаты совместимости и телеметрия — данные для проверки, а не сертификация.

## Возможности

- Инвентаризация Windows Plug-and-Play и ограниченный анализ INF/ZIP-пакетов.
- Проверка PE и Authenticode, нормализованные hardware ID, хэши и SPDX-инвентаризация.
- Доказательства совместимости устройств, проверка пакетов UDRV и структурированные отчёты.
- Локальная игровая телеметрия, анализ frametime и обратимые пользовательские профили производительности.

Подробнее: [Возможности](docs/FEATURES.md) · [Архитектура](docs/ARCHITECTURE.md) · [Authenticode](docs/AUTHENTICODE.md) · [Архитектура драйверов](docs/DRIVER_TARGET_ARCHITECTURE.md) · [UDRV](docs/UDRV_FORMAT_V1.md) · [Игровая станция](docs/GAMING_PERFORMANCE_WORKBENCH.md) · [GPU telemetry bridge v1](docs/GPU_TELEMETRY_BRIDGE_V1.md).

## Запуск и тесты

Для текущих desktop-инструментов и проверок требуется Python 3.10–3.12.

```sh
python oplague_app.py
python -m unittest discover -s tests -v
python -m oplague --verify
python -m oplague --catalog
```

Проверка пакета:

```sh
python tools/udrv_inspector.py path/to/package.udrv --json
```

Сборка отдельного Windows executable через PyInstaller:

```sh
python -m pip install --upgrade pyinstaller
python -m PyInstaller --noconfirm --clean --onefile --windowed --name OPlague oplague_app.py
```

## Интеграция и доказательства

- [Индекс документации](docs/README.md) · [Интеграция runtime Reaper](docs/REAPER_RUNTIME_INTEGRATION.md)
- [Интеграция DuckOS и Mora](https://github.com/Ivan-VHS/DuckOS/blob/main/docs/GAMING_PERFORMANCE_INTEGRATION.md)
- [Общие стандарты экосистемы](https://github.com/Ivan-VHS/DuckOS/blob/main/docs/SHARED_STANDARDS.md)

Текущее поведение определяют исходники, схемы и тесты. Станция не прошивает устройства, не устанавливает драйверы и не выдаёт автоматическую сертификацию совместимости.

[Вклад в проект](CONTRIBUTING.md) · [Безопасность](SECURITY.md) · [Apache-2.0](LICENSE)
