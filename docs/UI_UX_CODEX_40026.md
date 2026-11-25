# OPlague — UI/UX implementation profile

**Shared standard:** [UI/UX Codex 40026](https://github.com/Ivan-VHS/DuckOS/blob/main/docs/UI_UX_CODEX_40026.md).

This file keeps only the OPlague workbench toolkit notes and implementation boundaries. The shared specification owns common interaction rules, accessibility budgets, theme/component contracts and the definition of done.

### OPlague — локальная реализация

- Инвентаризация, совместимость и доказательства остаются read-only по умолчанию; внешний вид не должен создавать впечатление, что драйвер уже установлен/изменён.
- Для отчётов, INF/архивов, хэшей и сведений устройства сохраняются моноширинные идентификаторы, копирование, время проверки и источник доказательства.
- Theme tokens проверяются на контраст, а статусы scan/compatible/warning/error различаются текстом и семантическим токеном.
- Motion никогда не задерживает перечисление устройств, хэширование, проверку границ архивов, построение отчёта и driver inspection.
- Никакой автоматический «ремонт» или изменение драйвера не запускается как визуальная реакция; последствия и ручное подтверждение остаются явными.
