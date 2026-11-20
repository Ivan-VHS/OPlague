# OPlague — робоча станція для драйверів

<p align="center">
  <a href="https://github.com/Ivan-VHS/OPlague/actions/workflows/desktop-build.yml"><img alt="Збирання Windows" src="https://github.com/Ivan-VHS/OPlague/actions/workflows/desktop-build.yml/badge.svg"></a>
  <img alt="Python 3.10+" src="https://img.shields.io/badge/runtime-Python%203.10%2B-2563EB?style=flat-square">
  <img alt="Windows" src="https://img.shields.io/badge/desktop-Windows-DC2626?style=flat-square">
  <img alt="Apache 2.0" src="https://img.shields.io/badge/license-Apache--2.0-334155?style=flat-square">
</p>

**OPlague — орієнтована на Windows робоча станція для читання відомостей про обладнання та перевірки пакетів драйверів.** Встановлення й зміна драйверів не виконуються.

[English](README.md) · [Українська](README.uk.md) · [Русский](README.ru.md) · [简体中文](README.zh-CN.md)

## Попередній перегляд desktop-інтерфейсу

<p align="center"><img src="assets/oplague-workbench-preview.svg" alt="Ілюстративний попередній перегляд інтерфейсу OPlague" width="100%"></p>
<sub>Схематична реконструкція за Tkinter-розміткою в репозиторії, а не знімок запущеної програми Windows. Справжній скриншот поки не додано.</sub>

## Робочі модулі та інструменти

- **Інвентаризація пристроїв:** читання Windows Plug and Play: назва, статус, виробник і hardware ID.
- **INF / ZIP-інспектор:** вибрані INF-метадані, SHA-256, перевірка шляхів архіву й обмежень ресурсів, аналіз точних hardware ID та цільової архітектури. Вміст пакета не витягується й не запускається.
- **Пакетні звіти:** упорядковане об’єднання результатів, агреговані лічильники й детермінований fingerprint набору.
- **UDRV-інспектор:** перевірка версійованого маніфесту, переліку payload, розмірів, хешів і обмежень шляхів/ресурсів. Він не встановлює, не завантажує й не запускає payload.
- **Dry-run сумісності:** зв’язок пристроїв із INF Models лише за точним нормалізованим hardware ID. Кандидат не є рейтингом драйверів чи висновком про сумісність.
- **Metric Lab:** порівняння нормалізованих профілів, зважені відстані, cosine similarity, ортогональність і дисперсія повторних вимірювань.
- **Федерація пристроїв:** експорт обмежених JSON-знімків та офлайн-порівняння. Початкові PnP ID замінюються псевдонімними хешами; вони залишаються пов’язуваними й не є анонімізацією.
- **Нативна перевірка:** опційна перевірка метрик через Pytyliki C ABI v1 за явним шляхом до довіреної бібліотеки.
- **QCS-валідатор:** одна граматика й 66 іменованих апаратних доменів; перевірка метаданих контурів і маркерів передачі. Це не компілятор і не перевірка реального обладнання.
- **Системний каталог:** 66 профілів мов/toolchain; виявлення лише через `PATH`.

## Запуск desktop-програми

Потрібні Windows x64 і Python 3.10+.

```bash
git clone https://github.com/Ivan-VHS/OPlague.git
cd OPlague
python oplague_app.py
python -m unittest discover -s tests -v
```

Windows workflow збирає `OPlague.exe` та завантажує артефакт `OPlague-windows-x64.zip`. Тег `v*` публікує архів як GitHub Release.

## Корисні інструменти лише для читання

```bash
python tools/udrv_inspector.py path/to/package.udrv --json
python -m tools.federation snapshot --output device-snapshot.json
python -m tools.federation compare --reference baseline.json --candidate current.json
python -m tools.qcs dialects
python -m tools.qcs validate path/to/example.qcs
python tools/systems_languages.py --profile oplague
```

## Розвиток і межі безпеки

OPlague започатковано 19 листопада 2026 року як Windows-інструмент для роботи з драйверами. У main додано PnP-інвентаризацію, обмежену перевірку INF/ZIP, аналіз архітектур, dry-run за точними ID, перевірку UDRV, пакетні звіти, метрики, версійовані знімки пристроїв, міст Pytyliki та QCS-валідатор.

**Ще не реалізовано:** встановлення/видалення драйверів, увімкнення/вимкнення пристроїв, підпис, відкат, зміни прошивки та live-аналіз DPC/ISR. Цілісність пакета не доводить автентичність постачальника, безпеку чи сумісність драйвера. Імпортовані файли вважаються недовіреними. Тіло QCS зберігається як текст і не компілюється та не виконується.

## Документація та завантаження

[Формат UDRV](docs/UDRV_FORMAT_V1.md) · [Граф сумісності](docs/DEVICE_COMPATIBILITY_GRAPH.md) · [Федерація](docs/FEDERATED_INTEGRATION.md) · [Синтаксис QCS](docs/QUANTUM_CONTOUR_SYNTAX.md) · [Єдиний інженерний стандарт](docs/UNIFIED_ENGINEERING_STANDARD.md)

[Релізи Windows](https://github.com/Ivan-VHS/OPlague/releases) · [Збирання desktop](https://github.com/Ivan-VHS/OPlague/actions/workflows/desktop-build.yml)

**Екосистема:** [Reaper](https://github.com/Ivan-VHS/Reaper) · [Pytyliki](https://github.com/Ivan-VHS/Pytyliki) · [матриця 3×3](https://github.com/Ivan-VHS/Reaper/blob/main/docs/PROJECT_FEDERATION_MATRIX.md).

## Ліцензія

[Apache License 2.0](LICENSE)

UI motion: [12 animation principles](docs/DISNEY_MOTION_SYSTEM.md).
