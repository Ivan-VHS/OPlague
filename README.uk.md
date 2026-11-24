# OPlague — робоча станція перевірки пристроїв і драйверів

[English](README.md) · [Українська](README.uk.md) · [Русский](README.ru.md) · [简体中文](README.zh-CN.md)

<p align="center"><img src="assets/readme/dashboard.svg" alt="Огляд проєкту OPlague" width="100%"></p>

[Вихідний код](https://github.com/Ivan-VHS/OPlague) · [Windows desktop workflow](.github/workflows/desktop-build.yml) · [Індекс документації](docs/README.md) · [Apache-2.0](LICENSE)

## Реальний знімок Windows-робочої станції

<p align="center"><a href="assets/screenshots/oplague-workbench.png"><img src="assets/screenshots/oplague-workbench.png" alt="Реальний знімок OPlague у Windows" width="100%"></a></p>
<p align="center"><sub>1920×1080 · Натисніть зображення, щоб відкрити оригінальний PNG.</sub></p>

Справжній скріншот запущеного desktop-застосунку OPlague, створений Windows packaging workflow. Банер і схема процесу — авторські SVG-ілюстрації; зображення інтерфейсу не генерувалося і не монтувалося.

### Архітектура одним поглядом

<p align="center"><img src="assets/readme/workflow.svg" alt="OPlague implemented data flow" width="100%"></p>

Реальний шлях: Windows PnP і вибрані користувачем файли → обмежена перевірка INF/ZIP → нормалізовані ID та хеші → звіт із кандидатними доказами.


[![Windows build](https://img.shields.io/github/actions/workflow/status/Ivan-VHS/OPlague/desktop-build.yml?branch=main&label=Windows%20build)](https://github.com/Ivan-VHS/OPlague/actions/workflows/desktop-build.yml)  [![Docs checks](https://img.shields.io/github/actions/workflow/status/Ivan-VHS/OPlague/docs.yml?branch=main&label=Docs%20checks)](https://github.com/Ivan-VHS/OPlague/actions/workflows/docs.yml)  [![License](https://img.shields.io/github/license/Ivan-VHS/OPlague)](LICENSE)


> **Призначення:** OPlague — локальна read-only робоча станція для інвентаризації Windows Plug and Play, перегляду метаданих INF/ZIP-пакетів драйверів і порівняння доказів сумісності. Вона **не встановлює, не завантажує, не розпаковує та не змінює** вміст драйверів. Репозиторій не публікує hosted web demo, віддалений API чи production-сервіс керування пристроями. Документацію звірено з `main` **22.11.2026**.

## Призначення та межі

OPlague допомагає оператору переглянути записи пристроїв поточної машини, прочитати метадані пакета драйвера та порівняти нормалізовані апаратні ідентифікатори. Цільова аудиторія — інженери підтримки Windows, рев’юери апаратного забезпечення, QA та розробники, які досліджують вміст пакетів або докази сумісності.

Результат — запис доказів і список кандидатів, а не остаточний висновок щодо безпеки чи сумісності. Точний збіг hardware ID не доводить довіру до видавця, сумісність з ОС, придатність пристрою або безпечність встановлення. Розгортання драйверів не входить до функцій продукту.

### Реальні можливості робочої станції

| Напрям | Реалізована поведінка | Межа |
|---|---|---|
| Інвентаризація пристроїв | читає ідентичність Windows Plug and Play, статус, виробника та PNPDeviceID | збір живих даних доступний лише у Windows і лише для читання |
| Перевірка INF | читає вибрані метадані, оголошення hardware ID та цільову архітектуру | не виконує директиви INF |
| Перевірка ZIP | перевіряє шляхи, розмір, compression ratio, хеші та метадані INF | не розпаковує й не виконує payload |
| Перевірка PE/COFF | читає тип машини, optional header, секції, entry point і розташування certificate table | лише читання заголовків; без завантаження образу чи висновку про підпис |
| SPDX file inventory | створює детермінований SPDX 2.3-звіт файлів і хешів | без графа залежностей і висновків про ліцензії |
| Граф сумісності | формує кандидатні зв’язки за точними нормалізованими hardware ID | це лише кандидати; потрібна ручна перевірка |
| Metric Lab | порівнює введені користувачем нормалізовані профілі через weighted distance/variance | рекомендаційний аналіз, не вердикт щодо пристрою |
| UDRV v1 | перевіряє manifest, розміри та SHA-256 | перевірка цілісності, не автентифікація видавця |
| Звіти | формує структуровані докази, підсумки та fingerprints | без запису в систему й без встановлення драйверів |

У застосунку є чотири основні вкладки: **Devices**, **Package Inspection**, **Metric Lab** і **Compatibility Review**. Використовується єдина чорно-біло-жовта палітра DuckOS; налаштування руху містять Reduce Motion та Eco Visuals.

Скріншот нижче — знімок desktop-застосунку, а не браузерне прев’ю.

Локальний аналіз бінарних файлів та експорт інвентарю:

```sh
python tools/pe_inspector.py driver.sys --output driver-pe-report.json
python tools/sbom_inventory.py ./staging --output staging.spdx.json
```

PE-перевірка читає лише заголовки. SPDX-звіт зберігає хеші, а неперевірені відомості про ліцензії позначає `NOASSERTION`.


## Пов’язаний продукт ОС: DuckOS

Сім застосунків Mora (Cockos, Kavun, Ka-bon, Gloverty, Po, Illidia та Unify) описані в окремому проєкті [DuckOS](https://github.com/Ivan-VHS/DuckOS/blob/main/docs/PREINSTALLED_APPLICATIONS.md). Це рівень застосунків операційної системи, а не компонент OPlague. Цей репозиторій не заявляє про постачання цих застосунків або надання їхніх системних служб. Власні можливості та інтерфейси OPlague визначаються її вихідним кодом, тестами й версіонованими контрактами.

## Інтеграція з Reaper

## Політика виконання плагінів

Локальний plugin host тепер обмежує розмір вхідних і вихідних даних, конкурентний запуск та фіксує час виконання і стан обробників. Див. [політику виконання плагінів](docs/PLUGIN_EXECUTION_POLICY.md). Deadline для синхронних Python-обробників перевіряється після повернення й не є примусовим скасуванням.

OPlague може використовувати версійований C17 ABI Reaper для обмежених цілочисельних виразів над уже перевіреними даними. Це не передає Reaper керування драйверами, встановленням пакетів або висновками щодо сумісності.

Докладніше: [інтеграція Reaper](docs/REAPER_RUNTIME_INTEGRATION.md).

## Швидкий старт

### Вимоги

- Python **3.10 або новіший**.
- Tkinter для desktop UI.
- Windows і `powershell.exe` для живої інвентаризації Plug and Play. Інвентаризація використовує фіксований локальний PowerShell/CIM-запит.
- Git.

Застосунок імпортує власні модулі репозиторію та засоби стандартної бібліотеки Python; сторонні runtime-пакети для запуску з вихідного коду не потрібні. PyInstaller потрібний лише для пакування автономного виконуваного файла.

У Linux та macOS можна перевіряти збережені дані, але жива інвентаризація Windows PnP недоступна.

### Запуск desktop-застосунку

З кореня репозиторію:

```sh
python oplague_app.py
```

`oplague_app.py` — entry point із правильною назвою; він передає керування наявному модулю реалізації `oplage_app.py`.

### Тести та CLI-перевірки

```sh
python -m compileall -q oplague_app.py oplage_app.py tests
python tools/validate_visual_canon.py ui_theme.py
python -m unittest discover -s tests -v
```

Приклади команд CLI:

```sh
python -m oplague --verify
python -m oplague --catalog
python -m oplague --search "ballistic"
python -m oplague --profile 5
python -m oplague --rank reach
python tools/udrv_inspector.py path/to/package.udrv --json
python tools/clinical_systems.py --catalog --pretty
```

Необов’язковий розрахунок через Reaper C17 потребує явного шляху до довіреної бібліотеки:

```sh
python -m oplague --rank-total-native --reaper-library /absolute/path/to/libreaper_ffi.so
```

Усе це локальне виконання. OPlague не запускає HTTP listener, web UI, API endpoint або localhost preview.

### Збирання виконуваного файла Windows

Desktop workflow використовує Python 3.12 та PyInstaller. Для локального пакування:

```sh
python -m pip install --upgrade pyinstaller
python -m PyInstaller --noconfirm --clean --onefile --windowed --name OPlague oplague_app.py
```

Автономний файл створюється в `dist/OPlague.exe`. Перше пакування може тривати довше, поки PyInstaller збирає застосунок; фіксований час збірки не гарантується.

## Дані, обмеження та сценарії перевірки

OPlague не має спільної бази даних, входу, демоакаунта, віддаленого mock API чи hosted fixture service. Джерела даних розділені:

- **Інвентаризація пристроїв:** реальні локальні записи Windows Plug and Play через `Get-CimInstance`.
- **Перевірка пакетів:** файл, який оператор явно вибрав.
- **Metric Lab:** JSON, введений оператором. Початкові reference/candidate JSON у UI — ілюстративні приклади, нормалізовані до `[0, 1]`, а не живі вимірювання.
- **Автотести:** локальні fixture та синтетичні вхідні дані, а не встановлені драйвери чи реальний каталог драйверів.

Перевірте такі сценарії:

1. **Оновити пристрої у Windows:** натисніть **Refresh device list**. Застосунок читає локальні PnP-дані й показує назву, статус, виробника та hardware ID.
2. **Перевірити пакет:** виберіть файл `.inf` або `.zip`. Перегляньте метадані, SHA-256, архітектурні підказки й обмеження пакета; payload не встановлюється й не виконується.
3. **Пакетна перевірка:** виберіть кілька локальних пакетів та порівняйте їхні метадані.
4. **Порівняти метрики:** відредагуйте JSON reference/candidate. Значення мають бути нормалізовані до `[0, 1]`; порівняйте weighted output і задані ваги.
5. **План сумісності:** сформуйте кандидатні зв’язки з поточного списку пристроїв та hardware ID з INF; вручну перевірте кожного кандидата.
6. **Перевірити UDRV:** запустіть `tools/udrv_inspector.py` для локального пакета й перегляньте JSON-звіт.
7. **Regression suite:** запустіть `python -m unittest discover -s tests -v`.

### Обмеження вхідних файлів та архівів

Desktop inspector застосовує такі ліміти:

| Вхідні дані | Ліміт |
|---|---:|
| Файл пакета INF / ZIP | 512 MiB |
| Кількість ZIP entries | 10 000 |
| Загальний розмір розпакованого ZIP-вмісту | 2 GiB |
| Окремий INF | 2 MiB |
| Compression ratio | 200:1 |

UDRV v1 inspector має власний контракт: manifest до 4 MiB, до 10 000 entries, один файл до 512 MiB і загальний payload до 2 GiB. Inspector читає та хешує дані обмеженими блоками; він не розпаковує й не виконує payload.

Вбудованого симулятора затримки, перемикача HTTP 500, mock network service або браузерного upload немає. Помилки на кшталт пошкодженого ZIP, небезпечного archive path, завеликого INF чи недоступного PowerShell inventory відображаються локально.

Поточний список пристроїв і результати перевірки існують у desktop-процесі. Закриття застосунку очищає цю робочу сесію, але не змінює оригінальні пакети чи драйвери Windows. Тема й motion preferences обробляються native preferences layer. Browser localStorage, sessionStorage, IndexedDB та cookies немає.

## Конфігурація та доступ

Кореневого `.env.example`, Docker Compose web stack, API key, OAuth-акаунта, тестового login, CORS policy, HTTP proxy або локального HTTPS-сертифіката немає. Для звичайної локальної перевірки секрети не потрібні. Поточний застосунок не документує runtime ENV contract; не вигадуйте його.

Реальні UI-перемикачі: статичну мітку DUCK і налаштування руху (Reduce Motion, Eco Visuals та Expressive Motion).

Живий PnP-запит потребує Windows PowerShell і локального CIM provider. Якщо команду заблоковано або вона завершується помилкою, перевірка файлів пакетів і перегляд збережених даних залишаються окремими сценаріями; замість помилкового списку пристроїв застосунок показує помилку інвентаризації.

## Архітектура та структура репозиторію

Потік даних: **локальний вхід → обмежений parser → запис доказів → dry-run comparison/report → необов’язковий явний експорт**.

| Шлях | Вміст |
|---|---|
| `oplague_app.py` | публічний entry point desktop-застосунку з правильною назвою |
| `oplage_app.py` | реалізація desktop UI, перевірка пакетів та PnP-запит |
| `tools/` | CLI-утиліти, report composition, метрики та UDRV inspection |
| `tests/` | unit і regression-тести з локальними fixtures |
| `docs/` | архітектура, межі безпеки, схеми й інструкції оператору |
| `schemas/` | версійовані контракти звітів і пакетів |
| `assets/screenshots/` | знімок Windows desktop |
| `security/` | машинозчитувана політика Beelzebul |
| `.github/workflows/` | Windows-пакування й автоматизація релізів |

Застосунок — Python/Tkinter desktop-програма. Шлях Windows inventory викликає локальний PowerShell; package inspector читає метадані локальних INF/ZIP. Немає frontend/backend deployment, mock server, web port, browser storage, CORS config чи публічного live preview. Тому browser compatibility та responsive viewport rules не застосовуються.

## Пакування, CI та публікація релізів

[Windows desktop workflow](.github/workflows/desktop-build.yml):

1. використовує Python 3.12 у Windows;
2. компілює Python sources і запускає unit tests;
3. перевіряє visual canon;
4. пакує `OPlague.exe` за допомогою PyInstaller;
5. захоплює запущений desktop-застосунок і завантажує screenshot artifact;
6. створює `OPlague-windows-x64.zip` з executable, README та license.

Screenshot artifact зберігається 30 днів. Git-тег формату `v*` збирає Windows-архів, перевіряє SHA-256 sidecar і створює чернетку GitHub Release за бар’єром `release-review`. Чернетку має вручну опублікувати супровідник. Workflow artifact — це файл для завантаження, а не hosted web demo.

Для відкату розповсюдженої збірки виберіть попередній відомий робочий tagged release/archive. Серверного deployment для відкату немає. Логи workflow і тестів доступні в GitHub Actions.

## Усунення проблем

| Симптом | Що перевірити |
|---|---|
| Застосунок не запускається | використовуйте Python 3.10+ із Tkinter і запускайте з кореня репозиторію |
| Не працює device inventory | перевірте Windows, `powershell.exe` і локальний CIM access; inventory не реалізовано для Linux/macOS |
| ZIP відхиляється | перевірте archive validity, кількість entries, expanded size, compression ratio і шляхи |
| INF відхиляється | перевірте, що файл не перевищує 2 MiB та має коректне кодування |
| Пакет завеликий | desktop inspector обмежує розмір файлу пакета до 512 MiB |
| Metric comparison не працює | введіть коректні JSON-об’єкти та нормалізуйте значення до `[0, 1]` |
| Не працює native rank total | перевірте, що явно вказана Reaper library існує та є довіреною |

Desktop status і dialog messages описують безпосередню помилку. Для CI-збоїв перегляньте відповідні GitHub Actions logs.

## Відомі обмеження, внесок і ліцензія

OPlague навмисно не змінює систему. Він не встановлює, не завантажує, не розпаковує та не змінює драйвери; зіставлення є кандидатним доказом, а не сертифікацією. Жива інвентаризація апаратури доступна лише у Windows. Metric profiles мають рекомендаційний характер. Хеші доводять ідентичність байтів, але не автентичність видавця чи право власності. UDRV inspector не виконує payload.

Правила розробки, перевірки змін і оформлення Pull Request описані в [CONTRIBUTING.md](CONTRIBUTING.md). Повідомляйте про проблеми або пропонуйте зміни через [GitHub Issues](https://github.com/Ivan-VHS/OPlague/issues) чи Pull Request. Додавайте ОС, версію Python, безпечний тип тестового файла, точну команду та очікуваний/фактичний результат. Не прикріплюйте приватні driver packages або чутливі device identifiers без видалення ідентифікаційних даних.

Ліцензія: [Apache-2.0](LICENSE).

## Відповідність 66 правилам README

Чекліст вебстенду зіставлений із реальною desktop-робочою станцією, а не скопійований як вигаданий web deployment:

| Правила | Покриття в README |
|---|---|
| 1–11 · призначення та область | визначено read-only робочу станцію, користувачів, джерела даних, обмеження та відсутність hosted stand |
| 12–22 · швидкий старт | точні вимоги Python/Tkinter, GUI entry point, команди тестів і пакування executable |
| 23–33 · конфігурація та доступ | зазначено відсутність `.env`, test login, API secrets, CORS і HTTPS; описано реальну локальну PowerShell dependency |
| 34–44 · дані й сценарії | розділено live local PnP data, пакети користувача, приклади JSON для метрик і test fixtures; задокументовано ліміти та тривалість стану |
| 45–55 · архітектура та збірка | наведено реальні source, tools, tests, schemas, docs і Windows package workflow |
| 56–66 · експлуатація та підтримка | описано публікацію artifacts/release, rollback, логи, troubleshooting, обмеження, внесок і ліцензію |

**Публічного URL OPlague web demo немає.** Windows-скріншот і release archive не є онлайн-сервісом керування пристроями.

## Єдиний формат оболонки звіту

JSON-звіт із доказами можна обгорнути в загальний формат метаданих ivan-vhs.report.v1:

    python tools/report_envelope.py --tool oplague --version VERSION --input-file driver.zip < evidence.json

В оболонку записується лише SHA-256 вхідного файла, а не локальний шлях. Див. docs/REPORT_ENVELOPE.md і schemas/ivan-vhs.report.v1.schema.json.


## Карта документації

Використовуйте [індекс документації](docs/README.md) як точку входу, а [карту інформаційної архітектури](docs/INFORMATION_ARCHITECTURE.md) — для навігації перевіркою пристроїв, аналізом драйверів і пакетів, безпекою, архітектурою та інтерфейсом робочої станції. Хаби ведуть до детальних контрактів; режим лише читання та стан реалізації визначаються кодом, тестами й схемами.


## Інтеграція з робочим столом Mora

OPlague доступний зі спільного робочого простору Mora як read-only інструмент перевірки пристроїв і пакетів драйверів. Mora відповідає за виявлення програми та початкову тему; межі перевірки й безпеки не змінюються. Див. [інтеграцію Mora](docs/MORA_DESKTOP_INTEGRATION.md) та [контракт DuckOS](https://github.com/Ivan-VHS/DuckOS/blob/main/docs/MORA_DESKTOP.md).
