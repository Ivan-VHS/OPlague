# OPlague — робоча станція драйверів

[English](README.md) · [Українська](README.uk.md) · [Русский](README.ru.md) · [简体中文](README.zh-CN.md)

<p align="center"><img src="assets/readme/dashboard.svg" alt="Візуальний огляд OPlague 2026" width="100%"></p>
<sub>Візуальний огляд проєкту · README оновлено 22.11.2026 · палітра проєкту · читабельні схеми даних</sub>


[Збирання Windows](https://github.com/Ivan-VHS/OPlague/actions/workflows/desktop-build.yml) · [CI](https://github.com/Ivan-VHS/OPlague/actions) · Python 3.10+ · Windows · Apache-2.0
**Розробник:** [Ivan-VHS](https://github.com/Ivan-VHS)

**OPlague — інструмент лише для читання: інвентаризація пристроїв Windows, аналіз пакетів драйверів і зіставлення доказів. Він не встановлює, не завантажує та не змінює драйвери.**


## Реальний знімок Windows-застосунку

<p align="center"><img src="assets/screenshots/oplague-workbench.png" alt="Робоча станція OPlague у Windows" width="100%"></p>

<sub>Фактичний знімок програми · вихідне зображення 1920×1080 · початкові пікселі збережено, штучне збільшення не застосовується.</sub>

Зв’язки пристроїв і пакетів наведено як докази для перевірки оператором; встановлення драйвера не запускається.

## Потік функціональних даних

Схема показує реалізований рух даних між записами пристроїв Windows, аналізом пакетів і формуванням звіту.

```mermaid
flowchart TD
    A[Записи Windows Plug and Play] --> B[Інвентаризація лише для читання]
    B --> C[Нормалізовані hardware ID]
    D[Пакет INF / ZIP] --> E[Перевірка метаданих, шляхів і хешів]
    E --> F[Відомості про цільову архітектуру]
    C --> G[Кандидатні зв’язки сумісності]
    F --> G
    G --> H[Пакетний звіт порівняння]
    H --> I[Підсумки та fingerprint звіту]
  classDef readmeNode fill:#EDF5FE,stroke:#0D5CB8,color:#173653,stroke-width:1.5px;
  class A,B,C,D,E,F,G,H,I readmeNode;
  linkStyle default stroke:#0D5CB8,stroke-width:1.8px;
```

## Перевірка пакетів та аналіз метрик

Друга схема описує перевірку цілісності пакета та числовий аналіз наданих векторів.

```mermaid
flowchart LR
    A[Пакет UDRV v1] --> B[Перевірка manifest і розмірів]
    B --> C[Перевірка SHA-256]
    C --> D[Дані про цілісність]
    E[Надані числові вектори] --> F[Нормалізація та порівняння]
    F --> G[Звіт про зважену відстань і дисперсію]
  classDef readmeNode fill:#EDF5FE,stroke:#0D5CB8,color:#173653,stroke-width:1.5px;
  class A,B,C,D,E,F,G readmeNode;
  linkStyle default stroke:#0D5CB8,stroke-width:1.8px;
```

## Модулі робочої станції

| Модуль | Дані та результат | Межа |
|---|---|---|
| Пристрої | Plug and Play, стан і hardware ID | виявлення лише для читання |
| INF / ZIP | метадані, хеші, шляхи та ліміти ресурсів | без виконання пакета й інсталяції драйвера |
| Архітектура | INF target та архітектура хоста | доказ, а не вердикт сумісності |
| Граф сумісності | точні нормалізовані зв’язки hardware ID | лише кандидати |
| UDRV v1 | manifest, розміри файлів і SHA-256 | перевірка цілісності; без інсталяції/завантаження |
| DRIVE-LENS | походження, HMAC-псевдоніми та групування за атрибутами/часом | без автоматичного вердикту |
| Batch reports | порядок результатів, підсумки й fingerprint звіту | без запису в систему |
| Metric Lab | нормалізовані вектори, зважена відстань і дисперсія | аналіз наданих даних |
| Clinical Systems | 120 принципів і 36 телеметричних перевірок | рекомендації, не медична чи апаратна сертифікація |
| Impact Profiles | 20 семантичних профілів і п’ять порядкових вимірів | лише лексичний каталог; без висновків про обладнання |

## Запуск і тести

Запуск робочої станції Windows:

```sh
python oplague_app.py
```

Тести та каталог семантичних профілів:

```sh
python -m unittest discover -s tests -v
python -m oplague --verify
python -m oplague --catalog
python -m oplague --search "баллістичний"
python -m oplague --profile 5
python -m oplague --rank reach
python tools/udrv_inspector.py path/to/package.udrv --json
python tools/clinical_systems.py --catalog --pretty
```

Windows workflow перевіряє візуальний канон і тести, збирає автономний `OPlague.exe`, створює реальний знімок запущеного застосунку та публікує архів Windows x64.

## Довідник кодів

| INF target | PE machine |
|---|---:|
| NTx86 | `0x014C` |
| NTamd64 | `0x8664` |
| NTarm | `0x01C4` |
| NTarm64 | `0xAA64` |
| NTia64 (застарілий) | `0x0200` |

Ліміти UDRV v1: manifest ≤4 МіБ · ≤10 000 записів · файл ≤512 МіБ · загалом ≤2 ГіБ · буфер SHA-256 1 МіБ.

Збіг ID або хешу не доводить довіру до видавця, сумісність з ОС, придатність пристрою чи безпечність інсталяції. HMAC-псевдоніми та fingerprint звіту допомагають зберігати узгодженість і походження даних, але самі по собі не підтверджують справжність.

[Покажчик документації](docs/README.md) · [Ліцензія Apache-2.0](LICENSE)


## Довідник розподілу бюджету
Приклад моделі бюджету 500 грн із JSON-контрактом та автономним симулятором. Це документаційний приклад, а не функція runtime самого застосунку.

[Багатомовний довідник](docs/RESOURCE_ALLOCATION_500_UAH.md) · [Інтерактивний симулятор](docs/resource-allocation-500-uah.html) · [Приклад JSON](examples/resource-allocation-500-uah.json) · [JSON Schema](schemas/resource-allocation.v1.schema.json)
