# OPlague — рабочая станция устройств, драйверов и игр

<p align="center">[English](README.md) · [Українська](README.uk.md) · [Русский](README.ru.md) · [简体中文](README.zh-CN.md)</p>

[![Windows build](https://img.shields.io/github/actions/workflow/status/Ivan-VHS/OPlague/desktop-build.yml?branch=main&label=Windows%20build)](https://github.com/Ivan-VHS/OPlague/actions/workflows/desktop-build.yml) [![Docs checks](https://img.shields.io/github/actions/workflow/status/Ivan-VHS/OPlague/docs.yml?branch=main&label=Docs%20checks)](https://github.com/Ivan-VHS/OPlague/actions/workflows/docs.yml) [![Apache-2.0](https://img.shields.io/github/license/Ivan-VHS/OPlague)](LICENSE)

> **Проверяй устройства и пакеты. Не меняй систему. Публикуй доказательства, а не действия с драйверами.**

**Состояние:** Разработка · инструменты проверки с приоритетом Windows · **Версия:** версия не объявлена в контракте проекта · **License:** [Apache-2.0](LICENSE) · **Стандарт README:** Psychoporter 666 v1.0 · **Дата проверки:** 2026-11-25 · UTC · **Source:** [Ivan-VHS/OPlague](https://github.com/Ivan-VHS/OPlague)

<p align="center"><img src="assets/oplague-workbench-preview.svg" alt="OPlague — рабочая станция устройств, драйверов и игр — project overview" width="100%"></p>
<p align="center"><a href="assets/screenshots/oplague-workbench.png"><img src="assets/screenshots/oplague-workbench.png" alt="OPlague — рабочая станция устройств, драйверов и игр — application screenshot" width="100%"></a></p>

## Быстрая навигация

[🚀 Demo: workbench screenshot](assets/screenshots/oplague-workbench.png) · [Documentation](docs/README.md) · [Source repository](https://github.com/Ivan-VHS/OPlague) · [Issues](https://github.com/Ivan-VHS/OPlague/issues)

## Назначение и границы

Локальная рабочая станция для обнаружения устройств только на чтение, ограниченной проверки пакетов INF/ZIP/UDRV, анализа совместимости и игровой телеметрии. Живое обнаружение Windows Plug-and-Play доступно только в Windows; анализ сохранённых файлов и отчётов переносим. Приложение не устанавливает, не включает, не выгружает и не изменяет драйверы.

## Возможности

- Инвентаризация Windows Plug-and-Play через запросы только на чтение.
- Ограниченный анализ INF/ZIP, метаданные PE и Authenticode, SHA-256 и SPDX-инвентаризация.
- Проверка манифеста UDRV v1, размеров файлов, хэшей и путей; payload не устанавливается и не запускается.
- Кандидаты связей по точному нормализованному hardware ID; это не сертификация совместимости.
- Локальный анализ игровой производительности/frametime и read-only телеметрия NVIDIA через nvidia-smi, если доступна.
- Версионированные JSON-снимки устройств и необязательная проверка через доверенный C ABI Pytyliki.

## Архитектура и поток данных

~~~mermaid
flowchart TB
  U["User-selected device or file"] --> I["Bounded inspector"]
  I --> N["Normalize IDs / metadata / hashes"]
  N --> E["Evidence and candidate graph"]
  E --> R["Local report / JSON snapshot"]
  G["nvidia-smi — read only"] --> T["GPU telemetry snapshot"]
  T --> R
  R -.-> X["No driver install, load or certification"]
~~~

Исходный код, схемы, конфигурация сборки, тесты и CI подтверждают реализованное поведение. Дорожная карта и каталоги описывают планы и перечни, а не поставляемые функции.

## Требования

Python 3.10–3.12 для текущих desktop-инструментов и проверок. Для живой инвентаризации Plug-and-Play требуется Windows; offline-анализ файлов и отчётов не требует доступа к устройствам. Доступность Tk-интерфейса зависит от локальной установки Python.

## Сборка

~~~sh
python -m venv .venv
. .venv/bin/activate
python -m pip install --upgrade pip
python oplague_app.py
~~~


## Первые проверки

~~~sh
python -m unittest discover -s tests -v
python tools/udrv_inspector.py path/to/package.udrv --json
~~~

Запускайте desktop-точку входа после проверки тестов и вывода инспектора. Инспектор не распаковывает и не запускает содержимое пакета.

## Запуск

Текущая точка входа графического приложения — `oplague_app.py`. Инспектор принимает выбранный пользователем локальный файл и не выполняет содержимое пакета.

## Интерфейсы

| Surface | Contract / entry point | Boundary |
|---|---|---|
| Device snapshot | `oplage.device-snapshot.v1` | Versioned JSON; pseudonymous device fingerprint. |
| GPU telemetry | `oplage.gpu-telemetry.v1` | Read-only NVIDIA sensor export; unavailable values remain unknown. |
| UDRV inspector | `tools/udrv_inspector.py` | Manifest, size, hash and path checks; no install/load. |
| Native metrics | `Optional pytyliki.c-abi.v1` | Only through an explicitly selected trusted library. |

REST/GraphQL, WebSocket, OAuth, облачный deployment и cookie-механизмы не описываются как возможности, если в репозитории нет версионированной реализации и тестов.

## Безопасность и границы доверия

Импортируемые файлы и пакеты считаются недоверенными. Число записей архивов, пути, размеры и степень сжатия ограничены; payload не распаковывается и не исполняется. Совпадения hardware ID — лишь кандидаты, а не выводы о подписи, безопасности или поддержке ОС. Обнаружение устройств работает на чтение; драйверы, прошивки и состояние устройств не меняются.

Политика безопасности: [SECURITY.md](SECURITY.md). Не публикуйте секреты, идентификаторы устройств и приватные журналы в открытых задачах.

## Проверка качества

~~~sh
python -m unittest discover -s tests -v
~~~

Состав тестов определяется зарегистрированными CTest/unittest целями и workflow. Процент покрытия, fuzz-результат и нагрузочный отчёт не заявляются без опубликованного артефакта.

## Доказательства производительности

Игровые и GPU-метрики — локальные наблюдения, а не универсальные бенчмарки. Телеметрия NVIDIA работает только на чтение и содержит источник данных; отсутствующие измерения остаются unknown. Фиксированные значения задержки и потребления памяти не заявляются.

## Совместимость

Живая инвентаризация Windows Plug-and-Play доступна только в Windows. Offline-проверка пакетов, хэшей, схем и отчётов переносима с учётом локальной среды Python и необязательных платформенных источников данных.

## Документация и экосистема

- [Возможности и ограничения](docs/FEATURES.md)
- [Архитектура](docs/ARCHITECTURE.md)
- [Проверка Authenticode](docs/AUTHENTICODE.md)
- [Формат UDRV v1](docs/UDRV_FORMAT_V1.md)
- [Мост телеметрии GPU](docs/GPU_TELEMETRY_BRIDGE_V1.md)
- [Игровая рабочая станция](docs/GAMING_PERFORMANCE_WORKBENCH.md)
- [Индекс документации](docs/README.md)

Основные технические источники — границы возможностей, формат UDRV, проверка Authenticode и мост телеметрии GPU в режиме чтения.

Интеграции между проектами используют документированные версионированные интерфейсы и явные адаптеры. Необязательный адаптер не предоставляет другому проекту привилегий среды выполнения или доступа к оборудованию.

## Участие в разработке

Изучите [CONTRIBUTING.md](CONTRIBUTING.md) перед изменением кода или контрактов. Сохраняйте изменения небольшими и проверяемыми, добавляйте детерминированные тесты, используйте Conventional Commits, если это требуется руководством.

## Лицензия и правовые условия

Распространяется по лицензии [Apache-2.0](LICENSE). Программное обеспечение предоставляется «КАК ЕСТЬ» в пределах условий лицензии. Названия сторонних проектов и товарные знаки принадлежат их правообладателям.

Репозиторий описывает локальные программные интерфейсы. Условия облачного сервиса, согласие на cookies, OAuth и CORS не относятся к указанным компонентам, пока отдельно не будет внедрён и документирован сетевой сервис.

---

<p align="center"><sub>Psychoporter 666 README Standard v1.0 · Ivan-VHS · 2026-11-25 · UTC</sub></p>
