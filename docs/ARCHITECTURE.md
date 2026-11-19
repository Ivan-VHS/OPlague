# Архитектура OPlague

## 1. Цели

1. Нативная оболочка отделена от аппаратных привилегий.
2. Единая доменная модель при независимых API каждой ОС.
3. Read-only discovery и диагностика до внедрения системных изменений.
4. Модули взаимодействуют через явные контракты.
5. Любая запись проходит policy gate, планирование, snapshot, подтверждение и verification.
6. Неизвестные данные и неподдерживаемые возможности представлены явно.

## 2. Слои

### Layer 1 — Operating System
Документированные API ОС: Windows SetupAPI, Configuration Manager, PnP, WMI/CIM и ETW; Linux sysfs, udev, ioctl и PipeWire; другие платформы — отдельные реализации. Kernel bridge — опциональный будущий компонент, не условие запуска UI.

### Layer 2 — Platform Service / Capability Broker
Привилегированная служба запускает только allowlisted операции. UI не получает прямой доступ к произвольным IOCTL, реестру, DriverStore или sysfs записи. Сервис проверяет SID/UID, полномочия, тип команды, аргументы и лимиты. В текущем срезе этот слой не реализован; desktop вызывает read-only provider напрямую.

### Layer 3 — Hardware Intelligence
Обнаружение, нормализация Hardware ID, инвентаризация, телеметрия, парсинг пакетов, топология и диагностика. Платформенные детали заканчиваются на границе адаптера.

### Layer 4 — Orchestration
Dependency Resolver, Compatibility Engine, UDB, Driver Lifecycle, Snapshot Manager, Policy Engine и журнал операций. Здесь формируются планы; привилегированная запись выполняется только через Layer 2.

### Layer 5 — Native Desktop Experience
Slint UI, Dashboard, Hardware Graph, Driver Vault, UDB Hub, Latency Lab, Time Duck, настройки, уведомления и системный трей. UI показывает возможности на основании capability discovery.

## 3. Текущий Cargo workspace

- apps/desktop: Slint UI и точка входа.
- crates/oplague-core: платформонезависимые модели устройств, инвентаризации, оценка health и политики операций.
- crates/oplague-hardware: платформенные провайдеры; сейчас реализован read-only PCI/USB Linux sysfs.
- platform/windows: будущая изоляция Windows PnP/SetupAPI/ETW адаптеров.
- platform/linux: будущая изоляция udev/PipeWire и дополнительных sysfs адаптеров.

## 4. Модель домена

HardwareDevice содержит instance ID, friendly name, шину, аппаратные IDs, необязательную привязку драйвера и статус. SignatureState использует Verified/Invalid/Unknown; Unknown никогда не интерпретируется как Verified.

InventorySnapshot содержит платформу, поддержку провайдера, полноту покрытия, устройства и предупреждения. Coverage — свойство контракта провайдера, а не эвристика по количеству устройств.

HealthScore рассчитывается только из полного непустого набора HealthEvidence. Неизвестный результат возвращается как None.

OperationKind::policy() описывает базовые требования безопасности. Это не механизм исполнения: сервис обязан повторно проверить полномочия и политику.

## 5. Потоки данных

### Discovery
UI command → oplague-hardware::discover() → platform provider → normalized InventorySnapshot → oplague-core → UI model.

### Driver package analysis
Выбранный файл → лимиты размера/типа → изолированная распаковка → static parser → package manifest → hash/signature verification → dependency and compatibility report. Произвольный installer не запускается.

### Driver mutation (future)
User intent → immutable operation plan → compatibility validation → snapshot → exact confirmation → privileged service → OS API → post-operation verification → append-only audit event. При отказе preflight запись не выполняется.

### UDB command (future)
UI control → adapter capability lookup → validated command schema → broker policy → adapter → device response/event → journal. Нет capability — нет control.

## 6. IPC контракт

Целевой транспорт: Named Pipes на Windows и Unix Domain Sockets на Linux. Формат — FlatBuffers или другой версионируемый бинарный контракт после измерения нагрузки. Обязательные поля команды: protocol_version, request_id, operation, target_id, arguments, deadline, user_intent. Контекст доверия определяется каналом/токеном ОС, а не полем клиента.

События: device.discovered, device.removed, inventory.completed, operation.progress, operation.completed, operation.rejected, telemetry.sample, diagnostic.finding. Все события имеют timestamp, source/provider, schema version и correlation ID.

## 7. Локальное хранение

SQLite + WAL — целевая база. Таблицы: devices, device_ids, driver_packages, driver_bindings, adapter_capabilities, profiles, snapshots, snapshot_entries, operations, diagnostic_sessions, diagnostic_events, audit_events и schema_migrations. Миграции версионируются. Дамп не содержит содержимое исходных пакетов или секреты. Резервная копия проверяется восстановлением тестового набора.

## 8. Управление состояниями

Операция имеет состояния Draft → Preflight → AwaitingConfirmation → Running → Verifying → Succeeded. Дополнительные терминальные состояния: Rejected, Cancelled, Failed, RollbackRequired, RolledBack. UI не выставляет состояние самостоятельно; каждое изменение подтверждает исполнитель с журналом события.

## 9. Ограничение ресурсов

- Период опроса задаётся провайдером и профилем; нет агрессивного бесконечного polling.
- Телеметрия хранится в кольцевых буферах с лимитом времени/байтов.
- Парсеры ограничивают размер файла, глубину архивов, число записей и время анализа.
- IPC payloads ограничены по размеру.
- Тяжёлая обработка не выполняется в UI event loop.
- Любой latency граф показывает sample rate, потери данных и временную базу.

## 10. Правила модульности

- Core не знает о Slint, Windows registry, udev или путях платформы.
- Hardware provider не выполняет установку/удаление.
- UI не формирует произвольные системные команды.
- UDB adapter объявляет capabilities и ограниченный набор команд.
- Security policy не зависит от Duck Agent.
- Snapshot Engine не заявляет восстановление всей ОС, если снимок содержит только драйверный слой.
