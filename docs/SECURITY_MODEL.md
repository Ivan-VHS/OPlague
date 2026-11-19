# OPlague Security Model

## 1. Границы доверия

1. UI process — недоверенный клиент с обычными правами пользователя.
2. Local service — привилегированный доверенный компонент с минимальным allowlist.
3. Platform APIs — системная граница, результат которой всё равно проверяется.
4. Driver packages, INF, archive metadata и device strings — недоверенный ввод.
5. UDB plugins/adapters — отдельные capability principals.
6. Snapshot store — критичные локальные данные, защищаемые ACL и integrity hashes.

## 2. Базовые правила

- Принцип наименьших привилегий.
- Read-only по умолчанию.
- Нет произвольного command execution из UI.
- Нет запуска поставляемых installer EXE при статическом анализе.
- Ограниченные архивы и парсеры.
- Установка/удаление только через документированный API ОС.
- Проверка подписей и хэшей до применения.
- Снимок до записи; проверка снимка до операции.
- Точное согласие пользователя на конкретный change set.
- Журналирование без секретов.
- Доступ к сети — только для явно инициированного получения пакета и с указанием источника.

## 3. Privileged operation gate

Сервис проверяет каждый запрос независимо от UI:
- аутентифицированный локальный клиент и его SID/UID;
- версия протокола и schema;
- request ID / replay protection;
- допустимый operation enum;
- target ID существует и совпадает с preflight;
- package hash не изменился с момента проверки;
- elevation/role;
- compatibility status;
- snapshot ID и успешная integrity check;
- user approval token, связанный с точным plan hash;
- timeout и ресурсные лимиты.

Запрос отклоняется при любом несоответствии. UI не может повышать уровень доверия простым флагом.

## 4. Kernel components

Опциональный filter driver не входит в ранний MVP. Он может появиться только при доказанной невозможности нужной функции через user-mode API. Требования: минимальный код, отдельная подпись, совместимость с Secure Boot/HVCI, threat model, fuzzing, Verifier/driver tests, crash dump analysis, независимое выключение и официальная процедура удаления.

Не отключать Secure Boot, Driver Signature Enforcement, HVCI или другие защиты ради продукта.

## 5. Package handling

- Проверять zip/cab expansion ratio, file count, path traversal, symlinks и вложенность.
- Отклонять абсолютные пути, .., device paths и недопустимые имена.
- Временный каталог — уникальный, с ACL, автоматической очисткой и дисковым лимитом.
- Не доверять расширению файла и имени издателя.
- Не отображать внутренние абсолютные пути в отчётах по умолчанию.
- Отдельно хранить оригинал и modified artifacts.
- Подписывать и проверять пакет по платформенным правилам.

## 6. Privacy

- Локальная обработка по умолчанию.
- Не отправлять список оборудования/Hardware IDs без явного согласия.
- Диагностические отчёты проходят preview и redaction.
- Не экспортировать токены, ключи, серийные номера и пользовательские пути без необходимости.
- Retention для ETW sessions и логов ограничен.

## 7. Recovery and failure

- Никакая операция не считается успешной без post-check.
- Потеря IPC во время write не означает отмену OS операции; сервис восстанавливает состояние из operation journal.
- Crash recovery не должна повторять неидемпотентную команду слепо.
- Snapshot имеет хэш и manifest; restore — отдельный plan.
- Если автоматический rollback не поддерживается, UI сообщает ManualRecoveryRequired и предоставляет диагностику.

## 8. Security acceptance

Перед включением системной записи обязательны threat model, unit/property/fuzz tests парсеров, тесты path traversal и archive bombs, ACL/IPC tests, тесты подписи и tampering, аварийное завершение сервиса, проверка восстановления, audit log review и подпись релизных бинарников.
