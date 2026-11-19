# Unified Driver Bus (UDB) — Specification

## 1. Миссия

UDB предоставляет единый внутренний контракт для разных производителей и классов периферии. Он устраняет дублирование пользовательского интерфейса и моделей профилей, но не скрывает реальные ограничения протоколов или драйверов.

## 2. Состав адаптера

Каждый адаптер публикует:
- adapter_id, vendor, version и contract version;
- поддерживаемые ОС и архитектуры;
- match rules (VID/PID, Hardware ID, interface class и т.п.);
- capabilities и их read/write semantics;
- диапазоны, единицы измерения и допустимые значения;
- модель ошибок и timeout;
- ограничения эксклюзивного доступа;
- permissions required;
- тестовые fixtures и evidence of hardware validation.

## 3. Общий жизненный цикл

Discovered → Matched → CapabilityNegotiation → Ready/ReadOnly/Unsupported → Disconnected.

Адаптер может быть read-only. Запись на устройство требует индивидуальной capability, ограниченного аргумента и повторной проверки безопасности.

## 4. Домены

### HID / Input Hub
- Идентификация мышей, клавиатур, gamepad и контроллеров.
- Polling rate и DPI только при поддержке protocol/API.
- Кривые отклика и макросы с preview и ограничениями.
- On-board memory — capability-specific.
- Не отправлять произвольные HID reports без схемы устройства.

### Audio Hub
- Enumerate endpoints через системный audio API.
- Route/volume/device selection через API ОС.
- WASAPI/ASIO — раздельные adapter contracts.
- ASIO интеграция не заменяет драйвер производителя.
- Любое latency значение сопровождается методикой измерения.

### RGB Hub
- Обнаружить контроллер и доступные зоны.
- Нормализованные эффекты и палитры.
- Vendor protocol adapters и тестовые профили.
- Не открывать конкурентный доступ к SMBus/EC и не блокировать vendor service автоматически.

### Cooling / Sensor Hub
- Датчики с units, диапазонами и sampling interval.
- PWM write только для проверенных контроллеров с аппаратной поддержкой.
- Защитные ограничения скорости вентилятора и аварийного режима.
- При потере связи — возврат к безопасному состоянию, если оно документировано.

### Power Hub
- Показывать поддерживаемые ACPI/OS power states.
- Не менять voltage, clock, BIOS/UEFI или power limits как универсальную оптимизацию.
- Конфигурации питания требуют отдельной политики и восстановления.

### Device Profiles
Профиль хранит типизированные желаемые значения, adapter/capability IDs, schema version, target device match и timestamp. При переключении сначала проверяется, какие настройки доступны на устройстве. Unsupported values пропускаются с понятным отчётом.

## 5. API и события

Целевые команды: get_capabilities, read_state, apply_profile, set_value, reset_to_default, subscribe_events и unsubscribe_events. Команды принимают typed values, target instance ID, deadline и operation ID. События: state_changed, device_removed, adapter_error и capability_changed.

## 6. Безопасность и совместимость

- Никакой универсальной «перехватить весь драйвер» магии.
- Адаптер не получает общие привилегии ОС; ему выдаются точные операции.
- Разрешения выдаются по capabilities, а не по имени плагина.
- Адаптеры с kernel access выносятся в отдельный подписанный компонент и проходят отдельный аудит.
- Неизвестный vendor protocol работает в read-only исследовательском режиме.
- Versioned contract и conformance tests обязательны.

## 7. Матрица готовности

Адаптер считается Experimental, пока не имеет подтверждённого оборудования и regression fixtures. Supported требует повторяемых тестов на заявленных моделях/firmware. Отсутствие адаптера не препятствует базовой инвентаризации.
