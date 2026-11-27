<p align="center"><picture><source media="(prefers-color-scheme: dark)" srcset="assets/readme/hero-banner-dark.svg"><source media="(prefers-color-scheme: light)" srcset="assets/readme/hero-banner-light.svg"><img src="assets/readme/hero-banner-light.svg" alt="Робоча станція OPlague для пристроїв, драйверів та ігор" width="880"></picture></p>

# OPlague — робоча станція пристроїв, драйверів та ігрової продуктивності

[English](README.md) · [Українська](README.uk.md) · [Русский](README.ru.md) · [简体中文](README.zh-CN.md)

[![Quality](https://img.shields.io/github/actions/workflow/status/Ivan-VHS/OPlague/completeness-check.yml?branch=main&style=flat-square&label=Quality)](https://github.com/Ivan-VHS/OPlague/actions/workflows/completeness-check.yml) [![Windows build](https://img.shields.io/github/actions/workflow/status/Ivan-VHS/OPlague/desktop-build.yml?branch=main&style=flat-square&label=Windows%20build)](https://github.com/Ivan-VHS/OPlague/actions/workflows/desktop-build.yml) [![Apache-2.0](https://img.shields.io/github/license/Ivan-VHS/OPlague?style=flat-square)](LICENSE)

> Локальна Windows-first робоча станція для обмеженої перевірки пристроїв і драйверів, телеметрії з указаним джерелом та явного оборотного power-plan workflow для ігрового сеансу.

**Відомості про проєкт:** розробка · єдину версію продукту не оголошено · Python 3.10+ · JSON Schema · частковий Rust 2021 diagnostics consumer · Windows desktop і live-інвентаризація · Apache-2.0 · **Документацію перевірено:** 2026-11-27 UTC

## Призначення та межі

OPlague поєднує два навмисно відокремлені сценарії:

1. **Докази про пристрої та пакети.** Read-only-інвентаризація Windows Plug-and-Play, обмежена перевірка метаданих INF/ZIP/UDRV, зіставлення нормалізованих hardware ID, локальні звіти та GPU-телеметрія з указаним джерелом.
2. **Ігровий сеанс.** Явний Windows-workflow, який зберігає локальний знімок і може тимчасово вибрати вбудований план живлення Windows. Попередній план відновлюється лише тоді, коли активним залишається план, застосований самим OPlague.

Інспекція драйверів і пакетів не встановлює, не видаляє, не вмикає, не вивантажує, не розпаковує та не виконує драйвери чи payload. Ігровий workflow — окрема системна зміна, яка потребує підтвердження користувача: він не змінює драйвери, реєстр, прошивку, частоти, напруги, служби або мережеві налаштування.

## Можливості

- **Live-інвентаризація пристроїв:** поточні записи Windows Plug-and-Play через фіксований read-only-запит. Live-інвентаризація доступна лише у Windows.
- **Обмежена перевірка пакетів:** метадані INF і структура ZIP з лімітами шляхів, кількості записів, розміру та стиснення.
- **UDRV v1:** перевірка manifest, оголошеного складу payload, розмірів файлів, SHA-256 та обмежень ресурсів/шляхів без розпакування й виконання payload.
- **Звіти доказів:** детерміновані batch-зведення, digest вмісту та версіоновані JSON-знімки з псевдонімним відбитком пристрою.
- **Граф кандидатів сумісності:** точний збіг нормалізованих hardware ID створює лише ребро-кандидат. Він не ранжує, не сертифікує та не доводить безпечність або сумісність драйвера.
- **Метрики й телеметрія:** порівняння нормалізованих профілів і необов’язкові показники NVIDIA через `nvidia-smi`. Відсутні значення датчиків залишаються unknown; телеметрія доступна лише для читання.
- **Ігровий сеанс:** після явного підтвердження зберігається знімок пристроїв, драйверів і плану живлення, після чого можна тимчасово ввімкнути штатний план High Performance. Відновлення захищене: якщо активний план змінили поза сеансом, OPlague не перезаписує новий вибір.
- **Інтеграція:** версіоновані знімки пристроїв та звіти Reaper; необов’язкові виклики C ABI Pytyliki через довірену бібліотеку, явно вибрану стороною-викликом.
- **Міст Rust diagnostics:** обмежений споживач Pytyliki diagnostics ABI на Rust 2021 реалізований частково; це не повна міграція на Rust/Slint.

Offline-аналіз пакетів і звітів доступний у підтримуваних Python-оточеннях поза Windows, якщо конкретний сценарій не потребує live Plug-and-Play.

## Швидкий запуск

Потрібен Python 3.10+; Windows необхідна для desktop-застосунку, live-інвентаризації Plug-and-Play і керування планом живлення. Для телеметрії NVIDIA додатково потрібен підтримуваний локальний провайдер `nvidia-smi`.

Запуск Windows workstation:

~~~sh
python oplague_app.py
~~~

Запуск тестів і перевірка вибраного UDRV-пакета:

~~~sh
python -m unittest discover -s tests -v
python tools/udrv_inspector.py path/to/package.udrv --json
~~~

Інспектор UDRV перевіряє метадані й digest файлів у визначених межах. Він ніколи не розпаковує, не встановлює, не завантажує та не виконує вміст пакета.

## Контракти даних

| Інтерфейс | Контракт | Межа |
|---|---|---|
| Device snapshot | `oplage.device-snapshot.v1` | Версіонований JSON; псевдонімний fingerprint |
| GPU telemetry | `oplage.gpu-telemetry.v1` | Read-only-метадані джерела; невідомі значення залишаються unknown |
| Batch evidence | `oplage.inspection-bundle.v1` | Упорядкований звіт і детермінований digest |
| Пакет драйвера | UDRV v1 | Лише обмежена перевірка manifest і цілісності |
| Reaper comparison | `reaper.oplage-comparison.v1` | Offline-перевірка звіту без зміни пристрою |
| Метрики Pytyliki | `pytyliki.c-abi.v1` | Необов’язковий native-виклик через явно довірену бібліотеку |
| Ігровий сеанс | `oplague.gaming.v1` | Локальний знімок і захищений перехід Windows power plan |

SHA-256 виявляє зміну байтів відносно збереженого digest; це не цифровий підпис, не автентифікація видавця й не доказ безпечності. Метадані Authenticode є свідченням про підтримуваний файл, а не сертифікацією сумісності пристрою.

## Безпека та обмеження

Вважайте INF, ZIP, UDRV, експорт телеметрії та імпортовані звіти недовіреними даними. Парсери дотримуються ресурсних лімітів; payload пакетів не розпаковується й не виконується. Збіг hardware ID створює відношення кандидатів, а не висновок про безпечність.

Перемикання power plan — явна окрема операція, а не частина інспекції. Наразі вона підтримується лише у Windows, зберігає початковий знімок і не перезаписує пізніший зовнішній вибір плану. Вибір плану живлення та порівняння frametime не гарантують підвищення продуктивності.

Сканер репозиторію Beelzebul — локальний/static-інструмент перевірки вихідного коду. Це не endpoint-антивірус, не сканування пам’яті процесів і не карантин.

## Документація

- [Індекс документації](docs/README.md) · [Інформаційна архітектура](docs/INFORMATION_ARCHITECTURE.md)
- [Матриця функцій](docs/FEATURES.md) · [Архітектура](docs/ARCHITECTURE.md)
- [Формат UDRV v1](docs/UDRV_FORMAT_V1.md) · [Граф сумісності пристроїв](docs/DEVICE_COMPATIBILITY_GRAPH.md)
- [Міст GPU telemetry v1](docs/GPU_TELEMETRY_BRIDGE_V1.md) · [Інспекція пристроїв і драйверів](docs/clusters/device-driver-inspection.md)
- [Федеративна інтеграція](docs/FEDERATED_INTEGRATION.md) · [Реліз Windows](docs/RELEASE.md)
- [Reaper runtime integration](docs/REAPER_RUNTIME_INTEGRATION.md) · [Політика безпеки](SECURITY.md)
- [Візуальний стандарт публікації](docs/README_VISUAL_STANDARD.md)

Workflow релізу Windows створює чернетку GitHub Release для перевірки супроводжувачем. Публікація виконується окремо; SHA-256 sidecar не є цифровим підписом.

## Участь і ліцензія

Перед зміною парсерів, схем, телеметрії або системних інтеграцій прочитайте [CONTRIBUTING.md](CONTRIBUTING.md). Зберігайте обмеженість вхідних даних, явність дозволів і походження доказів. Не додавайте приватні payload драйверів або персональні hardware exports.

Ліцензія — [Apache-2.0](LICENSE). Зберігайте повідомлення та атрибуцію сторонніх компонентів.
