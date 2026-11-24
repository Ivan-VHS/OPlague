
<p align="center"><picture><source media="(prefers-color-scheme: dark)" srcset="assets/readme/hero-banner-dark.svg"><source media="(prefers-color-scheme: light)" srcset="assets/readme/hero-banner-light.svg"><img src="assets/readme/hero-banner-light.svg" alt="Робоча станція OPlague для пристроїв, драйверів та ігор" width="880"></picture></p>
<h1 align="center">OPlague — робоча станція пристроїв, драйверів та ігрової продуктивності</h1>
<p align="center"><strong>Локальний Windows-застосунок для обмеженої перевірки пристроїв і драйверів, доказових звітів та оборотного налаштування ігрового сеансу.</strong></p>
<p align="center"><a href="https://github.com/Ivan-VHS/OPlague/actions/workflows/completeness-check.yml"><img alt="Quality checks" src="https://img.shields.io/github/actions/workflow/status/Ivan-VHS/OPlague/completeness-check.yml?branch=main&style=flat-square&label=Quality"></a> <a href="https://github.com/Ivan-VHS/OPlague/actions/workflows/desktop-build.yml"><img alt="Windows build" src="https://img.shields.io/github/actions/workflow/status/Ivan-VHS/OPlague/desktop-build.yml?branch=main&style=flat-square&label=Windows%20build"></a> <a href="LICENSE"><img alt="Apache-2.0" src="https://img.shields.io/github/license/Ivan-VHS/OPlague?style=flat-square"></a></p>

[Швидкий старт](#швидкий-старт) · [Revival](#оновлення-документації-revival) · [Візуальний огляд](#візуальний-огляд) · [Архітектура](#архітектура) · [Документація](docs/README.md)

> **Межа безпеки:** перевірка драйверів і пакетів працює в режимі читання: payload не розпаковується, не виконується, не встановлюється й не завантажується. Точний збіг hardware ID — кандидат, а не сертифікація сумісності. Окремий ігровий сеанс може тимчасово вибрати вбудований план живлення Windows після збереження snapshot; відновлення захищене від перезапису пізніших зовнішніх змін.

## Швидкий старт

**Вимоги:** Python 3; для live Plug and Play inventory потрібна Windows. Збережені звіти й метадані пакетів можна переглядати офлайн. Для desktop UI потрібен Tkinter.

~~~sh
git clone https://github.com/Ivan-VHS/OPlague.git
cd OPlague
python oplague_app.py
~~~

Тести та перевірка візуального контракту:

~~~sh
python -m compileall -q oplague_app.py oplage_app.py tests
python tools/validate_visual_canon.py ui_theme.py
python -m unittest discover -s tests -v
~~~

Корисні CLI-перевірки:

~~~sh
python -m oplague --verify
python -m oplague --catalog
python -m oplague --search "ballistic"
python -m oplague --profile 5
python -m oplague --rank reach
~~~

## Оновлення документації Revival

| Було | Стало |
|---|---|
| Статичний огляд без чітких ролей зображень | Адаптивний банер і підписані знімок/архітектурна схема |
| Аналіз драйверів та ігрові налаштування виглядали як одна межа доступу | Read-only перевірка відокремлена від явної оборотної зміни power plan |
| Опис функцій без єдиної термінології зрілості | Матриця можливостей із межами джерел, даних і безпеки |
| Швидкий старт змішаний з операційними деталями | Перевірені команди запуску, тестів і CLI на початку |
| Посилання розпорошені | Тематичні хаби, індекс документації та стандарт публікації |

Це оновлення документації, **не версія ПЗ й не оголошення релізу**. Джерелами істини є код, тести, схеми та актуальні CI workflow.

## Реалізований функціонал

| Область | Поточна поведінка | Межа |
|---|---|---|
| Інвентаризація пристроїв | Збір Windows Plug and Play identity/status | Live inventory лише у Windows |
| INF / ZIP | Обмежений розбір метаданих, шляхів, hashes та architecture hints | Без розпакування й виконання |
| Authenticode | Метадані підпису, signer і timestamp вибраних файлів | Не підтверджує безпечність і не встановлює драйвер |
| Сумісність | Кандидати за точним нормалізованим hardware ID | Лише evidence для ручної перевірки |
| UDRV v1 | Перевірка manifest, розмірів файлів і SHA-256 | Без встановлення та завантаження |
| Звіти й snapshots | Версіонований JSON, batch summaries і offline compare | Локальні дані; hash не доводить довіру до видавця |
| Ігровий сеанс | Snapshot, тимчасовий вбудований power plan і guarded restore | Не розгін GPU, не зміна драйвера або firmware |
| Метрики | Зважена відстань і порівняння профілів | Рекомендаційна оцінка, не сертифікація |

## Візуальний огляд

<table><tr><td width="50%"><a href="assets/screenshots/oplague-workbench.png"><img src="assets/screenshots/oplague-workbench.png" alt="Знімок робочої станції OPlague у Windows" width="100%"></a><p><sub><strong>Реальний знімок застосунку</strong> — Windows desktop, 1920×1080.</sub></p></td><td width="50%"><img src="assets/readme/workflow.svg" alt="Потік OPlague: локальний ввід, обмежений parser, evidence, candidate analysis і звіт" width="100%"><p><sub><strong>Архітектурна ілюстрація</strong> — схема evidence pipeline, а не знімок UI.</sub></p></td></tr></table>

## Архітектура

~~~mermaid
flowchart LR
  A[Windows PnP / локальний пакет] --> B[Обмежений metadata parser]
  B --> C[Перевірений evidence record]
  C --> D[Candidate matching і review]
  D --> E[Dry-run report]
  E --> F[Явний JSON export]
  G[Збережений device snapshot] --> D
  H[Gaming session] --> I[Snapshot power plan]
  I --> J[Тимчасовий вбудований plan]
  J --> K[Guarded restore]
~~~

Інспекція та ігровий сеанс — різні потоки. Driver pipeline не встановлює, не завантажує, не розпаковує й не виконує вміст пакета.

## Конфігурація та доступ

Hosted service, API token, обліковий запис, root .env або тестовий логін не потрібні. Live inventory використовує локальні Windows PowerShell/CIM. Якщо провайдер недоступний, застосунок показує помилку інвентаризації й не підставляє фіктивний список пристроїв.

У desktop UI доступні палітра Duck і motion preferences. Зміна системного power plan належить лише до окремого явного ігрового сценарію.

## Структура репозиторію

| Шлях | Призначення |
|---|---|
| oplague_app.py | Публічна точка входу desktop-застосунку |
| oplage_app.py | Реалізація desktop UI та логіки інспекції |
| tools/ | CLI, звіти, метрики й UDRV utilities |
| tests/ | Unit та regression-тести із синтетичними fixtures |
| schemas/ | Версіоновані звіти й package contracts |
| docs/ | Архітектура, безпека, інтеграції та operator references |
| assets/readme/ | Адаптивний банер і workflow-ілюстрація |
| assets/screenshots/ | Знімки Windows-застосунку |
| .github/workflows/ | CI, Windows packaging і quality gates |

## Перевірки та статус

~~~sh
python -m unittest discover -s tests -v
python -m oplague --verify
python tools/udrv_inspector.py path/to/package.udrv --json
git diff --check
~~~

Поточні можливості й обмеження: [матриця функцій](docs/FEATURES.md), [архітектура](docs/ARCHITECTURE.md), [хаб перевірки пристроїв і драйверів](docs/clusters/device-driver-inspection.md) та [карта документації](docs/INFORMATION_ARCHITECTURE.md). Heuristic або збіг не є verdict про malware чи certification пристрою.

## Розробка та безпека

Перед змінами parser, системних інтеграцій і safety controls прочитайте [CONTRIBUTING.md](CONTRIBUTING.md). Правила публікації — у [README Visual Standard](docs/README_VISUAL_STANDARD.md), політика безпеки — у [SECURITY.md](SECURITY.md).

## Ліцензія

[Apache-2.0](LICENSE).
