# OPlague — read-only рабочая станция устройств и драйверов

[English](README.md) · [Українська](README.uk.md) · [Русский](README.ru.md) · [简体中文](README.zh-CN.md)

<p align="center"><img src="assets/readme/dashboard.svg" alt="Обзор проекта OPlague" width="100%"></p>

[Исходный код](https://github.com/Ivan-VHS/OPlague) · [Windows desktop workflow](.github/workflows/desktop-build.yml) · [Индекс документации](docs/README.md) · [Apache-2.0](LICENSE)

## Реальный снимок Windows-рабочей станции

<p align="center"><a href="assets/screenshots/oplague-workbench.png"><img src="assets/screenshots/oplague-workbench.png" alt="Реальный снимок OPlague в Windows" width="100%"></a></p>
<p align="center"><sub>1920×1080 · Нажмите на изображение, чтобы открыть исходный PNG.</sub></p>

Настоящий скриншот запущенного desktop-приложения OPlague, созданный Windows packaging workflow. Баннер и схема процесса — авторские SVG-иллюстрации; изображение интерфейса не генерировалось и не компоновалось.

### Архитектура с первого взгляда

<p align="center"><img src="assets/readme/workflow.svg" alt="OPlague implemented data flow" width="100%"></p>

Реальный путь: Windows PnP и выбранные пользователем файлы → ограниченная проверка INF/ZIP → нормализованные ID и хеши → отчёт с кандидатными доказательствами.


[![Windows build](https://img.shields.io/github/actions/workflow/status/Ivan-VHS/OPlague/desktop-build.yml?branch=main&label=Windows%20build)](https://github.com/Ivan-VHS/OPlague/actions/workflows/desktop-build.yml)  [![Docs checks](https://img.shields.io/github/actions/workflow/status/Ivan-VHS/OPlague/docs.yml?branch=main&label=Docs%20checks)](https://github.com/Ivan-VHS/OPlague/actions/workflows/docs.yml)  [![License](https://img.shields.io/github/license/Ivan-VHS/OPlague)](LICENSE)


> **Назначение:** OPlague — локальная read-only рабочая станция для инвентаризации Windows Plug and Play, просмотра метаданных INF/ZIP-пакетов драйверов и сравнения доказательств совместимости. Она **не устанавливает, не загружает, не распаковывает и не изменяет** содержимое драйверов. Репозиторий не публикует hosted web demo, удалённый API или production-сервис управления устройствами. Документация сверена с `main` **22.11.2026**.

## Назначение и границы

OPlague помогает оператору просматривать записи устройств текущей машины, читать метаданные пакетов драйверов и сравнивать нормализованные аппаратные идентификаторы. Целевая аудитория — инженеры поддержки Windows, ревьюеры оборудования, QA и разработчики, исследующие содержимое пакетов или доказательства совместимости.

Результат — запись доказательств и список кандидатов, а не окончательный вывод о безопасности или совместимости. Точное совпадение hardware ID не доказывает доверие к издателю, совместимость с ОС, пригодность устройства или безопасность установки. Развёртывание драйверов не входит в продукт.

### Реальные возможности рабочей станции

| Область | Реализованное поведение | Граница |
|---|---|---|
| Инвентаризация устройств | читает идентичность Windows Plug and Play, статус, производителя и PNPDeviceID | live-сбор доступен только в Windows и только для чтения |
| Проверка INF | читает выбранные метаданные, объявления hardware ID и целевую архитектуру | не выполняет директивы INF |
| Проверка ZIP | проверяет пути, размеры, compression ratio, хеши и метаданные INF | не распаковывает и не выполняет payload |
| Проверка PE/COFF | читает тип машины, optional header, секции, entry point и расположение certificate table | только чтение заголовков; без загрузки образа и вывода о подписи |
| SPDX file inventory | создаёт детерминированный SPDX 2.3-отчёт файлов и хешей | без графа зависимостей и выводов о лицензии |
| Граф совместимости | формирует кандидатные связи по точным нормализованным hardware ID | только кандидаты; требуется ручная проверка |
| Metric Lab | сравнивает введённые пользователем нормализованные профили через weighted distance/variance | рекомендательный анализ, не вердикт по устройству |
| UDRV v1 | проверяет manifest, размеры и SHA-256 | проверка целостности, не аутентификация издателя |
| Отчёты | формирует структурированные доказательства, итоги и fingerprints | без записи в систему и установки драйверов |

В приложении четыре основные вкладки: **Devices**, **Package Inspection**, **Metric Lab** и **Compatibility Review**. Используется единая чёрно-бело-жёлтая палитра DuckOS; настройки движения включают Reduce Motion и Eco Visuals.

Скриншот ниже — снимок desktop-приложения, а не браузерное превью.

Локальный анализ бинарных файлов и экспорт инвентаря:

```sh
python tools/pe_inspector.py driver.sys --output driver-pe-report.json
python tools/sbom_inventory.py ./staging --output staging.spdx.json
```

PE-проверка читает только заголовки. SPDX-отчёт сохраняет хеши, а непроверенные сведения о лицензии помечает `NOASSERTION`.


## Связанный продукт ОС: DuckOS

Семиприложенческий набор Mora (Cockos, Kavun, Ka-bon, Gloverty, Po, Illidia и Unify) описан в отдельном проекте [DuckOS](https://github.com/Ivan-VHS/DuckOS/blob/main/docs/PREINSTALLED_APPLICATIONS.md). Это уровень приложений операционной системы, а не компонент OPlague. Этот репозиторий не заявляет о поставке этих приложений или предоставлении их системных служб. Собственные возможности и интерфейсы OPlague определяются исходным кодом, тестами и версионируемыми контрактами.

## Интеграция с Reaper

## Политика выполнения плагинов

Локальный plugin host теперь ограничивает размер входных и выходных данных, конкурентный запуск и фиксирует время выполнения и состояние обработчиков. См. [политику выполнения плагинов](docs/PLUGIN_EXECUTION_POLICY.md). Deadline для синхронных Python-обработчиков проверяется после возврата и не является принудительной отменой.

OPlague может использовать версионированный C17 ABI Reaper для ограниченных целочисленных выражений над уже проверенными данными. Это не передаёт Reaper управление драйверами, установкой пакетов или выводами о совместимости.

Подробности: [интеграция Reaper](docs/REAPER_RUNTIME_INTEGRATION.md).

## Быстрый старт

### Требования

- Python **3.10 или новее**.
- Tkinter для desktop UI.
- Windows и `powershell.exe` для live-инвентаризации Plug and Play. Инвентаризация использует фиксированный локальный PowerShell/CIM-запрос.
- Git.

Приложение импортирует собственные модули репозитория и средства стандартной библиотеки Python; сторонние runtime-пакеты для запуска исходников не требуются. PyInstaller нужен только для упаковки автономного executable.

В Linux и macOS можно проверять сохранённые данные, но live-инвентаризация Windows PnP недоступна.

### Запуск desktop-приложения

Из корня репозитория:

```sh
python oplague_app.py
```

`oplague_app.py` — entry point с правильным написанием; он передаёт управление существующему модулю реализации `oplage_app.py`.

### Тесты и CLI-проверки

```sh
python -m compileall -q oplague_app.py oplage_app.py tests
python tools/validate_visual_canon.py ui_theme.py
python -m unittest discover -s tests -v
```

Примеры CLI:

```sh
python -m oplague --verify
python -m oplague --catalog
python -m oplague --search "ballistic"
python -m oplague --profile 5
python -m oplague --rank reach
python tools/udrv_inspector.py path/to/package.udrv --json
python tools/clinical_systems.py --catalog --pretty
```

Необязательный расчёт через Reaper C17 требует явного пути к доверенной библиотеке:

```sh
python -m oplague --rank-total-native --reaper-library /absolute/path/to/libreaper_ffi.so
```

Это локальное выполнение. OPlague не запускает HTTP listener, web UI, API endpoint или localhost preview.

### Сборка Windows executable

Desktop workflow использует Python 3.12 и PyInstaller. Для локальной упаковки:

```sh
python -m pip install --upgrade pyinstaller
python -m PyInstaller --noconfirm --clean --onefile --windowed --name OPlague oplague_app.py
```

Автономный executable создаётся в `dist/OPlague.exe`. Первая упаковка может занять больше времени, пока PyInstaller собирает приложение; фиксированное время сборки не обещается.

## Данные, ограничения и сценарии проверки

У OPlague нет общей базы данных, входа, демо-аккаунта, удалённого mock API или hosted fixture service. Источники данных разделены:

- **Инвентаризация устройств:** реальные локальные записи Windows Plug and Play через `Get-CimInstance`.
- **Проверка пакетов:** файл, явно выбранный оператором.
- **Metric Lab:** JSON, введённый оператором. Начальные reference/candidate JSON в UI — иллюстративные примеры, нормализованные к `[0, 1]`, а не live-измерения.
- **Автотесты:** локальные fixtures и синтетические входные данные, а не установленные драйверы или реальный каталог драйверов.

Проверьте следующие сценарии:

1. **Обновить устройства в Windows:** нажмите **Refresh device list**. Приложение читает локальные PnP-данные и показывает имя, статус, производителя и hardware ID.
2. **Проверить пакет:** выберите файл `.inf` или `.zip`. Просмотрите метаданные, SHA-256, архитектурные подсказки и ограничения пакета; payload не устанавливается и не выполняется.
3. **Пакетная проверка:** выберите несколько локальных пакетов и сравните отчёты метаданных.
4. **Сравнить метрики:** отредактируйте JSON reference/candidate. Значения должны быть нормализованы к `[0, 1]`; сравните weighted output и веса.
5. **План совместимости:** сформируйте кандидатные связи из текущего списка устройств и hardware ID из INF; вручную проверьте каждого кандидата.
6. **Проверить UDRV:** запустите `tools/udrv_inspector.py` для локального пакета и просмотрите JSON-отчёт.
7. **Regression suite:** выполните `python -m unittest discover -s tests -v`.

### Ограничения входных файлов и архивов

Desktop inspector применяет следующие лимиты:

| Входные данные | Лимит |
|---|---:|
| Файл пакета INF / ZIP | 512 MiB |
| Количество ZIP entries | 10 000 |
| Общий размер распакованного ZIP-содержимого | 2 GiB |
| Отдельный INF | 2 MiB |
| Compression ratio | 200:1 |

У UDRV v1 inspector отдельный контракт: manifest до 4 MiB, до 10 000 entries, один файл до 512 MiB и общий payload до 2 GiB. Inspector читает и хеширует данные ограниченными блоками; он не распаковывает и не выполняет payload.

Встроенного симулятора задержки, переключателя HTTP 500, mock network service или браузерной загрузки нет. Ошибки вроде повреждённого ZIP, небезопасного archive path, слишком большого INF или недоступного PowerShell inventory отображаются локально.

Текущий список устройств и результаты проверки существуют в desktop-процессе. Закрытие приложения очищает эту рабочую сессию, но не меняет исходные пакеты или драйверы Windows. Тема и motion preferences обрабатываются native preferences layer. Browser localStorage, sessionStorage, IndexedDB и cookies отсутствуют.

## Конфигурация и доступ

Корневого `.env.example`, Docker Compose web stack, API key, OAuth-аккаунта, тестового login, CORS policy, HTTP proxy или локального HTTPS-сертификата нет. Для обычной локальной проверки секреты не нужны. Приложение не документирует runtime ENV contract; не придумывайте его.

Реальные переключатели UI: статическую метку DUCK и настройки движения (Reduce Motion, Eco Visuals и Expressive Motion).

Live PnP-запрос требует Windows PowerShell и локальный CIM provider. Если команда заблокирована или завершается ошибкой, проверка файлов пакетов и просмотр сохранённых данных остаются отдельными сценариями; вместо фиктивного списка устройств приложение показывает ошибку инвентаризации.

## Архитектура и структура репозитория

Поток данных: **локальный вход → ограниченный parser → запись доказательств → dry-run comparison/report → необязательный явный экспорт**.

| Путь | Содержимое |
|---|---|
| `oplague_app.py` | публичный desktop entry point с корректным написанием |
| `oplage_app.py` | реализация desktop UI, проверка пакетов и PnP-запрос |
| `tools/` | CLI-утилиты, report composition, метрики и UDRV inspection |
| `tests/` | unit и regression тесты с локальными fixtures |
| `docs/` | архитектура, границы безопасности, схемы и руководство оператора |
| `schemas/` | версионированные контракты отчётов и пакетов |
| `assets/screenshots/` | снимок Windows desktop |
| `security/` | машиночитаемая политика Beelzebul |
| `.github/workflows/` | Windows-упаковка и автоматизация релизов |

Приложение — Python/Tkinter desktop-программа. Путь Windows inventory вызывает локальный PowerShell; package inspector читает метаданные локальных INF/ZIP. Нет frontend/backend deployment, mock server, web port, browser storage, CORS config или публичного live preview. Поэтому browser compatibility и responsive viewport rules неприменимы.

## Упаковка, CI и публикация релизов

[Windows desktop workflow](.github/workflows/desktop-build.yml):

1. использует Python 3.12 в Windows;
2. компилирует Python sources и запускает unit tests;
3. проверяет visual canon;
4. пакует `OPlague.exe` с помощью PyInstaller;
5. захватывает запущенное desktop-приложение и загружает screenshot artifact;
6. создаёт `OPlague-windows-x64.zip` с executable, README и license.

Screenshot artifact хранится 30 дней. Git-тег формата `v*` запускает публикацию GitHub Release. Workflow artifact — скачиваемый файл, а не hosted web demo.

Для отката распространяемой сборки выберите предыдущий известный рабочий tagged release/archive. Серверного deployment для отката нет. Логи workflow и тестов доступны в GitHub Actions.

## Устранение проблем

| Симптом | Что проверить |
|---|---|
| Приложение не запускается | используйте Python 3.10+ с Tkinter и запускайте из корня репозитория |
| Не работает device inventory | проверьте Windows, `powershell.exe` и локальный CIM access; inventory не реализован для Linux/macOS |
| ZIP отклоняется | проверьте archive validity, число entries, expanded size, compression ratio и пути |
| INF отклоняется | убедитесь, что файл не превышает 2 MiB и имеет корректную кодировку |
| Пакет слишком большой | desktop inspector ограничивает файл пакета размером 512 MiB |
| Metric comparison не работает | введите корректные JSON-объекты и нормализуйте значения до `[0, 1]` |
| Native rank total не работает | проверьте, что явно указанная Reaper library существует и заслуживает доверия |

Desktop status и dialog messages описывают непосредственную ошибку. Для CI-сбоев просмотрите соответствующие GitHub Actions logs.

## Известные ограничения, вклад и лицензия

OPlague намеренно не изменяет систему. Он не устанавливает, не загружает, не распаковывает и не изменяет драйверы; сопоставление является кандидатным доказательством, а не сертификацией. Живая инвентаризация оборудования доступна только в Windows. Metric profiles носят рекомендательный характер. Хеши доказывают идентичность байтов, но не подлинность издателя или право собственности. UDRV inspector не выполняет payload.

Правила разработки, проверки изменений и оформления Pull Request описаны в [CONTRIBUTING.md](CONTRIBUTING.md). Сообщайте о проблемах или предлагайте изменения через [GitHub Issues](https://github.com/Ivan-VHS/OPlague/issues) или Pull Request. Укажите ОС, версию Python, безопасный тип тестового файла, точную команду и ожидаемый/фактический результат. Не прикрепляйте приватные driver packages или чувствительные device identifiers без удаления идентифицирующих данных.

Лицензия: [Apache-2.0](LICENSE).

## Соответствие 66 правилам README

Чек-лист вебстенда сопоставлен с реальной desktop-рабочей станцией, а не скопирован как вымышленный web deployment:

| Правила | Покрытие в README |
|---|---|
| 1–11 · назначение и область | определены read-only рабочая станция, пользователи, реальные источники данных, ограничения и отсутствие hosted stand |
| 12–22 · быстрый старт | точные требования Python/Tkinter, GUI entry point, команды тестов и упаковки executable |
| 23–33 · конфигурация и доступ | указано отсутствие `.env`, test login, API secret, CORS и HTTPS; описана реальная локальная PowerShell dependency |
| 34–44 · данные и сценарии | разделены live local PnP data, пользовательские пакеты, пример JSON метрик и test fixtures; указаны лимиты и срок жизни состояния |
| 45–55 · архитектура и сборка | перечислены реальные source, tools, tests, schemas, docs и Windows package workflow |
| 56–66 · эксплуатация и поддержка | описаны публикация artifacts/release, rollback, логи, troubleshooting, ограничения, вклад и лицензия |

**Публичного URL OPlague web demo нет.** Windows-скриншот и release archive не являются онлайн-сервисом управления устройствами.

## Единый формат оболочки отчёта

JSON-отчёт с доказательствами можно обернуть в общий формат метаданных ivan-vhs.report.v1:

    python tools/report_envelope.py --tool oplague --version VERSION --input-file driver.zip < evidence.json

В оболочку записывается только SHA-256 входного файла, а не локальный путь. См. docs/REPORT_ENVELOPE.md и schemas/ivan-vhs.report.v1.schema.json.


## Карта документации

Используйте [индекс документации](docs/README.md) как точку входа, а [карту информационной архитектуры](docs/INFORMATION_ARCHITECTURE.md) — для навигации по проверке устройств, анализу драйверов и пакетов, безопасности, архитектуре и интерфейсу рабочей станции. Хабы ведут к подробным контрактам; режим только для чтения и статус реализации определяются кодом, тестами и схемами.


## Интеграция с рабочим столом Mora

OPlague доступен из общей рабочей области Mora как read-only инструмент проверки устройств и пакетов драйверов. Mora отвечает за обнаружение приложения и стартовую тему; границы проверки и безопасности остаются прежними. См. [интеграцию Mora](docs/MORA_DESKTOP_INTEGRATION.md) и [контракт DuckOS](https://github.com/Ivan-VHS/DuckOS/blob/main/docs/MORA_DESKTOP.md).
