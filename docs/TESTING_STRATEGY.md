# Testing Strategy

## 1. Test pyramid

- Unit tests: domain rules, parser boundaries, hash/identity normalization, health scoring и operation policy.
- Provider tests: sysfs fixtures, Windows API wrappers и capability manifests.
- Integration tests: inventory to UI model, package analysis, storage migrations, IPC authorization and operation state machine.
- Hardware tests: curated device matrix с OS build, firmware, driver version and evidence.
- Security tests: archive bombs, malformed INF, path traversal, invalid signatures, tampering, IPC replay и privilege escalation attempts.
- UI tests: navigation, empty/error/unknown states, keyboard operation, scaling и accessibility.
- Regression tests: каждый исправленный issue добавляет минимальное воспроизведение.

## 2. Required CI commands

~~~bash
cargo fmt --all -- --check
cargo test --workspace
cargo clippy --workspace --all-targets -- -D warnings
cargo build -p oplague-desktop
~~~

## 3. Evidence model

Каждый hardware-specific тест записывает:
- OS name/build and architecture;
- device vendor/product/revision или anonymized fixture;
- driver provider/version/date;
- firmware, если доступна;
- adapter version and capability set;
- steps, expected result and actual result;
- логи с удалёнными секретами и персональными путями.

Тест, который нельзя запустить из-за отсутствия hardware, имеет статус not_run, а не passed.

## 4. Property and boundary tests

- Hardware ID parsers отклоняют malformed и oversized values.
- Health score никогда не превышает 100 и не рассчитывается без полного evidence.
- Operation policy всегда ставит gates для write операций.
- Snapshot hash mismatch блокирует restore.
- Archive extraction не может писать вне sandbox.
- IPC проверяет protocol version, command enum, length и authorization.
- Event queues и telemetry buffers остаются bounded.

## 5. GUI и platform validation

CI compilation не заменяет запуск desktop на Windows и Linux. Release candidates требуют native launch smoke tests, resize, HiDPI scaling, display sleep/resume, hot-plug, device removal during scan и graceful provider failure.
