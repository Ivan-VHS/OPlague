# Roadmap and Implementation Status

Статус относится к коду в репозитории. Спецификация функции сама по себе не означает её реализацию.

## Milestone 0 — Repository foundation

**Статус: реализовано в текущей ветке**
- Cargo workspace, Rust toolchain pin, Slint desktop target.
- Tri-Color Duck UI shell и sidebar.
- Shared domain model.
- Linux PCI/USB sysfs read-only scan.
- Health scoring contract with unknown-on-incomplete evidence.
- Operation safety policy contract.
- Unit tests and CI workflow.
- Product, architecture, security, UDB and functional documentation.

## Milestone 1 — Windows read-only inventory

**Статус: следующий приоритет**
- SetupAPI/Configuration Manager provider.
- Friendly name, instance ID, Hardware IDs, Compatible IDs, class GUID, problem code.
- Driver binding/provider/version/date.
- Device add/remove events.
- Provider coverage manifest.
- Windows integration tests on supported runner/hardware fixtures.

**Acceptance:** повторяемый read-only inventory, без вызова install/remove и без повышения прав там, где они не нужны.

## Milestone 2 — Hardware Graph and Driver Vault

- Graph node/edge model and Inspector Drawer.
- Driver Store metadata reader.
- Local package import.
- SHA-256 and catalog signature verification.
- INF parser with size/count/path limits.
- Compatibility matching.

**Acceptance:** package report воспроизводит source hash и предоставляет evidence для каждого сопоставленного устройства.

## Milestone 3 — Service and IPC

- Windows service prototype.
- Named Pipe authentication and ACL.
- Versioned request/event schema.
- Allowlist, capability and operation journal.
- No arbitrary IOCTL surface.

**Acceptance:** тесты доказывают, что неавторизованный клиент не может вызвать привилегированную операцию.

## Milestone 4 — Time Duck and controlled lifecycle

- Driver package backup/export.
- Snapshot manifest and integrity verification.
- Transaction preflight.
- User confirmation bound to plan hash.
- Install/restore via documented OS APIs.
- Post-operation verification and rollback.

**Acceptance:** интеграционные тесты демонстрируют успех, отказ, прерывание и восстановление в disposable test environments.

## Milestone 5 — Latency Lab

- ETW session lifecycle and bounded buffers.
- ISR/DPC event model.
- Driver attribution with call stacks where available.
- Timeline UI, export and privacy redaction.

**Acceptance:** тестовые traces дают воспроизводимые отчёты, потерянные события видны, неподтверждённая атрибуция не выдаётся.

## Milestone 6 — UDB adapters

1. HID inventory, затем поддерживаемые операции конфигурации.
2. Audio endpoint and route control.
3. RGB adapters для выбранных проверенных устройств.
4. Cooling/sensors adapters с fail-safe ограничениями.
5. Profile manager и on-board memory capabilities.

**Acceptance:** каждая поддерживаемая модель/версия имеет conformance fixtures и явные capability declarations.

## Milestone 7 — Duck Agent and desktop polish

- Diagnostics wizard.
- Evidence-backed recommendations.
- System tray and notification policy.
- Full icon library and mascot motion.
- Accessibility and localization.
- UI automation tests.

## Milestone 8 — Linux expansion

- udev event provider.
- PipeWire audio.
- hidraw adapter contracts.
- distro/kernel compatibility matrix.

macOS остаётся вне committed support до проверки IOKit scope и продуктовой ценности.

## Release gate

Функция не помечается stable до code review, tests, security checks, supported-platform smoke test, signed packaging и reproducible build evidence. RAM, CPU idle, startup и FPS — измеряемые targets, не гарантия; для каждого нужны методика и tolerance.
