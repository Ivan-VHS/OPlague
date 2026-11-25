# OPlague — робоча станція пристроїв, драйверів та ігрової продуктивності

[English](README.md) · [Українська](README.uk.md) · [Русский](README.ru.md) · [简体中文](README.zh-CN.md)

[![Windows build](https://img.shields.io/github/actions/workflow/status/Ivan-VHS/OPlague/desktop-build.yml?branch=main&label=Windows%20build)](https://github.com/Ivan-VHS/OPlague/actions/workflows/desktop-build.yml) [![Перевірка документації](https://img.shields.io/github/actions/workflow/status/Ivan-VHS/OPlague/docs.yml?branch=main&label=Docs%20checks)](https://github.com/Ivan-VHS/OPlague/actions/workflows/docs.yml) [![Apache-2.0](https://img.shields.io/github/license/Ivan-VHS/OPlague)](LICENSE)

<p align="center"><img src="assets/readme/dashboard.svg" alt="Огляд OPlague" width="100%"></p>
<p align="center"><a href="assets/screenshots/oplague-workbench.png"><img src="assets/screenshots/oplague-workbench.png" alt="Робоча станція OPlague у Windows" width="100%"></a></p>

OPlague — локальна desktop-станція для перевірки пристроїв і драйверів, аналізу пакетів, доказів сумісності та ігрової продуктивності.

**Базова межа:** перевірка працює лише на читання. Виявлення пристроїв і аналіз вибраних файлів не встановлюють, не вмикають, не вимикають і не змінюють драйвери. Кандидати сумісності й телеметрія є даними для перевірки, а не сертифікацією.

## Можливості

- Інвентаризація Windows Plug-and-Play та обмежений аналіз INF/ZIP-пакетів.
- Перевірка PE й Authenticode, нормалізовані hardware ID, хеші та SPDX-інвентаризація.
- Докази сумісності пристроїв, перевірка пакетів UDRV і структуровані звіти.
- Локальна ігрова телеметрія, аналіз frametime та зворотні користувацькі профілі продуктивності.

Докладніше: [Можливості](docs/FEATURES.md) · [Архітектура](docs/ARCHITECTURE.md) · [Authenticode](docs/AUTHENTICODE.md) · [Архітектура драйверів](docs/DRIVER_TARGET_ARCHITECTURE.md) · [UDRV](docs/UDRV_FORMAT_V1.md) · [Ігрова станція](docs/GAMING_PERFORMANCE_WORKBENCH.md) · [GPU telemetry bridge v1](docs/GPU_TELEMETRY_BRIDGE_V1.md).

## Запуск і тести

Для поточних desktop-інструментів і перевірок потрібен Python 3.10–3.12.

```sh
python oplague_app.py
python -m unittest discover -s tests -v
python -m oplague --verify
python -m oplague --catalog
```

Перевірка пакета:

```sh
python tools/udrv_inspector.py path/to/package.udrv --json
```

Збирання окремого Windows executable через PyInstaller:

```sh
python -m pip install --upgrade pyinstaller
python -m PyInstaller --noconfirm --clean --onefile --windowed --name OPlague oplague_app.py
```

## Інтеграція та докази

- [Індекс документації](docs/README.md) · [Інтеграція runtime Reaper](docs/REAPER_RUNTIME_INTEGRATION.md)
- [Інтеграція DuckOS та Mora](https://github.com/Ivan-VHS/DuckOS/blob/main/docs/GAMING_PERFORMANCE_INTEGRATION.md)
- [Спільні стандарти екосистеми](https://github.com/Ivan-VHS/DuckOS/blob/main/docs/SHARED_STANDARDS.md)
- [Сходи еволюції проєкту](docs/PROJECT_LADDER.md) · [Поточний рівень](.github/project-ladder.v1.json)

Поточну поведінку визначають вихідний код, схеми й тести. Станція не прошиває пристрої, не встановлює драйвери й не сертифікує сумісність автоматично.

[Внесок у проєкт](CONTRIBUTING.md) · [Безпека](SECURITY.md) · [Apache-2.0](LICENSE)
