# OPlague — рабочая станция для драйверов

<p align="center">
  <a href="https://github.com/Ivan-VHS/OPlague/actions/workflows/desktop-build.yml"><img alt="Сборка Windows" src="https://github.com/Ivan-VHS/OPlague/actions/workflows/desktop-build.yml/badge.svg"></a>
  <img alt="Python 3.10+" src="https://img.shields.io/badge/runtime-Python%203.10%2B-2563EB?style=flat-square">
  <img alt="Windows" src="https://img.shields.io/badge/desktop-Windows-DC2626?style=flat-square">
  <img alt="Apache 2.0" src="https://img.shields.io/badge/license-Apache--2.0-334155?style=flat-square">
</p>

**OPlague — ориентированная на Windows рабочая станция для чтения сведений об оборудовании и проверки пакетов драйверов.** Установка и изменение драйверов не выполняются.

[English](README.md) · [Українська](README.uk.md) · [Русский](README.ru.md) · [简体中文](README.zh-CN.md)

## Предпросмотр desktop-интерфейса

<p align="center"><img src="assets/oplague-workbench-preview.svg" alt="Иллюстративный предпросмотр интерфейса OPlague" width="100%"></p>
<sub>Схематическая реконструкция по Tkinter-разметке в репозитории, а не снимок работающего приложения Windows. Реальный скриншот пока не добавлен.</sub>

## Рабочие модули и инструменты

- **Инвентаризация устройств:** чтение Windows Plug and Play: имя, статус, производитель и hardware ID.
- **INF / ZIP-инспектор:** извлечение выбранных INF-метаданных, SHA-256, проверка путей архива и ограничений ресурсов, анализ точных hardware ID и целевой архитектуры. Содержимое пакета не извлекается и не запускается.
- **Пакетные отчёты:** упорядоченное объединение результатов проверки, агрегированные счётчики и детерминированный fingerprint набора.
- **UDRV-инспектор:** проверка версионированного манифеста, списка payload, размеров, хешей и ограничений путей/ресурсов. Он не устанавливает, не загружает и не запускает payload.
- **Dry-run совместимости:** связь устройств с INF Models только по точному нормализованному hardware ID. Кандидат не является рейтингом драйверов или вердиктом совместимости.
- **Metric Lab:** сравнение нормализованных профилей, взвешенные расстояния, cosine similarity, ортогональность и дисперсия повторных измерений.
- **Федерация устройств:** экспорт ограниченных JSON-снимков и офлайн-сравнение. Исходные PnP ID заменяются псевдонимными хешами; они остаются связываемыми и не являются анонимизацией.
- **Нативная сверка:** опциональная проверка метрик через Pytyliki C ABI v1 при явном указании пути к доверенной библиотеке.
- **QCS-валидатор:** одна грамматика и 66 именованных аппаратных доменных профилей; проверяет метаданные контуров и маркеры передачи. Это не компилятор и не проверка реального оборудования.
- **Системный каталог:** 66 языковых/toolchain-позиций; обнаружение ограничено поиском в `PATH`.

## Запуск desktop-приложения

Требуются Windows x64 и Python 3.10+.

```bash
git clone https://github.com/Ivan-VHS/OPlague.git
cd OPlague
python oplague_app.py
python -m unittest discover -s tests -v
```

Windows workflow собирает `OPlague.exe` и публикует артефакт `OPlague-windows-x64.zip`. Тег формата `v*` выпускает архив как GitHub Release.

## Полезные инструменты только для чтения

```bash
python tools/udrv_inspector.py path/to/package.udrv --json
python -m tools.federation snapshot --output device-snapshot.json
python -m tools/federation compare --reference baseline.json --candidate current.json
python -m tools.qcs dialects
python -m tools.qcs validate path/to/example.qcs
python tools/systems_languages.py --profile oplague
```

## Развитие и границы безопасности

OPlague начался 19 ноября 2026 года как Windows-инструмент для работы с драйверами. В main появились PnP-инвентаризация, ограниченная проверка INF/ZIP, анализ архитектур, dry-run по точным ID, проверка UDRV, пакетные отчёты, метрики, версионированные снимки устройств, мост Pytyliki и QCS-валидатор.

**Пока не реализовано:** установка/удаление драйверов, включение/отключение устройств, подпись, откат, изменение прошивки и live-анализ DPC/ISR. Целостность пакета не доказывает подлинность поставщика, безопасность или совместимость драйвера. Импортированные файлы считаются недоверенными. Тело QCS сохраняется как текст и не компилируется и не исполняется.

## Документация и загрузки

[Формат UDRV](docs/UDRV_FORMAT_V1.md) · [Граф совместимости](docs/DEVICE_COMPATIBILITY_GRAPH.md) · [Федерация](docs/FEDERATED_INTEGRATION.md) · [Синтаксис QCS](docs/QUANTUM_CONTOUR_SYNTAX.md) · [Единый инженерный стандарт](docs/UNIFIED_ENGINEERING_STANDARD.md)

[Релизы Windows](https://github.com/Ivan-VHS/OPlague/releases) · [Сборка desktop](https://github.com/Ivan-VHS/OPlague/actions/workflows/desktop-build.yml)

**Экосистема:** [Reaper](https://github.com/Ivan-VHS/Reaper) · [Pytyliki](https://github.com/Ivan-VHS/Pytyliki) · [матрица 3×3](https://github.com/Ivan-VHS/Reaper/blob/main/docs/PROJECT_FEDERATION_MATRIX.md).

## Лицензия

[Apache License 2.0](LICENSE)